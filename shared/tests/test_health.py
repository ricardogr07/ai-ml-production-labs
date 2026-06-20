from __future__ import annotations

import pytest

from production_labs_shared.health import HealthResponse


@pytest.mark.unit
def test_health_response_defaults() -> None:
    h = HealthResponse(service="test-lab", version="0.1.0")

    assert h.status == "ok"
    assert h.service == "test-lab"
    assert h.version == "0.1.0"
    assert h.timestamp_utc is not None


@pytest.mark.unit
def test_health_response_serializes() -> None:
    h = HealthResponse(service="test-lab", version="0.1.0")
    data = h.model_dump()

    assert data["status"] == "ok"
    assert "timestamp_utc" in data
