from typing import Any, Dict
from fastmcp import FastMCP
from tools import auth


def register(mcp: FastMCP) -> None:
    @mcp.tool
    def check_auth_status() -> Dict[str, Any]:
        """
        Verifica si el servidor tiene credenciales válidas para enviar correos (Microsoft Graph).
        """
        token_data = auth.get_token()

        if not token_data:
            return {
                "status": "Not Authenticated",
                "message": "Server needs authentication. Operator must run 'uv run python auth_bootstrap.py'.",
                "valid": False,
            }

        claims = token_data.get("id_token_claims", {})
        user = claims.get("name") or claims.get("preferred_username") or "Unknown"

        return {
            "status": "Authenticated",
            "user": user,
            "valid": True,
            "scopes": token_data.get("scope", "").split(),
        }
