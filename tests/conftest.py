# tests/conftest.py
"""
Pytest configuration and fixtures for the testing suite.
"""

import tempfile
from pathlib import Path
from typing import Generator

import pytest

@pytest.fixture(scope="function")
def temp_output_dir() -> Generator[Path, None, None]:
    """
    Pytest fixture to create a temporary directory for test outputs.

    This fixture creates a unique, empty directory before a test function
    is executed and automatically cleans it up (deletes it) after the
    test is finished, regardless of whether it passed or failed.

    Yields:
        The Path object of the created temporary directory.
    """
    with tempfile.TemporaryDirectory() as temp_dir:
        yield Path(temp_dir)