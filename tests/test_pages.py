import uuid

from fastapi.testclient import TestClient

from agent_onboarding.core import domain, pages, products
from agent_onboarding.core.app import app
from agent_onboarding.core.domain import State

client = TestClient(app)
AGENT = {"Authorization": "Bearer dev-token"}
ALL_YES = {"knows_funds": "on", "knows_risk": "on", "knows_costs": "on", "has_experience": "on"}


def application_waiting_for_phone():
    body = {"idempotency_key": uuid.uuid4().hex, "fund_isin": "HRRBAGEQ0000", "monthly_amount": 100}
    application_id = client.post("/applications", json=body, headers=AGENT).json()["application_id"]
    client.post(f"/confirm/{application_id}/eid")
    client.post(f"/confirm/{application_id}/answers", data=ALL_YES)
    return domain.get_application(application_id)


def approve(application, key="phone-demo-key", offer_hash="", headers=None):
    client.get(f"/device/{application.application_id}?key=phone-demo-key")
    form = {
        "nonce": pages.NONCES.get(application.application_id, ""),
        "offer_hash": offer_hash or products.offer_hash(application.offer),
    }
    return client.post(f"/device/{application.application_id}/approve?key={key}", data=form, headers=headers)


def test_s1_customer_and_phone_open_the_account():
    application = application_waiting_for_phone()
    assert approve(application).status_code == 200
    status = client.get(f"/applications/{application.application_id}", headers=AGENT).json()
    assert status["state"] == "ACCOUNT_OPENED"
    assert status["next_step"] == "DONE"


def test_s8_confirm_without_the_phone_is_blocked():
    application = application_waiting_for_phone()
    assert approve(application, key="", headers=AGENT).status_code == 403
    assert application.state == State.CHECKS_CLEARED


def test_s5_phone_cannot_confirm_an_old_offer():
    application = application_waiting_for_phone()
    old_hash = products.offer_hash(application.offer)
    body = {"monthly_amount": 500, "expected_version": application.version}
    client.post(f"/applications/{application.application_id}/amount", json=body, headers=AGENT)
    response = approve(application, offer_hash=old_hash)
    assert response.json() == {"code": "OFFER_CHANGED"}


def test_phone_lists_applications_waiting_for_it():
    application = application_waiting_for_phone()
    assert client.get("/device", headers=AGENT).status_code == 403
    assert application.application_id in client.get("/device?key=phone-demo-key").text


def test_agent_gets_a_kid_link_for_each_fund():
    funds = client.get("/funds", headers=AGENT).json()
    assert funds["HRERSTEB0009"]["kid_url"].endswith("/kid/HRERSTEB0009")


def test_customer_can_read_the_kid():
    assert "4 von 7" in client.get("/kid/HRRBAGEQ0000").text
    assert client.get("/kid/UNKNOWN").status_code == 404


def test_nonce_works_only_once():
    application = application_waiting_for_phone()
    client.get(f"/device/{application.application_id}?key=phone-demo-key")
    form = {
        "nonce": pages.NONCES[application.application_id],
        "offer_hash": products.offer_hash(application.offer),
    }
    url = f"/device/{application.application_id}/approve?key=phone-demo-key"
    assert client.post(url, data=form).status_code == 200
    assert client.post(url, data=form).json() == {"code": "CONFIRMATION_EXPIRED"}


def test_agent_gets_a_link_for_the_customer():
    body = {"idempotency_key": uuid.uuid4().hex, "fund_isin": "HRRBAGEQ0000", "monthly_amount": 100}
    application = client.post("/applications", json=body, headers=AGENT).json()
    assert application["customer_link"].endswith(f"/confirm/{application['application_id']}")


def test_phone_shows_the_declared_hausbank():
    body = {"idempotency_key": uuid.uuid4().hex, "fund_isin": "HRRBAGEQ0000", "monthly_amount": 100}
    application_id = client.post("/applications", json=body, headers=AGENT).json()["application_id"]
    client.post(f"/confirm/{application_id}/eid")
    client.post(f"/confirm/{application_id}/answers", data=ALL_YES | {"hausbank": "SPK-KOELNBONN"})
    response = client.get(f"/device/{application_id}?key=phone-demo-key")
    assert "Sparkasse KölnBonn" in response.text


def test_missing_knowledge_shows_a_warning():
    body = {"idempotency_key": uuid.uuid4().hex, "fund_isin": "HRRBAGEQ0000", "monthly_amount": 100}
    application_id = client.post("/applications", json=body, headers=AGENT).json()["application_id"]
    client.post(f"/confirm/{application_id}/eid")
    response = client.post(f"/confirm/{application_id}/answers", data={"knows_funds": "on"})
    assert "nicht angemessen" in response.text
