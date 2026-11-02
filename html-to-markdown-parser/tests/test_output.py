from html_to_md.parser import Node, render_tree_to_markdown

# Create the example Node tree
root = Node(tag='document', children=[
    Node(tag='h1', content='Overview', level=1),
    Node(tag='p', content='This is the company.'),
    Node(tag='h2', content='Risk Factors', level=2),
    Node(tag='p', content='We may be affected by global conditions.')
])

# Render to Markdown
markdown = render_tree_to_markdown(root)

# Print the output
print(markdown) 