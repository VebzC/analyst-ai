"""Markdown generator functions for SEC filings."""

from typing import Dict, List, Optional, Any, Union
import yaml
import json

from sec_md_parser.models.document import DocumentNode


def generate_markdown_table(structure):
    """
    Generate a Markdown table from a table structure.
    
    Args:
        structure: List of rows, each containing a list of cells
        
    Returns:
        Markdown table representation
    """
    if not structure:
        return ""
    
    # Extract header rows and body rows
    header_rows = []
    body_rows = []
    
    # Identify header rows
    for row in structure:
        if any(isinstance(cell, dict) and cell.get('is_header', False) for cell in row):
            header_rows.append(row)
        else:
            body_rows.append(row)
    
    # If no explicit header rows, but first row looks like a header
    if not header_rows and body_rows:
        first_row = body_rows[0]
        if all(isinstance(cell, dict) and cell.get('content') and cell.get('content').strip() 
              for cell in first_row if isinstance(cell, dict)):
            header_rows = [first_row]
            body_rows = body_rows[1:]
    
    # Determine the number of columns
    num_cols = max(len(row) for row in structure if row) if structure else 0
    
    # Generate markdown table
    markdown = ""
    
    # Header row
    if header_rows:
        # Use the last header row as the actual header
        header = []
        for cell in header_rows[-1]:
            if isinstance(cell, dict):
                header.append(cell.get('content', ''))
            else:
                header.append('')
        
        # Ensure header has enough columns
        while len(header) < num_cols:
            header.append("")
        
        # Escape pipe characters
        header = [str(cell).replace("|", "\\|") for cell in header]
        
        markdown += "| " + " | ".join(header) + " |\n"
        markdown += "| " + " | ".join(["---"] * num_cols) + " |\n"
    else:
        # Create an empty header row if none exists
        markdown += "| " + " | ".join([""] * num_cols) + " |\n"
        markdown += "| " + " | ".join(["---"] * num_cols) + " |\n"
    
    # Body rows
    for row in body_rows:
        # Extract cell contents
        row_cells = []
        for cell in row:
            if isinstance(cell, dict):
                row_cells.append(cell.get('content', ''))
            else:
                row_cells.append('')
        
        # Ensure row has enough columns
        while len(row_cells) < num_cols:
            row_cells.append("")
        
        # Escape pipe characters in cell content
        escaped_row = [str(cell).replace("|", "\\|") for cell in row_cells]
        
        markdown += "| " + " | ".join(escaped_row) + " |\n"
    
    return markdown


def generate_markdown_from_tree(node, level=0, metadata_format='yaml'):
    """
    Generate Markdown content from document tree.
    
    Args:
        node: Document node to convert
        level: Current heading level (0 for document root)
        metadata_format: Format for metadata sections ('yaml' or 'json')
        
    Returns:
        Markdown string representation of the node and its children
    """
    md_content = []
    
    # Handle document node (root)
    if hasattr(node, 'node_type') and node.node_type == "document":
        # Add document title
        if hasattr(node, 'title') and node.title:
            md_content.append(f"# {node.title}\n")
            
        # Add document metadata
        if hasattr(node, 'metadata') and node.metadata:
            md_content.append("---")
            if metadata_format == 'yaml':
                for key, value in node.metadata.items():
                    if isinstance(value, dict):
                        md_content.append(f"{key}:")
                        for k, v in value.items():
                            md_content.append(f"  {k}: {v}")
                    else:
                        md_content.append(f"{key}: {value}")
            elif metadata_format == 'json':
                md_content.append(json.dumps(node.metadata, indent=2))
            md_content.append("---\n")
    
    # For compatibility with the existing DocumentNode class
    node_type = getattr(node, 'node_type', getattr(node, 'type', None))
            
    # Handle section nodes
    if node_type == "section":
        # Add section heading with appropriate level
        heading_level = '#' * (level + 1)
        title = getattr(node, 'title', getattr(node, 'content', 'Section'))
        md_content.append(f"{heading_level} {title}\n")
        
    # Handle paragraph nodes
    elif node_type == "paragraph":
        # Add paragraph text
        content = getattr(node, 'content', None)
        if content:
            md_content.append(f"{content}\n")
            
        # Add XBRL facts as metadata
        xbrl_facts = getattr(node, 'xbrl_facts', [])
        if xbrl_facts:
            for fact in xbrl_facts:
                fact_name = fact.name if hasattr(fact, 'name') else fact.get('name', '')
                context_ref = fact.context_ref if hasattr(fact, 'context_ref') else fact.get('contextRef', '')
                md_content.append(f"{{: xbrl-fact=\"{fact_name}\" context=\"{context_ref}\" }}\n")
                
    # Handle table nodes
    elif node_type == "table":
        # Add table title if available
        title = getattr(node, 'title', None)
        if not title:
            caption_node = next((child for child in getattr(node, 'children', []) 
                             if getattr(child, 'type', None) == "table_caption"), None)
            if caption_node:
                title = getattr(caption_node, 'content', None)
                
        if title:
            md_content.append(f"**{title}**\n")
            
        # Generate markdown table from structure
        metadata = getattr(node, 'metadata', {})
        if 'structure' in metadata:
            table_md = generate_markdown_table(metadata['structure'])
            md_content.append(table_md)
            md_content.append("\n")
            
        # Add table metadata
        statement_type = metadata.get('financial_statement_type')
        if statement_type:
            md_content.append(f"> Financial Statement Type: {statement_type}\n")
            
        # Add calculation relationships if available
        calc_relationships = metadata.get('calculation_relationships')
        if calc_relationships:
            md_content.append("<details>")
            md_content.append("<summary>Calculation Relationships</summary>\n")
            md_content.append("```yaml")
            if metadata_format == 'yaml':
                for calc_name, calc_info in calc_relationships.items():
                    md_content.append(f"{calc_name}:")
                    for k, v in calc_info.items():
                        if isinstance(v, dict):
                            md_content.append(f"  {k}:")
                            for k2, v2 in v.items():
                                md_content.append(f"    {k2}: {v2}")
                        else:
                            md_content.append(f"  {k}: {v}")
            elif metadata_format == 'json':
                md_content.append(json.dumps(calc_relationships, indent=2))
            md_content.append("```")
            md_content.append("</details>\n")
            
    # Handle heading nodes
    elif node_type == "heading":
        # Add heading with appropriate level
        heading_level = '#' * (level + 1)
        content = getattr(node, 'content', 'Heading')
        md_content.append(f"{heading_level} {content}\n")
            
    # Process children recursively
    children = getattr(node, 'children', [])
    for child in children:
        child_md = generate_markdown_from_tree(child, level + 1, metadata_format)
        md_content.append(child_md)
        
    return "\n".join(md_content)


def generate_markdown_document(document_tree, include_xbrl=True, include_financial_metadata=True, 
                              metadata_format='yaml'):
    """
    Generate complete Markdown document from a document tree.
    
    Args:
        document_tree: The document tree to convert
        include_xbrl: Whether to include XBRL metadata
        include_financial_metadata: Whether to include financial metadata
        metadata_format: Format for metadata sections ('yaml' or 'json')
        
    Returns:
        Complete Markdown document
    """
    # Generate the main content
    md_content = generate_markdown_from_tree(document_tree.root, 0, metadata_format)
    
    # Add document info
    title = getattr(document_tree, 'title', None)
    if title:
        md_content = f"# {title}\n\n" + md_content
    
    # Add XBRL summary if requested
    if include_xbrl:
        xbrl_facts = getattr(document_tree, 'xbrl_facts', [])
        if xbrl_facts:
            md_content += "\n\n## XBRL Facts Summary\n\n"
            md_content += "<details>\n"
            md_content += "<summary>XBRL Facts Summary</summary>\n\n"
            md_content += f"Total XBRL Facts: {len(xbrl_facts)}\n\n"
            # Add a sample of XBRL facts
            if xbrl_facts:
                md_content += "| Name | Value | Context | Unit |\n"
                md_content += "| ---- | ----- | ------- | ---- |\n"
                for fact in xbrl_facts[:10]:  # Show first 10 facts
                    name = fact.name if hasattr(fact, 'name') else fact.get('name', '')
                    value = fact.value if hasattr(fact, 'value') else fact.get('value', '')
                    context = fact.context_ref if hasattr(fact, 'context_ref') else fact.get('contextRef', '')
                    unit = fact.unit_ref if hasattr(fact, 'unit_ref') else fact.get('unitRef', '')
                    md_content += f"| {name} | {value} | {context} | {unit} |\n"
                if len(xbrl_facts) > 10:
                    md_content += "| ... | ... | ... | ... |\n"
            md_content += "</details>\n"
    
    # Add financial metadata summary if requested
    if include_financial_metadata:
        # Check if we have financial statement identification data
        financial_statements = {}
        for node in document_tree.find_nodes_by_type("table"):
            if node.metadata.get('financial_statement_type'):
                statement_type = node.metadata['financial_statement_type']
                if statement_type not in financial_statements:
                    financial_statements[statement_type] = []
                financial_statements[statement_type].append(node)
        
        if financial_statements:
            md_content += "\n\n## Financial Statements Summary\n\n"
            for statement_type, tables in financial_statements.items():
                md_content += f"### {statement_type.replace('_', ' ').title()}\n\n"
                md_content += f"Found {len(tables)} tables of type '{statement_type}'\n\n"
    
    return md_content 