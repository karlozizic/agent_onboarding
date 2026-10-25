from typing import Literal

from pydantic import BaseModel, Field

from agent_onboarding.core import domain, products


class NewApplication(BaseModel):
    idempotency_key: str
    fund_isin: str
    monthly_amount: int = Field(gt=0)


class NewAmount(BaseModel):
    monthly_amount: int = Field(gt=0)
    expected_version: int


class HumanRequest(BaseModel):
    reason: Literal["advice", "person"]


def application_view(application):
    return {
        "application_id": application.application_id,
        "state": application.state,
        "next_step": domain.NEXT_STEP[application.state],
        "version": application.version,
        "offer": application.offer,
        "offer_hash": products.offer_hash(application.offer),
    }
