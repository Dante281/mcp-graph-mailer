import os
import pytest
from unittest.mock import patch

# Import the code to test
# Since 'tools' is a package, we can import it directly if pytest is run from root
from tools.mail_preview import register


# We need a helper to access the tool function easily because FastMCP wraps it.
# We will create a mock MCP object that just captures the tool function.
class MockMCP:
    def __init__(self):
        self.tools = {}

    def tool(self, func_or_name=None):
        # Handle @mcp.tool() and @mcp.tool cases
        if callable(func_or_name):
            self.tools[func_or_name.__name__] = func_or_name
            return func_or_name

        def decorator(func):
            self.tools[func.__name__] = func
            return func

        return decorator


@pytest.fixture
def preview_tool():
    mcp_mock = MockMCP()
    register(mcp_mock)  # type: ignore
    return mcp_mock.tools["preview_email"]


def test_preview_valid_email(preview_tool):
    result = preview_tool(
        to=["user@example.com"],
        subject="Test Subject",
        body="Short body",
    )
    assert result["ok"] is True
    assert len(result["issues"]) == 0
    assert result["message"]["subject"] == "Test Subject"
    assert "user@example.com" in result["normalized"]["to"]


def test_preview_invalid_email(preview_tool):
    result = preview_tool(to=["not-an-email"], subject="Fail", body=".")
    assert result["ok"] is False
    assert any(i["type"] == "invalid_email" for i in result["issues"])


def test_preview_max_recipients(preview_tool):
    # Mock config via patch if needed, or rely on default env (which is 10)
    # Let's try 11 recipients
    recipients = [f"user{i}@example.com" for i in range(11)]
    result = preview_tool(to=recipients, subject="Spam", body=".")
    assert result["ok"] is False
    assert any(i["type"] == "too_many_recipients" for i in result["issues"])


def test_preview_body_too_large(preview_tool):
    # Default is 5000 chars
    long_body = "a" * 5001
    result = preview_tool(to=["user@example.com"], subject="Big", body=long_body)
    assert result["ok"] is False
    assert any(i["type"] == "body_too_large" for i in result["issues"])


@patch.dict(
    os.environ, {"ALLOWED_RECIPIENT_DOMAINS": "company.com, trusted.org"}, clear=True
)
def test_preview_blocked_domain(preview_tool):
    # Since the module reads env vars at IMPORT time, we might need to reload it
    # OR refactor the module to read env vars at runtime.
    # For now, let's assume the module logic reads global variables that we can patch?
    # NO, the module does: _ALLOWED_DOMAINS = ... at module level.
    # So patching os.environ here won't affect already imported module constants.

    # We will manually patch the constant in the module for this test.
    from tools import mail_preview

    original_domains = mail_preview._ALLOWED_DOMAINS
    mail_preview._ALLOWED_DOMAINS = {"company.com"}
    try:
        result = preview_tool(
            to=["hacker@evil.com", "valid@company.com"], subject="Hack", body="."
        )
        assert result["ok"] is False
        issues = result["issues"]
        blocked_issue = next(i for i in issues if i["type"] == "blocked_domain")
        assert "hacker@evil.com" in blocked_issue["items"]
        assert "valid@company.com" not in blocked_issue["items"]
    finally:
        mail_preview._ALLOWED_DOMAINS = original_domains


def test_normalize_emails(preview_tool):
    # Testing the normalization via the tool output
    result = preview_tool(
        to=[
            "  A@Test.KoM ",
            "",
            "a@test.kom",
        ],  # Duplicate (case insensitive) + empty + spaces
        subject="Norm",
        body=".",
    )
    # Should result in single unique email "A@Test.KoM" (logic preserves case or lowers?
    # Let's check logic: 'out.append(e)' -> preserves case of first occurrence, but checks lower for dupe.
    normalized = result["normalized"]["to"]
    assert len(normalized) == 1
    assert normalized[0] == "A@Test.KoM"
