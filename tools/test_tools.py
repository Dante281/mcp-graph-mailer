from fastmcp import FastMCP


def register(mcp: FastMCP) -> None:
    @mcp.tool
    def greet(name: str) -> str:
        return f"Hello, {name}!"
