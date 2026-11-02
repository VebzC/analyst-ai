"""XBRL Parser for SEC filings."""

from typing import Dict, List, Optional, Any, Tuple
from bs4 import BeautifulSoup
import re
from lxml import etree

from sec_md_parser.models.document import XBRLFact


class XBRLParser:
    """Parser for XBRL content in SEC filings."""
    
    def __init__(self) -> None:
        """Initialize the XBRL parser."""
        self.soup = None
        self.namespaces = {}
        self.contexts = {}
        self.units = {}
    
    def parse(self, soup: BeautifulSoup) -> List[XBRLFact]:
        """
        Parse XBRL content from a BeautifulSoup object.
        
        Args:
            soup: BeautifulSoup object with the parsed HTML
            
        Returns:
            List of XBRLFact objects
        """
        self.soup = soup
        
        # Extract namespaces
        self._extract_namespaces()
        
        # Extract contexts
        self._extract_contexts()
        
        # Extract units
        self._extract_units()
        
        # Extract facts
        return self._extract_facts()
    
    def _extract_namespaces(self) -> None:
        """Extract XBRL namespaces from the document."""
        if not self.soup or not self.soup.html:
            return
        
        # Find the namespace declarations in the HTML tag
        html_tag = self.soup.html
        if not html_tag:
            return
            
        # Get all attributes that start with xmlns:
        for attr_name, attr_value in html_tag.attrs.items():
            if attr_name.startswith('xmlns:'):
                ns_prefix = attr_name.replace('xmlns:', '')
                self.namespaces[ns_prefix] = attr_value
    
    def _extract_contexts(self) -> None:
        """Extract XBRL contexts from the document."""
        if not self.soup:
            return
            
        # Find all context elements
        context_elements = self.soup.find_all(re.compile(r'.*:context'))
        
        for context in context_elements:
            context_id = context.get('id')
            if not context_id:
                continue
                
            # Extract period information
            period = context.find(re.compile(r'.*:period'))
            period_info = {}
            
            if period:
                instant = period.find(re.compile(r'.*:instant'))
                if instant and instant.string:
                    period_info['instant'] = instant.string.strip()
                
                start_date = period.find(re.compile(r'.*:startdate'))
                end_date = period.find(re.compile(r'.*:enddate'))
                
                if start_date and start_date.string and end_date and end_date.string:
                    period_info['start_date'] = start_date.string.strip()
                    period_info['end_date'] = end_date.string.strip()
            
            # Extract entity information
            entity = context.find(re.compile(r'.*:entity'))
            entity_info = {}
            
            if entity:
                identifier = entity.find(re.compile(r'.*:identifier'))
                if identifier and identifier.string:
                    entity_info['identifier'] = identifier.string.strip()
                    entity_info['scheme'] = identifier.get('scheme', '')
                
                # Extract segment information for dimensions
                segment = entity.find(re.compile(r'.*:segment'))
                if segment:
                    dimensions = {}
                    for dim in segment.find_all(re.compile(r'.*:explicitMember')):
                        dimension = dim.get('dimension', '')
                        value = dim.string.strip() if dim.string else ''
                        if dimension and value:
                            dimensions[dimension] = value
                    
                    entity_info['dimensions'] = dimensions
            
            # Store the context
            self.contexts[context_id] = {
                'period': period_info,
                'entity': entity_info
            }
    
    def _extract_units(self) -> None:
        """Extract XBRL units from the document."""
        if not self.soup:
            return
            
        # Find all unit elements
        unit_elements = self.soup.find_all(re.compile(r'.*:unit'))
        
        for unit in unit_elements:
            unit_id = unit.get('id')
            if not unit_id:
                continue
                
            measure = unit.find(re.compile(r'.*:measure'))
            if measure and measure.string:
                self.units[unit_id] = measure.string.strip()
            else:
                # Handle complex units with divide
                divide = unit.find(re.compile(r'.*:divide'))
                if divide:
                    numerator = divide.find(re.compile(r'.*:unitNumerator'))
                    denominator = divide.find(re.compile(r'.*:unitDenominator'))
                    
                    numerator_measure = numerator.find(re.compile(r'.*:measure')) if numerator else None
                    denominator_measure = denominator.find(re.compile(r'.*:measure')) if denominator else None
                    
                    if numerator_measure and numerator_measure.string and denominator_measure and denominator_measure.string:
                        self.units[unit_id] = f"{numerator_measure.string.strip()}/{denominator_measure.string.strip()}"
    
    def _extract_facts(self) -> List[XBRLFact]:
        """Extract XBRL facts from the document."""
        if not self.soup:
            return []
            
        facts = []
        
        # For inline XBRL (iXBRL), look for elements with ix:continuation or ix:fraction attributes
        numeric_elements = self.soup.find_all(attrs={'contextref': True, 'name': True})
        
        for element in numeric_elements:
            name = element.get('name', '')
            if not name:
                continue
                
            # Get the context reference
            context_ref = element.get('contextref')
            
            # Get the unit reference for numeric facts
            unit_ref = element.get('unitref')
            
            # Get other attributes
            decimals = element.get('decimals')
            if decimals and decimals.isdigit():
                decimals = int(decimals)
            else:
                decimals = None
                
            scale = element.get('scale')
            if scale and scale.isdigit():
                scale = int(scale)
            else:
                scale = None
            
            # Get the value
            value = element.get('value', element.get_text(strip=True))
            
            # Create the fact
            fact = XBRLFact(
                name=name,
                value=value,
                context_ref=context_ref,
                unit_ref=unit_ref,
                decimals=decimals,
                scale=scale,
                format=element.get('format'),
                sign=element.get('sign'),
                balance=element.get('balance'),
                period=self._get_period_for_context(context_ref),
                dimension=self._get_dimensions_for_context(context_ref)
            )
            
            facts.append(fact)
        
        return facts
    
    def _get_period_for_context(self, context_ref: Optional[str]) -> Optional[str]:
        """Get period information for a context."""
        if not context_ref or context_ref not in self.contexts:
            return None
            
        period_info = self.contexts[context_ref].get('period', {})
        
        if 'instant' in period_info:
            return period_info['instant']
        elif 'start_date' in period_info and 'end_date' in period_info:
            return f"{period_info['start_date']} to {period_info['end_date']}"
            
        return None
    
    def _get_dimensions_for_context(self, context_ref: Optional[str]) -> Optional[Dict[str, str]]:
        """Get dimension information for a context."""
        if not context_ref or context_ref not in self.contexts:
            return None
            
        entity_info = self.contexts[context_ref].get('entity', {})
        return entity_info.get('dimensions')
