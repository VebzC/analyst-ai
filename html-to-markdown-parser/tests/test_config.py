import os
import unittest
from html_to_md.config import get_sec_api_key


class TestConfig(unittest.TestCase):
    def test_get_sec_api_key_success(self):
        """Test that get_sec_api_key returns the key when it's set"""
        # Save the original environment variable value if it exists
        original_key = os.environ.get("SEC_API_KEY")
        
        try:
            # Set a test key
            test_key = "test_api_key_12345"
            os.environ["SEC_API_KEY"] = test_key
            
            # Call the function and verify it returns the correct key
            result = get_sec_api_key()
            self.assertEqual(result, test_key)
            
        finally:
            # Restore the original environment
            if original_key:
                os.environ["SEC_API_KEY"] = original_key
            else:
                # If it wasn't set originally, remove it
                if "SEC_API_KEY" in os.environ:
                    del os.environ["SEC_API_KEY"]
    
    def test_get_sec_api_key_missing(self):
        """Test that get_sec_api_key raises ValueError when the key is not set"""
        # Save the original environment variable value if it exists
        original_key = os.environ.get("SEC_API_KEY")
        
        try:
            # Ensure the key is not set
            if "SEC_API_KEY" in os.environ:
                del os.environ["SEC_API_KEY"]
            
            # Call the function and verify it raises ValueError
            with self.assertRaises(ValueError) as context:
                get_sec_api_key()
            
            # Verify the error message
            self.assertEqual(
                str(context.exception),
                "SEC_API_KEY is not set in environment variables."
            )
            
        finally:
            # Restore the original environment
            if original_key:
                os.environ["SEC_API_KEY"] = original_key


if __name__ == "__main__":
    unittest.main() 