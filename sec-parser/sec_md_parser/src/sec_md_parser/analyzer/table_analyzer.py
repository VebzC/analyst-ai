"""Table structure analyzer for SEC filings."""

from typing import Dict, List, Optional, Any, Tuple
from bs4 import BeautifulSoup, Tag
import uuid
import re

from sec_md_parser.models.document import DocumentNode, XBRLFact


class TableAnalyzer:
    """Analyzer for tables in SEC filings."""
    
    def __init__(self) -> None:
        """Initialize the table analyzer."""
        pass
    
    def analyze_table(self, table_element: Tag, xbrl_facts: List[XBRLFact] = None) -> DocumentNode:
        """
        Analyze a table element and create a structured representation.
        
        Args:
            table_element: BeautifulSoup Tag object representing a table
            xbrl_facts: List of XBRLFact objects that might be related to this table
            
        Returns:
            DocumentNode object with the table structure
        """
        # Extract table metadata
        metadata = self._extract_table_metadata(table_element)
        
        # Create table node
        table_node = DocumentNode(
            id=str(uuid.uuid4()),
            type="table",
            content=None,
            metadata=metadata
        )
        
        # Process table caption/title
        caption = table_element.find('caption')
        if caption:
            caption_node = DocumentNode(
                id=str(uuid.uuid4()),
                type="table_caption",
                content=caption.get_text(strip=True)
            )
            table_node.add_child(caption_node)
        
        # Extract rows and cells structure
        rows_data = self._extract_table_structure(table_element, xbrl_facts)
        
        # Store the detailed structure in metadata
        table_node.metadata['structure'] = rows_data
        
        # Process table header
        thead = table_element.find('thead')
        if thead:
            header_node = self._process_table_header(thead, xbrl_facts)
            table_node.add_child(header_node)
        
        # Process table body
        tbody = table_element.find('tbody')
        if tbody:
            body_node = self._process_table_body(tbody, xbrl_facts)
            table_node.add_child(body_node)
        elif not thead:  # If no thead or tbody, process all rows directly
            rows = table_element.find_all('tr', recursive=False)
            
            # If the first row looks like a header row, treat it as such
            if rows and all(cell.name == 'th' for cell in rows[0].find_all(['th', 'td'])):
                header_node = self._process_rows_as_header([rows[0]], xbrl_facts)
                table_node.add_child(header_node)
                body_node = self._process_rows_as_body(rows[1:], xbrl_facts)
                table_node.add_child(body_node)
            else:
                body_node = self._process_rows_as_body(rows, xbrl_facts)
                table_node.add_child(body_node)
        
        # Process table footer
        tfoot = table_element.find('tfoot')
        if tfoot:
            footer_node = self._process_table_footer(tfoot, xbrl_facts)
            table_node.add_child(footer_node)
        
        # Determine the table type
        table_node.metadata['table_type'] = self.detect_table_type(table_node)
        
        return table_node
    
    def _extract_table_structure(self, table_element: Tag, xbrl_facts: List[XBRLFact] = None) -> List[List[Dict[str, Any]]]:
        """
        Extract the detailed structure of a table including all cells.
        
        Args:
            table_element: BeautifulSoup Tag object representing a table
            xbrl_facts: List of XBRLFact objects to associate with cells
            
        Returns:
            List of rows, each containing a list of cell dictionaries
        """
        rows_data = []
        
        # Process all rows
        for row_idx, tr in enumerate(table_element.find_all('tr')):
            cells_data = []
            
            # Process cells in this row
            for cell_idx, cell in enumerate(tr.find_all(['th', 'td'])):
                # Extract cell attributes
                rowspan = int(cell.get('rowspan', 1))
                colspan = int(cell.get('colspan', 1))
                is_header = cell.name == 'th'
                cell_content = cell.get_text(strip=True)
                
                # Extract XBRL facts for this cell
                cell_xbrl_facts = []
                if xbrl_facts:
                    cell_xbrl_facts = self._find_xbrl_facts_for_cell(cell, cell_content, xbrl_facts)
                
                # Create cell data structure
                cell_data = {
                    'content': cell_content,
                    'rowspan': rowspan,
                    'colspan': colspan,
                    'is_header': is_header,
                    'row_index': row_idx,
                    'col_index': cell_idx,
                    'attributes': self._extract_cell_attributes(cell),
                    'xbrl_fact_ids': [fact.name for fact in cell_xbrl_facts]
                }
                
                cells_data.append(cell_data)
            
            rows_data.append(cells_data)
        
        return rows_data
    
    def _find_xbrl_facts_for_cell(self, cell: Tag, content: str, xbrl_facts: List[XBRLFact]) -> List[XBRLFact]:
        """
        Find XBRL facts that are associated with a table cell.
        
        Args:
            cell: BeautifulSoup Tag object representing a table cell
            content: Text content of the cell
            xbrl_facts: List of all XBRL facts
            
        Returns:
            List of XBRLFact objects associated with this cell
        """
        if not xbrl_facts:
            return []
        
        matching_facts = []
        
        # Check inline XBRL elements within the cell
        for ix_element in cell.find_all(lambda tag: tag.name and tag.name.startswith('ix:')):
            for fact in xbrl_facts:
                # Check if this element has attributes that match the XBRL fact
                if (ix_element.get('name') == fact.name and 
                    ix_element.get('contextref') == fact.context_ref):
                    matching_facts.append(fact)
        
        # Also check for numeric content that matches a fact value
        if not matching_facts and content:
            # Try to extract a numeric value from the content
            numeric_value = self._extract_numeric_value(content)
            if numeric_value is not None:
                for fact in xbrl_facts:
                    # If the fact has a numeric value that matches the cell content
                    fact_value = self._extract_numeric_value(str(fact.value)) if fact.value else None
                    if fact_value is not None and abs(fact_value - numeric_value) < 0.001:
                        matching_facts.append(fact)
        
        return matching_facts
    
    def _extract_numeric_value(self, text: str) -> Optional[float]:
        """Extract a numeric value from text."""
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
    
    def _extract_table_metadata(self, table_element: Tag) -> Dict[str, Any]:
        """Extract metadata from a table element."""
        metadata = {
            "rows": len(table_element.find_all('tr')),
            "cols": self._estimate_columns(table_element),
            "attributes": {k: v for k, v in table_element.attrs.items()}
        }
        
        # Try to determine if this is a financial table
        financial_indicators = [
            'revenue', 'income', 'expense', 'asset', 'liability', 'equity',
            'cash flow', 'balance sheet', 'statement', 'fiscal', 'quarter',
            'annual', 'consolidated', 'financial', 'earnings', 'profit', 'loss'
        ]
        
        table_text = table_element.get_text().lower()
        financial_score = sum(1 for indicator in financial_indicators if indicator in table_text)
        metadata["is_financial_table"] = financial_score > 2
        
        return metadata
    
    def _estimate_columns(self, table_element: Tag) -> int:
        """Estimate the number of columns in a table."""
        max_cols = 0
        
        # Check all rows
        for row in table_element.find_all('tr'):
            # Count cells, considering colspan
            col_count = 0
            for cell in row.find_all(['td', 'th']):
                colspan = cell.get('colspan')
                if colspan and colspan.isdigit():
                    col_count += int(colspan)
                else:
                    col_count += 1
            
            max_cols = max(max_cols, col_count)
        
        return max_cols
    
    def _process_table_header(self, thead: Tag, xbrl_facts: List[XBRLFact] = None) -> DocumentNode:
        """Process table header element."""
        header_node = DocumentNode(
            id=str(uuid.uuid4()),
            type="table_header",
            content=None
        )
        
        # Process header rows
        rows = thead.find_all('tr')
        header_rows_node = self._process_rows_as_header(rows, xbrl_facts)
        
        for child in header_rows_node.children:
            header_node.add_child(child)
        
        return header_node
    
    def _process_rows_as_header(self, rows: List[Tag], xbrl_facts: List[XBRLFact] = None) -> DocumentNode:
        """Process rows as header rows."""
        header_node = DocumentNode(
            id=str(uuid.uuid4()),
            type="table_header_rows",
            content=None
        )
        
        for row in rows:
            row_node = DocumentNode(
                id=str(uuid.uuid4()),
                type="table_header_row",
                content=None
            )
            
            # Process header cells
            for cell in row.find_all(['th', 'td']):
                cell_content = cell.get_text(strip=True)
                
                # Find XBRL facts for this cell
                cell_xbrl_facts = []
                if xbrl_facts:
                    cell_xbrl_facts = self._find_xbrl_facts_for_cell(cell, cell_content, xbrl_facts)
                
                # Create cell node
                cell_node = DocumentNode(
                    id=str(uuid.uuid4()),
                    type="table_header_cell",
                    content=cell_content,
                    attributes=self._extract_cell_attributes(cell)
                )
                
                # Add XBRL facts to the cell node
                for fact in cell_xbrl_facts:
                    cell_node.xbrl_facts.append(fact)
                
                row_node.add_child(cell_node)
            
            header_node.add_child(row_node)
        
        return header_node
    
    def _process_table_body(self, tbody: Tag, xbrl_facts: List[XBRLFact] = None) -> DocumentNode:
        """Process table body element."""
        body_node = DocumentNode(
            id=str(uuid.uuid4()),
            type="table_body",
            content=None
        )
        
        # Process body rows
        rows = tbody.find_all('tr')
        body_rows_node = self._process_rows_as_body(rows, xbrl_facts)
        
        for child in body_rows_node.children:
            body_node.add_child(child)
        
        return body_node
    
    def _process_rows_as_body(self, rows: List[Tag], xbrl_facts: List[XBRLFact] = None) -> DocumentNode:
        """Process rows as body rows."""
        body_node = DocumentNode(
            id=str(uuid.uuid4()),
            type="table_body_rows",
            content=None
        )
        
        for i, row in enumerate(rows):
            row_node = DocumentNode(
                id=str(uuid.uuid4()),
                type="table_body_row",
                content=None,
                metadata={"row_index": i}
            )
            
            # Process body cells
            for j, cell in enumerate(row.find_all(['td', 'th'])):
                cell_content = cell.get_text(strip=True)
                
                # Find XBRL facts for this cell
                cell_xbrl_facts = []
                if xbrl_facts:
                    cell_xbrl_facts = self._find_xbrl_facts_for_cell(cell, cell_content, xbrl_facts)
                
                # Create cell node
                cell_node = DocumentNode(
                    id=str(uuid.uuid4()),
                    type="table_body_cell",
                    content=cell_content,
                    attributes=self._extract_cell_attributes(cell),
                    metadata={"column_index": j, "row_index": i}
                )
                
                # Add XBRL facts to the cell node
                for fact in cell_xbrl_facts:
                    cell_node.xbrl_facts.append(fact)
                
                row_node.add_child(cell_node)
            
            body_node.add_child(row_node)
        
        return body_node
    
    def _process_table_footer(self, tfoot: Tag, xbrl_facts: List[XBRLFact] = None) -> DocumentNode:
        """Process table footer element."""
        footer_node = DocumentNode(
            id=str(uuid.uuid4()),
            type="table_footer",
            content=None
        )
        
        # Process footer rows
        rows = tfoot.find_all('tr')
        for i, row in enumerate(rows):
            row_node = DocumentNode(
                id=str(uuid.uuid4()),
                type="table_footer_row",
                content=None,
                metadata={"row_index": i}
            )
            
            # Process footer cells
            for j, cell in enumerate(row.find_all(['td', 'th'])):
                cell_content = cell.get_text(strip=True)
                
                # Find XBRL facts for this cell
                cell_xbrl_facts = []
                if xbrl_facts:
                    cell_xbrl_facts = self._find_xbrl_facts_for_cell(cell, cell_content, xbrl_facts)
                
                # Create cell node
                cell_node = DocumentNode(
                    id=str(uuid.uuid4()),
                    type="table_footer_cell",
                    content=cell_content,
                    attributes=self._extract_cell_attributes(cell),
                    metadata={"column_index": j}
                )
                
                # Add XBRL facts to the cell node
                for fact in cell_xbrl_facts:
                    cell_node.xbrl_facts.append(fact)
                
                row_node.add_child(cell_node)
            
            footer_node.add_child(row_node)
        
        return footer_node
    
    def _extract_cell_attributes(self, cell: Tag) -> Dict[str, str]:
        """Extract attributes from a table cell."""
        attrs = {}
        
        # Copy attributes
        for attr, value in cell.attrs.items():
            if attr in ['rowspan', 'colspan', 'class', 'style', 'align', 'valign']:
                attrs[attr] = value
        
        return attrs
    
    def detect_table_type(self, table_node: DocumentNode) -> str:
        """
        Detect the type of table based on its structure and content.
        
        Args:
            table_node: DocumentNode representing a table
            
        Returns:
            Table type (e.g., 'financial_statement', 'data_table', etc.)
        """
        # Get table metadata
        metadata = table_node.metadata
        
        # Check if it's a financial table
        if metadata.get('is_financial_table', False):
            # Try to determine specific financial statement type
            table_text = self._get_full_table_text(table_node).lower()
            
            if any(term in table_text for term in ['balance sheet', 'assets', 'liabilities', 'equity']):
                return 'balance_sheet'
            elif any(term in table_text for term in ['income statement', 'revenue', 'expenses', 'earnings per share']):
                return 'income_statement'
            elif any(term in table_text for term in ['cash flow', 'operating activities', 'investing activities', 'financing activities']):
                return 'cash_flow_statement'
            else:
                return 'financial_statement'
        
        # Check for simple data table
        if metadata.get('rows', 0) <= 5 and metadata.get('cols', 0) <= 5:
            return 'simple_data_table'
        
        # Default
        return 'general_table'
    
    def _get_full_table_text(self, table_node: DocumentNode) -> str:
        """Get the full text content of a table node."""
        texts = []
        
        def collect_text(node):
            if node.content:
                texts.append(node.content)
            for child in node.children:
                collect_text(child)
        
        collect_text(table_node)
        return ' '.join(texts)
