"""XBRL metadata extractor for SEC filings."""

from typing import Dict, List, Optional, Any, Set, Tuple, Union
from bs4 import BeautifulSoup, Tag
import re
from datetime import datetime

from sec_md_parser.models.document import XBRLFact


class XbrlMetadataExtractor:
    """Extracts detailed XBRL metadata from HTML/XBRL documents."""
    
    def __init__(self, html_content: str):
        """
        Initialize the XBRL metadata extractor.
        
        Args:
            html_content: HTML content as a string
        """
        self.soup = BeautifulSoup(html_content, 'lxml')
        self.namespaces = {}
        self.contexts = {}
        self.units = {}
        self.facts = []
        self.calculation_links = []
        self.presentations = []
        self.taxonomy_refs = []
        self.custom_extensions = []
        
    def extract_metadata(self) -> Dict[str, Any]:
        """
        Extract all XBRL metadata from the document.
        
        Returns:
            Dictionary containing all extracted XBRL metadata
        """
        self.namespaces = self._extract_namespaces()
        self.contexts = self._extract_contexts()
        self.units = self._extract_units()
        self.facts = self._extract_facts()
        self.calculation_links = self._extract_calculation_links()
        self.presentations = self._extract_presentation_links()
        self.taxonomy_refs = self._extract_taxonomy_refs()
        self.custom_extensions = self._extract_custom_extensions()
        
        return {
            'namespaces': self.namespaces,
            'contexts': self.contexts,
            'units': self.units,
            'facts': self.facts,
            'calculation_links': self.calculation_links,
            'presentations': self.presentations,
            'taxonomy_refs': self.taxonomy_refs,
            'custom_extensions': self.custom_extensions
        }
    
    def _extract_namespaces(self) -> Dict[str, str]:
        """
        Extract all namespaces from the document.
        
        Returns:
            Dictionary mapping namespace prefixes to URIs
        """
        namespaces = {}
        
        # Check the HTML tag first
        html_tag = self.soup.html
        if html_tag and html_tag.attrs:
            for attr, value in html_tag.attrs.items():
                if attr.startswith('xmlns:'):
                    prefix = attr[6:]  # Remove 'xmlns:'
                    namespaces[prefix] = value
        
        # Check other tags in case namespaces are defined elsewhere
        for tag in self.soup.find_all(True, limit=100):  # Limit to avoid processing the entire document
            for attr in tag.attrs:
                if attr.startswith('xmlns:'):
                    prefix = attr[6:]  # Remove 'xmlns:'
                    namespaces[prefix] = tag.attrs[attr]
        
        return namespaces
    
    def _extract_contexts(self) -> Dict[str, Dict[str, Any]]:
        """
        Extract context information from the document.
        
        Returns:
            Dictionary mapping context IDs to context details
        """
        contexts = {}
        
        # Find all context elements, handling different namespace prefixes
        context_pattern = re.compile(r'.*:context$')
        for context in self.soup.find_all(lambda tag: tag.name and re.match(context_pattern, tag.name)):
            context_id = context.get('id')
            if context_id:
                entity_info = self._extract_entity_info(context)
                period_info = self._extract_period_info(context)
                segment_info = self._extract_segment_info(context)
                scenario_info = self._extract_scenario_info(context)
                
                contexts[context_id] = {
                    'entity': entity_info,
                    'period': period_info,
                    'segment': segment_info,
                    'scenario': scenario_info
                }
        
        return contexts
    
    def _extract_entity_info(self, context_tag: Tag) -> Dict[str, Any]:
        """
        Extract entity information from a context tag.
        
        Args:
            context_tag: BeautifulSoup Tag representing a context
            
        Returns:
            Dictionary with entity information
        """
        entity_info = {'identifier': None, 'segment': None}
        
        # Find entity tag (might have different namespace prefixes)
        entity_pattern = re.compile(r'.*:entity$')
        entity_tag = context_tag.find(lambda tag: tag.name and re.match(entity_pattern, tag.name))
        
        if entity_tag:
            # Extract identifier
            identifier_pattern = re.compile(r'.*:identifier$')
            identifier_tag = entity_tag.find(lambda tag: tag.name and re.match(identifier_pattern, tag.name))
            
            if identifier_tag:
                entity_info['identifier'] = {
                    'scheme': identifier_tag.get('scheme'),
                    'value': identifier_tag.text.strip()
                }
            
            # Extract segment information (will be processed separately)
            segment_pattern = re.compile(r'.*:segment$')
            segment_tag = entity_tag.find(lambda tag: tag.name and re.match(segment_pattern, tag.name))
            
            if segment_tag:
                entity_info['segment'] = True
        
        return entity_info
    
    def _extract_period_info(self, context_tag: Tag) -> Dict[str, Any]:
        """
        Extract period information from a context tag.
        
        Args:
            context_tag: BeautifulSoup Tag representing a context
            
        Returns:
            Dictionary with period information
        """
        period_info = {'type': None}
        
        # Find period tag (might have different namespace prefixes)
        period_pattern = re.compile(r'.*:period$')
        period_tag = context_tag.find(lambda tag: tag.name and re.match(period_pattern, tag.name))
        
        if period_tag:
            # Check for instant period
            instant_pattern = re.compile(r'.*:instant$')
            instant_tag = period_tag.find(lambda tag: tag.name and re.match(instant_pattern, tag.name))
            
            if instant_tag:
                period_info['type'] = 'instant'
                period_info['instant'] = instant_tag.text.strip()
                return period_info
            
            # Check for start/end period
            start_pattern = re.compile(r'.*:(start|startDate)$')
            end_pattern = re.compile(r'.*:(end|endDate)$')
            
            start_tag = period_tag.find(lambda tag: tag.name and re.match(start_pattern, tag.name))
            end_tag = period_tag.find(lambda tag: tag.name and re.match(end_pattern, tag.name))
            
            if start_tag and end_tag:
                period_info['type'] = 'duration'
                period_info['startDate'] = start_tag.text.strip()
                period_info['endDate'] = end_tag.text.strip()
                return period_info
            
            # Check for forever period
            forever_pattern = re.compile(r'.*:forever$')
            forever_tag = period_tag.find(lambda tag: tag.name and re.match(forever_pattern, tag.name))
            
            if forever_tag:
                period_info['type'] = 'forever'
        
        return period_info
    
    def _extract_segment_info(self, context_tag: Tag) -> List[Dict[str, Any]]:
        """
        Extract segment information from a context tag.
        
        Args:
            context_tag: BeautifulSoup Tag representing a context
            
        Returns:
            List of dictionaries with segment information
        """
        segments = []
        
        # Find entity tag
        entity_pattern = re.compile(r'.*:entity$')
        entity_tag = context_tag.find(lambda tag: tag.name and re.match(entity_pattern, tag.name))
        
        if entity_tag:
            # Find segment tag
            segment_pattern = re.compile(r'.*:segment$')
            segment_tag = entity_tag.find(lambda tag: tag.name and re.match(segment_pattern, tag.name))
            
            if segment_tag:
                # Extract explicit members
                member_pattern = re.compile(r'.*:explicitMember$')
                for member_tag in segment_tag.find_all(lambda tag: tag.name and re.match(member_pattern, tag.name)):
                    dimension = member_tag.get('dimension')
                    if dimension:
                        segments.append({
                            'type': 'explicitMember',
                            'dimension': dimension,
                            'value': member_tag.text.strip()
                        })
                
                # Extract typed members
                typed_pattern = re.compile(r'.*:typedMember$')
                for typed_tag in segment_tag.find_all(lambda tag: tag.name and re.match(typed_pattern, tag.name)):
                    dimension = typed_tag.get('dimension')
                    if dimension:
                        # Extract the first child as the typed value
                        child_tags = [t for t in typed_tag.children if isinstance(t, Tag)]
                        if child_tags:
                            value_tag = child_tags[0]
                            segments.append({
                                'type': 'typedMember',
                                'dimension': dimension,
                                'domain': value_tag.name,
                                'value': value_tag.text.strip()
                            })
        
        return segments
    
    def _extract_scenario_info(self, context_tag: Tag) -> List[Dict[str, Any]]:
        """
        Extract scenario information from a context tag.
        
        Args:
            context_tag: BeautifulSoup Tag representing a context
            
        Returns:
            List of dictionaries with scenario information
        """
        scenarios = []
        
        # Find scenario tag
        scenario_pattern = re.compile(r'.*:scenario$')
        scenario_tag = context_tag.find(lambda tag: tag.name and re.match(scenario_pattern, tag.name))
        
        if scenario_tag:
            # Extract explicit members
            member_pattern = re.compile(r'.*:explicitMember$')
            for member_tag in scenario_tag.find_all(lambda tag: tag.name and re.match(member_pattern, tag.name)):
                dimension = member_tag.get('dimension')
                if dimension:
                    scenarios.append({
                        'type': 'explicitMember',
                        'dimension': dimension,
                        'value': member_tag.text.strip()
                    })
            
            # Extract typed members
            typed_pattern = re.compile(r'.*:typedMember$')
            for typed_tag in scenario_tag.find_all(lambda tag: tag.name and re.match(typed_pattern, tag.name)):
                dimension = typed_tag.get('dimension')
                if dimension:
                    # Extract the first child as the typed value
                    child_tags = [t for t in typed_tag.children if isinstance(t, Tag)]
                    if child_tags:
                        value_tag = child_tags[0]
                        scenarios.append({
                            'type': 'typedMember',
                            'dimension': dimension,
                            'domain': value_tag.name,
                            'value': value_tag.text.strip()
                        })
        
        return scenarios
    
    def _extract_units(self) -> Dict[str, Dict[str, Any]]:
        """
        Extract unit information from the document.
        
        Returns:
            Dictionary mapping unit IDs to unit details
        """
        units = {}
        
        # Find unit tags
        unit_pattern = re.compile(r'.*:unit$')
        for unit_tag in self.soup.find_all(lambda tag: tag.name and re.match(unit_pattern, tag.name)):
            unit_id = unit_tag.get('id')
            if not unit_id:
                continue
            
            # Find measure tags
            measure_pattern = re.compile(r'.*:measure$')
            measure_tags = unit_tag.find_all(lambda tag: tag.name and re.match(measure_pattern, tag.name))
            
            if measure_tags:
                # Simple unit with one or more measures
                measures = [tag.text.strip() for tag in measure_tags]
                units[unit_id] = {
                    'type': 'simple',
                    'measures': measures
                }
                continue
            
            # Check for divide structure
            divide_pattern = re.compile(r'.*:divide$')
            divide_tag = unit_tag.find(lambda tag: tag.name and re.match(divide_pattern, tag.name))
            
            if divide_tag:
                numerator_pattern = re.compile(r'.*:unitNumerator$')
                denominator_pattern = re.compile(r'.*:unitDenominator$')
                
                numerator_tag = divide_tag.find(lambda tag: tag.name and re.match(numerator_pattern, tag.name))
                denominator_tag = divide_tag.find(lambda tag: tag.name and re.match(denominator_pattern, tag.name))
                
                if numerator_tag and denominator_tag:
                    # Extract measures from numerator and denominator
                    numerator_measures = []
                    denominator_measures = []
                    
                    for measure_tag in numerator_tag.find_all(lambda tag: tag.name and re.match(measure_pattern, tag.name)):
                        numerator_measures.append(measure_tag.text.strip())
                    
                    for measure_tag in denominator_tag.find_all(lambda tag: tag.name and re.match(measure_pattern, tag.name)):
                        denominator_measures.append(measure_tag.text.strip())
                    
                    units[unit_id] = {
                        'type': 'divide',
                        'numerator': numerator_measures,
                        'denominator': denominator_measures
                    }
        
        return units
    
    def _extract_facts(self) -> List[Dict[str, Any]]:
        """
        Extract all XBRL facts from the document.
        
        Returns:
            List of dictionaries containing fact information
        """
        facts = []
        
        # Regular expression patterns for different types of facts
        inline_patterns = [
            re.compile(r'ix:nonFraction$', re.IGNORECASE),
            re.compile(r'ix:fraction$', re.IGNORECASE),
            re.compile(r'ix:nonNumeric$', re.IGNORECASE),
            re.compile(r'ix:tuple$', re.IGNORECASE),
            re.compile(r'ix:footnote$', re.IGNORECASE)
        ]
        
        # Find all inline XBRL tags
        for pattern in inline_patterns:
            for tag in self.soup.find_all(lambda t: t.name and pattern.search(t.name)):
                # Extract fact information based on tag type
                fact_type = pattern.pattern.split(':')[1].rstrip('$')
                fact_info = self._extract_fact_info(tag, fact_type)
                if fact_info:
                    facts.append(fact_info)
        
        # Also look for regular XBRL tags (non-inline)
        for tag in self.soup.find_all(True):
            # Check if this is an XBRL fact (has contextRef attribute)
            if 'contextref' in tag.attrs or 'contextRef' in tag.attrs:
                fact_info = self._extract_fact_info(tag, 'regular')
                if fact_info:
                    facts.append(fact_info)
        
        return facts
    
    def _extract_fact_info(self, tag: Tag, fact_type: str) -> Optional[Dict[str, Any]]:
        """
        Extract information from a fact tag.
        
        Args:
            tag: BeautifulSoup Tag representing a fact
            fact_type: Type of fact (nonFraction, fraction, nonNumeric, etc.)
            
        Returns:
            Dictionary with fact information or None if not a valid fact
        """
        # Get the name attribute (concept name)
        name = tag.get('name')
        if not name:
            return None
        
        # Get context reference
        context_ref = tag.get('contextref') or tag.get('contextRef')
        if not context_ref:
            return None
        
        # Basic fact information
        fact_info = {
            'type': fact_type,
            'name': name,
            'contextRef': context_ref,
            'id': tag.get('id')
        }
        
        # Get unit reference for numeric facts
        unit_ref = tag.get('unitref') or tag.get('unitRef')
        if unit_ref:
            fact_info['unitRef'] = unit_ref
        
        # Get format attribute
        format_attr = tag.get('format')
        if format_attr:
            fact_info['format'] = format_attr
        
        # Get scale attribute
        scale_attr = tag.get('scale')
        if scale_attr:
            try:
                fact_info['scale'] = int(scale_attr)
            except ValueError:
                pass
        
        # Get decimals attribute
        decimals_attr = tag.get('decimals')
        if decimals_attr:
            try:
                fact_info['decimals'] = int(decimals_attr)
            except ValueError:
                pass
        
        # Get sign attribute
        sign_attr = tag.get('sign')
        if sign_attr:
            fact_info['sign'] = sign_attr
        
        # Get other relevant attributes
        for attr in ['precision', 'order', 'tuple', 'footnoteRole', 'footnoteLinkRole']:
            if attr.lower() in tag.attrs:
                fact_info[attr] = tag.attrs[attr.lower()]
        
        # Get the value
        if fact_type == 'nonFraction' or fact_type == 'nonNumeric' or fact_type == 'regular':
            # Handle continuation elements
            continuation_elements = []
            if 'continuedAt' in tag.attrs:
                continued_at = tag.get('continuedAt')
                continuation_elements = self.soup.find_all(lambda t: t.name and 'id' in t.attrs and t.attrs['id'] == continued_at)
            
            # Get text content
            value = tag.get_text(strip=True)
            
            # Add continuation text
            for elem in continuation_elements:
                value += elem.get_text(strip=True)
            
            fact_info['value'] = value
        
        elif fact_type == 'fraction':
            # Handle fractions (numerator and denominator)
            numerator_tag = tag.find('ix:numerator')
            denominator_tag = tag.find('ix:denominator')
            
            if numerator_tag and denominator_tag:
                fact_info['value'] = {
                    'numerator': numerator_tag.get_text(strip=True),
                    'denominator': denominator_tag.get_text(strip=True)
                }
            else:
                fact_info['value'] = tag.get_text(strip=True)
        
        # Add context and unit information
        if context_ref in self.contexts:
            fact_info['context'] = self.contexts[context_ref]
        
        if 'unitRef' in fact_info and fact_info['unitRef'] in self.units:
            fact_info['unit'] = self.units[fact_info['unitRef']]
        
        return fact_info
    
    def _extract_calculation_links(self) -> List[Dict[str, Any]]:
        """
        Extract calculation relationships from the document.
        
        Returns:
            List of dictionaries representing calculation relationships
        """
        calculation_links = []
        
        # Look for link:calculationLink elements
        calc_link_pattern = re.compile(r'.*:calculationLink$')
        for calc_link in self.soup.find_all(lambda tag: tag.name and re.match(calc_link_pattern, tag.name)):
            role = calc_link.get('xlink:role') or calc_link.get('role')
            
            # Look for link:calculationArc elements
            calc_arc_pattern = re.compile(r'.*:calculationArc$')
            for calc_arc in calc_link.find_all(lambda tag: tag.name and re.match(calc_arc_pattern, tag.name)):
                from_attr = calc_arc.get('xlink:from') or calc_arc.get('from')
                to_attr = calc_arc.get('xlink:to') or calc_arc.get('to')
                weight = calc_arc.get('weight')
                order = calc_arc.get('order')
                
                if from_attr and to_attr:
                    calculation_links.append({
                        'role': role,
                        'from': from_attr,
                        'to': to_attr,
                        'weight': weight,
                        'order': order
                    })
        
        return calculation_links
    
    def _extract_presentation_links(self) -> List[Dict[str, Any]]:
        """
        Extract presentation relationships from the document.
        
        Returns:
            List of dictionaries representing presentation relationships
        """
        presentation_links = []
        
        # Look for link:presentationLink elements
        pres_link_pattern = re.compile(r'.*:presentationLink$')
        for pres_link in self.soup.find_all(lambda tag: tag.name and re.match(pres_link_pattern, tag.name)):
            role = pres_link.get('xlink:role') or pres_link.get('role')
            
            # Look for link:presentationArc elements
            pres_arc_pattern = re.compile(r'.*:presentationArc$')
            for pres_arc in pres_link.find_all(lambda tag: tag.name and re.match(pres_arc_pattern, tag.name)):
                from_attr = pres_arc.get('xlink:from') or pres_arc.get('from')
                to_attr = pres_arc.get('xlink:to') or pres_arc.get('to')
                preferred_label = pres_arc.get('preferredLabel')
                order = pres_arc.get('order')
                
                if from_attr and to_attr:
                    presentation_links.append({
                        'role': role,
                        'from': from_attr,
                        'to': to_attr,
                        'preferredLabel': preferred_label,
                        'order': order
                    })
        
        return presentation_links
    
    def _extract_taxonomy_refs(self) -> List[Dict[str, str]]:
        """
        Extract taxonomy references from the document.
        
        Returns:
            List of dictionaries with taxonomy references
        """
        taxonomy_refs = []
        
        # Look for link:schemaRef elements
        schema_ref_pattern = re.compile(r'.*:schemaRef$')
        for schema_ref in self.soup.find_all(lambda tag: tag.name and re.match(schema_ref_pattern, tag.name)):
            href = schema_ref.get('xlink:href') or schema_ref.get('href')
            if href:
                taxonomy_refs.append({
                    'type': 'schema',
                    'href': href
                })
        
        # Look for link:linkbaseRef elements
        linkbase_ref_pattern = re.compile(r'.*:linkbaseRef$')
        for linkbase_ref in self.soup.find_all(lambda tag: tag.name and re.match(linkbase_ref_pattern, tag.name)):
            href = linkbase_ref.get('xlink:href') or linkbase_ref.get('href')
            role = linkbase_ref.get('xlink:role') or linkbase_ref.get('role')
            
            if href:
                taxonomy_refs.append({
                    'type': 'linkbase',
                    'href': href,
                    'role': role
                })
        
        return taxonomy_refs
    
    def _extract_custom_extensions(self) -> List[Dict[str, Any]]:
        """
        Extract custom taxonomy extensions from the document.
        
        Returns:
            List of dictionaries with custom extensions
        """
        custom_extensions = []
        
        # A more comprehensive implementation would parse the taxonomy schema
        # files to identify custom elements. This is a simplified approach:
        
        # Identify potential custom elements in the facts
        standard_prefixes = {'us-gaap', 'ifrs', 'dei', 'currency', 'iso4217', 'xbrli', 'link', 'xlink'}
        
        # Collect all fact names with prefixes
        for fact in self.facts:
            name = fact.get('name')
            if name and ':' in name:
                prefix, local_name = name.split(':', 1)
                if prefix.lower() not in standard_prefixes:
                    # This might be a custom extension
                    custom_extensions.append({
                        'prefix': prefix,
                        'name': local_name,
                        'fullName': name
                    })
        
        # Remove duplicates by full name
        unique_extensions = []
        seen = set()
        
        for ext in custom_extensions:
            if ext['fullName'] not in seen:
                seen.add(ext['fullName'])
                unique_extensions.append(ext)
        
        return unique_extensions
    
    def get_xbrl_facts(self) -> List[XBRLFact]:
        """
        Convert extracted facts to XBRLFact objects.
        
        Returns:
            List of XBRLFact objects
        """
        xbrl_facts = []
        
        for fact_dict in self.facts:
            # Skip facts without name or value
            if 'name' not in fact_dict or 'value' not in fact_dict:
                continue
            
            # Extract basic properties
            name = fact_dict.get('name')
            value = fact_dict.get('value')
            context_ref = fact_dict.get('contextRef')
            unit_ref = fact_dict.get('unitRef')
            
            # Parse numeric attributes
            decimals = fact_dict.get('decimals')
            if decimals and isinstance(decimals, str):
                try:
                    decimals = int(decimals)
                except ValueError:
                    decimals = None
            
            scale = fact_dict.get('scale')
            if scale and isinstance(scale, str):
                try:
                    scale = int(scale)
                except ValueError:
                    scale = None
            
            # Extract period information
            period = None
            dimension = None
            
            if context_ref and context_ref in self.contexts:
                context = self.contexts[context_ref]
                period_info = context.get('period', {})
                
                if period_info.get('type') == 'instant':
                    period = period_info.get('instant')
                elif period_info.get('type') == 'duration':
                    period = f"{period_info.get('startDate')} to {period_info.get('endDate')}"
                
                # Extract dimensions from segment
                segments = context.get('segment', [])
                if segments:
                    dimension = {}
                    for segment in segments:
                        if segment.get('type') == 'explicitMember':
                            dimension[segment.get('dimension')] = segment.get('value')
            
            # Create XBRLFact object
            xbrl_fact = XBRLFact(
                name=name,
                value=value,
                context_ref=context_ref,
                unit_ref=unit_ref,
                decimals=decimals,
                scale=scale,
                format=fact_dict.get('format'),
                sign=fact_dict.get('sign'),
                balance=None,  # Would need to be determined from taxonomy
                period=period,
                dimension=dimension
            )
            
            xbrl_facts.append(xbrl_fact)
        
        return xbrl_facts
