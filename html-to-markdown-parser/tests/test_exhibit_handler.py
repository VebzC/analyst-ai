import os
import unittest
from unittest.mock import patch, MagicMock, mock_open
import tempfile
import shutil

from html_to_md.exhibit_handler import extract_exhibit_links, fetch_and_parse_exhibits, _parse_sec_url


class TestExhibitHandler(unittest.TestCase):
    def test_extract_exhibit_links_basic(self):
        html = """
        <html>
            <body>
                <a href="exhibit10.1.htm">Exhibit 10.1</a>
                <a href="regular_link.html">Regular Link</a>
                <a href="path/to/exhibit99.2.txt">Exhibit 99.2</a>
                <a href="https://example.com/exhibits/ex101.html">Exhibit 10.1 Description</a>
            </body>
        </html>
        """
        base_url = "https://example.com/"
        
        results = extract_exhibit_links(html, base_url)
        
        self.assertEqual(len(results), 4)
        self.assertEqual(results[0], ("Exhibit 10.1", "https://example.com/exhibit10.1.htm"))
        self.assertEqual(results[1], ("Regular Link", "https://example.com/regular_link.html"))
        self.assertEqual(results[2], ("Exhibit 99.2", "https://example.com/path/to/exhibit99.2.txt"))
        self.assertEqual(results[3], ("Exhibit 10.1 Description", "https://example.com/exhibits/ex101.html"))
    
    def test_extract_exhibit_links_malformed(self):
        html = """
        <html>
            <body>
                <a href="">Empty href</a>
                <a>No href attribute</a>
                <a href="exhibit10.1.htm"></a>  <!-- No link text -->
                <a href="exhibit10.2.htm">   </a>  <!-- Whitespace only -->
            </body>
        </html>
        """
        base_url = "https://example.com/"
        
        results = extract_exhibit_links(html, base_url)
        
        # Should only find the empty href since it matches .htm
        self.assertEqual(len(results), 0)
    
    def test_parse_sec_url(self):
        # Test SEC URL with Archives format
        sec_url1 = "https://www.sec.gov/Archives/edgar/data/1318605/000156459022027165/tsla-ex991_254.htm"
        result1 = _parse_sec_url(sec_url1)
        self.assertIsNotNone(result1)
        self.assertEqual(result1["accessionNo"], "000156459022027165")
        self.assertEqual(result1["document"], "tsla-ex991_254.htm")
        
        # Test SEC URL with query parameters
        sec_url2 = "https://www.sec.gov/document/view?accessionNumber=0001193125-22-067873&doc=ex99-1.htm"
        result2 = _parse_sec_url(sec_url2)
        self.assertIsNotNone(result2)
        self.assertEqual(result2["accessionNo"], "0001193125-22-067873")
        self.assertEqual(result2["document"], "ex99-1.htm")
        
        # Test invalid URL
        invalid_url = "https://example.com/not/an/sec/url.html"
        result3 = _parse_sec_url(invalid_url)
        self.assertIsNone(result3)
    
    @patch('html_to_md.exhibit_handler.get_sec_api_key')
    @patch('html_to_md.exhibit_handler.get_with_retries')
    @patch('html_to_md.exhibit_handler._parse_sec_url')
    def test_fetch_and_parse_exhibits_with_sec_api(self, mock_parse_url, mock_get_with_retries, mock_get_api_key):
        # Set up mock API key
        mock_get_api_key.return_value = "test_api_key"
        
        # Set up mock URL parser to return valid SEC params
        mock_parse_url.return_value = {
            "accessionNo": "000156459022027165",
            "document": "tsla-ex991_254.htm"
        }
        
        # Set up mock response from API
        mock_response = MagicMock()
        mock_response.text = "<html><body><h1>Exhibit Content from SEC API</h1></body></html>"
        mock_response.headers = {'Content-Type': 'text/html'}
        mock_response.content = b"<html><body><h1>Exhibit Content from SEC API</h1></body></html>"
        
        # Configure the mock get_with_retries
        mock_get_with_retries.return_value = mock_response
        
        # Set up mock parser function
        def mock_parser(content):
            return f"Parsed: {content}"
        
        # Create a temporary directory for testing
        temp_dir = tempfile.mkdtemp()
        try:
            # Test data
            exhibit_links = [
                ("Exhibit 10.1", "https://www.sec.gov/Archives/edgar/data/1318605/000156459022027165/tsla-ex991_254.htm")
            ]
            
            # Execute the function
            with patch('builtins.open', mock_open()) as m:
                results = fetch_and_parse_exhibits(exhibit_links, temp_dir, mock_parser)
            
            # Check results
            self.assertEqual(len(results), 1)
            
            # Check that the SEC API was used with correct parameters
            mock_get_with_retries.assert_called_with(
                url="https://api.sec-api.io/filing-doc",
                headers={
                    "Authorization": "Bearer test_api_key",
                    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"
                },
                params={
                    "accessionNo": "000156459022027165",
                    "document": "tsla-ex991_254.htm"
                },
                timeout=30,
                retries=3,
                backoff_factor=1.0
            )
            
            # Check result content
            self.assertEqual(results[0]["title"], "Exhibit 10.1")
            self.assertEqual(results[0]["url"], "https://www.sec.gov/Archives/edgar/data/1318605/000156459022027165/tsla-ex991_254.htm")
            self.assertEqual(results[0]["markdown"], f"Parsed: {mock_response.text}")
            
        finally:
            # Clean up the temporary directory
            shutil.rmtree(temp_dir)
    
    @patch('html_to_md.exhibit_handler.get_sec_api_key')
    @patch('html_to_md.exhibit_handler.get_with_retries')
    @patch('html_to_md.exhibit_handler._parse_sec_url')
    def test_fetch_and_parse_exhibits_fallback(self, mock_parse_url, mock_get_with_retries, mock_get_api_key):
        # Set up mock API key
        mock_get_api_key.return_value = "test_api_key"
        
        # Set up mock URL parser to return None (trigger fallback)
        mock_parse_url.return_value = None
        
        # Set up mock response for direct request
        mock_response = MagicMock()
        mock_response.text = "<html><body><h1>Exhibit Content from Direct Request</h1></body></html>"
        mock_response.headers = {'Content-Type': 'text/html'}
        mock_response.content = b"<html><body><h1>Exhibit Content from Direct Request</h1></body></html>"
        
        # Configure the mock get_with_retries
        mock_get_with_retries.return_value = mock_response
        
        # Set up mock parser function
        def mock_parser(content):
            return f"Parsed: {content}"
        
        # Create a temporary directory for testing
        temp_dir = tempfile.mkdtemp()
        try:
            # Test data
            exhibit_links = [
                ("Exhibit 10.1", "https://example.com/not-sec-url/exhibit10.1.htm")
            ]
            
            # Execute the function
            with patch('builtins.open', mock_open()) as m:
                results = fetch_and_parse_exhibits(exhibit_links, temp_dir, mock_parser)
            
            # Check results
            self.assertEqual(len(results), 1)
            
            # Check that direct request was used (fallback)
            mock_get_with_retries.assert_called_with(
                url="https://example.com/not-sec-url/exhibit10.1.htm",
                timeout=30,
                retries=2,
                backoff_factor=0.5
            )
            
            # Check result content
            self.assertEqual(results[0]["title"], "Exhibit 10.1")
            self.assertEqual(results[0]["url"], "https://example.com/not-sec-url/exhibit10.1.htm")
            self.assertEqual(results[0]["markdown"], f"Parsed: {mock_response.text}")
            
        finally:
            # Clean up the temporary directory
            shutil.rmtree(temp_dir)
    
    @patch('html_to_md.exhibit_handler.get_sec_api_key')
    def test_fetch_and_parse_exhibits_missing_api_key(self, mock_get_api_key):
        # Set up mock API key to raise ValueError
        mock_get_api_key.side_effect = ValueError("SEC_API_KEY is not set in environment variables.")
        
        # Set up mock parser function
        def mock_parser(content):
            return f"Parsed: {content}"
        
        # Create a temporary directory for testing
        temp_dir = tempfile.mkdtemp()
        try:
            # Test data
            exhibit_links = [
                ("Exhibit 10.1", "https://www.sec.gov/Archives/edgar/data/1318605/000156459022027165/tsla-ex991_254.htm")
            ]
            
            # Execute the function
            results = fetch_and_parse_exhibits(exhibit_links, temp_dir, mock_parser)
            
            # Check results - should return error for missing API key
            self.assertEqual(len(results), 1)
            self.assertEqual(results[0]["title"], "Exhibit 10.1")
            self.assertEqual(results[0]["url"], "https://www.sec.gov/Archives/edgar/data/1318605/000156459022027165/tsla-ex991_254.htm")
            self.assertEqual(results[0]["markdown"], None)
            self.assertEqual(results[0]["error"], "SEC API key not configured")
            
        finally:
            # Clean up the temporary directory
            shutil.rmtree(temp_dir)
    
    @patch('html_to_md.exhibit_handler.get_sec_api_key')
    @patch('html_to_md.exhibit_handler.get_with_retries')
    @patch('html_to_md.exhibit_handler._parse_sec_url')
    def test_fetch_and_parse_exhibits_with_api_error(self, mock_parse_url, mock_get_with_retries, mock_get_api_key):
        # Set up mock API key
        mock_get_api_key.return_value = "test_api_key"
        
        # Set up mock URL parser to return valid SEC params
        mock_parse_url.return_value = {
            "accessionNo": "000156459022027165",
            "document": "tsla-ex991_254.htm"
        }
        
        # Set up mock get_with_retries to raise an exception
        mock_get_with_retries.side_effect = Exception("API Error: Too many requests")
        
        # Set up mock parser function
        def mock_parser(content):
            return f"Parsed: {content}"
        
        # Create a temporary directory for testing
        temp_dir = tempfile.mkdtemp()
        try:
            # Test data
            exhibit_links = [
                ("Exhibit 10.1", "https://www.sec.gov/Archives/edgar/data/1318605/000156459022027165/tsla-ex991_254.htm")
            ]
            
            # Execute the function
            results = fetch_and_parse_exhibits(exhibit_links, temp_dir, mock_parser)
            
            # Check results - should return error but not fail completely
            self.assertEqual(len(results), 1)
            self.assertEqual(results[0]["title"], "Exhibit 10.1")
            self.assertEqual(results[0]["url"], "https://www.sec.gov/Archives/edgar/data/1318605/000156459022027165/tsla-ex991_254.htm")
            self.assertEqual(results[0]["markdown"], None)
            self.assertEqual(results[0]["error"], "API Error: Too many requests")
            
        finally:
            # Clean up the temporary directory
            shutil.rmtree(temp_dir)


if __name__ == '__main__':
    unittest.main() 