from helpers import AGENT, OTHER, client, new_application

from agent_onboarding.core import products


def test_health_with_token():
    assert client.get("/health", headers=AGENT).json() == {"status": "ok"}


def test_agent_needs_a_token():
    assert new_application(headers={}).status_code == 401


def test_new_application_tells_agent_the_next_step():
    response = new_application()
    assert response.status_code == 201
    assert response.json()["next_step"] == "IDENT_REQUIRED"


def test_amount_must_be_positive():
    assert new_application(amount=-5).status_code == 422


def test_other_agent_cannot_see_the_application():
    application_id = new_application().json()["application_id"]
    assert client.get(f"/applications/{application_id}", headers=OTHER).json() == {"code": "UNKNOWN_APPLICATION"}


def test_s7_advice_and_person_are_handed_over():
    url = f"/applications/{new_application().json()['application_id']}/human"
    assert client.post(url, json={"reason": "advice"}, headers=AGENT).json()["code"] == "ADVICE_HANDOFF"
    assert client.post(url, json={"reason": "person"}, headers=AGENT).json()["code"] == "HUMAN_CONTACT"


def test_agent_can_tell_what_the_customer_needs():
    assert client.get("/requirements", headers=AGENT).json()["requirements"] == products.REQUIREMENTS


def test_costs_per_year():
    # 100 EUR a month = 1200 EUR a year; 1.2 % of that is 14.40 EUR
    response = client.get("/funds/HRRBAGEQ0000/costs?monthly_amount=100", headers=AGENT)
    assert response.json() == {"paid_in_per_year_eur": 1200, "costs_per_year_eur": 14.4}


def test_costs_for_unknown_fund_are_rejected():
    response = client.get("/funds/UNKNOWN/costs?monthly_amount=100", headers=AGENT)
    assert response.json() == {"code": "UNKNOWN_FUND"}


def test_same_offer_has_a_different_hash_per_application():
    assert new_application().json()["offer_hash"] != new_application().json()["offer_hash"]


def test_invalid_application_id_is_rejected():
    assert client.get("/applications/not-an-id", headers=AGENT).status_code == 422
    assert client.post("/confirm/not-an-id/eid").status_code == 422
