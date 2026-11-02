import os
import unittest
from unittest.mock import patch, MagicMock, mock_open
import tempfile
import shutil
from pathlib import Path

from html_to_md.converter import convert_full_sec_filing


class TestConverter(unittest.TestCase):
    def setUp(self):
        # Create a temporary directory for test output
        self.test_dir = tempfile.mkdtemp()
    
    def tearDown(self):
        # Clean up temporary directory
        shutil.rmtree(self.test_dir)
    
    @patch('html_to_md.converter.clean_html')
    @patch('html_to_md.converter.extract_and_replace_images')
    @patch('html_to_md.converter.extract_exhibit_links')
    @patch('html_to_md.converter.fetch_and_parse_exhibits')
    @patch('html_to_md.converter.build_semantic_tree')
    @patch('html_to_md.converter.render_tree_to_markdown')
    def test_convert_full_sec_filing(
        self, 
        mock_render, 
        mock_build_tree, 
        mock_fetch_exhibits, 
        mock_extract_links, 
        mock_extract_images,
        mock_clean_html
    ):
        # Create test paths
        relative_img_path = os.path.join("images", "sec_img_1.png")
        abs_img_path = os.path.join(self.test_dir, relative_img_path)
        
        # Set up our mocks
        mock_cleaned_html = "<html><body><h1>Cleaned HTML</h1></body></html>"
        mock_clean_html.return_value = mock_cleaned_html
        
        mock_html_with_images = "<html><body><h1>HTML with image references</h1></body></html>"
        mock_extract_images.return_value = (mock_html_with_images, [abs_img_path])
        
        mock_extract_links.return_value = [("Exhibit 10.1", "https://example.com/exhibit10.1.htm")]
        
        mock_exhibits = [{
            "title": "Exhibit 10.1",
            "url": "https://example.com/exhibit10.1.htm",
            "markdown": "# Exhibit 10.1\n\nTest exhibit content"
        }]
        mock_fetch_exhibits.return_value = mock_exhibits
        
        mock_tree = MagicMock()
        mock_build_tree.return_value = mock_tree
        
        mock_markdown = "# Test Document\n\nThis is test content."
        mock_render.return_value = mock_markdown
        
        # Run the function
        with patch('builtins.open', mock_open()) as m:
            result = convert_full_sec_filing(
                "<html><body><h1>Test</h1></body></html>",
                "https://example.com/",
                self.test_dir
            )
        
        # Verify the result structure
        self.assertIn("main_markdown", result)
        self.assertIn("images", result)
        self.assertIn("exhibits", result)
        
        # Verify mock calls
        mock_clean_html.assert_called_once()
        mock_extract_images.assert_called_once()
        mock_extract_links.assert_called_once()
        mock_fetch_exhibits.assert_called_once()
        mock_build_tree.assert_called_once()
        mock_render.assert_called_once()
        
        # Verify the main markdown includes exhibits section
        self.assertTrue("## Exhibits" in result["main_markdown"])
        self.assertTrue("[Exhibit 10.1]" in result["main_markdown"])
        
        # Verify image paths
        self.assertEqual(len(result["images"]), 1)
        self.assertEqual(result["images"][0], relative_img_path)
        
        # Verify exhibits
        self.assertEqual(len(result["exhibits"]), 1)
        self.assertEqual(result["exhibits"][0]["title"], "Exhibit 10.1")
    
    @patch('html_to_md.converter.clean_html')
    @patch('html_to_md.converter.extract_and_replace_images')
    @patch('html_to_md.converter.extract_exhibit_links')
    @patch('html_to_md.converter.fetch_and_parse_exhibits')
    @patch('html_to_md.converter.build_semantic_tree')
    @patch('html_to_md.converter.render_tree_to_markdown')
    def test_convert_without_saving_files(
        self, 
        mock_render, 
        mock_build_tree, 
        mock_fetch_exhibits, 
        mock_extract_links, 
        mock_extract_images,
        mock_clean_html
    ):
        # Create test paths
        relative_img_path = os.path.join("images", "sec_img_1.png")
        abs_img_path = os.path.join(self.test_dir, relative_img_path)
        
        # Set up our mocks
        mock_cleaned_html = "<html><body><h1>Cleaned HTML</h1></body></html>"
        mock_clean_html.return_value = mock_cleaned_html
        
        mock_html_with_images = "<html><body><h1>HTML with image references</h1></body></html>"
        mock_extract_images.return_value = (mock_html_with_images, [abs_img_path])
        
        mock_extract_links.return_value = []  # No exhibits in this test
        mock_fetch_exhibits.return_value = []
        
        mock_tree = MagicMock()
        mock_build_tree.return_value = mock_tree
        
        mock_markdown = "# Test Document\n\nThis is test content."
        mock_render.return_value = mock_markdown
        
        # Run the function with save_files=False
        with patch('builtins.open', mock_open()) as m:
            result = convert_full_sec_filing(
                "<html><body><h1>Test</h1></body></html>",
                "https://example.com/",
                self.test_dir,
                save_files=False
            )
        
        # Verify the result structure
        self.assertIn("main_markdown", result)
        self.assertIn("images", result)
        self.assertIn("exhibits", result)
        
        # Verify mock calls
        mock_clean_html.assert_called_once()
        mock_extract_images.assert_called_once()
        mock_extract_links.assert_called_once()
        mock_fetch_exhibits.assert_called_once()
        mock_build_tree.assert_called_once()
        mock_render.assert_called_once()
        
        # Verify no "## Exhibits" section since there are no exhibits
        self.assertFalse("## Exhibits" in result["main_markdown"])
        
        # Verify image paths
        self.assertEqual(len(result["images"]), 1)
        self.assertEqual(result["images"][0], relative_img_path)
        
        # Verify the main file wasn't saved
        for call in m.mock_calls:
            if len(call) >= 2 and isinstance(call[1][0], str) and call[1][0].endswith("main.md"):
                self.fail("Should not have tried to save main.md")


if __name__ == '__main__':
    unittest.main() 