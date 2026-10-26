import os

import httpx
from mcp.server import MCPServer

CORE_URL = os.environ.get("CORE_URL", "http://127.0.0.1:8000")
CORE_TOKEN = os.environ.get("CORE_TOKEN", "dev-token")

mcp = MCPServer("Account Onboarding")


def call(method, path, body=None):
    headers = {"Authorization": f"Bearer {CORE_TOKEN}"}
    response = httpx.request(method, f"{CORE_URL}{path}", json=body, headers=headers, timeout=5)
    return response.json()


@mcp.tool()
def ping() -> dict:
    return {"core_status": call("GET", "/health")["status"]}


@mcp.tool()
def list_funds() -> dict:
    return call("GET", "/funds")


@mcp.tool()
def get_requirements() -> dict:
    return call("GET", "/requirements")


@mcp.tool()
def estimate_costs(fund_isin: str, monthly_amount: int) -> dict:
    return call("GET", f"/funds/{fund_isin}/costs?monthly_amount={monthly_amount}")


@mcp.tool()
def start_account_opening(idempotency_key: str, fund_isin: str, monthly_amount: int) -> dict:
    body = {"idempotency_key": idempotency_key, "fund_isin": fund_isin, "monthly_amount": monthly_amount}
    return call("POST", "/applications", body)


@mcp.tool()
def get_application_status(application_id: str) -> dict:
    return call("GET", f"/applications/{application_id}")


@mcp.tool()
def change_amount(application_id: str, monthly_amount: int, expected_version: int) -> dict:
    body = {"monthly_amount": monthly_amount, "expected_version": expected_version}
    return call("POST", f"/applications/{application_id}/amount", body)


@mcp.tool()
def request_human(application_id: str, reason: str) -> dict:
    return call("POST", f"/applications/{application_id}/human", {"reason": reason})


if __name__ == "__main__":
    mcp.run(transport="stdio")
