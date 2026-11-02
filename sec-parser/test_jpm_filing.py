#!/usr/bin/env python3
"""
Test script to parse a JPMorgan Chase SEC filing using the sec_md_parser library.
This script downloads the filing from the SEC website and converts it to markdown.
"""

import requests
import os
from pathlib import Path
from sec_md_parser import SECParser

# URL of the JPMorgan Chase SEC filing
SEC_URL = "https://www.sec.gov/ix?doc=/Archives/edgar/data/0000019617/000001961724000611/jpm-20240930.htm"

# Headers to avoid being blocked by SEC.gov
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1",
}

def download_sec_filing(url, output_dir="output"):
    """Download an SEC filing from the given URL."""
    print(f"Downloading SEC filing from {url}...")
    
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    # Extract filename from URL
    filename = url.split("/")[-1]
    filepath = os.path.join(output_dir, filename)
    
    # Download the file
    response = requests.get(url, headers=HEADERS)
    response.raise_for_status()
    
    # Save the HTML content
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(response.text)
    
    print(f"Filing downloaded and saved to {filepath}")
    return filepath, response.text

def parse_sec_filing(html_content, output_dir="output"):
    """Parse an SEC filing using sec_md_parser and save the result."""
    print("Parsing SEC filing...")
    
    # Initialize the parser
    parser = SECParser()
    
    # Parse the HTML content
    document = parser.parse_from_html(html_content)
    
    # Extract metadata
    print("\nMetadata:")
    for key, value in document.metadata.items():
        print(f"  {key}: {value}")
    
    # Convert to markdown
    markdown = parser.document_to_markdown(document)
    
    # Save the markdown content
    markdown_path = os.path.join(output_dir, "jpm-filing.md")
    with open(markdown_path, "w", encoding="utf-8") as f:
        f.write(markdown)
    
    print(f"\nMarkdown output saved to {markdown_path}")
    
    # Print XBRL facts statistics
    if document.xbrl_facts:
        print(f"\nExtracted {len(document.xbrl_facts)} XBRL facts")
        
        # Group facts by name
        fact_counts = {}
        for fact in document.xbrl_facts:
            if fact.name not in fact_counts:
                fact_counts[fact.name] = 0
            fact_counts[fact.name] += 1
        
        print("\nTop 10 XBRL fact types:")
        for name, count in sorted(fact_counts.items(), key=lambda x: x[1], reverse=True)[:10]:
            print(f"  {name}: {count}")
    
    return document, markdown

def main():
    """Main function to download and parse an SEC filing."""
    try:
        # Download the SEC filing
        _, html_content = download_sec_filing(SEC_URL)
        
        # Parse the SEC filing
        document, markdown = parse_sec_filing(html_content)
        
        # Print a sample of the markdown
        print("\nSample of markdown output (first 500 characters):")
        print(markdown[:500] + "...")
        
        print("\nProcessing complete!")
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main() 