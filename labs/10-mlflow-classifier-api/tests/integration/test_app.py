"""Integration tests: the FastAPI app over the real service against tmp mlruns.

The predict path is not mocked; requests go through model resolution, the
runs:/ artifact load, and predict_proba exactly as in production.
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient
from mlflow_classifier_api.app import app

_VALID_BODY = {
    "service_name": "auth-service",
    "error_count": 90,
    "latency_p95_ms": 4200.0,
    "failed_jobs": 17,
    "deployment_recent": True,
}


@pytest.fixture()
def client() -> TestClient:
    return TestClient(app)


@pytest.mark.integration
def test_health(client: TestClient) -> None:
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["service"] == "mlflow-classifier-api"
    assert "version" in data
    assert "timestamp_utc" in data


@pytest.mark.integration
@pytest.mark.usefixtures("unready_settings")
def test_ready_returns_503_when_no_model_trained(client: TestClient) -> None:
    response = client.get("/ready")
    assert response.status_code == 503
    data = response.json()
    assert data["ready"] is False
    assert "run scripts/train.py" in data["checks"]["model"]


@pytest.mark.integration
@pytest.mark.usefixtures("ready_settings")
def test_ready_returns_200_when_model_loads(client: TestClient) -> None:
    response = client.get("/ready")
    assert response.status_code == 200
    assert response.json() == {"ready": True, "checks": {"model": "ok"}}


@pytest.mark.integration
def test_predict_happy_path(client: TestClient, ready_settings: str) -> None:
    response = client.post("/predict", json=_VALID_BODY)
    assert response.status_code == 200
    data = response.json()
    assert data["severity"] in {"low", "medium", "high", "critical"}
    assert 0.0 <= data["confidence"] <= 1.0
    assert data["model_version"] == ready_settings


@pytest.mark.integration
@pytest.mark.usefixtures("unready_settings")
def test_predict_returns_503_when_no_model_trained(client: TestClient) -> None:
    response = client.post("/predict", json=_VALID_BODY)
    assert response.status_code == 503
    assert "run scripts/train.py" in response.json()["detail"]


@pytest.mark.integration
def test_predict_rejects_negative_error_count(client: TestClient) -> None:
    response = client.post("/predict", json={**_VALID_BODY, "error_count": -1})
    assert response.status_code == 422


@pytest.mark.integration
def test_predict_rejects_missing_fields(client: TestClient) -> None:
    response = client.post("/predict", json={"service_name": "auth-service"})
    assert response.status_code == 422
