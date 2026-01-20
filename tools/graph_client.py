import requests
from typing import Dict, Any, List

GRAPH_API_URL = "https://graph.microsoft.com/v1.0"


def _build_recipient_list(emails: List[str]) -> List[Dict[str, Any]]:
    return [{"emailAddress": {"address": email}} for email in emails]


class GraphError(Exception):
    """Base class for Graph API errors."""

    pass


class GraphAuthError(GraphError):
    """401 Unauthorized."""

    pass


class GraphThrottlingError(GraphError):
    """429 Too Many Requests."""

    pass


class GraphClientError(GraphError):
    """400-499 Client Errors."""

    pass


class GraphServerError(GraphError):
    """500+ Server Errors."""

    pass


def send_mail(token: str, draft: Dict[str, Any]) -> None:
    """
    Sends an email using Microsoft Graph API.
    Raises GraphError subclasses on failure.
    """
    url = f"{GRAPH_API_URL}/me/sendMail"
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

    # Construct Message Resource
    # https://learn.microsoft.com/en-us/graph/api/resources/message
    message = {
        "subject": draft["subject"],
        "body": {
            "contentType": draft.get("content_type", "Text"),
            "content": draft["body"],
        },
        "toRecipients": _build_recipient_list(draft["to"]),
        "ccRecipients": _build_recipient_list(draft.get("cc") or []),
        "bccRecipients": _build_recipient_list(draft.get("bcc") or []),
    }

    payload = {"message": message, "saveToSentItems": "true"}

    try:
        response = requests.post(url, headers=headers, json=payload, timeout=10)
    except requests.RequestException as e:
        raise GraphError(f"Network error: {str(e)}")

    if not response.ok:
        # Try to parse error details
        try:
            error_data = response.json()
            error_msg = error_data.get("error", {}).get("message", response.text)
        except Exception:
            error_msg = response.text

        status = response.status_code
        full_msg = f"Graph API Error ({status}): {error_msg}"

        if status == 401:
            raise GraphAuthError(full_msg)
        elif status == 429:
            raise GraphThrottlingError(full_msg)
        elif 400 <= status < 500:
            raise GraphClientError(full_msg)
        elif status >= 500:
            raise GraphServerError(full_msg)
        else:
            raise GraphError(full_msg)
