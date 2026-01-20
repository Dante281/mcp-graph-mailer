import pytest
import time
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
    # Clear draft store before each test
    drafts.store._store.clear()
    yield
    drafts.store._store.clear()


def test_prepare_success(flow_tools):
    prepare = flow_tools["prepare_email"]
    res = prepare(to=["test@example.com"], subject="Draft", body="Body")
    assert "draft_id" in res
    assert res["status"].startswith("Draft created")

    # Verify it's in the store
    did = res["draft_id"]
    stored = drafts.store.get_draft(did)
    assert stored is not None
    assert stored["subject"] == "Draft"


def test_confirm_flow(flow_tools):
    prepare = flow_tools["prepare_email"]
    confirm = flow_tools["confirm_send"]

    # 1. Create
    res = prepare(to=["final@example.com"], subject="Sent", body="Hi")
    did = res["draft_id"]

    # 2. Confirm
    confirm_res = confirm(did)
    assert "sent successfully" in confirm_res

    # 3. Verify deleted
    assert drafts.store.get_draft(did) is None

    # 4. Confirm again (should fail)
    retry = confirm(did)
    assert "not found" in retry


def test_expiration_logic(flow_tools):
    # Set short expiry
    drafts.store.expiry_seconds = 1

    prepare = flow_tools["prepare_email"]
    res = prepare(to=["slow@example.com"], subject="Slow", body=".")
    did = res["draft_id"]

    # Wait for expire
    time.sleep(1.1)

    # Try confirm
    confirm = flow_tools["confirm_send"]
    out = confirm(did)
    assert "not found or expired" in out


def test_prepare_validation_fail(flow_tools):
    prepare = flow_tools["prepare_email"]
    # Invalid email
    res = prepare(to=["bad-email"], subject="X", body=".")
    assert "error" in res
    assert "Invalid email" in res["error"]
