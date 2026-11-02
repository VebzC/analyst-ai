#!/usr/bin/env python3
"""
Simple script to convert an SEC filing to pure markdown without analysis.
Usage: python convert_to_markdown.py <input_file> <output_file>
"""

import sys
import os
from sec_md_parser import SECParser

def convert_to_markdown(input_file, output_file):
    """Convert SEC filing to markdown without any analysis."""
    print(f"Converting {input_file} to markdown...")
    
    # Initialize the parser
    parser = SECParser()
    
    # Read the input file
    with open(input_file, 'r', encoding='utf-8') as f:
        html_content = f.read()
    
    # Parse the HTML content
    document = parser.parse_from_html(html_content)
    
    # Convert to markdown (without any additional analysis)
    markdown = parser.document_to_markdown(document)
    
    # Create the output directory if it doesn't exist
    os.makedirs(os.path.dirname(os.path.abspath(output_file)), exist_ok=True)
    
    # Write the markdown to the output file
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(markdown)
    
    print(f"Conversion complete. Markdown saved to {output_file}")
    print(f"Document contained {len(document.xbrl_facts)} XBRL facts (not included in markdown)")

def main():
    """Main function."""
    # Check arguments
    if len(sys.argv) != 3:
        print("Usage: python convert_to_markdown.py <input_file> <output_file>")
        sys.exit(1)
    
    input_file = sys.argv[1]
    output_file = sys.argv[2]
    
    # Check if input file exists
    if not os.path.exists(input_file):
        print(f"Error: Input file {input_file} does not exist")
        sys.exit(1)
    
    # Convert to markdown
    convert_to_markdown(input_file, output_file)

if __name__ == "__main__":
    main() 