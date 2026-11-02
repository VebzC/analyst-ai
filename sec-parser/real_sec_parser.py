#!/usr/bin/env python3
"""
SEC filing parser for real-world usage with robust error handling.

This script can:
1. Download and parse an SEC filing from a URL or local file
2. Extract XBRL data and generate enhanced markdown with financial analysis
3. Handle connection issues with SEC.gov by using a local cache
4. Support both online and offline modes

Usage:
    python real_sec_parser.py --url <sec_filing_url>
    python real_sec_parser.py --file <local_html_file>
"""

import os
import re
import json
import argparse
import requests
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple, Optional, Any, Union
from sec_md_parser import SECParser
from sec_md_parser.models.base import XBRLFact

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("sec_parser.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("sec_parser")

# Constants
USER_AGENT = "AnalystAI Research Tool your-email@example.com"
CACHE_DIR = "sec_cache"
OUTPUT_DIR = "sec_output"

class SECFilingParser:
    """Wrapper around sec_md_parser with enhanced functionality."""
    
    def __init__(self, use_cache: bool = True):
        """Initialize the SEC filing parser.
        
        Args:
            use_cache: Whether to use cached files if available
        """
        self.parser = SECParser()
        self.use_cache = use_cache
        
        # Create necessary directories
        os.makedirs(CACHE_DIR, exist_ok=True)
        os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    def download_filing(self, url: str) -> Tuple[str, str]:
        """Download an SEC filing from the given URL.
        
        Args:
            url: URL of the SEC filing
            
        Returns:
            Tuple of (HTML content, cache file path)
        
        Raises:
            requests.RequestException: If the download fails
        """
        # Generate cache filename from URL
        file_hash = str(abs(hash(url)))
        cache_path = os.path.join(CACHE_DIR, f"{file_hash}.html")
        
        # Check cache first if enabled
        if self.use_cache and os.path.exists(cache_path):
            logger.info(f"Using cached filing from {cache_path}")
            with open(cache_path, "r", encoding="utf-8") as f:
                return f.read(), cache_path
        
        # Download the filing
        logger.info(f"Downloading SEC filing from {url}")
        headers = {
            "User-Agent": USER_AGENT,
            "Accept-Encoding": "gzip, deflate",
            "Host": "www.sec.gov"
        }
        
        try:
            response = requests.get(url, headers=headers, timeout=30)
            response.raise_for_status()
            html_content = response.text
            
            # Save to cache
            with open(cache_path, "w", encoding="utf-8") as f:
                f.write(html_content)
            
            logger.info(f"Filing downloaded and cached to {cache_path}")
            return html_content, cache_path
            
        except requests.RequestException as e:
            logger.error(f"Failed to download filing: {e}")
            raise
    
    def load_filing_from_file(self, file_path: str) -> str:
        """Load an SEC filing from a local file.
        
        Args:
            file_path: Path to the local HTML file
            
        Returns:
            HTML content
        """
        logger.info(f"Loading SEC filing from {file_path}")
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read()
    
    def parse_filing(self, html_content: str) -> Tuple[Any, Dict[str, Any], str]:
        """Parse an SEC filing and generate enhanced markdown.
        
        Args:
            html_content: HTML content of the SEC filing
            
        Returns:
            Tuple of (document, metadata dict, enhanced markdown)
        """
        logger.info("Parsing SEC filing")
        
        # Parse the HTML content
        document = self.parser.parse_from_html(html_content)
        
        # Extract metadata
        metadata = document.metadata
        logger.info(f"Extracted metadata: {metadata}")
        
        # Convert to markdown
        standard_markdown = self.parser.document_to_markdown(document)
        
        # Generate enhanced markdown with XBRL data
        enhanced_markdown = self._generate_enhanced_markdown(document, standard_markdown)
        
        return document, metadata, enhanced_markdown
    
    def _generate_enhanced_markdown(self, document: Any, original_markdown: str) -> str:
        """Generate enhanced markdown with XBRL data analysis.
        
        Args:
            document: Parsed SEC document
            original_markdown: Original markdown content
            
        Returns:
            Enhanced markdown with XBRL data analysis
        """
        # Start with original markdown
        enhanced_md = original_markdown
        
        # If no XBRL facts, return original markdown
        if not document.xbrl_facts:
            logger.warning("No XBRL facts found in document")
            return enhanced_md
        
        # Add XBRL data section
        enhanced_md += "\n\n# XBRL Data Analysis\n\n"
        
        # Group XBRL facts by name
        fact_by_name = {}
        for fact in document.xbrl_facts:
            if fact.name not in fact_by_name:
                fact_by_name[fact.name] = []
            fact_by_name[fact.name].append(fact)
        
        # Create sections for each fact type
        for fact_name, facts in fact_by_name.items():
            enhanced_md += f"## {fact_name}\n\n"
            enhanced_md += "| Value | Context | Unit | Decimals |\n"
            enhanced_md += "| --- | --- | --- | --- |\n"
            
            for fact in facts:
                enhanced_md += f"| {fact.value} | {fact.context_ref} | {fact.unit_ref} | {fact.decimals} |\n"
            
            enhanced_md += "\n"
        
        # Add financial analysis section if we have common financial metrics
        if any(name in fact_by_name for name in [
            "us-gaap:Revenue", "us-gaap:NetIncome", 
            "us-gaap:EarningsPerShareBasic", "us-gaap:Assets"
        ]):
            enhanced_md += self._generate_financial_analysis(fact_by_name)
        
        return enhanced_md
    
    def _generate_financial_analysis(self, fact_by_name: Dict[str, List[XBRLFact]]) -> str:
        """Generate financial analysis section based on XBRL facts.
        
        Args:
            fact_by_name: Dictionary of XBRL facts grouped by name
            
        Returns:
            Financial analysis markdown section
        """
        analysis_md = "\n\n# Financial Analysis\n\n"
        
        # Try to find the most recent quarter
        current_quarter = None
        previous_quarter = None
        
        # Look for context references that match quarterly patterns
        quarterly_pattern = re.compile(r'duration_(\d{4})-(\d{2})-(\d{2})_(\d{4})-(\d{2})-(\d{2})')
        
        contexts = set()
        for facts in fact_by_name.values():
            for fact in facts:
                if fact.context_ref:
                    contexts.add(fact.context_ref)
        
        # Find quarters
        quarterly_contexts = []
        for context in contexts:
            match = quarterly_pattern.match(context)
            if match:
                start_year, start_month, start_day, end_year, end_month, end_day = match.groups()
                start_date = datetime(int(start_year), int(start_month), int(start_day))
                end_date = datetime(int(end_year), int(end_month), int(end_day))
                
                # Calculate duration in days
                duration = (end_date - start_date).days
                
                # If duration is roughly a quarter (60-120 days)
                if 60 <= duration <= 120:
                    quarterly_contexts.append((context, end_date))
        
        # Sort by end date, most recent first
        quarterly_contexts.sort(key=lambda x: x[1], reverse=True)
        
        # Get current and previous quarter contexts
        if len(quarterly_contexts) >= 1:
            current_quarter = quarterly_contexts[0][0]
        if len(quarterly_contexts) >= 2:
            previous_quarter = quarterly_contexts[1][0]
        
        # Analyze revenue if available
        if "us-gaap:Revenue" in fact_by_name and current_quarter:
            revenue_facts = fact_by_name["us-gaap:Revenue"]
            
            # Get current quarter revenue
            current_revenue = next(
                (fact for fact in revenue_facts if fact.context_ref == current_quarter), 
                None
            )
            
            if current_revenue:
                analysis_md += f"## Revenue Analysis\n\n"
                
                try:
                    current_rev_value = self._parse_number(current_revenue.value)
                    analysis_md += f"* Current Quarter Revenue: ${self._format_number(current_rev_value)}\n"
                    
                    # Compare with previous quarter if available
                    if previous_quarter:
                        prev_revenue = next(
                            (fact for fact in revenue_facts if fact.context_ref == previous_quarter), 
                            None
                        )
                        
                        if prev_revenue:
                            prev_rev_value = self._parse_number(prev_revenue.value)
                            growth = ((current_rev_value - prev_rev_value) / prev_rev_value) * 100
                            analysis_md += f"* Previous Quarter Revenue: ${self._format_number(prev_rev_value)}\n"
                            analysis_md += f"* Quarter-over-Quarter Growth: {growth:.2f}%\n"
                    
                    analysis_md += "\n"
                    
                except (ValueError, TypeError) as e:
                    logger.warning(f"Error processing revenue values: {e}")
                    analysis_md += "* Could not analyze revenue due to data format issues\n\n"
        
        # Analyze net income if available
        if "us-gaap:NetIncome" in fact_by_name and current_quarter:
            income_facts = fact_by_name["us-gaap:NetIncome"]
            
            # Get current quarter net income
            current_income = next(
                (fact for fact in income_facts if fact.context_ref == current_quarter), 
                None
            )
            
            if current_income:
                analysis_md += f"## Profitability Analysis\n\n"
                
                try:
                    current_inc_value = self._parse_number(current_income.value)
                    analysis_md += f"* Current Quarter Net Income: ${self._format_number(current_inc_value)}\n"
                    
                    # Calculate profit margin if we have revenue
                    if "us-gaap:Revenue" in fact_by_name:
                        current_revenue = next(
                            (fact for fact in fact_by_name["us-gaap:Revenue"] if fact.context_ref == current_quarter), 
                            None
                        )
                        
                        if current_revenue:
                            current_rev_value = self._parse_number(current_revenue.value)
                            margin = (current_inc_value / current_rev_value) * 100
                            analysis_md += f"* Profit Margin: {margin:.2f}%\n"
                    
                    # Compare with previous quarter if available
                    if previous_quarter:
                        prev_income = next(
                            (fact for fact in income_facts if fact.context_ref == previous_quarter), 
                            None
                        )
                        
                        if prev_income:
                            prev_inc_value = self._parse_number(prev_income.value)
                            growth = ((current_inc_value - prev_inc_value) / prev_inc_value) * 100
                            analysis_md += f"* Previous Quarter Net Income: ${self._format_number(prev_inc_value)}\n"
                            analysis_md += f"* Quarter-over-Quarter Growth: {growth:.2f}%\n"
                    
                    analysis_md += "\n"
                    
                except (ValueError, TypeError) as e:
                    logger.warning(f"Error processing net income values: {e}")
                    analysis_md += "* Could not analyze net income due to data format issues\n\n"
        
        # Add more analysis sections as needed (EPS, Assets, etc.)
        return analysis_md
    
    def _parse_number(self, value_str: str) -> float:
        """Parse a numeric string to float.
        
        Args:
            value_str: String containing a number
            
        Returns:
            Parsed float value
        """
        # Remove commas and other non-numeric characters
        clean_str = re.sub(r'[^\d.-]', '', value_str)
        return float(clean_str)
    
    def _format_number(self, num: float) -> str:
        """Format a number for display.
        
        Args:
            num: Number to format
            
        Returns:
            Formatted string
        """
        if num >= 1e9:
            return f"{num/1e9:.2f} billion"
        elif num >= 1e6:
            return f"{num/1e6:.2f} million"
        elif num >= 1e3:
            return f"{num/1e3:.2f} thousand"
        else:
            return f"{num:,.2f}"
    
    def save_outputs(self, 
                    document: Any, 
                    metadata: Dict[str, Any], 
                    markdown: str, 
                    prefix: str = "") -> Dict[str, str]:
        """Save all outputs to files.
        
        Args:
            document: Parsed SEC document
            metadata: Document metadata
            markdown: Enhanced markdown content
            prefix: Prefix for output files
            
        Returns:
            Dict mapping output type to file path
        """
        # Generate a filename from metadata
        if not prefix and "cik" in metadata and "filing_date" in metadata:
            prefix = f"{metadata['cik']}_{metadata['filing_date']}"
        elif not prefix:
            prefix = f"sec_filing_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        output_files = {}
        
        # Save markdown
        md_path = os.path.join(OUTPUT_DIR, f"{prefix}_enhanced.md")
        with open(md_path, "w", encoding="utf-8") as f:
            f.write(markdown)
        output_files["markdown"] = md_path
        logger.info(f"Enhanced markdown saved to {md_path}")
        
        # Save XBRL facts as JSON
        if document.xbrl_facts:
            xbrl_facts = [fact.to_dict() for fact in document.xbrl_facts]
            json_path = os.path.join(OUTPUT_DIR, f"{prefix}_xbrl.json")
            with open(json_path, "w", encoding="utf-8") as f:
                json.dump(xbrl_facts, f, indent=2)
            output_files["xbrl_json"] = json_path
            logger.info(f"XBRL facts saved to {json_path}")
        
        # Save metadata
        meta_path = os.path.join(OUTPUT_DIR, f"{prefix}_metadata.json")
        with open(meta_path, "w", encoding="utf-8") as f:
            json.dump(metadata, f, indent=2)
        output_files["metadata"] = meta_path
        logger.info(f"Metadata saved to {meta_path}")
        
        return output_files

def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Parse SEC filings from URL or local file")
    
    input_group = parser.add_mutually_exclusive_group(required=True)
    input_group.add_argument("--url", help="URL of SEC filing to parse")
    input_group.add_argument("--file", help="Local HTML file to parse")
    
    parser.add_argument("--no-cache", action="store_true", help="Disable caching of SEC filings")
    parser.add_argument("--output-prefix", help="Prefix for output files")
    parser.add_argument("--verbose", action="store_true", help="Enable verbose logging")
    
    return parser.parse_args()

def main():
    """Main entry point."""
    args = parse_args()
    
    # Set logging level
    if args.verbose:
        logger.setLevel(logging.DEBUG)
    
    # Initialize parser
    sec_parser = SECFilingParser(use_cache=not args.no_cache)
    
    try:
        # Get HTML content
        if args.url:
            try:
                html_content, cache_path = sec_parser.download_filing(args.url)
                print(f"Filing downloaded from {args.url}")
            except requests.RequestException as e:
                print(f"Error downloading filing: {e}")
                print("Please try using a local HTML file instead with --file")
                return 1
        else:
            html_content = sec_parser.load_filing_from_file(args.file)
            print(f"Filing loaded from {args.file}")
        
        # Parse the filing
        document, metadata, enhanced_markdown = sec_parser.parse_filing(html_content)
        
        # Save outputs
        output_files = sec_parser.save_outputs(
            document, 
            metadata, 
            enhanced_markdown, 
            prefix=args.output_prefix
        )
        
        # Print summary
        print("\nParsing complete!")
        print(f"Title: {metadata.get('title', 'Unknown')}")
        print(f"Document type: {metadata.get('document_type', 'Unknown')}")
        print(f"Filing date: {metadata.get('filing_date', 'Unknown')}")
        print(f"CIK: {metadata.get('cik', 'Unknown')}")
        
        if document.xbrl_facts:
            print(f"Extracted {len(document.xbrl_facts)} XBRL facts")
            
            # Group facts by name
            fact_counts = {}
            for fact in document.xbrl_facts:
                if fact.name not in fact_counts:
                    fact_counts[fact.name] = 0
                fact_counts[fact.name] += 1
            
            print("\nXBRL fact types:")
            for name, count in sorted(fact_counts.items(), key=lambda x: x[1], reverse=True)[:10]:
                print(f"  {name}: {count}")
            
            if len(fact_counts) > 10:
                print(f"  ... and {len(fact_counts) - 10} more types")
        
        print("\nOutput files:")
        for output_type, file_path in output_files.items():
            print(f"  {output_type}: {file_path}")
        
        return 0
        
    except Exception as e:
        logger.exception(f"Error processing SEC filing: {e}")
        print(f"Error: {e}")
        return 1

if __name__ == "__main__":
    exit_code = main()
    exit(exit_code) 