"""
Tests for the markdown rendering functionality.
"""
import unittest
from html_to_md.parser import Node, render_tree_to_markdown


class TestMarkdownRenderer(unittest.TestCase):
    """Test cases for the render_tree_to_markdown function."""
    
    def test_render_tree_to_markdown(self):
        """Test that a Node tree is rendered correctly to Markdown."""
        # Create a sample Node tree with text children instead of direct content
        h1 = Node(tag='h1', level=1)
        h1.children = [Node(tag='text', content='Overview')]
        
        p1 = Node(tag='p')
        p1.children = [Node(tag='text', content='This is the company.')]
        
        h2 = Node(tag='h2', level=2)
        h2.children = [Node(tag='text', content='Risk Factors')]
        
        p2 = Node(tag='p')
        p2.children = [Node(tag='text', content='We may be affected by global conditions.')]
        
        root = Node(tag='document', children=[h1, p1, h2, p2])
        
        # Render the tree to Markdown
        markdown = render_tree_to_markdown(root)
        
        # Expected Markdown output
        expected = "# Overview\n\nThis is the company.\n\n## Risk Factors\n\nWe may be affected by global conditions."
        
        # Assert equality
        self.assertEqual(markdown.strip(), expected)
    
    def test_render_tree_with_multiple_heading_levels(self):
        """Test rendering a tree with multiple heading levels."""
        # Create nodes with text children
        h1 = Node(tag='h1', level=1)
        h1.children = [Node(tag='text', content='Main Heading')]
        
        h2_1 = Node(tag='h2', level=2)
        h2_1.children = [Node(tag='text', content='Subheading 1')]
        
        p1 = Node(tag='p')
        p1.children = [Node(tag='text', content='Content under subheading 1.')]
        
        h3 = Node(tag='h3', level=3)
        h3.children = [Node(tag='text', content='Nested Heading')]
        
        p2 = Node(tag='p')
        p2.children = [Node(tag='text', content='Deeply nested content.')]
        
        h2_2 = Node(tag='h2', level=2)
        h2_2.children = [Node(tag='text', content='Subheading 2')]
        
        p3 = Node(tag='p')
        p3.children = [Node(tag='text', content='More content.')]
        
        root = Node(tag='document', children=[h1, h2_1, p1, h3, p2, h2_2, p3])
        
        markdown = render_tree_to_markdown(root)
        
        expected = (
            "# Main Heading\n\n"
            "## Subheading 1\n\n"
            "Content under subheading 1.\n\n"
            "### Nested Heading\n\n"
            "Deeply nested content.\n\n"
            "## Subheading 2\n\n"
            "More content."
        )
        
        self.assertEqual(markdown.strip(), expected)
    
    def test_render_empty_tree(self):
        """Test rendering an empty tree."""
        root = Node(tag='document')
        
        markdown = render_tree_to_markdown(root)
        
        self.assertEqual(markdown, "")


if __name__ == "__main__":
    unittest.main()