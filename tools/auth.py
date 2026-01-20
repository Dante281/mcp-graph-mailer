import os
import atexit
import logging
import msal  # type: ignore

# Configuration
# This should match your Azure App Registration
CLIENT_ID = os.getenv("GRAPH_CLIENT_ID", "YOUR_CLIENT_ID_HERE")
AUTHORITY = (
    f"https://login.microsoftonline.com/{os.getenv('GRAPH_TENANT_ID', 'common')}"
)
SCOPES = ["User.Read", "Mail.Send", "Mail.ReadWrite"]
CACHE_FILE = "token_cache.bin"


def _load_cache():
    cache = msal.SerializableTokenCache()
    if os.path.exists(CACHE_FILE):
        cache.deserialize(open(CACHE_FILE, "r").read())
    return cache


def _save_cache(cache):
    if cache.has_state_changed:
        with open(CACHE_FILE, "w") as f:
            f.write(cache.serialize())


def get_msal_app(cache=None):
    if cache is None:
        cache = _load_cache()
        # Auto-save when script exits (if state changed)
        atexit.register(lambda: _save_cache(cache))

    return msal.PublicClientApplication(
        CLIENT_ID, authority=AUTHORITY, token_cache=cache
    )


def get_token() -> dict | None:
    """
    Attempts to get a valid token silently from cache.
    Returns the token dict (containing 'access_token') or None if login required.
    """
    app = get_msal_app()
    accounts = app.get_accounts()

    if not accounts:
        return None

    # Attempt silent acquisition
    result = app.acquire_token_silent(SCOPES, account=accounts[0])

    if not result:
        return None

    if "error" in result:
        # e.g. interaction_required
        logging.warning(f"Token error: {result.get('error_description')}")
        return None

    return result
