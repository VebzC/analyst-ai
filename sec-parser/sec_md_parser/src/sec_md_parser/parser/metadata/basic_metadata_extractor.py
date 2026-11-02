"""Basic metadata extractor for SEC filings."""

from typing import Dict, Any, Optional
from bs4 import BeautifulSoup
import re
from datetime import datetime


class BasicMetadataExtractor:
    """Basic metadata extractor for SEC filings."""
    
    def __init__(self) -> None:
        """Initialize the basic metadata extractor."""
        pass
    
    def extract_metadata(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """
        Extract basic metadata from SEC filing.
        
        Args:
            soup: BeautifulSoup object containing the SEC filing HTML
            
        Returns:
            Dictionary containing metadata
        """
        metadata = {}
        
        # Extract title
        title_tag = soup.find('title')
        if title_tag and title_tag.text:
            metadata['title'] = title_tag.text.strip()
        
        # Extract document type (10-K, 10-Q, etc.)
        doc_type = self._extract_document_type(soup)
        if doc_type:
            metadata['document_type'] = doc_type
        
        # Extract filing date
        filing_date = self._extract_filing_date(soup)
        if filing_date:
            metadata['filing_date'] = filing_date
        
        # Extract company info
        company_info = self._extract_company_info(soup)
        if company_info:
            metadata.update(company_info)
        
        return metadata
    
    def _extract_document_type(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract document type from SEC filing."""
        # Try to find document type from common patterns
        for pattern in ['Form 10-K', 'Form 10-Q', 'Form 8-K', 'Form 20-F']:
            if soup.find(string=re.compile(pattern, re.IGNORECASE)):
                return pattern.replace('Form ', '')
        
        # Try to find from title
        title_tag = soup.find('title')
        if title_tag and title_tag.text:
            title = title_tag.text.strip().upper()
            if '10-K' in title:
                return '10-K'
            elif '10-Q' in title:
                return '10-Q'
            elif '8-K' in title:
                return '8-K'
            elif '20-F' in title:
                return '20-F'
        
        return None
    
    def _extract_filing_date(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract filing date from SEC filing."""
        # Look for common date patterns
        date_pattern = re.compile(r'filed\s*:?\s*([a-zA-Z]+\s+\d{1,2},\s+\d{4}|'
                                 r'\d{4}-\d{2}-\d{2}|\d{2}/\d{2}/\d{4})',
                                 re.IGNORECASE)
        
        date_tags = soup.find_all(string=date_pattern)
        for tag in date_tags:
            match = date_pattern.search(tag)
            if match:
                date_str = match.group(1)
                # Try to parse the date string
                try:
                    # Handle different date formats
                    if re.match(r'\d{4}-\d{2}-\d{2}', date_str):
                        date_obj = datetime.strptime(date_str, '%Y-%m-%d')
                    elif re.match(r'\d{2}/\d{2}/\d{4}', date_str):
                        date_obj = datetime.strptime(date_str, '%m/%d/%Y')
                    else:
                        date_obj = datetime.strptime(date_str, '%B %d, %Y')
                    return date_obj.strftime('%Y-%m-%d')
                except ValueError:
                    continue
        
        return None
    
    def _extract_company_info(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """Extract company information from SEC filing."""
        company_info = {}
        
        # Try to find company name
        company_pattern = re.compile(r'registrant|company|issuer', re.IGNORECASE)
        company_tags = soup.find_all(['span', 'div', 'p'], string=company_pattern)
        
        for tag in company_tags:
            tag_text = tag.text.strip()
            if re.search(r'name\s+of', tag_text, re.IGNORECASE) and ':' in tag_text:
                company_name = tag_text.split(':', 1)[1].strip()
                if company_name:
                    company_info['company_name'] = company_name
                    break
        
        # Try to find CIK
        cik_pattern = re.compile(r'CIK:?\s*(\d{10}|\d{9}|\d{8})')
        cik_tags = soup.find_all(string=cik_pattern)
        for tag in cik_tags:
            match = cik_pattern.search(tag)
            if match:
                company_info['cik'] = match.group(1)
                break
        
        return company_info 