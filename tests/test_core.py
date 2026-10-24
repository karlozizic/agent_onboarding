from fastapi.testclient import TestClient

from agent_onboarding.core.app import app

client = TestClient(app)


def test_health_requires_token():
    assert client.get("/health").status_code == 401


def test_health_with_token():
    response = client.get("/health", headers={"Authorization": "Bearer dev-token"})
    assert response.json() == {"status": "ok"}