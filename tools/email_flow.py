from typing import Any, Dict, List, Literal, Optional
from fastmcp import FastMCP
# Reuse the logic from preview, but we will call it internally or just reimplement strict call
# Actually, better to re-use the preview logic to valid and then save.
# But preview logic is inside a closure in 'register'.
# Refactoring 'mail_preview' to expose 'validate_and_preview' would be cleaner,
# but for now let's just use the validation logic if possible or duplicate simple checks.
# To avoid duplication, let's keep it simple: prepare_email does the same validates as preview.

# WAIT: best approach is to refactor mail_preview.py to share validation logic.
# For now, I will implement the tools and rely on the existing preview tool to be called by user BEFORE prepare,
# OR prepare re-runs validations. Roadmap said: "prepare_email: devuelve preview + draft_id".
# So it should generate the preview too.

from tools import drafts

# We need to import the validator helper from mail_preview or move it to a shared lib.
# Let's import the private helpers for now (Python allows it).
from tools.mail_preview import _normalize_emails, _is_valid_email, _domain_allowed
from tools.mail_preview import MAX_RECIPIENTS, MAX_BODY_CHARS
from tools import auth, graph_client


def register(mcp: FastMCP) -> None:
    @mcp.tool
    def prepare_email(
        to: List[str],
        subject: str,
        body: str,
        content_type: Literal["Text", "HTML"] = "Text",
        cc: Optional[List[str]] = None,
        bcc: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Guarda un borrador de email y devuelve un draft_id.
        Requiere llamar a confirm_send(draft_id) para enviarlo realmente.
        """
        # 1. Validation (Clean & Simple version)
        to_n = _normalize_emails(to)
        cc_n = _normalize_emails(cc)
        bcc_n = _normalize_emails(bcc)
        all_rcpts = to_n + cc_n + bcc_n

        if not to_n:
            return {"error": "Missing 'to' recipients"}

        if len(all_rcpts) > MAX_RECIPIENTS:
            return {"error": f"Too many recipients (max {MAX_RECIPIENTS})"}

        if any(not _is_valid_email(e) for e in all_rcpts):
            return {"error": "Invalid email format detected"}

        if any(not _domain_allowed(e) for e in all_rcpts):
            return {"error": "Domain not allowed by policy"}

        if len(body) > MAX_BODY_CHARS:
            return {"error": f"Body too long (max {MAX_BODY_CHARS})"}

        # 2. Save Draft
        email_data = {
            "to": to_n,
            "cc": cc_n,
            "bcc": bcc_n,
            "subject": subject,
            "body": body,
            "content_type": content_type,
        }

        draft_id = drafts.store.create_draft(email_data)

        return {
            "status": "Draft created. ACTION REQUIRED: Call confirm_send(draft_id) to send.",
            "draft_id": draft_id,
            "expires_in_seconds": drafts.store.expiry_seconds,
            "preview": {"subject": subject, "recipients_count": len(all_rcpts)},
        }

    @mcp.tool
    def confirm_send(draft_id: str) -> str:
        """
        Confirma y envía un borrador previamente creado con prepare_email.
        """
        data = drafts.store.get_draft(draft_id)
        if not data:
            return f"Error: Draft '{draft_id}' not found or expired."

        # 3. Get Token
        token_data = auth.get_token()
        if not token_data or "access_token" not in token_data:
            return "Error: Authentication required. Run auth_bootstrap.py or check auth status."

        token = token_data["access_token"]

        # 4. Send via Graph
        try:
            graph_client.send_mail(token, data)
        except Exception as e:
            return f"Error sending email: {str(e)}"

        recipients = ", ".join(data["to"])

        # 5. Burn the draft (only on success)
        drafts.store.delete_draft(draft_id)

        return f"Email sent successfully to {recipients}"

    @mcp.tool
    def cancel_draft(draft_id: str) -> str:
        """Cancela un borrador para que no pueda ser enviado."""
        drafts.store.delete_draft(draft_id)
        return f"Draft {draft_id} cancelled."
