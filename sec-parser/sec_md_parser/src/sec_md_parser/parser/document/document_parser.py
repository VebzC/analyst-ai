"""Document parser for SEC filings."""

from typing import Dict, Any, List, Optional
from bs4 import BeautifulSoup, Tag

from sec_md_parser.models.base import DocumentNode


class DocumentParser:
    """Parser for SEC document structures."""
    
    def __init__(self) -> None:
        """Initialize the document parser."""
        pass
    
    def parse_document(self, soup: BeautifulSoup) -> DocumentNode:
        """
        Parse a SEC filing into a document tree.
        
        Args:
            soup: BeautifulSoup object containing the SEC filing HTML
            
        Returns:
            DocumentNode representing the root of the document tree
        """
        # Create the root document node
        root = DocumentNode(type="document", content=None)
        
        # Extract the body element
        body = soup.find('body')
        if not body:
            # If no body tag, use the whole document
            body = soup
        
        # Parse the body content
        self._parse_element(body, root)
        
        return root
    
    def _parse_element(self, element: Tag, parent: DocumentNode) -> None:
        """
        Recursively parse an HTML element and its children.
        
        Args:
            element: BeautifulSoup Tag to parse
            parent: Parent DocumentNode
        """
        if not element:
            return
        
        # Process different element types
        if element.name == 'h1' or element.name == 'h2' or element.name == 'h3' or \
           element.name == 'h4' or element.name == 'h5' or element.name == 'h6':
            # Create a heading node
            heading_level = int(element.name[1])
            heading_node = parent.add_child(DocumentNode(
                type="heading",
                content=element.get_text(strip=True),
                attributes={"level": heading_level}
            ))
            
        elif element.name == 'p':
            # Create a paragraph node
            parent.add_child(DocumentNode(
                type="paragraph",
                content=element.get_text(strip=True)
            ))
            
        elif element.name == 'table':
            # Create a table node
            table_node = parent.add_child(DocumentNode(
                type="table",
                content=None
            ))
            
            # Process table elements
            self._parse_table(element, table_node)
            
        elif element.name == 'div':
            # Check if this div is a section
            if element.get('class') and ('section' in element.get('class') or 
                                         'item' in element.get('class')):
                # Create a section node
                section_node = parent.add_child(DocumentNode(
                    type="section",
                    content=None
                ))
                
                # Process section children
                for child in element.children:
                    if isinstance(child, Tag):
                        self._parse_element(child, section_node)
            else:
                # Process div children directly under parent
                for child in element.children:
                    if isinstance(child, Tag):
                        self._parse_element(child, parent)
                        
        elif element.name == 'ul' or element.name == 'ol':
            # Create a list node
            list_node = parent.add_child(DocumentNode(
                type="list",
                content=None,
                attributes={"list_type": "ordered" if element.name == 'ol' else "unordered"}
            ))
            
            # Process list items
            for li in element.find_all('li', recursive=False):
                list_item = list_node.add_child(DocumentNode(
                    type="list_item",
                    content=li.get_text(strip=True)
                ))
                
        else:
            # For other elements, process children directly under parent
            for child in element.children:
                if isinstance(child, Tag):
                    self._parse_element(child, parent)
    
    def _parse_table(self, table: Tag, table_node: DocumentNode) -> None:
        """
        Parse a table element.
        
        Args:
            table: BeautifulSoup table Tag to parse
            table_node: Parent table DocumentNode
        """
        # Extract caption if it exists
        caption = table.find('caption')
        if caption:
            table_node.add_child(DocumentNode(
                type="table_caption",
                content=caption.get_text(strip=True)
            ))
        
        # Extract header rows
        thead = table.find('thead')
        if thead:
            header_node = table_node.add_child(DocumentNode(
                type="table_header",
                content=None
            ))
            
            for tr in thead.find_all('tr', recursive=False):
                row_node = header_node.add_child(DocumentNode(
                    type="table_header_row",
                    content=None
                ))
                
                for th in tr.find_all(['th', 'td'], recursive=False):
                    row_node.add_child(DocumentNode(
                        type="table_header_cell",
                        content=th.get_text(strip=True)
                    ))
        
        # Extract body rows
        tbody = table.find('tbody')
        if not tbody:
            tbody = table  # If no tbody tag, use the whole table
            
        body_node = table_node.add_child(DocumentNode(
            type="table_body",
            content=None
        ))
        
        for tr in tbody.find_all('tr', recursive=False):
            # Skip if this is a header row in tbody
            if tr.find('th') and not tr.find('td'):
                continue
                
            row_node = body_node.add_child(DocumentNode(
                type="table_body_row",
                content=None
            ))
            
            for td in tr.find_all(['td', 'th'], recursive=False):
                row_node.add_child(DocumentNode(
                    type="table_body_cell",
                    content=td.get_text(strip=True)
                )) 