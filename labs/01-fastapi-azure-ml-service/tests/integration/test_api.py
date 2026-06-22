from __future__ import annotations

import pytest
from fastapi.testclient import TestClient
from fastapi_azure_ml_service.app import app


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


@pytest.mark.integration
def test_health_endpoint(client: TestClient) -> None:
    response = client.get("/health")

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "service" in data
    assert "version" in data
    assert "timestamp_utc" in data


@pytest.mark.integration
def test_predict_incident(client: TestClient) -> None:
    response = client.post("/predict", json={"text": "The job failed."})

    assert response.status_code == 200
    data = response.json()
    assert data["label"] == "incident"
    assert 0.0 <= data["confidence"] <= 1.0
    assert data["model_version"]


@pytest.mark.integration
def test_predict_general(client: TestClient) -> None:
    response = client.post("/predict", json={"text": "Routine status update."})

    assert response.status_code == 200
    assert response.json()["label"] == "general"


@pytest.mark.integration
def test_predict_rejects_empty_text(client: TestClient) -> None:
    response = client.post("/predict", json={"text": ""})

    assert response.status_code == 422


@pytest.mark.integration
def test_predict_rejects_missing_text(client: TestClient) -> None:
    response = client.post("/predict", json={})

    assert response.status_code == 422


@pytest.mark.integration
def test_predict_enforces_rate_limit(client: TestClient) -> None:
    from fastapi_azure_ml_service.app import limiter

    limiter._storage.reset()
    for _ in range(10):
        r = client.post("/predict", json={"text": "rate limit probe"})
        assert r.status_code == 200

    r = client.post("/predict", json={"text": "rate limit probe"})
    assert r.status_code == 429
