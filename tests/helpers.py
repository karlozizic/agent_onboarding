import uuid

from fastapi.testclient import TestClient

from agent_onboarding.core import domain
from agent_onboarding.core.app import AGENTS, app

client = TestClient(app)
AGENT = {"Authorization": "Bearer dev-token"}
AGENTS["other-token"] = {"sub": "sub-other", "client_id": "other-agent"}
OTHER = {"Authorization": "Bearer other-token"}
PHONE_KEY = "phone-demo-key"
ALL_YES = {"knows_funds": "on", "knows_risk": "on", "knows_costs": "on", "has_experience": "on"}


def new_application(headers=AGENT, amount=100):
    body = {"idempotency_key": uuid.uuid4().hex, "fund_isin": "DE000DEMO015", "monthly_amount": amount}
    return client.post("/applications", json=body, headers=headers)


def waiting_for_phone(answers=ALL_YES):
    application_id = new_application().json()["application_id"]
    client.post(f"/confirm/{application_id}/eid")
    client.post(f"/confirm/{application_id}/answers", data=answers)
    return domain.get_application(application_id)
