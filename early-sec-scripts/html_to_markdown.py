#!/usr/bin/env python3
"""
HTML to Markdown Converter

This script provides functionality to convert HTML content to Markdown format
using the html2text library. It includes a main function that demonstrates
the conversion using a sample HTML file.
"""

import html2text
from pathlib import Path
from typing import Optional


def convert_html_to_markdown(html_str: str) -> str:
    """
    Convert HTML string to Markdown format using html2text.
    
    Args:
        html_str (str): Input HTML string to convert
        
    Returns:
        str: Converted Markdown string
        
    Example:
        >>> html = "<h1>Hello</h1>"
        >>> convert_html_to_markdown(html)
        '# Hello\n'
    """
    # Initialize html2text converter with default settings
    h = html2text.HTML2Text()
    
    # Convert HTML to Markdown
    markdown = h.handle(html_str)
    
    return markdown


def read_html_file(file_path: str) -> Optional[str]:
    """
    Read contents of an HTML file.
    
    Args:
        file_path (str): Path to the HTML file
        
    Returns:
        Optional[str]: Contents of the file if successful, None otherwise
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        print(f"Error reading file: {e}")
        return None


def main():
    """Main function to demonstrate HTML to Markdown conversion."""
    # Get the directory where this script is located
    script_dir = Path(__file__).parent
    
    # Path to sample HTML file
    sample_file = script_dir / "sample.html"
    
    # Read the sample HTML file
    html_content = read_html_file(str(sample_file))
    
    if html_content:
        # Convert HTML to Markdown
        markdown_content = convert_html_to_markdown(html_content)
        
        # Print the converted Markdown
        print("Converted Markdown:")
        print("-" * 50)
        print(markdown_content)
    else:
        print("Failed to read HTML file")


if __name__ == "__main__":
    main() 