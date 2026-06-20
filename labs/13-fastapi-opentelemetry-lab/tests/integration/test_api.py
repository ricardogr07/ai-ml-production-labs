from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from fastapi_opentelemetry_lab.app import app


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


@pytest.mark.integration
def test_health_endpoint(client: TestClient) -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


@pytest.mark.integration
def test_work_endpoint(client: TestClient) -> None:
    response = client.get("/work")
    assert response.status_code == 200
    assert response.json()["result"] == "done"


@pytest.mark.integration
def test_request_id_header_present(client: TestClient) -> None:
    response = client.get("/health")
    assert "X-Request-ID" in response.headers
