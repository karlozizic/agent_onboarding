import uuid

import pytest

from agent_onboarding.core import domain, products
from agent_onboarding.core.domain import Rejected, State

ANNA = {"given_name": "Anna", "family_name": "Schmidt", "birth_date": "1990-05-01"}
BLOCKED = {"given_name": "Max", "family_name": "Blocked", "birth_date": "1980-01-01"}
ANSWERS = {"knows_funds": True, "knows_risk": True, "knows_costs": True, "has_experience": True}
FUND = "HRRBAGEQ0000"


def new_application(key=""):
    return domain.create_application("sub-anna", "claude", key or uuid.uuid4().hex, FUND, 100)


def identified(person=ANNA):
    application = new_application()
    domain.verify_identity(application.application_id, person)
    return application


def ready_to_confirm():
    application = identified()
    domain.answer_questions(application.application_id, ANSWERS, "")
    domain.run_checks(application.application_id)
    return application


def confirm(application, offer_hash=""):
    domain.confirm(application.application_id, offer_hash or products.offer_hash(application.offer))


def test_s1_account_opens_after_phone_confirmation():
    application = ready_to_confirm()
    confirm(application)
    domain.open_account(application.application_id)
    assert application.state == State.ACCOUNT_OPENED


def test_same_key_returns_same_application():
    assert new_application("key-1") is new_application("key-1")


def test_same_key_with_other_data_is_rejected():
    new_application("key-2")
    with pytest.raises(Rejected, match="IDEMPOTENCY_KEY_REUSED"):
        domain.create_application("sub-anna", "claude", "key-2", FUND, 500)


def test_s5_offer_change_cancels_confirmation():
    application = ready_to_confirm()
    confirm(application)
    domain.change_offer(application.application_id, 200, application.version)
    assert application.state == State.CHECKS_CLEARED


def test_s5_old_offer_cannot_be_confirmed():
    application = ready_to_confirm()
    old_hash = products.offer_hash(application.offer)
    domain.change_offer(application.application_id, 200, application.version)
    with pytest.raises(Rejected, match="OFFER_CHANGED"):
        confirm(application, offer_hash=old_hash)


def test_no_account_without_checks():
    application = identified()
    with pytest.raises(Rejected, match="WRONG_STATE"):
        domain.open_account(application.application_id)


def test_offer_cannot_change_after_account_opened():
    application = ready_to_confirm()
    confirm(application)
    domain.open_account(application.application_id)
    with pytest.raises(Rejected, match="WRONG_STATE"):
        domain.change_offer(application.application_id, 999, application.version)


def test_answers_cannot_change_after_checks():
    application = ready_to_confirm()
    with pytest.raises(Rejected, match="WRONG_STATE"):
        domain.answer_questions(application.application_id, ANSWERS, "")


def test_aml_hit_goes_to_review():
    application = identified(BLOCKED)
    domain.answer_questions(application.application_id, ANSWERS, "")
    domain.run_checks(application.application_id)
    assert application.state == State.REVIEW_REQUIRED


def test_customer_declares_a_partner_bank():
    application = identified()
    domain.answer_questions(application.application_id, ANSWERS, "SPK-KOELNBONN")
    assert application.hausbank == "SPK-KOELNBONN"


def test_unknown_bank_is_rejected():
    application = identified()
    with pytest.raises(Rejected, match="UNKNOWN_BANK"):
        domain.answer_questions(application.application_id, ANSWERS, "OTHER-BANK")


def test_stale_version_is_rejected():
    application = new_application()
    with pytest.raises(Rejected, match="VERSION_CONFLICT"):
        domain.change_offer(application.application_id, 200, application.version - 1)
