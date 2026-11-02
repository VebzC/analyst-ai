"""
Utility to convert HTML files to Markdown format.
"""
import os
from pathlib import Path

from html_to_md import convert_html_to_markdown


def convert_html_file_to_markdown(html_file_path, output_file_path=None):
    """
    Converts an HTML file to Markdown format.
    
    Args:
        html_file_path (str): Path to the HTML file to convert
        output_file_path (str, optional): Path to save the output Markdown file.
            If not provided, the result is only returned but not saved.
            
    Returns:
        str: The converted Markdown content
    """
    # Check if the file exists
    if not os.path.exists(html_file_path):
        raise FileNotFoundError(f"HTML file not found: {html_file_path}")
    
    # Read the HTML file
    with open(html_file_path, 'r', encoding='utf-8') as f:
        html_content = f.read()
    
    # Convert the HTML to Markdown
    markdown_content = convert_html_to_markdown(html_content)
    
    # Save the result if output path is provided
    if output_file_path:
        output_dir = os.path.dirname(output_file_path)
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir)
            
        with open(output_file_path, 'w', encoding='utf-8') as f:
            f.write(markdown_content)
            
    return markdown_content


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Convert HTML file to Markdown")
    parser.add_argument("html_file", help="Path to the HTML file to convert")
    parser.add_argument("-o", "--output", help="Path to save the output Markdown file")
    
    args = parser.parse_args()
    
    result = convert_html_file_to_markdown(args.html_file, args.output)
    
    if not args.output:
        print(result) 