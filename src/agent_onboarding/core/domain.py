import uuid
from dataclasses import dataclass, field
from enum import StrEnum

from agent_onboarding.core import checks
from agent_onboarding.core.products import FUNDS, PARTNER_BANKS, build_offer, offer_hash


class State(StrEnum):
    PREPARED = "PREPARED"
    IDENTITY_VERIFIED = "IDENTITY_VERIFIED"
    CHECKS_CLEARED = "CHECKS_CLEARED"
    CUSTOMER_CONFIRMED = "CUSTOMER_CONFIRMED"
    ACCOUNT_OPENED = "ACCOUNT_OPENED"
    REVIEW_REQUIRED = "REVIEW_REQUIRED"


class Rejected(Exception):
    def __init__(self, code):
        super().__init__(code)
        self.code = code


@dataclass
class AccountApplication:
    application_id: str
    sub: str  # user id from OAuth; we identify the customer after eID
    client_id: str  # which agent app sends the requests (e.g. Claude Desktop)
    offer: dict
    state: State = State.PREPARED
    version: int = 1
    identity: dict = field(default_factory=dict)
    answers: dict = field(default_factory=dict)
    hausbank: str = ""
    confirmed_hash: str = ""


APPLICATIONS = {}
APPLICATION_BY_KEY = {}


def get_application(application_id):
    if application_id not in APPLICATIONS:
        raise Rejected("UNKNOWN_APPLICATION")
    return APPLICATIONS[application_id]


def require_state(application, state):
    if application.state != state:
        raise Rejected("WRONG_STATE")


def create_application(sub, client_id, idempotency_key, fund_isin, monthly_amount):
    key = (sub, client_id, idempotency_key)
    request = (fund_isin, monthly_amount)
    if key in APPLICATION_BY_KEY:
        application_id, first_request = APPLICATION_BY_KEY[key]
        if request != first_request:
            raise Rejected("IDEMPOTENCY_KEY_REUSED")
        return APPLICATIONS[application_id]

    if fund_isin not in FUNDS:
        raise Rejected("UNKNOWN_FUND")

    application = AccountApplication(
        application_id=uuid.uuid4().hex,
        sub=sub,
        client_id=client_id,
        offer=build_offer(fund_isin, monthly_amount, 1),
    )
    APPLICATIONS[application.application_id] = application
    APPLICATION_BY_KEY[key] = (application.application_id, request)
    return application


def verify_identity(application_id, eid_data):
    application = get_application(application_id)
    require_state(application, State.PREPARED)
    application.identity = eid_data
    application.state = State.IDENTITY_VERIFIED
    application.version += 1


def answer_questions(application_id, answers, hausbank):
    if hausbank and hausbank not in PARTNER_BANKS:
        raise Rejected("UNKNOWN_BANK")
    application = get_application(application_id)
    require_state(application, State.IDENTITY_VERIFIED)
    application.answers = answers
    application.hausbank = hausbank
    application.version += 1


def run_checks(application_id):
    application = get_application(application_id)
    require_state(application, State.IDENTITY_VERIFIED)
    if not application.answers:
        raise Rejected("CUSTOMER_INPUT_REQUIRED")
    if checks.aml_screening(application.identity):
        application.state = State.CHECKS_CLEARED
    else:
        application.state = State.REVIEW_REQUIRED
    application.version += 1


def change_offer(application_id, monthly_amount, expected_version):
    application = get_application(application_id)
    if expected_version != application.version:
        raise Rejected("VERSION_CONFLICT")
    if application.state in (State.ACCOUNT_OPENED, State.REVIEW_REQUIRED):
        raise Rejected("WRONG_STATE")
    old_offer = application.offer
    application.offer = build_offer(old_offer["fund_isin"], monthly_amount, old_offer["offer_version"] + 1)
    if application.state == State.CUSTOMER_CONFIRMED:
        application.state = State.CHECKS_CLEARED
        application.confirmed_hash = ""
    application.version += 1


def confirm(application_id, confirmed_hash):
    application = get_application(application_id)
    require_state(application, State.CHECKS_CLEARED)
    if confirmed_hash != offer_hash(application.offer):
        raise Rejected("OFFER_CHANGED")
    application.confirmed_hash = confirmed_hash
    application.state = State.CUSTOMER_CONFIRMED
    application.version += 1


def open_account(application_id):
    application = get_application(application_id)
    require_state(application, State.CUSTOMER_CONFIRMED)
    if application.confirmed_hash != offer_hash(application.offer):
        raise Rejected("CONSENT_REQUIRED")
    application.state = State.ACCOUNT_OPENED
    application.version += 1
