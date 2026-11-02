"""
Tests for inline formatting in the HTML to Markdown converter.
"""
import unittest
from bs4 import BeautifulSoup
from html_to_md.parser import build_semantic_tree, render_tree_to_markdown, Node


class TestInlineFormatting(unittest.TestCase):
    """Test cases for inline formatting (bold, italic) in HTML to Markdown conversion."""
    
    def test_bold_text(self):
        """Test that bold text is correctly identified and converted."""
        html = "<p>This is <b>bold</b> text.</p>"
        soup = BeautifulSoup(html, 'html.parser')
        
        # Build the semantic tree and render to Markdown
        root = build_semantic_tree(soup)
        markdown = render_tree_to_markdown(root)
        
        # Verify the output - strip trailing newlines for comparison
        self.assertEqual(markdown.strip(), "This is **bold** text.")
    
    def test_italic_text(self):
        """Test that italic text is correctly identified and converted."""
        html = "<p>This is <i>italic</i> text.</p>"
        soup = BeautifulSoup(html, 'html.parser')
        
        root = build_semantic_tree(soup)
        markdown = render_tree_to_markdown(root)
        
        self.assertEqual(markdown.strip(), "This is *italic* text.")
    
    def test_both_bold_and_italic(self):
        """Test that text that is both bold and italic is correctly converted."""
        html = "<p>This is <b><i>bold and italic</i></b> text.</p>"
        soup = BeautifulSoup(html, 'html.parser')
        
        root = build_semantic_tree(soup)
        markdown = render_tree_to_markdown(root)
        
        self.assertEqual(markdown.strip(), "This is ***bold and italic*** text.")
    
    def test_mixed_formatting(self):
        """Test a paragraph with mixed formatting."""
        html = "<p>Normal <b>bold</b> and <i>italic</i> and <b><i>both</i></b>.</p>"
        soup = BeautifulSoup(html, 'html.parser')
        
        root = build_semantic_tree(soup)
        markdown = render_tree_to_markdown(root)
        
        self.assertEqual(markdown.strip(), "Normal **bold** and *italic* and ***both***.")
    
    def test_heading_with_formatting(self):
        """Test that formatting in headings is correctly handled."""
        html = "<h1>Heading with <b>bold</b> text</h1>"
        soup = BeautifulSoup(html, 'html.parser')
        
        root = build_semantic_tree(soup)
        markdown = render_tree_to_markdown(root)
        
        self.assertEqual(markdown.strip(), "# Heading with **bold** text")
    
    def test_em_strong_tags(self):
        """Test that <em> and <strong> tags are correctly handled."""
        html = "<p><strong>Strong</strong> and <em>emphasized</em> text.</p>"
        soup = BeautifulSoup(html, 'html.parser')
        
        root = build_semantic_tree(soup)
        markdown = render_tree_to_markdown(root)
        
        self.assertEqual(markdown.strip(), "**Strong** and *emphasized* text.")
    
    def test_node_structure(self):
        """Test the structure of the node tree created for inline formatting."""
        html = "<p>This is <b>bold</b> and <i>italic</i>.</p>"
        soup = BeautifulSoup(html, 'html.parser')
        
        root = build_semantic_tree(soup)
        
        # Verify the paragraph node exists
        p_node = root.children[0]
        self.assertEqual(p_node.tag, "p")
        
        # Our implementation may produce different number of text nodes based on whitespace handling
        # Just check that there are at least 4 text nodes (normal, bold, normal, italic, normal)
        self.assertGreaterEqual(len(p_node.children), 4)
        
        # Find the bold and italic nodes by their metadata
        bold_nodes = [node for node in p_node.children if node.metadata.get("bold", False)]
        italic_nodes = [node for node in p_node.children if node.metadata.get("italic", False)]
        
        # Verify we have at least one bold and one italic node
        self.assertGreaterEqual(len(bold_nodes), 1)
        self.assertGreaterEqual(len(italic_nodes), 1)
        
        # Check content of formatted nodes
        bold_content = "".join(node.content for node in bold_nodes)
        italic_content = "".join(node.content for node in italic_nodes)
        
        self.assertEqual(bold_content, "bold")
        self.assertEqual(italic_content, "italic")


if __name__ == "__main__":
    unittest.main() 