import os

import httpx
from mcp.server import MCPServer
from pydantic import BaseModel

CORE_URL = os.environ.get("CORE_URL", "http://127.0.0.1:8000")
CORE_TOKEN = os.environ.get("CORE_TOKEN", "dev-token")

mcp = MCPServer("Account Onboarding")


class PingResult(BaseModel):
    core_status: str


@mcp.tool()
def ping() -> PingResult:
    """Check that the account onboarding service is reachable."""
    response = httpx.get(
        f"{CORE_URL}/health",
        headers={"Authorization": f"Bearer {CORE_TOKEN}"},
        timeout=5,
    )
    response.raise_for_status()
    return PingResult(core_status=response.json()["status"])


if __name__ == "__main__":
    mcp.run(transport="stdio")