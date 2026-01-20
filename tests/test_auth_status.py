import pytest
from unittest.mock import patch
from tools import auth_status


class MockMCP:
    def __init__(self):
        self.tools = {}

    def tool(self, func):
        self.tools[func.__name__] = func
        return func


@pytest.fixture
def status_tool():
    mcp_mock = MockMCP()
    auth_status.register(mcp_mock)  # type: ignore
    return mcp_mock.tools["check_auth_status"]


def test_not_authenticated(status_tool):
    # Mock get_token to return None
    with patch("tools.auth.get_token", return_value=None):
        result = status_tool()
        assert result["valid"] is False
        assert result["status"] == "Not Authenticated"


def test_authenticated(status_tool):
    # Mock valid token data
    fake_token = {
        "id_token_claims": {"name": "Test User"},
        "scope": "User.Read Mail.Send",
    }
    with patch("tools.auth.get_token", return_value=fake_token):
        result = status_tool()
        assert result["valid"] is True
        assert result["status"] == "Authenticated"
        assert result["user"] == "Test User"
        assert "Mail.Send" in result["scopes"]
