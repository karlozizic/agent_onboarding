from fastapi.testclient import TestClient

from agent_onboarding.core import products
from agent_onboarding.core.app import app

client = TestClient(app)
AGENT = {"Authorization": "Bearer dev-token"}


def test_agent_can_tell_what_the_customer_needs():
    assert client.get("/requirements", headers=AGENT).json()["requirements"] == products.REQUIREMENTS


def test_costs_per_year():
    # 100 EUR a month = 1200 EUR a year; 1.2 % of that is 14.40 EUR
    response = client.get("/funds/HRRBAGEQ0000/costs?monthly_amount=100", headers=AGENT)
    assert response.json() == {"paid_in_per_year_eur": 1200, "costs_per_year_eur": 14.4}


def test_costs_for_unknown_fund():
    response = client.get("/funds/UNKNOWN/costs?monthly_amount=100", headers=AGENT)
    assert response.json() == {"code": "UNKNOWN_FUND"}
