"""
Script to manually verify the Hito 6 email sending capabilities.
Usage: uv run scripts/manual_send.py <TOKEN_FROM_BOOTSTRAP_IF_NEEDED_BUT_WE_USE_CACHE>
Actually, it just uses the tools which use the cache.
"""

import sys
import os

# Add project root to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv

load_dotenv()

from tools.email_flow import register as register_email_flow  # noqa: E402
from tools import auth  # noqa: E402


def main():
    print("=== Manual Graph Email Sender Verification ===")

    # 1. Check Env
    if not os.getenv("GRAPH_CLIENT_ID"):
        print("ERROR: GRAPH_CLIENT_ID not found in environment.")
        print("Please copy .env.example to .env and configure it.")
        return

    # 2. Check Auth
    token = auth.get_token()
    if not token:
        print("ERROR: Authentication required.")
        print("Run 'uv run auth_bootstrap.py' first.")
        return
    print("Auth OK: Found token for user.")

    # 3. Setup Mock MCP to get access to tools
    # We can't easily call the tool functions directly because they are wrapped inside 'register'.
    # So we use the same MockMCP trick as in tests, but for real execution.

    class LocalMCP:
        def __init__(self):
            self.tools = {}

        def tool(self, func):
            self.tools[func.__name__] = func
            return func

    mcp = LocalMCP()
    register_email_flow(mcp)  # type: ignore

    prepare_email = mcp.tools["prepare_email"]
    confirm_send = mcp.tools["confirm_send"]

    # 4. Get User Input
    recipient = input("\nEnter recipient email (e.g. your own email): ").strip()
    if not recipient:
        print("Cancelled.")
        return

    subject = f"Test Email from MCP Graph Mailer - {str(os.urandom(4).hex())}"
    body = "This is a test email sent via the manual verification script.\n\nIt confirms that Hito 6 is working!"

    print(f"\nPreparing email to {recipient}...")

    # 5. Call Prepare
    try:
        res = prepare_email(to=[recipient], subject=subject, body=body)
    except Exception as e:
        print(f"Error calling prepare_email: {e}")
        return

    if "error" in res:
        print(f"FAILED to prepare draft: {res['error']}")
        return

    draft_id = res.get("draft_id")
    print(f"Draft created! ID: {draft_id}")
    print(f"Preview: {res.get('preview')}")

    confirm = input("\nDo you want to SEND this email now? (y/N): ").strip().lower()
    if confirm != "y":
        print("Cancelled. Draft remains (it will expire).")
        return

    # 6. Call Confirm
    print("Sending...")
    try:
        result = confirm_send(draft_id)
        print(f"\nRESULT: {result}")
    except Exception as e:
        print(f"EXCEPTION during send: {e}")


if __name__ == "__main__":
    main()
