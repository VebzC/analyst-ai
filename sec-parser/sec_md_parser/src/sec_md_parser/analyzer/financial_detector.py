"""Financial structure detector for SEC filings."""

from typing import Dict, List, Optional, Any, Set
from bs4 import BeautifulSoup
import re

from sec_md_parser.models.document import DocumentNode, DocumentTree


class FinancialDetector:
    """Detector for financial structures in SEC filings."""
    
    def __init__(self) -> None:
        """Initialize the financial detector."""
        # Common financial statement section titles
        self.balance_sheet_indicators = {
            'balance sheet', 'statement of financial position', 'consolidated balance',
            'assets', 'liabilities', 'stockholders equity', 'shareholders equity'
        }
        
        self.income_statement_indicators = {
            'income statement', 'statement of operations', 'statement of earnings',
            'consolidated income', 'consolidated earnings', 'statement of comprehensive income',
            'profit and loss', 'results of operations'
        }
        
        self.cash_flow_indicators = {
            'cash flow', 'statement of cash flows', 'cash flows',
            'operating activities', 'investing activities', 'financing activities'
        }
        
        self.notes_indicators = {
            'notes to', 'financial statement', 'notes to consolidated', 
            'footnotes', 'accounting policies'
        }
    
    def detect_financial_sections(self, document_tree: DocumentTree) -> Dict[str, List[str]]:
        """
        Detect financial sections in the document tree.
        
        Args:
            document_tree: DocumentTree object representing the document
            
        Returns:
            Dictionary mapping section types to lists of node IDs
        """
        sections = {
            'balance_sheet': [],
            'income_statement': [],
            'cash_flow': [],
            'notes': [],
            'other_financial': []
        }
        
        # Traverse the tree to find financial sections
        self._traverse_for_financial_sections(document_tree.root, sections)
        
        return sections
    
    def _traverse_for_financial_sections(self, node: DocumentNode, sections: Dict[str, List[str]]) -> None:
        """
        Recursively traverse the document tree to find financial sections.
        
        Args:
            node: Current node in the tree
            sections: Dictionary to populate with financial section IDs
        """
        # Check if this node is a heading or table that might indicate a financial section
        if node.type in ('heading', 'table_caption') and node.content:
            content_lower = node.content.lower()
            
            if any(indicator in content_lower for indicator in self.balance_sheet_indicators):
                sections['balance_sheet'].append(node.id)
            elif any(indicator in content_lower for indicator in self.income_statement_indicators):
                sections['income_statement'].append(node.id)
            elif any(indicator in content_lower for indicator in self.cash_flow_indicators):
                sections['cash_flow'].append(node.id)
            elif any(indicator in content_lower for indicator in self.notes_indicators):
                sections['notes'].append(node.id)
            elif self._is_other_financial_section(content_lower):
                sections['other_financial'].append(node.id)
        
        # Process children
        for child in node.children:
            self._traverse_for_financial_sections(child, sections)
    
    def _is_other_financial_section(self, text: str) -> bool:
        """
        Check if text indicates another financial section.
        
        Args:
            text: Text to check
            
        Returns:
            True if the text indicates a financial section
        """
        financial_indicators = {
            'financial', 'fiscal', 'quarter', 'annual', 'statement',
            'consolidated', 'summary', 'highlights', 'results',
            'year ended', 'revenue', 'expenses', 'earnings', 'per share',
            'dividend', 'liquidity', 'capital resources'
        }
        
        return any(indicator in text for indicator in financial_indicators)
    
    def detect_financial_facts(self, node: DocumentNode) -> List[Dict[str, Any]]:
        """
        Detect financial facts in a document node.
        
        Args:
            node: DocumentNode to analyze
            
        Returns:
            List of detected financial facts
        """
        facts = []
        
        # If the node has XBRL facts, those are already financial facts
        if node.xbrl_facts:
            for fact in node.xbrl_facts:
                facts.append({
                    'node_id': node.id,
                    'fact_type': 'xbrl',
                    'name': fact.name,
                    'value': fact.value,
                    'context': fact.context_ref,
                    'unit': fact.unit_ref,
                    'period': fact.period
                })
            return facts
        
        # Check if this is a table cell that might contain a financial value
        if node.type == 'table_body_cell' and node.content:
            # Try to extract numeric values that might be financial
            numeric_value = self._extract_numeric_value(node.content)
            if numeric_value is not None:
                # Try to determine what this number represents
                context = self._determine_financial_context(node)
                facts.append({
                    'node_id': node.id,
                    'fact_type': 'table_value',
                    'value': numeric_value,
                    'content': node.content,
                    'context': context
                })
        
        # Process children recursively
        for child in node.children:
            facts.extend(self.detect_financial_facts(child))
        
        return facts
    
    def _extract_numeric_value(self, text: str) -> Optional[float]:
        """
        Extract a numeric value from text.
        
        Args:
            text: Text to extract from
            
        Returns:
            Extracted numeric value or None
        """
        # Remove common currency symbols and thousands separators
        clean_text = text.replace('$', '').replace('€', '').replace('£', '').replace(',', '')
        
        # Try to find numbers with optional decimal points
        match = re.search(r'(-?\d+(\.\d+)?)', clean_text)
        if match:
            try:
                return float(match.group(1))
            except ValueError:
                return None
        
        return None
    
    def _determine_financial_context(self, node: DocumentNode) -> Dict[str, Any]:
        """
        Determine the financial context of a node.
        
        Args:
            node: Node to analyze
            
        Returns:
            Context information
        """
        context = {
            'heading': None,
            'row_label': None,
            'column_label': None
        }
        
        # Find the closest heading
        current = node
        while current.parent:
            current = current.parent
            if current.type == 'heading' and current.content:
                context['heading'] = current.content
                break
        
        # If this is a table cell, try to determine row and column labels
        if node.type == 'table_body_cell':
            # Find row label (might be the first cell in the row)
            parent_row = node.parent
            if parent_row and parent_row.children:
                first_cell = parent_row.children[0]
                if first_cell and first_cell.content:
                    context['row_label'] = first_cell.content
            
            # Find column label (check the header row)
            if parent_row and parent_row.parent and parent_row.parent.parent:
                table_node = parent_row.parent.parent
                header_node = None
                
                for child in table_node.children:
                    if child.type == 'table_header':
                        header_node = child
                        break
                
                if header_node and header_node.children:
                    header_row = header_node.children[-1]  # Last header row
                    if header_row and header_row.children:
                        column_index = node.metadata.get('column_index')
                        if column_index is not None and column_index < len(header_row.children):
                            column_cell = header_row.children[column_index]
                            if column_cell and column_cell.content:
                                context['column_label'] = column_cell.content
        
        return context
    
    def identify_financial_statement_type(self, section_node: DocumentNode) -> str:
        """
        Identify the type of financial statement.
        
        Args:
            section_node: Section node to analyze
            
        Returns:
            Financial statement type
        """
        # First check the heading or caption
        if section_node.content:
            content_lower = section_node.content.lower()
            if any(indicator in content_lower for indicator in self.balance_sheet_indicators):
                return 'balance_sheet'
            elif any(indicator in content_lower for indicator in self.income_statement_indicators):
                return 'income_statement'
            elif any(indicator in content_lower for indicator in self.cash_flow_indicators):
                return 'cash_flow'
            elif any(indicator in content_lower for indicator in self.notes_indicators):
                return 'notes'
        
        # Check child nodes for content that might indicate the statement type
        all_text = self._get_all_text(section_node).lower()
        
        # Count indicators for each type
        bs_count = sum(1 for ind in self.balance_sheet_indicators if ind in all_text)
        is_count = sum(1 for ind in self.income_statement_indicators if ind in all_text)
        cf_count = sum(1 for ind in self.cash_flow_indicators if ind in all_text)
        notes_count = sum(1 for ind in self.notes_indicators if ind in all_text)
        
        # Return the type with the most indicators
        counts = [
            (bs_count, 'balance_sheet'),
            (is_count, 'income_statement'),
            (cf_count, 'cash_flow'),
            (notes_count, 'notes')
        ]
        
        return max(counts)[1] if any(count > 0 for count, _ in counts) else 'unknown'
    
    def _get_all_text(self, node: DocumentNode) -> str:
        """
        Get all text content from a node and its children.
        
        Args:
            node: Node to extract text from
            
        Returns:
            Concatenated text content
        """
        texts = []
        
        if node.content:
            texts.append(node.content)
        
        for child in node.children:
            texts.append(self._get_all_text(child))
        
        return ' '.join(texts)
