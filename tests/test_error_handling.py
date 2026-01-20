import pytest
from unittest.mock import patch
from tools import email_flow, drafts


class MockMCP:
    def __init__(self):
        self.tools = {}

    def tool(self, func):
        self.tools[func.__name__] = func
        return func


@pytest.fixture
def flow_tools():
    mcp_mock = MockMCP()
    email_flow.register(mcp_mock)  # type: ignore
    return mcp_mock.tools


@pytest.fixture(autouse=True)
def clean_store():
    drafts.store._store.clear()
    yield
    drafts.store._store.clear()


def test_auth_error(flow_tools):
    prepare = flow_tools["prepare_email"]
    confirm = flow_tools["confirm_send"]
    res = prepare(to=["user@example.com"], subject="AuthFail", body=".")
    did = res["draft_id"]

    with patch("tools.auth.get_token", return_value={"access_token": "fake"}):
        with patch("requests.post") as mock_post:
            mock_post.return_value.ok = False
            mock_post.return_value.status_code = 401
            mock_post.return_value.json.return_value = {
                "error": {"message": "Token expired"}
            }

            msg = confirm(did)
            assert "Authentication failed" in msg
            assert "Token invalid or expired" in msg


def test_throttling_error(flow_tools):
    prepare = flow_tools["prepare_email"]
    confirm = flow_tools["confirm_send"]
    res = prepare(to=["user@example.com"], subject="Throttled", body=".")
    did = res["draft_id"]

    with patch("tools.auth.get_token", return_value={"access_token": "fake"}):
        with patch("requests.post") as mock_post:
            mock_post.return_value.ok = False
            mock_post.return_value.status_code = 429
            mock_post.return_value.json.return_value = {
                "error": {"message": "Too many requests"}
            }

            msg = confirm(did)
            assert "Rate limit exceeded" in msg


def test_client_error(flow_tools):
    prepare = flow_tools["prepare_email"]
    confirm = flow_tools["confirm_send"]
    res = prepare(to=["user@example.com"], subject="BadReq", body=".")
    did = res["draft_id"]

    with patch("tools.auth.get_token", return_value={"access_token": "fake"}):
        with patch("requests.post") as mock_post:
            mock_post.return_value.ok = False
            mock_post.return_value.status_code = 400
            mock_post.return_value.json.return_value = {
                "error": {"message": "Bad Request Argument"}
            }

            msg = confirm(did)
            assert "Invalid request" in msg
            assert "Bad Request Argument" in msg


def test_server_error(flow_tools):
    prepare = flow_tools["prepare_email"]
    confirm = flow_tools["confirm_send"]
    res = prepare(to=["user@example.com"], subject="ServerFail", body=".")
    did = res["draft_id"]

    with patch("tools.auth.get_token", return_value={"access_token": "fake"}):
        with patch("requests.post") as mock_post:
            mock_post.return_value.ok = False
            mock_post.return_value.status_code = 503
            mock_post.return_value.text = "Service Unavailable"
            mock_post.return_value.json.side_effect = ValueError("No JSON")

            msg = confirm(did)
            assert "Microsoft Graph Server Error" in msg
