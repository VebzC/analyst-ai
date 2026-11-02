"""Document tree builder for SEC filings."""

from typing import Dict, List, Optional, Any, Set, Tuple
from bs4 import BeautifulSoup, Tag
import re
import uuid
from datetime import datetime

from sec_md_parser.models.document import DocumentNode, DocumentTree, XBRLFact
from sec_md_parser.analyzer.table_analyzer import TableAnalyzer
from sec_md_parser.analyzer.financial_detector import FinancialDetector
from sec_md_parser.parser.xbrl_parser import XBRLParser


class DocumentTreeBuilder:
    """Builds a hierarchical tree representation of the document."""
    
    def __init__(self):
        """Initialize the document tree builder."""
        self.table_analyzer = TableAnalyzer()
        self.financial_detector = FinancialDetector()
        self.xbrl_parser = XBRLParser()
        self.soup = None
        self.root = None
        self.current_path = []
        self.heading_patterns = {
            'h1': re.compile(r'<h1', re.IGNORECASE),
            'h2': re.compile(r'<h2', re.IGNORECASE),
            'h3': re.compile(r'<h3', re.IGNORECASE),
            'h4': re.compile(r'<h4', re.IGNORECASE),
            'h5': re.compile(r'<h5', re.IGNORECASE),
            'h6': re.compile(r'<h6', re.IGNORECASE)
        }
        self.xbrl_facts = []
    
    def build_from_html(self, html_content: str) -> DocumentTree:
        """
        Build a document tree from HTML content.
        
        Args:
            html_content: HTML content as a string
            
        Returns:
            DocumentTree object representing the document structure
        """
        # Parse the HTML
        self.soup = BeautifulSoup(html_content, 'lxml')
        
        # Extract XBRL facts
        self.xbrl_facts = self.xbrl_parser.parse(self.soup)
        
        # Create the root node
        self.root = DocumentNode(
            id=str(uuid.uuid4()),
            type="document",
            content=None,
            metadata=self._extract_document_metadata()
        )
        
        # Initialize the current path
        self.current_path = [self.root]
        
        # Process the document body
        body = self.soup.find('body')
        if body:
            self._process_element(body)
        
        # Post-process the tree
        self._resolve_references()
        self._detect_financial_sections()
        self._associate_xbrl_facts_with_sections()
        
        return DocumentTree(root=self.root)
    
    def _extract_document_metadata(self) -> Dict[str, Any]:
        """Extract metadata from the document."""
        metadata = {}
        
        # Extract document title
        title_tag = self.soup.find('title')
        if title_tag:
            metadata['title'] = title_tag.get_text(strip=True)
        else:
            # Try to extract title from the first h1 tag
            h1_tag = self.soup.find('h1')
            if h1_tag:
                metadata['title'] = h1_tag.get_text(strip=True)
            else:
                metadata['title'] = "SEC Filing"
        
        # Extract document type
        doc_type = self._extract_filing_type()
        if doc_type:
            metadata['filing_type'] = doc_type
        
        # Extract company name
        company_name = self._extract_company_name()
        if company_name:
            metadata['company_name'] = company_name
        
        # Extract filing date
        filing_date = self._extract_filing_date()
        if filing_date:
            metadata['filing_date'] = filing_date
        
        # Add XBRL statistics if available
        if self.xbrl_facts:
            metadata['xbrl_fact_count'] = len(self.xbrl_facts)
            
            # Count facts by type
            fact_types = {}
            for fact in self.xbrl_facts:
                prefix = fact.name.split(':')[0] if ':' in fact.name else 'unknown'
                fact_types[prefix] = fact_types.get(prefix, 0) + 1
            
            metadata['xbrl_fact_types'] = fact_types
        
        return metadata
    
    def _extract_filing_type(self) -> Optional[str]:
        """Extract the filing type from the document."""
        # Common filing types to look for
        filing_types = ['10-K', '10-Q', '8-K', '20-F', '6-K', 'S-1', 'DEF 14A']
        
        # Look for a pattern like "Form 10-K" or "FORM 10-K"
        form_pattern = re.compile(r'form\s+(\d+-\w+|\w+-\d+|DEF\s+\d+\w+)', re.IGNORECASE)
        
        # Try to find it in the title first
        title_tag = self.soup.find('title')
        if title_tag:
            title_text = title_tag.get_text()
            form_match = form_pattern.search(title_text)
            if form_match:
                return form_match.group(1).upper()
            
            # Direct match for filing types
            for filing_type in filing_types:
                if filing_type in title_text:
                    return filing_type
        
        # Try to find it in the first few paragraphs
        first_paras = self.soup.find_all('p', limit=5)
        for para in first_paras:
            form_match = form_pattern.search(para.get_text())
            if form_match:
                return form_match.group(1).upper()
            
            # Direct match for filing types
            for filing_type in filing_types:
                if filing_type in para.get_text():
                    return filing_type
        
        return None
    
    def _extract_company_name(self) -> Optional[str]:
        """Extract the company name from the document."""
        # Look for common patterns that might indicate the company name
        
        # Try to find it in the title
        title_tag = self.soup.find('title')
        if title_tag:
            title_text = title_tag.get_text().strip()
            
            # If the title follows a pattern like "Form 10-K - Company Name"
            if ' - ' in title_text:
                return title_text.split(' - ', 1)[1]
        
        # Try to find it in a heading or paragraph near the beginning
        for tag in self.soup.find_all(['h1', 'h2', 'p'], limit=10):
            text = tag.get_text().strip()
            
            # Look for company name keyword patterns
            company_patterns = [
                re.compile(r'(.*?)\s+\(the "Company"', re.IGNORECASE),
                re.compile(r'(.*?)\s+\(the "Corporation"', re.IGNORECASE),
                re.compile(r'(.*?)\s+\([^)]+\)\s+is a', re.IGNORECASE)
            ]
            
            for pattern in company_patterns:
                match = pattern.search(text)
                if match:
                    return match.group(1).strip()
        
        return None
    
    def _extract_filing_date(self) -> Optional[str]:
        """Extract the filing date from the document."""
        # Look for date patterns in the text
        date_pattern = re.compile(r'(?:dated|as of|filing date|filed on|submitted on)\s+(\w+\s+\d{1,2},\s+\d{4})', re.IGNORECASE)
        
        # Check a limited number of elements
        for tag in self.soup.find_all(['p', 'div', 'td'], limit=20):
            text = tag.get_text().strip()
            match = date_pattern.search(text)
            if match:
                try:
                    date_str = match.group(1)
                    # Try to parse the date
                    date_obj = datetime.strptime(date_str, '%B %d, %Y')
                    return date_obj.strftime('%Y-%m-%d')
                except ValueError:
                    # If the date format is different, try another approach
                    pass
        
        return None
    
    def _process_element(self, element: Tag) -> None:
        """
        Process an HTML element and its children.
        
        Args:
            element: BeautifulSoup Tag to process
        """
        # Skip hidden elements
        if element.get('style') and 'display:none' in element.get('style'):
            return
        
        # Process element based on its type
        if element.name in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']:
            self._process_heading(element)
        elif element.name == 'table':
            self._process_table(element)
        elif element.name in ['p', 'div'] and element.get_text(strip=True):
            self._process_paragraph(element)
        elif element.name in ['ul', 'ol']:
            self._process_list(element)
        
        # Process children for some elements
        if element.name not in ['table', 'ul', 'ol']:  # Skip children for certain elements
            for child in element.children:
                if isinstance(child, Tag):  # Skip NavigableString objects
                    self._process_element(child)
    
    def _process_heading(self, element: Tag) -> None:
        """
        Process a heading element.
        
        Args:
            element: Heading element to process
        """
        # Get heading level (h1 = 1, h2 = 2, etc.)
        level = int(element.name[1])
        title = element.get_text(strip=True)
        
        # Adjust the current path based on heading level
        while len(self.current_path) > 1 and self.current_path[-1].metadata.get('heading_level', 1) >= level:
            self.current_path.pop()
        
        # Create a new section node
        section_node = DocumentNode(
            id=str(uuid.uuid4()),
            type="section",
            content=None,
            metadata={"heading_level": level}
        )
        
        # Create a heading node
        heading_node = DocumentNode(
            id=str(uuid.uuid4()),
            type="heading",
            content=title,
            metadata={"level": level}
        )
        
        # Add to the current section
        self.current_path[-1].add_child(section_node)
        
        # Add the heading to the section
        section_node.add_child(heading_node)
        
        # Update the current path
        self.current_path.append(section_node)
    
    def _process_table(self, element: Tag) -> None:
        """
        Process a table element.
        
        Args:
            element: Table element to process
        """
        # Use the table analyzer to analyze the table with XBRL facts
        table_node = self.table_analyzer.analyze_table(element, self.xbrl_facts)
        
        # Add the table to the current section
        self.current_path[-1].add_child(table_node)
    
    def _process_paragraph(self, element: Tag) -> None:
        """
        Process a paragraph element.
        
        Args:
            element: Paragraph element to process
        """
        text = element.get_text(strip=True)
        if not text:
            return
        
        # Create a paragraph node
        para_node = DocumentNode(
            id=str(uuid.uuid4()),
            type="paragraph",
            content=text
        )
        
        # Attach XBRL facts if any
        self._attach_xbrl_facts_to_paragraph(para_node, element)
        
        # Add to the current section
        self.current_path[-1].add_child(para_node)
    
    def _process_list(self, element: Tag) -> None:
        """
        Process a list element.
        
        Args:
            element: List element to process
        """
        # Determine list type
        list_type = "ordered" if element.name == "ol" else "unordered"
        
        # Create a list node
        list_node = DocumentNode(
            id=str(uuid.uuid4()),
            type="list",
            content=None,
            attributes={"list_type": list_type}
        )
        
        # Process list items
        for item in element.find_all('li', recursive=False):
            item_node = DocumentNode(
                id=str(uuid.uuid4()),
                type="list_item",
                content=item.get_text(strip=True),
                attributes={"list_type": list_type}
            )
            
            # Process nested lists
            nested_list = item.find(['ul', 'ol'])
            if nested_list:
                # Create a temporary parent for nested list processing
                temp_parent = DocumentNode(
                    id=str(uuid.uuid4()),
                    type="temp",
                    content=None
                )
                
                # Save current path
                old_path = self.current_path
                self.current_path = [temp_parent]
                
                # Process the nested list
                self._process_list(nested_list)
                
                # Add nested list to item
                if temp_parent.children:
                    for child in temp_parent.children:
                        item_node.add_child(child)
                
                # Restore path
                self.current_path = old_path
            
            # Add item to list
            list_node.add_child(item_node)
        
        # Add list to the current section
        self.current_path[-1].add_child(list_node)
    
    def _attach_xbrl_facts_to_paragraph(self, node: DocumentNode, element: Tag) -> None:
        """
        Attach XBRL facts to a paragraph node.
        
        Args:
            node: Paragraph node to attach facts to
            element: Original HTML element
        """
        if not self.xbrl_facts:
            return
            
        # Find any XBRL elements within this paragraph
        for fact in self.xbrl_facts:
            # Check for inline XBRL elements with name attribute
            ix_elements = element.find_all(lambda tag: tag.name and tag.name.startswith('ix:') and tag.get('name') == fact.name)
            if ix_elements:
                node.xbrl_facts.append(fact)
                continue
                
            # Check if the fact value appears in the text
            if fact.value and str(fact.value) in node.content:
                node.xbrl_facts.append(fact)
    
    def _resolve_references(self) -> None:
        """Resolve references between nodes in the document tree."""
        # This is a placeholder for more complex reference resolution
        # In a real implementation, you might handle cross-references, footnotes, etc.
        pass
    
    def _detect_financial_sections(self) -> None:
        """Detect financial sections in the document tree."""
        # Use the financial detector to identify financial sections
        financial_sections = self.financial_detector.detect_financial_sections(DocumentTree(root=self.root))
        
        # Mark sections in the tree
        for section_type, node_ids in financial_sections.items():
            for node_id in node_ids:
                node = self._find_node_by_id(node_id)
                if node:
                    if 'financial_section_type' not in node.metadata:
                        node.metadata['financial_section_type'] = section_type
    
    def _associate_xbrl_facts_with_sections(self) -> None:
        """Associate XBRL facts with appropriate sections based on content matching."""
        if not self.xbrl_facts:
            return
            
        # Find financial sections
        financial_sections = []
        
        def _find_financial_sections(node: DocumentNode) -> None:
            if node.metadata.get('financial_section_type'):
                financial_sections.append(node)
            for child in node.children:
                _find_financial_sections(child)
        
        _find_financial_sections(self.root)
        
        # Group XBRL facts by their taxonomy prefixes
        fact_groups = {}
        for fact in self.xbrl_facts:
            prefix = fact.name.split(':')[0] if ':' in fact.name else 'unknown'
            if prefix not in fact_groups:
                fact_groups[prefix] = []
            fact_groups[prefix].append(fact)
        
        # Associate facts with financial sections based on the section type
        for section in financial_sections:
            section_type = section.metadata.get('financial_section_type')
            
            if section_type == 'balance_sheet':
                # Associate balance sheet related facts
                for prefix in ['us-gaap', 'ifrs']:
                    if prefix in fact_groups:
                        for fact in fact_groups[prefix]:
                            if any(term in fact.name.lower() for term in ['asset', 'liability', 'equity', 'balance']):
                                section.xbrl_facts.append(fact)
            
            elif section_type == 'income_statement':
                # Associate income statement related facts
                for prefix in ['us-gaap', 'ifrs']:
                    if prefix in fact_groups:
                        for fact in fact_groups[prefix]:
                            if any(term in fact.name.lower() for term in ['revenue', 'income', 'expense', 'earnings', 'profit', 'loss']):
                                section.xbrl_facts.append(fact)
            
            elif section_type == 'cash_flow':
                # Associate cash flow related facts
                for prefix in ['us-gaap', 'ifrs']:
                    if prefix in fact_groups:
                        for fact in fact_groups[prefix]:
                            if any(term in fact.name.lower() for term in ['cash', 'flow', 'operating', 'investing', 'financing']):
                                section.xbrl_facts.append(fact)
    
    def _find_node_by_id(self, node_id: str) -> Optional[DocumentNode]:
        """
        Find a node by its ID.
        
        Args:
            node_id: ID of the node to find
            
        Returns:
            DocumentNode if found, None otherwise
        """
        def _find_node(node: DocumentNode) -> Optional[DocumentNode]:
            if node.id == node_id:
                return node
            for child in node.children:
                result = _find_node(child)
                if result:
                    return result
            return None
        
        return _find_node(self.root)
