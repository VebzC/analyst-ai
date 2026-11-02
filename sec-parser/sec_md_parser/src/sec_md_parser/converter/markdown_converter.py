"""Markdown converter for SEC filings."""

from typing import Dict, List, Optional, Any, Tuple
import re
import json

from sec_md_parser.models.base import DocumentNode, XBRLFact

# Forward declaration for type hints
class DocumentTree:
    """Document tree model forward declaration for type hints."""
    root: DocumentNode


class MarkdownConverter:
    """Converter for SEC filing document trees to Markdown."""
    
    def __init__(self) -> None:
        """Initialize the markdown converter."""
        self.toc_entries = []
        self.section_level = 0
        self.include_xbrl_metadata = True
        self.include_financial_metadata = True
    
    def convert(self, document_tree: DocumentTree, include_xbrl: bool = True, 
                include_financial_metadata: bool = True) -> str:
        """
        Convert a document tree to Markdown.
        
        Args:
            document_tree: DocumentTree object to convert
            include_xbrl: Whether to include XBRL metadata in the Markdown
            include_financial_metadata: Whether to include financial metadata
            
        Returns:
            Markdown string representation of the document
        """
        self.toc_entries = []
        self.section_level = 0
        self.include_xbrl_metadata = include_xbrl
        self.include_financial_metadata = include_financial_metadata
        
        # Convert the document tree to Markdown
        markdown = self._convert_node(document_tree.root)
        
        # Add table of contents at the beginning if there are entries
        if self.toc_entries:
            toc = "# Table of Contents\n\n"
            for level, text, anchor in self.toc_entries:
                toc += "  " * (level - 1) + f"- [{text}](#{anchor})\n"
            
            # Add the TOC at the beginning of the document
            markdown = toc + "\n---\n\n" + markdown
        
        return markdown
    
    def _convert_node(self, node: DocumentNode, parent_level: int = 0) -> str:
        """
        Recursively convert a document node to Markdown.
        
        Args:
            node: DocumentNode to convert
            parent_level: Level of the parent section for heading level determination
            
        Returns:
            Markdown string for the node
        """
        if not node:
            return ""
        
        # Process the node based on its type
        if node.type == "document":
            return self._convert_document(node)
        elif node.type == "section":
            self.section_level = parent_level + 1
            return self._convert_section(node, self.section_level)
        elif node.type == "heading":
            level = min(parent_level + 1, 6)  # Markdown only supports h1-h6
            return self._convert_heading(node, level)
        elif node.type == "paragraph":
            return self._convert_paragraph(node)
        elif node.type == "table":
            return self._convert_table(node)
        elif node.type.startswith("table_"):
            # Table components are handled in the table conversion
            return ""
        elif node.type == "list":
            return self._convert_list(node)
        elif node.type == "list_item":
            return self._convert_list_item(node)
        else:
            # For unknown node types, recursively process children
            markdown = ""
            if node.content:
                markdown += node.content + "\n\n"
            
            for child in node.children:
                markdown += self._convert_node(child, parent_level)
            
            return markdown
    
    def _convert_document(self, node: DocumentNode) -> str:
        """Convert a document node to Markdown."""
        markdown = ""
        
        # Add document title if available
        if node.metadata and "title" in node.metadata:
            markdown += f"# {node.metadata['title']}\n\n"
            
            # Add to TOC
            self._add_toc_entry(1, node.metadata["title"])
        
        # Process children
        for child in node.children:
            markdown += self._convert_node(child, 1)  # Start at level 1
        
        return markdown
    
    def _convert_section(self, node: DocumentNode, level: int) -> str:
        """Convert a section node to Markdown."""
        markdown = ""
        
        # Process children
        for child in node.children:
            markdown += self._convert_node(child, level)
        
        # Add XBRL metadata if available and requested
        if self.include_xbrl_metadata and node.xbrl_facts and node.metadata.get('financial_section_type'):
            markdown += self._format_section_xbrl_facts(node)
        
        return markdown
    
    def _convert_heading(self, node: DocumentNode, level: int) -> str:
        """Convert a heading node to Markdown."""
        if not node.content:
            return ""
        
        # Create heading with appropriate level
        heading_md = "#" * level + f" {node.content}\n\n"
        
        # Add to TOC
        self._add_toc_entry(level, node.content)
        
        return heading_md
    
    def _convert_paragraph(self, node: DocumentNode) -> str:
        """Convert a paragraph node to Markdown."""
        if not node.content:
            return ""
        
        # Add XBRL metadata if available and requested
        xbrl_md = ""
        if self.include_xbrl_metadata and node.xbrl_facts:
            xbrl_md = self._format_xbrl_facts(node.xbrl_facts)
        
        return f"{node.content}\n\n{xbrl_md}"
    
    def _convert_table(self, node: DocumentNode) -> str:
        """Convert a table node to Markdown."""
        markdown = ""
        
        # Add table caption if available
        caption_node = next((child for child in node.children if child.type == "table_caption"), None)
        if caption_node and caption_node.content:
            markdown += f"**{caption_node.content}**\n\n"
            
            # Add to TOC if it's a significant table
            if node.metadata.get('is_financial_table', False):
                self._add_toc_entry(self.section_level + 1, caption_node.content)
        
        # Check if we have structured table data in metadata
        if 'structure' in node.metadata and node.metadata['structure']:
            # Use the structured data for better table representation
            return markdown + self._convert_structured_table(node)
        
        # Find header and body nodes
        header_node = next((child for child in node.children if child.type == "table_header"), None)
        body_node = next((child for child in node.children if child.type == "table_body"), None)
        
        # Extract header rows
        header_rows = []
        if header_node:
            for row_node in header_node.children:
                if row_node.type == "table_header_row" or row_node.type == "table_header_rows":
                    if row_node.children:
                        header_row = []
                        for cell_node in row_node.children:
                            if hasattr(cell_node, "content") and cell_node.content:
                                header_row.append(cell_node.content)
                            else:
                                header_row.append("")
                        header_rows.append(header_row)
        
        # Extract body rows
        body_rows = []
        if body_node:
            for row_node in body_node.children:
                if row_node.type == "table_body_row" or row_node.type == "table_body_rows":
                    if row_node.children:
                        body_row = []
                        for cell_node in row_node.children:
                            if hasattr(cell_node, "content") and cell_node.content:
                                body_row.append(cell_node.content)
                            else:
                                body_row.append("")
                        body_rows.append(body_row)
        
        # Combine header and body rows
        all_rows = header_rows + body_rows
        if not all_rows:
            return markdown
        
        # Determine the number of columns
        num_cols = max(len(row) for row in all_rows)
        
        # Create the Markdown table
        # Header row
        if header_rows:
            # Use the last header row as the actual header
            header = header_rows[-1]
            # Ensure header has enough columns
            while len(header) < num_cols:
                header.append("")
            
            markdown += "| " + " | ".join(header) + " |\n"
            markdown += "| " + " | ".join(["---"] * num_cols) + " |\n"
        else:
            # Create an empty header row if none exists
            markdown += "| " + " | ".join([""] * num_cols) + " |\n"
            markdown += "| " + " | ".join(["---"] * num_cols) + " |\n"
        
        # Body rows
        for row in body_rows:
            # Ensure row has enough columns
            while len(row) < num_cols:
                row.append("")
            
            # Escape pipe characters in cell content
            escaped_row = [cell.replace("|", "\\|") for cell in row]
            
            markdown += "| " + " | ".join(escaped_row) + " |\n"
        
        markdown += "\n"
        
        # Add financial metadata if available and requested
        if self.include_financial_metadata and node.metadata and "is_financial_table" in node.metadata:
            markdown += "<details>\n"
            markdown += "<summary>Financial Table Metadata</summary>\n\n"
            markdown += "```json\n"
            
            # Generate a clean metadata representation (without circular references)
            clean_metadata = {
                'is_financial_table': node.metadata.get('is_financial_table', False),
                'table_type': node.metadata.get('table_type', 'general_table'),
                'rows': node.metadata.get('rows', 0),
                'cols': node.metadata.get('cols', 0)
            }
            
            markdown += json.dumps(clean_metadata, indent=2)
            markdown += "\n```\n\n"
            markdown += "</details>\n\n"
        
        # Add XBRL metadata if available and requested
        if self.include_xbrl_metadata and node.xbrl_facts:
            markdown += self._format_xbrl_facts(node.xbrl_facts)
        
        return markdown
    
    def _convert_structured_table(self, node: DocumentNode) -> str:
        """
        Convert a table node with structured data to Markdown.
        
        Args:
            node: DocumentNode representing a table with structured data
            
        Returns:
            Markdown representation of the structured table
        """
        structure = node.metadata['structure']
        if not structure:
            return ""
        
        # Extract header rows and body rows
        header_rows = []
        body_rows = []
        
        # Identify header rows
        for row in structure:
            if any(cell.get('is_header', False) for cell in row):
                header_rows.append(row)
            else:
                body_rows.append(row)
        
        # If no explicit header rows, but first row looks like a header
        if not header_rows and body_rows and all(cell.get('content') and cell.get('content').strip() for cell in body_rows[0]):
            header_rows = [body_rows[0]]
            body_rows = body_rows[1:]
        
        # Determine the number of columns
        num_cols = max(len(row) for row in structure) if structure else 0
        
        # Generate markdown table
        markdown = ""
        
        # Header row
        if header_rows:
            # Use the last header row as the actual header
            header = [cell.get('content', '') for cell in header_rows[-1]]
            # Ensure header has enough columns
            while len(header) < num_cols:
                header.append("")
            
            markdown += "| " + " | ".join(header) + " |\n"
            markdown += "| " + " | ".join(["---"] * num_cols) + " |\n"
        else:
            # Create an empty header row if none exists
            markdown += "| " + " | ".join([""] * num_cols) + " |\n"
            markdown += "| " + " | ".join(["---"] * num_cols) + " |\n"
        
        # Body rows
        for row in body_rows:
            # Extract cell contents
            row_cells = [cell.get('content', '') for cell in row]
            
            # Ensure row has enough columns
            while len(row_cells) < num_cols:
                row_cells.append("")
            
            # Escape pipe characters in cell content
            escaped_row = [str(cell).replace("|", "\\|") for cell in row_cells]
            
            markdown += "| " + " | ".join(escaped_row) + " |\n"
        
        markdown += "\n"
        
        return markdown
    
    def _convert_list(self, node: DocumentNode) -> str:
        """Convert a list node to Markdown."""
        markdown = ""
        
        # Process list items
        for child in node.children:
            markdown += self._convert_node(child, self.section_level)
        
        return markdown + "\n"
    
    def _convert_list_item(self, node: DocumentNode) -> str:
        """Convert a list item node to Markdown."""
        if not node.content and not node.children:
            return ""
        
        # Determine if this is an ordered or unordered list item
        list_type = node.attributes.get("list_type", "unordered")
        bullet = "1." if list_type == "ordered" else "-"
        
        markdown = f"{bullet} "
        
        # Add content
        if node.content:
            markdown += node.content
        
        # Process children
        has_nested_list = False
        for child in node.children:
            if child.type == "list":
                has_nested_list = True
                # Add nested list with indentation
                nested_list = self._convert_node(child, self.section_level)
                nested_list = "\n" + "\n".join(f"  {line}" for line in nested_list.split("\n"))
                markdown += nested_list
        
        if not has_nested_list:
            markdown += "\n"
        
        return markdown
    
    def _format_xbrl_facts(self, facts: List[XBRLFact]) -> str:
        """Format XBRL facts as Markdown."""
        if not facts:
            return ""
        
        markdown = "<details>\n"
        markdown += "<summary>XBRL Metadata</summary>\n\n"
        
        # Group facts by context
        facts_by_context = {}
        for fact in facts:
            context = fact.context_ref or "unknown"
            if context not in facts_by_context:
                facts_by_context[context] = []
            facts_by_context[context].append(fact)
        
        # Format facts as tables by context
        for context, context_facts in facts_by_context.items():
            if context != "unknown":
                markdown += f"**Context: {context}**\n\n"
            
            # Create a table for the facts
            markdown += "| Name | Value | Unit | Period |\n"
            markdown += "| ---- | ----- | ---- | ------ |\n"
            
            for fact in context_facts:
                name = fact.name
                value = fact.value
                unit = fact.unit_ref or ""
                period = fact.period or ""
                
                # Escape pipe characters
                name = str(name).replace("|", "\\|")
                value = str(value).replace("|", "\\|")
                unit = str(unit).replace("|", "\\|")
                period = str(period).replace("|", "\\|")
                
                markdown += f"| {name} | {value} | {unit} | {period} |\n"
            
            markdown += "\n"
        
        markdown += "</details>\n\n"
        
        return markdown
    
    def _format_section_xbrl_facts(self, node: DocumentNode) -> str:
        """Format XBRL facts for a financial section."""
        if not node.xbrl_facts:
            return ""
        
        section_type = node.metadata.get('financial_section_type', '')
        if not section_type:
            return ""
        
        markdown = "<details>\n"
        markdown += f"<summary>Financial Data: {section_type.replace('_', ' ').title()}</summary>\n\n"
        
        # Create a table for the facts
        markdown += "| Name | Value | Unit | Period |\n"
        markdown += "| ---- | ----- | ---- | ------ |\n"
        
        for fact in node.xbrl_facts:
            name = fact.name
            value = fact.value
            unit = fact.unit_ref or ""
            period = fact.period or ""
            
            # Escape pipe characters
            name = str(name).replace("|", "\\|")
            value = str(value).replace("|", "\\|")
            unit = str(unit).replace("|", "\\|")
            period = str(period).replace("|", "\\|")
            
            markdown += f"| {name} | {value} | {unit} | {period} |\n"
        
        markdown += "\n</details>\n\n"
        
        return markdown
    
    def _add_toc_entry(self, level: int, text: str) -> None:
        """
        Add an entry to the table of contents.
        
        Args:
            level: Heading level
            text: Heading text
        """
        # Create an anchor from the text
        anchor = text.lower()
        anchor = re.sub(r'[^\w\s-]', '', anchor)  # Remove special characters
        anchor = re.sub(r'\s+', '-', anchor)      # Replace spaces with hyphens
        
        self.toc_entries.append((level, text, anchor))
