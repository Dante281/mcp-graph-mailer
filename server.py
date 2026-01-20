import os
from fastmcp import FastMCP
from dotenv import load_dotenv

from tools.mail_preview import register as register_mail_preview
from tools.test_tools import register as register_test_tools

load_dotenv()

mcp = FastMCP("My MCP Server")


if os.getenv("ENABLE_TEST_TOOLS") == "1":
    register_test_tools(mcp)

register_mail_preview(mcp)

if __name__ == "__main__":
    mcp.run(transport="http", port=8000)
