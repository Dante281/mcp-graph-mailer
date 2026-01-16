import os
import re
from typing import Any, Dict, List, Literal, Optional

from fastmcp import FastMCP

# --- config (leída al importar el módulo) ---
_ALLOWED_DOMAINS = {
    d.strip().lower()
    for d in os.getenv("ALLOWED_RECIPIENT_DOMAINS", "").split(",")
    if d.strip()
}
MAX_RECIPIENTS = int(os.getenv("MAX_RECIPIENTS", "10"))
MAX_BODY_CHARS = int(os.getenv("MAX_BODY_CHARS", "5000"))

_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def _normalize_emails(values: Optional[List[str]]) -> List[str]:
    """Trim + drop empties + de-dup preserving order."""
    if not values:
        return []
    seen: set[str] = set()
    out: List[str] = []
    for v in values:
        if not v:
            continue
        e = v.strip()
        if not e:
            continue
        key = e.lower()
        if key not in seen:
            seen.add(key)
            out.append(e)
    return out


def _is_valid_email(e: str) -> bool:
    return bool(_EMAIL_RE.match(e.strip()))


def _domain_allowed(e: str) -> bool:
    """Allow all if allowlist is empty, otherwise require domain to be in allowlist."""
    if not _ALLOWED_DOMAINS:
        return True
    parts = e.split("@")
    if len(parts) != 2:
        return False
    return parts[1].lower() in _ALLOWED_DOMAINS


def register(mcp: FastMCP) -> None:
    @mcp.tool
    def preview_email(
        to: List[str],
        subject: str,
        body: str,
        content_type: Literal["Text", "HTML"] = "Text",
        cc: Optional[List[str]] = None,
        bcc: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Prepara un email (preview) sin enviarlo.
        Devuelve un JSON con validaciones, destinatarios normalizados y un resumen del body.
        """
        to_n = _normalize_emails(to)
        cc_n = _normalize_emails(cc)
        bcc_n = _normalize_emails(bcc)

        all_rcpts = to_n + cc_n + bcc_n

        issues: List[Dict[str, Any]] = []

        if not to_n:
            issues.append(
                {
                    "type": "missing_to",
                    "message": "Debe existir al menos un destinatario en 'to'.",
                }
            )

        if len(all_rcpts) > MAX_RECIPIENTS:
            issues.append(
                {
                    "type": "too_many_recipients",
                    "message": f"Demasiados destinatarios ({len(all_rcpts)}). Máximo: {MAX_RECIPIENTS}.",
                    "max": MAX_RECIPIENTS,
                    "count": len(all_rcpts),
                }
            )

        invalid = [e for e in all_rcpts if not _is_valid_email(e)]
        if invalid:
            issues.append(
                {
                    "type": "invalid_email",
                    "message": "Emails con formato inválido.",
                    "items": invalid,
                }
            )

        blocked = [
            e for e in all_rcpts if _is_valid_email(e) and not _domain_allowed(e)
        ]
        if blocked:
            issues.append(
                {
                    "type": "blocked_domain",
                    "message": "Destinatarios fuera de la allowlist de dominios.",
                    "items": blocked,
                    "allowed_domains": sorted(_ALLOWED_DOMAINS),
                }
            )

        if len(body) > MAX_BODY_CHARS:
            issues.append(
                {
                    "type": "body_too_large",
                    "message": f"Body demasiado largo ({len(body)} chars). Máximo: {MAX_BODY_CHARS}.",
                    "max": MAX_BODY_CHARS,
                    "count": len(body),
                }
            )

        if not subject.strip():
            issues.append(
                {
                    "type": "empty_subject",
                    "message": "Subject vacío (permitido, pero no recomendado).",
                }
            )

        ok = len(issues) == 0
        body_preview = body[:200] + ("…" if len(body) > 200 else "")

        return {
            "ok": ok,
            "issues": issues,
            "normalized": {"to": to_n, "cc": cc_n, "bcc": bcc_n},
            "message": {
                "subject": subject,
                "content_type": content_type,
                "body_preview": body_preview,
                "body_length": len(body),
            },
            "policy": {
                "allowed_domains": sorted(_ALLOWED_DOMAINS),
                "max_recipients": MAX_RECIPIENTS,
                "max_body_chars": MAX_BODY_CHARS,
            },
            "next_step": "If ok=true, call prepare_email (next milestone) or proceed to confirm/send flow later.",
        }
