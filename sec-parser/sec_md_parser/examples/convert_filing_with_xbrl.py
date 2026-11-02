#!/usr/bin/env python
"""
Example script demonstrating how to parse an SEC filing with XBRL data and convert it to Markdown.

This example:
1. Downloads a 10-Q filing with XBRL data
2. Parses it using the SECParser
3. Extracts XBRL facts and financial tables
4. Converts the document to Markdown with financial metadata
"""

import os
import argparse
import logging
import requests
from pathlib import Path

from sec_md_parser import SECParser


def setup_logging(verbose: bool = False) -> None:
    """Set up logging configuration."""
    log_level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[logging.StreamHandler()],
    )


def download_filing(url: str, output_dir: str) -> str:
    """
    Download an SEC filing from a URL.
    
    Args:
        url: URL to the SEC filing
        output_dir: Directory to save the filing
        
    Returns:
        Path to the downloaded file
    """
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    # Download the filing
    response = requests.get(url, headers={
        'User-Agent': 'SEC-MD-Parser/0.1.0 (example script; research use)'
    })
    response.raise_for_status()
    
    # Extract filename from URL
    filename = url.split('/')[-1]
    if not filename:
        filename = "sec_filing.html"
    
    # Save the filing
    file_path = os.path.join(output_dir, filename)
    with open(file_path, "wb") as f:
        f.write(response.content)
    
    return file_path


def main() -> None:
    """Run the example script."""
    parser = argparse.ArgumentParser(
        description="Example script for parsing an SEC filing with XBRL data"
    )
    
    parser.add_argument(
        "--url", 
        type=str, 
        default="https://www.sec.gov/Archives/edgar/data/320193/000032019323000077/aapl-20230701.htm",
        help="URL to the SEC filing (defaults to an Apple 10-Q)"
    )
    
    parser.add_argument(
        "--output-dir", 
        type=str, 
        default="output", 
        help="Directory to save the output files"
    )
    
    parser.add_argument(
        "-v", "--verbose", 
        action="store_true", 
        help="Enable verbose logging"
    )
    
    args = parser.parse_args()
    setup_logging(args.verbose)
    
    # Get logger
    logger = logging.getLogger(__name__)
    
    # Download the filing
    logger.info(f"Downloading SEC filing from {args.url}")
    try:
        file_path = download_filing(args.url, args.output_dir)
        logger.info(f"Downloaded filing to {file_path}")
    except Exception as e:
        logger.error(f"Error downloading filing: {str(e)}")
        return
    
    # Create output directory
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Initialize the parser
    parser = SECParser()
    
    # Read the HTML content
    with open(file_path, "r", encoding="utf-8") as f:
        html_content = f.read()
    
    # Parse the document
    logger.info("Parsing the SEC filing")
    document = parser.parse_from_html(html_content)
    
    # Save document as JSON
    json_path = output_dir / "document.json"
    with open(json_path, "w", encoding="utf-8") as f:
        f.write(document.to_json())
    logger.info(f"Saved document as JSON to {json_path}")
    
    # Extract XBRL facts
    logger.info(f"Extracted {len(document.xbrl_facts)} XBRL facts")
    
    # Save XBRL facts as JSON
    if document.xbrl_facts:
        xbrl_path = output_dir / "xbrl_facts.json"
        with open(xbrl_path, "w", encoding="utf-8") as f:
            import json
            json.dump([fact.to_dict() for fact in document.xbrl_facts], f, indent=2)
        logger.info(f"Saved XBRL facts to {xbrl_path}")
    
    # Extract tables
    tables = document.extract_tables()
    logger.info(f"Extracted {len(tables)} tables from the document")
    
    # Save tables as JSON
    tables_path = output_dir / "tables.json"
    with open(tables_path, "w", encoding="utf-8") as f:
        import json
        json.dump(tables, f, indent=2)
    logger.info(f"Saved tables to {tables_path}")
    
    # Analyze the document
    analysis = document.analyze()
    
    # Save analysis as JSON
    analysis_path = output_dir / "analysis.json"
    with open(analysis_path, "w", encoding="utf-8") as f:
        import json
        json.dump(analysis, f, indent=2)
    logger.info(f"Saved document analysis to {analysis_path}")
    
    # Convert to Markdown with XBRL data
    logger.info("Converting document to Markdown with XBRL data")
    markdown_with_xbrl = document.to_markdown(include_xbrl=True, include_financial_metadata=True)
    
    # Save Markdown with XBRL data
    md_with_xbrl_path = output_dir / "document_with_xbrl.md"
    with open(md_with_xbrl_path, "w", encoding="utf-8") as f:
        f.write(markdown_with_xbrl)
    logger.info(f"Saved Markdown with XBRL data to {md_with_xbrl_path}")
    
    # Convert to Markdown without XBRL data
    logger.info("Converting document to Markdown without XBRL data")
    markdown_without_xbrl = document.to_markdown(include_xbrl=False, include_financial_metadata=False)
    
    # Save Markdown without XBRL data
    md_without_xbrl_path = output_dir / "document_without_xbrl.md"
    with open(md_without_xbrl_path, "w", encoding="utf-8") as f:
        f.write(markdown_without_xbrl)
    logger.info(f"Saved Markdown without XBRL data to {md_without_xbrl_path}")
    
    # Print summary
    logger.info("\nSummary:")
    logger.info(f"- Document metadata: {len(document.metadata)} attributes")
    logger.info(f"- XBRL facts: {len(document.xbrl_facts)}")
    logger.info(f"- Tables: {len(tables)}")
    
    if 'structure' in analysis:
        structure = analysis['structure']
        logger.info(f"- Document structure: {structure.get('sections', 0)} sections, "
                   f"{structure.get('headings', 0)} headings, "
                   f"{structure.get('paragraphs', 0)} paragraphs")
    
    if 'financial_sections' in analysis:
        logger.info(f"- Financial sections: {len(analysis['financial_sections'])}")
        for section in analysis['financial_sections']:
            logger.info(f"  - {section['type']}: {section['tables']} tables, {section['xbrl_facts']} XBRL facts")


if __name__ == "__main__":
    main() 