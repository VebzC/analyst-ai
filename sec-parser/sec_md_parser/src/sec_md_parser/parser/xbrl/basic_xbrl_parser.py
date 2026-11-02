"""Basic XBRL parser for SEC filings."""

from typing import Dict, Any, List, Optional
from bs4 import BeautifulSoup, Tag
import re

from sec_md_parser.models.base import XBRLFact


class BasicXBRLParser:
    """Basic parser for XBRL data in SEC filings."""
    
    def __init__(self) -> None:
        """Initialize the basic XBRL parser."""
        pass
    
    def extract_facts(self, soup: BeautifulSoup) -> List[XBRLFact]:
        """
        Extract XBRL facts from SEC filing.
        
        Args:
            soup: BeautifulSoup object containing the SEC filing HTML
            
        Returns:
            List of XBRLFact objects
        """
        facts = []
        
        # Look for inline XBRL tags
        ix_tags = soup.find_all(['ix:nonfraction', 'ix:fraction', 'ix:nonnumeric'])
        
        for tag in ix_tags:
            # Extract attributes
            name = tag.get('name', '')
            context_ref = tag.get('contextref', '')
            unit_ref = tag.get('unitref', '')
            decimals = tag.get('decimals', '')
            precision = tag.get('precision', '')
            id_attr = tag.get('id', '')
            
            # Extract value
            value = tag.get_text(strip=True)
            
            # Create XBRL fact
            fact = XBRLFact(
                name=name,
                value=value,
                context_ref=context_ref,
                unit_ref=unit_ref,
                decimals=decimals,
                precision=precision,
                id=id_attr
            )
            
            facts.append(fact)
        
        # Also look for hidden XBRL data
        hidden_data = soup.find('div', {'style': re.compile(r'display:\s*none')})
        if hidden_data:
            # Process hidden XBRL data
            facts.extend(self._process_hidden_xbrl(hidden_data))
        
        return facts
    
    def _process_hidden_xbrl(self, element: Tag) -> List[XBRLFact]:
        """
        Process hidden XBRL data.
        
        Args:
            element: BeautifulSoup Tag containing hidden XBRL data
            
        Returns:
            List of XBRLFact objects
        """
        facts = []
        
        # Look for XBRL tags in hidden data
        xbrl_tags = element.find_all(re.compile(r'us-gaap:|dei:|ifrs:|srt:'))
        
        for tag in xbrl_tags:
            # Extract tag name and value
            name = tag.name
            value = tag.get_text(strip=True)
            
            # Extract context ref if available
            context_ref = tag.get('contextref', '')
            if not context_ref:
                context_ref = tag.get('context', '')
            
            # Extract unit ref if available
            unit_ref = tag.get('unitref', '')
            if not unit_ref:
                unit_ref = tag.get('unit', '')
            
            # Create XBRL fact
            fact = XBRLFact(
                name=name,
                value=value,
                context_ref=context_ref,
                unit_ref=unit_ref
            )
            
            facts.append(fact)
        
        return facts 