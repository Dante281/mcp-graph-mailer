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


def test_confirm_send_success(flow_tools):
    prepare = flow_tools["prepare_email"]
    confirm = flow_tools["confirm_send"]

    # 1. Create Draft
    res = prepare(to=["user@example.com"], subject="Test", body="Hello")
    did = res["draft_id"]

    # 2. Mock Auth and Graph
    fake_token = {"access_token": "fake-jwt"}

    with patch("tools.auth.get_token", return_value=fake_token):
        with patch("requests.post") as mock_post:
            # Simulate Success 202 Accepted
            mock_post.return_value.ok = True
            mock_post.return_value.status_code = 202

            # Confirm
            msg = confirm(did)

            assert "sent successfully" in msg

            # Verify Graph Call
            mock_post.assert_called_once()
            args, kwargs = mock_post.call_args
            assert kwargs["headers"]["Authorization"] == "Bearer fake-jwt"
            assert kwargs["json"]["message"]["subject"] == "Test"

    # 3. Verify Draft Deleted
    assert drafts.store.get_draft(did) is None


def test_confirm_send_failure_keeps_draft(flow_tools):
    prepare = flow_tools["prepare_email"]
    confirm = flow_tools["confirm_send"]

    res = prepare(to=["fail@example.com"], subject="Fail", body=".")
    did = res["draft_id"]

    with patch("tools.auth.get_token", return_value={"access_token": "tkn"}):
        with patch("requests.post") as mock_post:
            # Simulate Error 500
            mock_post.return_value.ok = False
            mock_post.return_value.status_code = 500
            mock_post.return_value.text = "Internal Server Error"
            # Ensure json() returns dict or raises to trigger the text fallback
            mock_post.return_value.json.side_effect = ValueError("No JSON")

            msg = confirm(did)

            # Should return error message
            # Should return error message
            assert "Microsoft Graph Server Error" in msg

    # 4. Verify Draft STILL EXISTS (for retry)
    assert drafts.store.get_draft(did) is not None
