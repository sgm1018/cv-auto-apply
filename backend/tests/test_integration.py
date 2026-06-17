"""Integration test: full register -> login -> profile -> settings -> mapping flow."""
import json
import pytest
import respx
from httpx import Response
from fastapi.testclient import TestClient

from cvapplier.main import create_app


@pytest.fixture
def app_client(mongo_db) -> TestClient:  # type: ignore[no-untyped-def]
    app = create_app()
    return TestClient(app)


def test_health(app_client: TestClient) -> None:
    r = app_client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_metrics(app_client: TestClient) -> None:
    r = app_client.get("/metrics")
    assert r.status_code == 200
    assert "python_info" in r.text or "process" in r.text


def test_register_and_get_me(app_client: TestClient) -> None:
    r = app_client.post("/api/v1/auth/register", json={
        "email": "a@b.com", "password": "super-secret-password-123",
        "language": "en", "consent_terms": True,
    })
    assert r.status_code == 200, r.text
    token = r.json()["access_token"]
    r = app_client.get("/api/v1/auth/me",
                        headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 200
    assert r.json()["email"] == "a@b.com"
    assert r.json()["llm_provider"] == "deepseek"
    assert r.json()["llm_model"] == "deepseek-v4-flash"


def test_register_then_profile_patch(app_client: TestClient) -> None:
    r = app_client.post("/api/v1/auth/register", json={
        "email": "a@b.com", "password": "super-secret-password-123",
        "language": "en", "consent_terms": True,
    })
    token = r.json()["access_token"]
    r = app_client.patch("/api/v1/profile",
                          json={"first_name": "Jane", "skills": ["Python", "FastAPI"]},
                          headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 200, r.text
    assert r.json()["first_name"] == "Jane"
    r = app_client.get("/api/v1/profile",
                        headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 200
    assert r.json()["first_name"] == "Jane"
    assert r.json()["skills"] == ["Python", "FastAPI"]


def test_settings_encrypts_api_key(app_client: TestClient) -> None:
    r = app_client.post("/api/v1/auth/register", json={
        "email": "a@b.com", "password": "super-secret-password-123",
        "language": "en", "consent_terms": True,
    })
    token = r.json()["access_token"]
    r = app_client.patch("/api/v1/settings",
                          json={"llm_api_key": "sk-secret-test-key"},
                          headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 200
    assert r.json()["llm_api_key_set"] is True
    assert "sk-secret" not in r.text


def test_learned_lookup(app_client: TestClient) -> None:
    r = app_client.post("/api/v1/auth/register", json={
        "email": "a@b.com", "password": "super-secret-password-123",
        "language": "en", "consent_terms": True,
    })
    token = r.json()["access_token"]
    r = app_client.get(
        "/api/v1/mappings/learned?signatures=phone&language=en",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r.status_code == 200
    # Catalog is not seeded in tests; this asserts the endpoint works
    body = r.json()
    assert "mappings" in body


def test_register_validates_password(app_client: TestClient) -> None:
    r = app_client.post("/api/v1/auth/register", json={
        "email": "a@b.com", "password": "short",
        "language": "en", "consent_terms": True,
    })
    # Pydantic validates password length (min_length=12) at the request layer
    assert r.status_code == 422
