"""E2E smoke test against the deployed Azure Container Apps URL."""

from __future__ import annotations

import os

import pytest


@pytest.mark.e2e
def test_deployed_health() -> None:
    base_url = os.environ.get("LAB05_BASE_URL", "")
    if not base_url:
        pytest.skip("LAB05_BASE_URL not set — skipping deployed E2E test")

    import httpx

    response = httpx.get(f"{base_url}/health", timeout=15)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["service"] == "ollama-local-llm-api"
