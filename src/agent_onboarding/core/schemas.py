import os
from typing import Annotated, Literal

from fastapi import Path
from pydantic import BaseModel, Field

from agent_onboarding.core import domain, products

BASE_URL = os.environ.get("BASE_URL", "http://127.0.0.1:8000")

# Application ids are 32 hex characters (uuid4)
ApplicationId = Annotated[str, Path(pattern="^[0-9a-f]{32}$")]

#upper limit because of hash
MAX_MONTHLY_AMOUNT = 100_000


class NewApplication(BaseModel):
    idempotency_key: str = Field(max_length=100)
    fund_isin: str
    monthly_amount: int = Field(gt=0, le=MAX_MONTHLY_AMOUNT)


class NewAmount(BaseModel):
    monthly_amount: int = Field(gt=0, le=MAX_MONTHLY_AMOUNT)
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
        "customer_link": f"{BASE_URL}/confirm/{application.application_id}"
    }
