"""
Debug script for inline formatting.
"""
from bs4 import BeautifulSoup
from html_to_md.parser import build_semantic_tree

# Test case
html = "<p>This is <b>bold</b> text.</p>"
soup = BeautifulSoup(html, 'html.parser')

# Build the tree
root = build_semantic_tree(soup)

# Debug output
print(f"Root tag: {root.tag}")
print(f"Root children count: {len(root.children)}")

if root.children:
    p_node = root.children[0]
    print(f"First child tag: {p_node.tag}")
    print(f"Paragraph children count: {len(p_node.children)}")
    
    for i, child in enumerate(p_node.children):
        print(f"Child {i}:")
        print(f"  Tag: {child.tag}")
        print(f"  Content: '{child.content}'")
        print(f"  Metadata: {child.metadata}")
else:
    print("No children in root node!") 