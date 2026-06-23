"""E2E smoke test against the deployed Azure Functions URL."""

from __future__ import annotations

import os

import pytest


@pytest.mark.e2e
def test_deployed_classify_incident() -> None:
    base_url = os.environ.get("LAB02_BASE_URL", "")
    if not base_url:
        pytest.skip("LAB02_BASE_URL not set — skipping deployed E2E test")

    import httpx

    r = httpx.post(
        f"{base_url.rstrip('/')}/api/classify",
        json={"text": "Service crashed in production."},
        timeout=30,
    )
    assert r.status_code == 200
    body = r.json()
    assert body["label"] == "incident"
    assert 0.0 <= body["confidence"] <= 1.0
    assert body["model_version"]
