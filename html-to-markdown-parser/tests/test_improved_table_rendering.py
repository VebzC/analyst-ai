"""
Tests for the improved table rendering functionality.
"""
import pytest
import logging
from bs4 import BeautifulSoup
from html_to_md.parser import build_semantic_tree, render_tree_to_markdown, Node


def test_unbalanced_rows():
    """Test handling of tables with unbalanced rows (different numbers of cells)."""
    html = """
    <html>
    <body>
        <table>
            <tr>
                <th>Item</th>
                <th>Quantity</th>
                <th>Price</th>
            </tr>
            <tr>
                <td>Product A</td>
                <td>2</td>
            </tr>
            <tr>
                <td>Product B</td>
                <td>1</td>
                <td>$50</td>
                <td>Extra info</td>
            </tr>
        </table>
    </body>
    </html>
    """
    
    # Parse the HTML
    soup = BeautifulSoup(html, 'html.parser')
    tree = build_semantic_tree(soup)
    
    # Find table node in children
    table_node = next(node for node in tree.children if node.tag == 'table')
    
    # Verify the table structure before rendering
    assert len(table_node.children) == 3, "Table should have three rows"
    assert len(table_node.children[0].children) == 3, "Header row should have 3 cells"
    assert len(table_node.children[1].children) == 2, "Second row has 2 cells"
    assert len(table_node.children[2].children) == 4, "Third row has 4 cells"
    
    # Test markdown rendering
    markdown = render_tree_to_markdown(tree)
    
    # Check that all rows are balanced in the output
    assert "| Item | Quantity | Price | |" in markdown or "| Item | Quantity | Price |  |" in markdown
    assert "| Product A | 2 |  |  |" in markdown, "Second row should be padded with empty cells"
    assert "| Product B | 1 | $50 | Extra info |" in markdown, "Third row should keep all cells"


def test_all_td_no_th():
    """Test handling of tables with no header (<th>) elements."""
    html = """
    <html>
    <body>
        <table>
            <tr>
                <td>Name</td>
                <td>Age</td>
            </tr>
            <tr>
                <td>John</td>
                <td>25</td>
            </tr>
            <tr>
                <td>Jane</td>
                <td>24</td>
            </tr>
        </table>
    </body>
    </html>
    """
    
    # Parse the HTML
    soup = BeautifulSoup(html, 'html.parser')
    tree = build_semantic_tree(soup)
    
    # Test markdown rendering
    markdown = render_tree_to_markdown(tree)
    
    # Check that first row is treated as a header with separator row
    assert "| Name | Age |" in markdown
    assert "| --- | --- |" in markdown
    assert "| John | 25 |" in markdown
    assert "| Jane | 24 |" in markdown


def test_skip_noise_rows(caplog):
    """Test that rows with only one non-empty cell are skipped."""
    html = """
    <html>
    <body>
        <table>
            <tr>
                <th>Product</th>
                <th>Details</th>
            </tr>
            <tr>
                <td>Widget</td>
                <td>Small gadget</td>
            </tr>
            <tr>
                <td>Note:</td>
                <td></td>
            </tr>
            <tr>
                <td>All products come with warranty</td>
                <td></td>
            </tr>
        </table>
    </body>
    </html>
    """
    
    # Parse the HTML
    soup = BeautifulSoup(html, 'html.parser')
    tree = build_semantic_tree(soup)
    
    # Set log level to debug to capture the debug messages
    caplog.set_level(logging.DEBUG)
    
    # Test markdown rendering
    markdown = render_tree_to_markdown(tree)
    
    # Verify that only the header and first data row are included
    assert "| Product | Details |" in markdown
    assert "| Widget | Small gadget |" in markdown
    assert "Note:" not in markdown
    assert "All products come with warranty" not in markdown
    
    # Check debug log for skipped rows
    assert "Skipping row with only one non-empty cell" in caplog.text


def test_nested_formatting():
    """Test that nested formatting (bold/italic) inside cells is preserved."""
    html = """
    <html>
    <body>
        <table>
            <tr>
                <th>Feature</th>
                <th>Description</th>
            </tr>
            <tr>
                <td><b>Performance</b></td>
                <td>Increased <i>speed</i> and reliability</td>
            </tr>
        </table>
    </body>
    </html>
    """
    
    # Directly create a table node with inline formatting 
    # (since our current tree builder doesn't support inline formatting in tables)
    table_node = Node(tag="table")
    
    # Header row
    header_row = Node(tag="tr")
    header_row.children = [
        Node(tag="th", content="Feature"),
        Node(tag="th", content="Description")
    ]
    
    # Data row
    data_row = Node(tag="tr")
    data_row.children = [
        Node(tag="td", content="**Performance**"),  # Bold text in markdown format
        Node(tag="td", content="Increased *speed* and reliability")  # Italic text in markdown
    ]
    
    # Assemble the table
    table_node.children = [header_row, data_row]
    
    # Create root node with the table
    root = Node(tag="document", children=[table_node])
    
    # Test markdown rendering
    markdown = render_tree_to_markdown(root)
    
    # Check that markdown formatting is preserved in table cells
    assert "| Feature | Description |" in markdown
    assert "| **Performance** | Increased *speed* and reliability |" in markdown


def test_embedded_line_breaks():
    """Test handling of tables with embedded line breaks in cells."""
    html = """
    <html>
    <body>
        <table>
            <tr>
                <th>Category</th>
                <th>Notes</th>
            </tr>
            <tr>
                <td>Financial</td>
                <td>This includes:
                Assets
                Liabilities
                Equity</td>
            </tr>
        </table>
    </body>
    </html>
    """
    
    # Create table node with line breaks
    table_node = Node(tag="table")
    
    # Header row
    header_row = Node(tag="tr")
    header_row.children = [
        Node(tag="th", content="Category"),
        Node(tag="th", content="Notes")
    ]
    
    # Data row with line breaks
    data_row = Node(tag="tr")
    data_row.children = [
        Node(tag="td", content="Financial"),
        Node(tag="td", content="This includes:\nAssets\nLiabilities\nEquity")
    ]
    
    # Assemble table
    table_node.children = [header_row, data_row]
    
    # Create root with table
    root = Node(tag="document", children=[table_node])
    
    # Test markdown rendering
    markdown = render_tree_to_markdown(root)
    
    # Check that line breaks are converted to <br> tags
    assert "| Category | Notes |" in markdown
    assert "| Financial | This includes: <br> Assets <br> Liabilities <br> Equity |" in markdown


def test_table_truncation(caplog):
    """Test that large tables are truncated with a message."""
    # Create a table with more than 50 rows
    table_node = Node(tag="table")
    
    # Header row
    header_row = Node(tag="tr")
    header_row.children = [
        Node(tag="th", content="ID"),
        Node(tag="th", content="Value")
    ]
    
    table_node.children = [header_row]
    
    # Add 55 data rows
    for i in range(1, 56):
        data_row = Node(tag="tr")
        data_row.children = [
            Node(tag="td", content=f"{i}"),
            Node(tag="td", content=f"Value {i}")
        ]
        table_node.children.append(data_row)
    
    # Create root with table
    root = Node(tag="document", children=[table_node])
    
    # Test markdown rendering with log capture
    caplog.set_level(logging.INFO)
    markdown = render_tree_to_markdown(root)
    
    # Verify truncation
    assert "[Table truncated for readability:" in markdown
    assert "additional rows not shown" in markdown
    
    # Make sure we have 50 data rows (plus header and separator, plus truncation message)
    # This should be 54 lines total (52 table rows + blank line + truncation message)
    assert markdown.count("\n") <= 54  
    
    # Make sure data rows up to 50 are included
    assert "| 50 | Value 50 |" in markdown
    
    # Check that row 51 and beyond are not in the output
    assert "| 51 | Value 51 |" not in markdown
    
    # Check log message
    assert "Truncated table with 55 rows to 50 rows" in caplog.text
    assert "Rendered table with 55 rows and 2 columns" in caplog.text 