"""
Integration tests for the markdown cleaner with the HTML to Markdown pipeline.
"""
import pytest
from bs4 import BeautifulSoup
from html_to_md.parser import build_semantic_tree, render_tree_to_markdown
from html_to_md.markdown_cleaner import clean_markdown
from html_to_md.converter import convert_html_to_markdown


def test_cleaner_integration_with_parser():
    """Test that the markdown cleaner works correctly with the parser pipeline."""
    # Sample HTML with issues that the cleaner should fix
    html = """
    <html>
    <body>
        <h1>Test Document</h1>
        <p>Some content with trailing spaces    </p>
        <ul>
            <li></li>
            <li>Item 1</li>
            <li>
            Item 2 with line break
            </li>
        </ul>
        <hr>
        <table>
            <tr>
                <th>Column 1</th>
                <th>Column 2</th>
                <th>Column 3</th>
            </tr>
            <tr>
                <td>Data 1</td>
                <td>Data 2</td>
                <td></td>
            </tr>
            <tr>
                <td>More data</td>
                <td>More info</td>
                <td></td>
            </tr>
        </table>
        <p>Footer text</p>
        <p>Footer text</p>
        <p>Footer text</p>
        <p>Footer text</p>
    </body>
    </html>
    """
    
    # Convert directly through the pipeline
    result = convert_html_to_markdown(html)
    
    # Verify specific cleanup features worked
    
    # 1. No trailing whitespace
    assert "trailing spaces    " not in result
    assert "trailing spaces" in result
    
    # 2. Table formatting
    assert "| Column 1 | Column 2 | Column 3" in result  # No trailing pipe
    
    # 3. Empty list items handled
    assert "* \n*" not in result  # No empty list items
    
    # 4. Repeated footer removed
    footer_count = result.count("Footer text")
    assert footer_count == 1, f"Expected 1 footer, found {footer_count}"
    
    # 5. Two newlines after heading
    assert "# Test Document\n\n" in result


def test_multi_stage_pipeline():
    """Test that the cleaner works correctly in a multi-stage pipeline."""
    html = """
    <html>
    <body>
        <h2>Section Title</h2>
        <p>Content paragraph    </p>
        <hr>
        <p> </p>
        <table>
            <tr><td>A</td><td>B</td><td>C</td></tr>
            <tr><td>1</td><td>2</td><td> </td></tr>
        </table>
    </body>
    </html>
    """
    
    # Process in stages
    soup = BeautifulSoup(html, 'html.parser')
    tree = build_semantic_tree(soup)
    markdown = render_tree_to_markdown(tree)
    cleaned = clean_markdown(markdown)
    
    # Basic structure intact
    assert "## Section Title" in cleaned
    assert "Content paragraph" in cleaned
    
    # Table formatting fixed
    assert "| A | B | C" in cleaned  # No trailing pipe
    assert "| 1 | 2 |" in cleaned    # Empty cell properly formatted 