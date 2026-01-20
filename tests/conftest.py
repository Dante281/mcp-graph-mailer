import sys
import os

# Add project root to sys.path so we can import 'tools' module
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import pytest
from fastmcp import FastMCP


# This fixture allows us to instantiate a real FastMCP server object if needed,
# or provides a common entry point for mocking.
@pytest.fixture
def mcp():
    server = FastMCP("Test Server")
    return server
