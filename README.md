# agent_onboarding

Prototype: an AI agent (Claude via MCP) prepares a securities account with a fund savings plan; the customer identifies and confirms on their phone.

## Requirements

Python 3.15 and [uv](https://docs.astral.sh/uv/).

## Run

```
uv sync
uv run uvicorn agent_onboarding.core.app:app --host 127.0.0.1 --port 8000
```

Tests:

```
uv run pytest -q
```

## Connect Claude Desktop

Add to `claude_desktop_config.json` (replace `<repo>` with the path to this folder), then restart Claude Desktop:

```json
{
  "mcpServers": {
    "account-onboarding": {
      "command": "<repo>\\.venv\\Scripts\\python.exe",
      "args": ["-m", "agent_onboarding.mcp_adapter.server"],
      "env": { "CORE_URL": "http://127.0.0.1:8000", "CORE_TOKEN": "dev-token" }
    }
  }
}
```

## Try it

1. Open the phone page: `http://127.0.0.1:8000/device?key=phone-demo-key`
2. Ask Claude: *"I'd like to open a securities account and invest 100 EUR a month in a fund."*
3. Open the `customer_link` Claude returns: identify (mock eID), answer the questions, pick a Hausbank.
4. Open `http://127.0.0.1:8000/device?key=phone-demo-key`, click "Antrag ansehen" and press "Bestätigen". Then ask Claude for the status (`ACCOUNT_OPENED`).

Data is kept in memory; restarting the server clears it.
