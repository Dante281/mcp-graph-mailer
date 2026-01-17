from fastmcp import FastMCP

"""
Test-only MCP tools.

These tools are intended for development and debugging only
and must not be used in production workflows.
"""


def register(mcp: FastMCP) -> None:
    @mcp.tool
    def greet(name: str) -> str:
        """Return a simple greeting."""
        return f"Hello, {name}!"

    @mcp.tool
    def add(a: int, b: int) -> int:
        """Add two numbers together."""
        return a + b

    @mcp.tool
    def echo(text: str) -> str:
        """Echo the input text."""
        return text
