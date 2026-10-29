from helpers import AGENT, ALL_YES, PHONE_KEY, client, new_application, waiting_for_phone

from agent_onboarding.core import pages, products
from agent_onboarding.core.domain import State


def open_phone(application):
    client.get(f"/device/{application.application_id}?key={PHONE_KEY}")
    return {"nonce": pages.NONCES[application.application_id], "offer_hash": products.offer_hash(application.offer)}


def approve(application, form, key=PHONE_KEY):
    return client.post(f"/device/{application.application_id}/approve?key={key}", data=form)


def test_s1_customer_and_phone_open_the_account():
    application = waiting_for_phone()
    assert approve(application, open_phone(application)).status_code == 200
    status = client.get(f"/applications/{application.application_id}", headers=AGENT).json()
    assert status["state"] == "ACCOUNT_OPENED"
    assert status["next_step"] == "DONE"


def test_s8_confirm_without_the_phone_is_blocked():
    application = waiting_for_phone()
    assert approve(application, open_phone(application), key="").status_code == 403
    assert application.state == State.CHECKS_CLEARED


def test_s5_phone_cannot_confirm_an_old_offer():
    application = waiting_for_phone()
    form = open_phone(application)
    body = {"monthly_amount": 500, "expected_version": application.version}
    client.post(f"/applications/{application.application_id}/amount", json=body, headers=AGENT)
    assert approve(application, form).json() == {"code": "OFFER_CHANGED"}


def test_nonce_works_only_once():
    application = waiting_for_phone()
    form = open_phone(application)
    assert approve(application, form).status_code == 200
    assert approve(application, form).json() == {"code": "CONFIRMATION_EXPIRED"}


def test_phone_lists_applications_waiting_for_it():
    application = waiting_for_phone()
    assert client.get("/device").status_code == 403
    assert application.application_id in client.get(f"/device?key={PHONE_KEY}").text


def test_phone_shows_the_declared_hausbank():
    application = waiting_for_phone(ALL_YES | {"hausbank": "SPK-KOELNBONN"})
    assert "Sparkasse KölnBonn" in client.get(f"/device/{application.application_id}?key={PHONE_KEY}").text


def test_missing_knowledge_shows_a_warning():
    application = waiting_for_phone({"knows_funds": "on"})
    assert "may not be appropriate" in client.get(f"/confirm/{application.application_id}").text


def test_agent_gets_a_link_for_the_customer():
    application = new_application().json()
    assert application["customer_link"].endswith(f"/confirm/{application['application_id']}")


def test_agent_gets_a_kid_link_for_each_fund():
    funds = client.get("/funds", headers=AGENT).json()
    assert funds["DE000DEMO023"]["kid_url"].endswith("/kid/DE000DEMO023")


def test_customer_can_read_the_kid():
    assert "4 of 7" in client.get("/kid/DE000DEMO015").text
    assert client.get("/kid/UNKNOWN").status_code == 404
