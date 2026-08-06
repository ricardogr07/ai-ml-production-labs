#!/usr/bin/env python3
"""Smoke test against a running instance of the MLflow Classifier API.

Assumes the tracking store already holds a finished run (the compose `train`
service, or the model baked into the image).
"""

from __future__ import annotations

import argparse
import os
import sys

import httpx

DEFAULT_BASE_URL = "http://localhost:8000"
LABELS = {"low", "medium", "high", "critical"}

# Same body as tests/integration/test_app.py, so the script and the suite
# cannot drift into asserting on different inputs.
_VALID_BODY = {
    "service_name": "auth-service",
    "error_count": 90,
    "latency_p95_ms": 4200.0,
    "failed_jobs": 17,
    "deployment_recent": True,
}


def main() -> int:
    parser = argparse.ArgumentParser(description="Smoke test the MLflow Classifier API.")
    parser.add_argument(
        "base_url",
        nargs="?",
        default=os.environ.get("BASE_URL", DEFAULT_BASE_URL),
        help="Base URL of the service (default: $BASE_URL or http://localhost:8000)",
    )
    args = parser.parse_args()
    base_url = args.base_url.rstrip("/")
    health_only = os.environ.get("HEALTH_ONLY", "").lower() in ("1", "true", "yes")

    print(f"Target: {base_url}")
    print(f"Mode: {'health-only' if health_only else 'full'}\n")
    client = httpx.Client(base_url=base_url, timeout=15)

    print("GET /health ...", end=" ")
    r = client.get("/health")
    assert r.status_code == 200, f"Expected 200, got {r.status_code}: {r.text}"
    assert r.json()["status"] == "ok"
    assert r.json()["service"] == "mlflow-classifier-api"
    print("OK")

    if health_only:
        print("\nHealth-only mode: skipping /ready and /predict (no trained model).")
        print("\nAll smoke tests passed.")
        return 0

    print("GET /ready ...", end=" ")
    r = client.get("/ready")
    assert r.status_code == 200, f"Expected 200, got {r.status_code}: {r.text}"
    assert r.json()["ready"] is True, f"Service not ready: {r.text}"
    print("OK")

    print("POST /predict ...", end=" ")
    r = client.post("/predict", json=_VALID_BODY)
    assert r.status_code == 200, f"Expected 200, got {r.status_code}: {r.text}"
    data = r.json()
    assert data["severity"] in LABELS, f"Unexpected severity {data['severity']!r}"
    assert 0.0 < data["confidence"] <= 1.0, f"Confidence out of range: {data['confidence']}"
    assert data["model_version"], "model_version must be non-empty"
    print(f"OK ({data['severity']}, {data['confidence']:.3f}, v{data['model_version']})")

    print("POST /predict (negative error_count, expect 422) ...", end=" ")
    r = client.post("/predict", json={**_VALID_BODY, "error_count": -1})
    assert r.status_code == 422, f"Expected 422, got {r.status_code}"
    print("OK")

    print("\nAll smoke tests passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
