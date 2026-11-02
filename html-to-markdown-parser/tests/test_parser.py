"""
Tests for the parser module.
"""
import unittest
from html_to_md.parser import Node, clean_html, build_semantic_tree
from bs4 import BeautifulSoup


class TestNode(unittest.TestCase):
    """Test cases for the Node class."""
    
    def test_node_initialization(self):
        """Test that a Node can be properly initialized with various parameters."""
        node = Node("div", "Test Content", level=2, metadata={"class": "container"})
        
        self.assertEqual(node.tag, "div")
        self.assertEqual(node.content, "Test Content")
        self.assertEqual(node.level, 2)
        self.assertEqual(node.metadata, {"class": "container"})
        self.assertEqual(node.children, [])
    
    def test_node_children(self):
        """Test that a Node can have child nodes correctly added."""
        parent = Node("div")
        child1 = Node("p", "Paragraph 1")
        child2 = Node("p", "Paragraph 2")
        
        parent.children.append(child1)
        parent.children.append(child2)
        
        self.assertEqual(len(parent.children), 2)
        self.assertEqual(parent.children[0].content, "Paragraph 1")
        self.assertEqual(parent.children[1].content, "Paragraph 2")


class TestCleanHTML(unittest.TestCase):
    """Test cases for the clean_html function."""
    
    def test_remove_scripts(self):
        """Test that script tags are removed from HTML."""
        html = "<html><head><script>alert('test');</script></head><body><p>Content</p></body></html>"
        cleaned = clean_html(html)
        self.assertNotIn("<script>", cleaned)
        self.assertNotIn("alert('test');", cleaned)
        self.assertIn("<p>Content</p>", cleaned)
    
    def test_remove_styles(self):
        """Test that style tags are removed from HTML."""
        html = "<html><head><style>body { color: red; }</style></head><body><p>Content</p></body></html>"
        cleaned = clean_html(html)
        self.assertNotIn("<style>", cleaned)
        self.assertNotIn("body { color: red; }", cleaned)
        self.assertIn("<p>Content</p>", cleaned)
    
    def test_remove_noscript(self):
        """Test that noscript tags are removed from HTML."""
        html = "<html><body><noscript>JavaScript is required.</noscript><p>Content</p></body></html>"
        cleaned = clean_html(html)
        self.assertNotIn("<noscript>", cleaned)
        self.assertNotIn("JavaScript is required.", cleaned)
        self.assertIn("<p>Content</p>", cleaned)
    
    def test_remove_comments(self):
        """Test that HTML comments are removed."""
        html = "<html><body><!-- This is a comment --><p>Content</p></body></html>"
        cleaned = clean_html(html)
        self.assertNotIn("<!-- This is a comment -->", cleaned)
        self.assertIn("<p>Content</p>", cleaned)


class TestBuildSemanticTree(unittest.TestCase):
    """Test cases for the build_semantic_tree function."""
    
    def test_build_semantic_tree(self):
        """Test that a semantic tree is built correctly from HTML."""
        # Create a sample HTML with headings and paragraphs
        html = "<html><body><h1>Heading</h1><p>Paragraph</p><h2>Subheading</h2></body></html>"
        soup = BeautifulSoup(html, 'html.parser')
        
        # Build the semantic tree
        root = build_semantic_tree(soup)
        
        # Assertions
        self.assertEqual(root.tag, "document")
        self.assertEqual(len(root.children), 3)
        
        # Check first child (h1)
        self.assertEqual(root.children[0].tag, "h1")
        self.assertEqual(root.children[0].level, 1)
        
        # Check content of h1 (now in children)
        if root.children[0].children:
            h1_content = "".join(child.content for child in root.children[0].children)
            self.assertEqual(h1_content, "Heading")
        else:
            # Fallback for backward compatibility
            self.assertEqual(root.children[0].content, "Heading")
        
        # Check second child (paragraph)
        self.assertEqual(root.children[1].tag, "p")
        
        # Check content of paragraph (now in children)
        if root.children[1].children:
            p_content = "".join(child.content for child in root.children[1].children)
            self.assertEqual(p_content, "Paragraph")
        else:
            # Fallback for backward compatibility
            self.assertEqual(root.children[1].content, "Paragraph")
        
        # Check third child (h2)
        self.assertEqual(root.children[2].tag, "h2")
        self.assertEqual(root.children[2].level, 2)
        
        # Check content of h2 (now in children)
        if root.children[2].children:
            h2_content = "".join(child.content for child in root.children[2].children)
            self.assertEqual(h2_content, "Subheading")
        else:
            # Fallback for backward compatibility
            self.assertEqual(root.children[2].content, "Subheading")
    
    def test_empty_body(self):
        """Test handling of HTML with an empty body."""
        html = "<html><body></body></html>"
        soup = BeautifulSoup(html, 'html.parser')
        
        root = build_semantic_tree(soup)
        
        self.assertEqual(root.tag, "document")
        self.assertEqual(len(root.children), 0)
    
    def test_no_body(self):
        """Test handling of HTML without a body tag."""
        html = "<html><div>No body here</div></html>"
        soup = BeautifulSoup(html, 'html.parser')
        
        root = build_semantic_tree(soup)
        
        self.assertEqual(root.tag, "document")
        self.assertEqual(len(root.children), 0)


if __name__ == "__main__":
    unittest.main() 