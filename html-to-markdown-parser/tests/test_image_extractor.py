import os
import shutil
import base64
import pytest
import responses
from pathlib import Path
from html_to_md.image_extractor import extract_and_replace_images


class TestImageExtractor:
    @pytest.fixture
    def output_dir(self):
        # Create a temporary output directory for testing
        test_output_dir = "test_images"
        os.makedirs(test_output_dir, exist_ok=True)
        yield test_output_dir
        # Clean up after tests
        shutil.rmtree(test_output_dir)
    
    def test_base64_image_extraction(self, output_dir):
        # Simple base64 encoded 1x1 transparent PNG
        base64_data = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNkYAAAAAYAAjCB0C8AAAAASUVORK5CYII="
        
        html = f"""
        <html>
        <body>
            <p>Here is a test image:</p>
            <img src="data:image/png;base64,{base64_data}" alt="Test Image">
        </body>
        </html>
        """
        
        modified_html, saved_images = extract_and_replace_images(html, output_dir, "test")
        
        # Check that one image was saved
        assert len(saved_images) == 1
        assert os.path.exists(saved_images[0])
        
        # Check that the HTML was modified correctly
        assert '<p>Here is a test image:</p>' in modified_html
        assert '<p>![Test Image](./images/test_1.png)</p>' in modified_html
        assert '<img' not in modified_html
    
    @responses.activate
    def test_remote_image_extraction(self, output_dir):
        # Mock a remote image URL
        image_url = "https://example.com/image.png"
        # Simple 1x1 transparent PNG for the mock response
        image_data = base64.b64decode("iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNkYAAAAAYAAjCB0C8AAAAASUVORK5CYII=")
        
        # Setup mock response
        responses.add(
            responses.GET,
            image_url,
            body=image_data,
            status=200,
            content_type='image/png'
        )
        
        html = f"""
        <html>
        <body>
            <p>Here is a remote image:</p>
            <img src="{image_url}" alt="Remote Image">
        </body>
        </html>
        """
        
        modified_html, saved_images = extract_and_replace_images(html, output_dir, "remote")
        
        # Check that one image was saved
        assert len(saved_images) == 1
        assert os.path.exists(saved_images[0])
        
        # Check that the HTML was modified correctly
        assert '<p>Here is a remote image:</p>' in modified_html
        assert '<p>![Remote Image](./images/remote_1.png)</p>' in modified_html
        assert '<img' not in modified_html
    
    def test_missing_src_attribute(self, output_dir):
        html = """
        <html>
        <body>
            <p>Image with no src:</p>
            <img alt="No Source">
        </body>
        </html>
        """
        
        modified_html, saved_images = extract_and_replace_images(html, output_dir, "missing")
        
        # Check that no images were saved
        assert len(saved_images) == 0
        
        # Check that the HTML still contains the img tag (should be skipped)
        assert 'alt="No Source"' in modified_html
    
    def test_empty_img_tag(self, output_dir):
        html = """
        <html>
        <body>
            <p>Empty image tag:</p>
            <img>
        </body>
        </html>
        """
        
        modified_html, saved_images = extract_and_replace_images(html, output_dir, "empty")
        
        # Check that no images were saved
        assert len(saved_images) == 0
        
        # Check that the HTML still contains the empty img tag
        assert '<img/>' in modified_html.replace(" ", "")
    
    def test_multiple_images(self, output_dir):
        # Simple base64 encoded 1x1 transparent PNG
        base64_data = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNkYAAAAAYAAjCB0C8AAAAASUVORK5CYII="
        
        html = f"""
        <html>
        <body>
            <p>First image:</p>
            <img src="data:image/png;base64,{base64_data}" alt="First Image">
            <p>Second image:</p>
            <img src="data:image/png;base64,{base64_data}" alt="Second Image">
            <p>Invalid image:</p>
            <img>
        </body>
        </html>
        """
        
        modified_html, saved_images = extract_and_replace_images(html, output_dir, "multi")
        
        # Check that two images were saved
        assert len(saved_images) == 2
        assert all(os.path.exists(path) for path in saved_images)
        
        # Check that the HTML was modified correctly
        assert '<p>First image:</p>' in modified_html
        assert '<p>![First Image](./images/multi_1.png)</p>' in modified_html
        assert '<p>Second image:</p>' in modified_html
        assert '<p>![Second Image](./images/multi_2.png)</p>' in modified_html
        assert '<p>Invalid image:</p>' in modified_html
        assert '<img/>' in modified_html.replace(" ", "")
    
    @responses.activate
    def test_failed_remote_image(self, output_dir):
        # Mock a failing remote image URL
        image_url = "https://example.com/broken-image.png"
        
        # Setup mock response with error
        responses.add(
            responses.GET,
            image_url,
            status=404
        )
        
        html = f"""
        <html>
        <body>
            <p>Here is a broken remote image:</p>
            <img src="{image_url}" alt="Broken Image">
        </body>
        </html>
        """
        
        modified_html, saved_images = extract_and_replace_images(html, output_dir, "broken")
        
        # Check that no images were saved
        assert len(saved_images) == 0
        
        # Check that the HTML still contains the img tag (should be skipped)
        assert 'src="https://example.com/broken-image.png"' in modified_html
        assert 'alt="Broken Image"' in modified_html 