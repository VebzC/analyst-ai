"""SEC MD Parser - A library for parsing SEC filings into Markdown."""

__version__ = "0.1.0"

import os
import requests
from datetime import datetime
from typing import Dict, Optional, Any, List, Union
import logging
from bs4 import BeautifulSoup

# Import base models first to avoid circular imports
from sec_md_parser.models.base import DocumentNode, XBRLFact, FinancialMetric
from sec_md_parser.models.document import DocumentTree, SECDocument

# Import core modules
from sec_md_parser.parser.metadata.basic_metadata_extractor import BasicMetadataExtractor
from sec_md_parser.parser.document.document_parser import DocumentParser
from sec_md_parser.parser.xbrl.basic_xbrl_parser import BasicXBRLParser
from sec_md_parser.converter.markdown_converter import MarkdownConverter


class SECParser:
    """Parser for SEC filings."""
    
    def __init__(self) -> None:
        """Initialize the SEC parser."""
        self.metadata_extractor = BasicMetadataExtractor()
        self.document_parser = DocumentParser()
        self.xbrl_parser = BasicXBRLParser()
        self.logger = logging.getLogger(__name__)
    
    def parse_from_url(self, url: str) -> SECDocument:
        """
        Parse SEC filing from a URL.
        
        Args:
            url: URL to the SEC filing
            
        Returns:
            SECDocument object containing the parsed document
        """
        # Fetch HTML content
        response = requests.get(url)
        response.raise_for_status()
        html_content = response.text
        
        return self.parse_from_html(html_content, source_url=url)
    
    def parse_from_file(self, file_path: str) -> SECDocument:
        """
        Parse SEC filing from a local file.
        
        Args:
            file_path: Path to the SEC filing HTML file
            
        Returns:
            SECDocument object containing the parsed document
        """
        with open(file_path, 'r', encoding='utf-8') as f:
            html_content = f.read()
        
        return self.parse_from_html(html_content, source_path=file_path)
    
    def parse_from_html(self, html_content: str, extract_xbrl: bool = True, **kwargs) -> SECDocument:
        """
        Parse a SEC filing from HTML content.
        
        Args:
            html_content: HTML content of the SEC filing
            extract_xbrl: Whether to extract XBRL data from the document
            **kwargs: Additional arguments to pass to the parser
            
        Returns:
            SECDocument object representing the parsed document
        """
        self.logger.info("Parsing SEC filing from HTML content")
        
        # Parse HTML using BeautifulSoup
        soup = BeautifulSoup(html_content, "html.parser")
        
        # Extract basic metadata
        metadata = self.metadata_extractor.extract_metadata(soup)
        self.logger.info(f"Extracted metadata: {len(metadata)} attributes")
        
        # Extract XBRL data
        xbrl_facts = []
        
        if extract_xbrl:
            # Use the basic XBRL parser
            xbrl_facts = self.xbrl_parser.extract_facts(soup)
            self.logger.info(f"Extracted {len(xbrl_facts)} XBRL facts")
            
            # Add XBRL info to metadata
            metadata['xbrl_facts_count'] = len(xbrl_facts)
        
        # Parse document structure
        document_root = self.document_parser.parse_document(soup)
        document_tree = DocumentTree(root=document_root)
        self.logger.info("Parsed document structure")
        
        # Create SEC document
        document = SECDocument(
            document_tree=document_tree,
            metadata=metadata,
            xbrl_facts=xbrl_facts
        )
        
        return document
    
    def document_to_markdown(self, document: SECDocument, include_xbrl: bool = True,
                            include_financial_metadata: bool = True) -> str:
        """
        Convert a SEC document to Markdown.
        
        Args:
            document: SECDocument to convert
            include_xbrl: Whether to include XBRL metadata in the Markdown
            include_financial_metadata: Whether to include financial metadata
            
        Returns:
            Markdown string representation of the document
        """
        return document.to_markdown(
            include_xbrl=include_xbrl,
            include_financial_metadata=include_financial_metadata
        )
    
    def html_to_markdown(self, html_content: str, include_xbrl: bool = True,
                        include_financial_metadata: bool = True) -> str:
        """
        Convert a SEC filing HTML to Markdown in one step.
        
        Args:
            html_content: HTML content of the SEC filing
            include_xbrl: Whether to include XBRL metadata in the Markdown
            include_financial_metadata: Whether to include financial metadata
            
        Returns:
            Markdown string representation of the document
        """
        document = self.parse_from_html(
            html_content, 
            extract_xbrl=include_xbrl
        )
        
        return self.document_to_markdown(
            document,
            include_xbrl=include_xbrl,
            include_financial_metadata=include_financial_metadata
        )


__all__ = [
    "SECParser", "SECDocument", "DocumentTree", 
    "HTMLParser", "XBRLParser", "XbrlMetadataExtractor",
    "MarkdownConverter", "DocumentTreeBuilder", "FinancialDetector", 
    "TableAnalyzer", "FinancialStatementIdentifier", "CalculationRelationshipHandler",
    "generate_markdown_from_tree", "generate_markdown_table", "generate_markdown_document",
    "generate_llm_optimized_output", "simplify_tree_for_llm", "extract_key_metrics",
    "generate_table_of_contents", "generate_section_summaries", "convert_to_qa_format"
]
