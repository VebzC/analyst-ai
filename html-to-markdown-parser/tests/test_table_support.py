"""
Tests for the HTML table parsing functionality.
"""
import pytest
from bs4 import BeautifulSoup
from html_to_md.parser import build_semantic_tree, render_tree_to_markdown, Node


def test_table_parsing_simple():
    """Test parsing a simple table with headers and data rows."""
    html = """
    <html>
    <body>
        <table>
            <tr>
                <th>Header 1</th>
                <th>Header 2</th>
                <th>Header 3</th>
            </tr>
            <tr>
                <td>Data 1</td>
                <td>Data 2</td>
                <td>Data 3</td>
            </tr>
            <tr>
                <td>Data 4</td>
                <td>Data 5</td>
                <td>Data 6</td>
            </tr>
        </table>
    </body>
    </html>
    """
    
    # Parse the HTML
    soup = BeautifulSoup(html, 'html.parser')
    tree = build_semantic_tree(soup)
    
    # Find table node in children
    table_nodes = [node for node in tree.children if node.tag == 'table']
    assert len(table_nodes) == 1, "Should have one table node"
    table_node = table_nodes[0]
    
    # Table should have three rows
    assert len(table_node.children) == 3, "Table should have three rows"
    
    # Verify header row
    header_row = table_node.children[0]
    assert len(header_row.children) == 3, "Header row should have three cells"
    assert header_row.children[0].content == 'Header 1'
    assert header_row.children[1].content == 'Header 2'
    assert header_row.children[2].content == 'Header 3'
    
    # Verify first data row
    first_data_row = table_node.children[1]
    assert len(first_data_row.children) == 3, "First data row should have three cells"
    assert first_data_row.children[0].content == 'Data 1'
    assert first_data_row.children[1].content == 'Data 2'
    assert first_data_row.children[2].content == 'Data 3'
    
    # Verify second data row
    second_data_row = table_node.children[2]
    assert len(second_data_row.children) == 3, "Second data row should have three cells"
    assert second_data_row.children[0].content == 'Data 4'
    assert second_data_row.children[1].content == 'Data 5'
    assert second_data_row.children[2].content == 'Data 6'
    
    # Test markdown rendering
    markdown = render_tree_to_markdown(tree)
    # Check that table is rendered as expected
    assert "| Header 1 | Header 2 | Header 3 |" in markdown
    assert "| --- | --- | --- |" in markdown
    assert "| Data 1 | Data 2 | Data 3 |" in markdown
    assert "| Data 4 | Data 5 | Data 6 |" in markdown


def test_table_parsing_malformed():
    """Test parsing a malformed table with empty cells and missing elements."""
    html = """
    <html>
    <body>
        <table>
            <tr>
                <th>Header 1</th>
                <th></th>  <!-- Empty header -->
                <th>Header 3</th>
            </tr>
            <tr>
                <td>Data 1</td>
                <!-- Missing cell -->
            </tr>
            <tr>
                <!-- Empty row -->
            </tr>
        </table>
    </body>
    </html>
    """
    
    # Parse the HTML
    soup = BeautifulSoup(html, 'html.parser')
    tree = build_semantic_tree(soup)
    
    # Find table node in children
    table_nodes = [node for node in tree.children if node.tag == 'table']
    assert len(table_nodes) == 1, "Should have one table node"
    table_node = table_nodes[0]
    
    # Table should have three rows (including the empty one)
    assert len(table_node.children) == 3, "Table should have three rows"
    
    # Verify header row
    header_row = table_node.children[0]
    assert len(header_row.children) == 3, "Header row should have three cells"
    assert header_row.children[0].content == 'Header 1'
    assert header_row.children[1].content == '', "Empty header should have empty content"
    assert header_row.children[2].content == 'Header 3'
    
    # Verify incomplete data row
    data_row = table_node.children[1]
    assert len(data_row.children) == 1, "Data row should have one cell"
    assert data_row.children[0].content == 'Data 1'
    
    # Verify empty row
    empty_row = table_node.children[2]
    assert len(empty_row.children) == 0, "Empty row should have no cells"
    
    # Test markdown rendering
    markdown = render_tree_to_markdown(tree)
    
    # The table rendering logic will:
    # 1. Skip rows with only one non-empty cell (the data row with just "Data 1")
    # 2. Skip completely empty rows
    # That leaves just the header row in the final output
    assert "| Header 1 |  | Header 3 |" in markdown
    assert "| --- | --- | --- |" in markdown
    
    # Verify Data 1 is not in the output because that row was skipped as noise
    assert "| Data 1 |" not in markdown


def test_table_with_inline_formatting():
    """Test parsing a table with inline formatting inside cells."""
    html = """
    <html>
    <body>
        <table>
            <tr>
                <th>Category</th>
                <th>Description</th>
            </tr>
            <tr>
                <td><b>Financial</b></td>
                <td>Related to <i>financial</i> matters</td>
            </tr>
        </table>
    </body>
    </html>
    """
    
    # Parse the HTML
    soup = BeautifulSoup(html, 'html.parser')
    tree = build_semantic_tree(soup)
    
    # Find table node in children
    table_nodes = [node for node in tree.children if node.tag == 'table']
    assert len(table_nodes) == 1, "Should have one table node"
    
    # Test markdown rendering
    markdown = render_tree_to_markdown(tree)
    # Currently inline formatting is lost in table cells, but the table should render
    assert "| Category | Description |" in markdown
    assert "| Financial | Related to financial matters |" in markdown


def test_mixed_content():
    """Test parsing a document with mixed headings, paragraphs and tables."""
    html = """
    <html>
    <body>
        <h1>Financial Report</h1>
        <p>Annual breakdown of revenue.</p>
        <table>
            <tr>
                <th>Year</th>
                <th>Revenue</th>
            </tr>
            <tr>
                <td>2021</td>
                <td>$90M</td>
            </tr>
            <tr>
                <td>2022</td>
                <td>$100M</td>
            </tr>
        </table>
        <h2>Analysis</h2>
        <p>Revenue increased by 11% in 2022.</p>
    </body>
    </html>
    """
    
    # Parse the HTML
    soup = BeautifulSoup(html, 'html.parser')
    tree = build_semantic_tree(soup)
    
    # Verify we have all expected element types
    node_types = [node.tag for node in tree.children]
    assert 'h1' in node_types, "Should have h1 heading"
    assert 'p' in node_types, "Should have paragraphs"
    assert 'h2' in node_types, "Should have h2 heading"
    assert 'table' in node_types, "Should have table"
    
    # Find the table node
    table_node = next(node for node in tree.children if node.tag == 'table')
    assert len(table_node.children) == 3, "Table should have 3 rows"
    
    # Test markdown rendering
    markdown = render_tree_to_markdown(tree)
    # Check headings, paragraphs and table are all present
    assert "# Financial Report" in markdown
    assert "Annual breakdown of revenue." in markdown
    assert "| Year | Revenue |" in markdown
    assert "| 2021 | $90M |" in markdown
    assert "| 2022 | $100M |" in markdown
    assert "## Analysis" in markdown
    assert "Revenue increased by 11% in 2022." in markdown


def test_render_multiple_elements():
    """Test rendering a document with headings, paragraphs, and tables."""
    # Create a tree with multiple elements
    root = Node(tag="document")
    
    # Add a heading
    h1 = Node(tag="h1", level=1)
    h1.children = [Node(tag="text", content="Document Title")]
    
    # Add a paragraph
    p = Node(tag="p")
    p.children = [Node(tag="text", content="A sample paragraph.")]
    
    # Add a table
    table = Node(tag="table")
    
    # Header row
    header_row = Node(tag="tr")
    header_row.children = [
        Node(tag="th", content="Item"),
        Node(tag="th", content="Value")
    ]
    
    # Data row
    data_row = Node(tag="tr")
    data_row.children = [
        Node(tag="td", content="Item 1"),
        Node(tag="td", content="Value 1")
    ]
    
    table.children = [header_row, data_row]
    
    # Add all elements to root
    root.children = [h1, p, table]
    
    # Test markdown rendering
    markdown = render_tree_to_markdown(root)
    
    # Check that all elements are rendered correctly
    expected_parts = [
        "# Document Title",
        "A sample paragraph.",
        "| Item | Value |",
        "| --- | --- |",
        "| Item 1 | Value 1 |"
    ]
    
    for part in expected_parts:
        assert part in markdown, f"Expected '{part}' in the markdown output" 