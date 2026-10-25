import os

from fastapi import Depends, FastAPI, Header, HTTPException
from starlette.responses import JSONResponse

from agent_onboarding.core import products, domain
from agent_onboarding.core.domain import Rejected
from agent_onboarding.core.schemas import application_view, NewApplication, NewAmount, HumanRequest

AGENTS = {
    os.environ.get("CORE_TOKEN", "dev-token"): {
        "sub": "sub-demo",
        "client_id": "claude-desktop",
    }
}

app = FastAPI()

@app.exception_handler(Rejected)
def rejected(request, error):
    return JSONResponse(status_code=409, content={"code": error.code})


def current_agent(authorization: str = Header(default="")):
    token = authorization.removeprefix("Bearer ")
    if token not in AGENTS:
        raise HTTPException(status_code = 401)
    return AGENTS[token]

@app.get("/health")
def health(agent=Depends(current_agent)):
    return {"status": "ok"}


@app.get("/funds")
def funds(agent=Depends(current_agent)):
    return products.FUNDS


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
def get_application(application_id: str, agent=Depends(current_agent)):
    return application_view(domain.get_agent_application(application_id, agent["sub"]))


@app.post("/applications/{application_id}/amount")
def change_amount(application_id: str, body: NewAmount, agent=Depends(current_agent)):
    domain.get_agent_application(application_id, agent["sub"])
    domain.change_offer(application_id, body.monthly_amount, body.expected_version)
    return application_view(domain.get_application(application_id))


@app.post("/applications/{application_id}/human")
def request_human(application_id: str, body: HumanRequest, agent=Depends(current_agent)):
    domain.get_agent_application(application_id, agent["sub"])
    if body.reason == "advice":
        return {"code": "ADVICE_HANDOFF"}
    return {"code": "HUMAN_CONTACT"}