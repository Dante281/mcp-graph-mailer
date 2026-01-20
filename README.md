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

### Common Commandsamples
- Start the MCP server:
  `uv run python server.py`

- Run the HTTP client:
  `uv run python client.py`

- Run tests:
  `uv run pytest`

This project does not support `pip`, `virtualenv`, or direct `python` execution.
