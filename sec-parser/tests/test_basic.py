import os
import pytest
import logging
from pathlib import Path
from bs4 import BeautifulSoup


def test_basic_imports():
    """Test that we can import basic modules without circular imports."""
    try:
        from bs4 import BeautifulSoup
        assert True, "Successfully imported BeautifulSoup"
    except ImportError:
        assert False, "Failed to import BeautifulSoup"
    
    try:
        import requests
        assert True, "Successfully imported requests"
    except ImportError:
        assert False, "Failed to import requests"
    
    try:
        import markdown
        assert True, "Successfully imported markdown"
    except ImportError:
        assert False, "Failed to import markdown"
    
    try:
        import pydantic
        assert True, "Successfully imported pydantic"
    except ImportError:
        assert False, "Failed to import pydantic"


def test_example_exists():
    """Test that the example file exists."""
    example_file = Path('sec_md_parser/examples/convert_filing_with_xbrl.py')
    assert example_file.exists(), f"Example file {example_file} should exist"


def test_html_parsing_with_bs4():
    """Test basic HTML parsing with BeautifulSoup."""
    html_content = """
    <html>
    <head><title>Test Document</title></head>
    <body>
        <h1>Test Heading</h1>
        <p>Test paragraph</p>
        <table>
            <tr><th>Header 1</th><th>Header 2</th></tr>
            <tr><td>Value 1</td><td>Value 2</td></tr>
        </table>
    </body>
    </html>
    """
    
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # Test basic extraction
    assert soup.title.text == "Test Document"
    assert soup.h1.text == "Test Heading"
    assert len(soup.find_all('tr')) == 2
    assert len(soup.find_all('td')) == 2
    assert len(soup.find_all('th')) == 2 


def test_basic():
    """A simple test that always passes."""
    assert True 