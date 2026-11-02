import os
import pytest
import logging
from pathlib import Path


@pytest.fixture(scope="session", autouse=True)
def setup_test_environment():
    """Set up the test environment."""
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    
    # Create a temporary directory for test outputs if needed
    test_output_dir = Path("test_output")
    test_output_dir.mkdir(exist_ok=True)
    
    # Return the test output directory path for use in tests
    return test_output_dir


@pytest.fixture
def test_data_dir():
    """Return the path to the test data directory."""
    return Path(__file__).parent / "data"
