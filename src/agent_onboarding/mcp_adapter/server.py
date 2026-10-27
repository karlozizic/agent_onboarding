import os
from typing import Annotated, Literal

import httpx
from mcp.server import MCPServer
from pydantic import Field

CORE_URL = os.environ.get("CORE_URL", "http://127.0.0.1:8000")
CORE_TOKEN = os.environ.get("CORE_TOKEN", "dev-token")

mcp = MCPServer("Account Onboarding")

ApplicationId = Annotated[str, Field(pattern="^[0-9a-f]{32}$")]
FundIsin = Annotated[str, Field(pattern="^[A-Z0-9]{12}$")]
# Same limits as the core API
MonthlyAmount = Annotated[int, Field(gt=0, le=100_000)]
IdempotencyKey = Annotated[str, Field(max_length=100)]


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
def estimate_costs(fund_isin: FundIsin, monthly_amount: MonthlyAmount) -> dict:
    return call("GET", f"/funds/{fund_isin}/costs?monthly_amount={monthly_amount}")


@mcp.tool()
def start_account_opening(idempotency_key: IdempotencyKey, fund_isin: FundIsin, monthly_amount: MonthlyAmount) -> dict:
    body = {"idempotency_key": idempotency_key, "fund_isin": fund_isin, "monthly_amount": monthly_amount}
    return call("POST", "/applications", body)


@mcp.tool()
def get_application_status(application_id: ApplicationId) -> dict:
    return call("GET", f"/applications/{application_id}")


@mcp.tool()
def change_amount(application_id: ApplicationId, monthly_amount: MonthlyAmount, expected_version: int) -> dict:
    body = {"monthly_amount": monthly_amount, "expected_version": expected_version}
    return call("POST", f"/applications/{application_id}/amount", body)


@mcp.tool()
def request_human(application_id: ApplicationId, reason: Literal["advice", "person"]) -> dict:
    return call("POST", f"/applications/{application_id}/human", {"reason": reason})


if __name__ == "__main__":
    mcp.run(transport="stdio")
