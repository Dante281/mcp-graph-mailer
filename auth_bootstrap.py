"""
Script to perform initial authentication using Device Code Flow.
Run this locally once to populate token_cache.bin.
"""

import sys
from dotenv import load_dotenv
from tools import auth


def bootstrap():
    load_dotenv()

    app = auth.get_msal_app()
    accounts = app.get_accounts()

    if accounts:
        print(f"Already found account: {accounts[0].get('username')}")
        print("Attempting silent token acquisition...")
        result = auth.get_token()
        if result and "access_token" in result:
            print("SUCCESS: Token refreshed and valid.")
            return
        else:
            print("Silent refresh failed. Re-authenticating...")

    # No accounts or silent failed -> Start Device Code Flow
    flow = app.initiate_device_flow(scopes=auth.SCOPES)
    if "user_code" not in flow:
        print("Error: Could not initiate device flow.")
        print(flow)
        sys.exit(1)

    print("\n" + "=" * 60)
    print("AUTHENTICATION REQUIRED")
    print(f"1. Open this URL: {flow['verification_uri']}")
    print(f"2. Enter code:    {flow['user_code']}")
    print("=" * 60 + "\n")

    # Poll for completion
    result = app.acquire_token_by_device_flow(flow)

    if "access_token" in result:
        print("SUCCESS: Authentication complete.")
        print(f"User: {result.get('id_token_claims', {}).get('name')}")
        print("Token saved to token_cache.bin")
    else:
        print("FAILURE: Could not acquire token.")
        print(result.get("error"))
        print(result.get("error_description"))


if __name__ == "__main__":
    bootstrap()
