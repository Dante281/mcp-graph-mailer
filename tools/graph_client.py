import requests
from typing import Dict, Any, List

GRAPH_API_URL = "https://graph.microsoft.com/v1.0"


def _build_recipient_list(emails: List[str]) -> List[Dict[str, Any]]:
    return [{"emailAddress": {"address": email}} for email in emails]


def send_mail(token: str, draft: Dict[str, Any]) -> None:
    """
    Sends an email using Microsoft Graph API.
    Raises Exception on failure.
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

    response = requests.post(url, headers=headers, json=payload, timeout=10)

    if not response.ok:
        # Try to parse error details
        try:
            error_data = response.json()
            error_msg = error_data.get("error", {}).get("message", response.text)
        except Exception:
            error_msg = response.text

        raise Exception(f"Graph API Error ({response.status_code}): {error_msg}")
