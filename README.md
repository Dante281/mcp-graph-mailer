## Development Environment

This project uses **uv** for dependency management and execution.

### Requirements
- Python 3.13+
- uv

### Setup

```bash
uv sync

All examples and workflows assume:
- Dependencies are managed via `uv`
- Scripts are executed using `uv run`

### Common Commands
- **Start the MCP server:**
  `uv run server.py`

- **Authenticate (First time only):**
  `uv run auth_bootstrap.py`

- **Manual Verification (Send Real Email):**
  `uv run scripts/manual_send.py`

- **Run HTTP Test Client:**
  `uv run scripts/test_client.py` (Requires server running in another terminal)

- **Run tests:**
  `uv run pytest`

## Project Structure
```text
/
├── server.py             # Entry point (MCP Server)
├── auth_bootstrap.py     # Initial Authentication Script
├── .env                  # Secrets (see .env.example)
├── scripts/              # Helper scripts
│   ├── manual_send.py    # Independent interactive test
│   └── test_client.py    # HTTP client for checking server
├── tools/                # Logic & Tools Implementation
│   ├── auth.py           # MSAL Integration
│   ├── email_flow.py     # Prepare/Confirm tools
│   ├── graph_client.py   # Microsoft Graph API wrapper
│   └── ...
└── tests/                # Automated Tests
```

This project does not support `pip`, `virtualenv`, or direct `python` execution.
