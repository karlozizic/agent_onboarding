import uuid

from fastapi.testclient import TestClient

from agent_onboarding.core.app import AGENTS, app

client = TestClient(app)
AGENT = {"Authorization": "Bearer dev-token"}


def new_application(headers=AGENT, amount=100):
    body = {"idempotency_key": uuid.uuid4().hex, "fund_isin": "HRRBAGEQ0000", "monthly_amount": amount}
    return client.post("/applications", json=body, headers=headers)


def test_new_application_tells_agent_the_next_step():
    response = new_application()
    assert response.status_code == 201
    assert response.json()["next_step"] == "IDENT_REQUIRED"


def test_agent_needs_a_token():
    assert new_application(headers={}).status_code == 401


def test_amount_must_be_positive():
    assert new_application(amount=-5).status_code == 422


def test_other_agent_cannot_see_the_application():
    AGENTS["other-token"] = {"sub": "sub-other", "client_id": "other-agent"}
    application_id = new_application().json()["application_id"]
    other = {"Authorization": "Bearer other-token"}
    assert client.get(f"/applications/{application_id}", headers=other).json() == {"code": "UNKNOWN_APPLICATION"}


def test_stale_version_is_rejected():
    application = new_application().json()
    body = {"monthly_amount": 200, "expected_version": application["version"] + 1}
    response = client.post(f"/applications/{application['application_id']}/amount", json=body, headers=AGENT)
    assert response.json() == {"code": "VERSION_CONFLICT"}


def test_s7_advice_and_person_are_handed_over():
    url = f"/applications/{new_application().json()['application_id']}/human"
    assert client.post(url, json={"reason": "advice"}, headers=AGENT).json()["code"] == "ADVICE_HANDOFF"
    assert client.post(url, json={"reason": "person"}, headers=AGENT).json()["code"] == "HUMAN_CONTACT"
