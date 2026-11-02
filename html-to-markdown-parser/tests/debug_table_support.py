"""
Debug script for the table support.
"""
from bs4 import BeautifulSoup
from html_to_md.parser import build_semantic_tree, render_tree_to_markdown

# Simple HTML with a table
html = """
<html>
<body>
    <h1>Sample Heading</h1>
    <p>Sample paragraph.</p>
    <table>
        <tr>
            <th>Year</th>
            <th>Revenue</th>
        </tr>
        <tr>
            <td>2022</td>
            <td>$100M</td>
        </tr>
    </table>
</body>
</html>
"""

# Parse the HTML
soup = BeautifulSoup(html, 'html.parser')

# Debug what elements the parser is finding
print("\nElements found in HTML:")
if soup.body:
    search_scope = soup.body
else:
    search_scope = soup

print("\nAll table elements in soup:")
for table in search_scope.find_all('table', recursive=True):
    print(f"- Found table: {table.name}")
    for tr in table.find_all('tr', recursive=True):
        print(f"  - Found row: {tr.name}")
        for cell in tr.find_all(['th', 'td'], recursive=False):
            print(f"    - Found cell: {cell.name} with content: {cell.get_text().strip()}")

print("\nAll elements being searched in build_semantic_tree:")
for element in search_scope.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'p', 'table'], recursive=True):
    print(f"- Found element: {element.name}")

# Build the tree
tree = build_semantic_tree(soup)

# Print the tree structure
print("\nTree structure:")
print(f"Root node with {len(tree.children)} children")
for i, node in enumerate(tree.children):
    print(f"- Child {i+1}: tag={node.tag}")
    if node.tag == 'table':
        print(f"  Table has {len(node.children)} rows")
        for j, row in enumerate(node.children):
            print(f"    Row {j+1} has {len(row.children)} cells")

# Render the tree to Markdown
markdown = render_tree_to_markdown(tree)
print("\nMarkdown output:")
print(markdown) 