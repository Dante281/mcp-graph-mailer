import os
from fastmcp import FastMCP
from dotenv import load_dotenv

load_dotenv()

from tools.mail_preview import register as register_mail_preview  # noqa: E402
from tools.email_flow import register as register_email_flow  # noqa: E402
from tools.auth_status import register as register_auth_status  # noqa: E402
from tools.test_tools import register as register_test_tools  # noqa: E402

mcp = FastMCP("My MCP Server")


if os.getenv("ENABLE_TEST_TOOLS") == "1":
    register_test_tools(mcp)

register_mail_preview(mcp)
register_email_flow(mcp)
register_auth_status(mcp)

if __name__ == "__main__":
    mcp.run(transport="http", port=8000)
