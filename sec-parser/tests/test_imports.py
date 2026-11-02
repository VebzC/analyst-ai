import os
import pytest
import logging
import importlib


def test_no_circular_imports():
    """Test that there are no circular imports in the codebase."""
    # This will fail if there are circular imports
    try:
        import sec_md_parser
        assert True, "Successfully imported the main package"
    except ImportError as e:
        assert False, f"Failed to import the main package: {str(e)}" 