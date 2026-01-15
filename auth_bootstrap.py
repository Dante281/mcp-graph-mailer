import os
from pathlib import Path
import msal
from dotenv import load_dotenv

load_dotenv()

TENANT_ID = os.environ["TENANT_ID"]
CLIENT_ID = os.environ["CLIENT_ID"]
TOKEN_CACHE_PATH = Path(os.getenv("TOKEN_CACHE_PATH", "token_cache.bin"))

AUTHORITY = f"https://login.microsoftonline.com/{TENANT_ID}"
SCOPES = ["https://graph.microsoft.com/Mail.Send"]


def main():
    cache = msal.SerializableTokenCache()
    if TOKEN_CACHE_PATH.exists():
        cache.deserialize(TOKEN_CACHE_PATH.read_text())

    app = msal.PublicClientApplication(
        client_id=CLIENT_ID,
        authority=AUTHORITY,
        token_cache=cache,
    )

    flow = app.initiate_device_flow(scopes=SCOPES)
    if "user_code" not in flow:
        raise RuntimeError(f"Device flow init failed: {flow}")

    print(flow["message"])  # URL + código
    result = app.acquire_token_by_device_flow(flow)

    if "access_token" not in result:
        raise RuntimeError(f"Token acquisition failed: {result}")

    TOKEN_CACHE_PATH.write_text(cache.serialize())
    print(f"OK. Token cache guardado en: {TOKEN_CACHE_PATH}")


if __name__ == "__main__":
    main()
