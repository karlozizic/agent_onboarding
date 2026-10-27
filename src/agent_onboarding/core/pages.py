import os
import uuid
from pathlib import Path

from fastapi import APIRouter, Form, HTTPException, Request
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates

from agent_onboarding.core import domain, products
from agent_onboarding.core.domain import Rejected, State
from agent_onboarding.core.schemas import ApplicationId

DEVICE_KEY = os.environ.get("DEVICE_KEY", "phone-demo-key")

# application_id -> nonce of the last phone page shown; usable once.
NONCES = {}

# In production this comes from the eID provider.
MOCK_EID = {"given_name": "Anna", "family_name": "Schmidt", "birth_date": "1990-05-01"}

router = APIRouter()
templates = Jinja2Templates(directory=Path(__file__).parent / "templates")


def back_to(application_id):
    return RedirectResponse(f"/confirm/{application_id}", status_code=303)


@router.get("/confirm/{application_id}")
def confirm_page(request: Request, application_id: ApplicationId):
    application = domain.get_application(application_id)
    context = {
        "application": application,
        "banks": products.PARTNER_BANKS,
        "unsuitable": not all(application.answers.values()),
    }
    return templates.TemplateResponse(request, "confirm.html", context)


@router.get("/kid/{fund_isin}")
def kid_page(request: Request, fund_isin: str):
    if fund_isin not in products.FUNDS:
        raise HTTPException(status_code=404)
    context = {"isin": fund_isin, "fund": products.FUNDS[fund_isin]}
    return templates.TemplateResponse(request, "kid.html", context)


@router.post("/confirm/{application_id}/eid")
def eid_done(application_id: ApplicationId):
    domain.verify_identity(application_id, MOCK_EID)
    return back_to(application_id)


@router.post("/confirm/{application_id}/answers")
def answers_done(
    application_id: ApplicationId,
    knows_funds: bool = Form(False),
    knows_risk: bool = Form(False),
    knows_costs: bool = Form(False),
    has_experience: bool = Form(False),
    hausbank: str = Form(""),
):
    answers = {
        "knows_funds": knows_funds,
        "knows_risk": knows_risk,
        "knows_costs": knows_costs,
        "has_experience": has_experience,
    }
    domain.answer_questions(application_id, answers, hausbank)
    domain.run_checks(application_id)
    return back_to(application_id)


@router.get("/device")
def device_inbox(request: Request, key: str = ""):
    if key != DEVICE_KEY:
        raise HTTPException(status_code=403)
    waiting = [a for a in domain.APPLICATIONS.values() if a.state == State.CHECKS_CLEARED]
    return templates.TemplateResponse(request, "inbox.html", {"waiting": waiting, "key": key})


@router.get("/device/{application_id}")
def device_page(request: Request, application_id: ApplicationId, key: str = ""):
    if key != DEVICE_KEY:
        raise HTTPException(status_code=403)
    application = domain.get_application(application_id)
    nonce = uuid.uuid4().hex
    NONCES[application_id] = nonce
    context = {
        "application": application,
        "hausbank": products.PARTNER_BANKS.get(application.offer["hausbank"], "Keine (Direktdepot)"),
        "offer_hash": products.offer_hash(application.offer),
        "nonce": nonce,
        "key": key,
    }
    return templates.TemplateResponse(request, "device.html", context)


@router.post("/device/{application_id}/approve")
def device_approve(
    request: Request, application_id: ApplicationId, nonce: str = Form(), offer_hash: str = Form(), key: str = ""
):
    if key != DEVICE_KEY:
        raise HTTPException(status_code=403)
    if NONCES.pop(application_id, None) != nonce:
        raise Rejected("CONFIRMATION_EXPIRED")
    domain.confirm(application_id, offer_hash)
    domain.open_account(application_id)
    return templates.TemplateResponse(request, "device.html", {"opened": True, "key": key})
