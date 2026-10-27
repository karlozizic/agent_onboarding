import os
from pathlib import Path

from fastapi import Depends, FastAPI, Header, HTTPException, Query
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from agent_onboarding.core import domain, pages, products
from agent_onboarding.core.domain import Rejected
from agent_onboarding.core.schemas import (
    BASE_URL,
    MAX_MONTHLY_AMOUNT,
    ApplicationId,
    HumanRequest,
    NewAmount,
    NewApplication,
    application_view,
)

AGENTS = {
    os.environ.get("CORE_TOKEN", "dev-token"): {
        "sub": "sub-demo",
        "client_id": "claude-desktop",
    }
}

app = FastAPI(docs_url=None, redoc_url=None, openapi_url=None)

app.include_router(pages.router)
app.mount("/static", StaticFiles(directory=Path(__file__).parent / "static"), name="static")


@app.exception_handler(Rejected)
def rejected(request, error):
    return JSONResponse(status_code=409, content={"code": error.code})


def current_agent(authorization: str = Header(default="")):
    token = authorization.removeprefix("Bearer ")
    if not token or token not in AGENTS:
        raise HTTPException(status_code = 401)
    return AGENTS[token]

@app.get("/health")
def health(agent=Depends(current_agent)):
    return {"status": "ok"}


@app.get("/funds")
def funds(agent=Depends(current_agent)):
    return {isin: fund | {"kid_url": f"{BASE_URL}/kid/{isin}"} for isin, fund in products.FUNDS.items()}


@app.get("/funds/{fund_isin}/costs")
def costs(fund_isin: str, monthly_amount: int = Query(gt=0, le=MAX_MONTHLY_AMOUNT), agent=Depends(current_agent)):
    if fund_isin not in products.FUNDS:
        raise Rejected("UNKNOWN_FUND")
    return products.estimate_costs(fund_isin, monthly_amount)


@app.get("/requirements")
def requirements(agent=Depends(current_agent)):
    return {"requirements": products.REQUIREMENTS}


@app.post("/applications", status_code=201)
def create_application(body: NewApplication, agent=Depends(current_agent)):
    application = domain.create_application(
        agent["sub"],
        agent["client_id"],
        body.idempotency_key,
        body.fund_isin,
        body.monthly_amount
    )
    return application_view(application)


@app.get("/applications/{application_id}")
def get_application(application_id: ApplicationId, agent=Depends(current_agent)):
    return application_view(domain.get_agent_application(application_id, agent["sub"]))


@app.post("/applications/{application_id}/amount")
def change_amount(application_id: ApplicationId, body: NewAmount, agent=Depends(current_agent)):
    application = domain.get_agent_application(application_id, agent["sub"])
    domain.change_offer(application_id, body.monthly_amount, body.expected_version)
    return application_view(application)


@app.post("/applications/{application_id}/human")
def request_human(application_id: ApplicationId, body: HumanRequest, agent=Depends(current_agent)):
    domain.get_agent_application(application_id, agent["sub"])
    if body.reason == "advice":
        return {"code": "ADVICE_HANDOFF"}
    return {"code": "HUMAN_CONTACT"}