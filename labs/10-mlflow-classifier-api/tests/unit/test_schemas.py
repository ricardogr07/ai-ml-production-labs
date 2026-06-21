from __future__ import annotations

import pytest
from mlflow_classifier_api.schemas import IncidentFeatures, SeverityResponse
from pydantic import ValidationError


@pytest.mark.unit
def test_incident_features_valid() -> None:
    f = IncidentFeatures(
        service_name="auth-service",
        error_count=10,
        latency_p95_ms=500.0,
        failed_jobs=2,
        deployment_recent=True,
    )
    assert f.service_name == "auth-service"


@pytest.mark.unit
def test_incident_features_rejects_negative_error_count() -> None:
    with pytest.raises(ValidationError):
        IncidentFeatures(
            service_name="svc",
            error_count=-1,
            latency_p95_ms=100.0,
            failed_jobs=0,
            deployment_recent=False,
        )


@pytest.mark.unit
def test_severity_response_valid() -> None:
    r = SeverityResponse(severity="high", confidence=0.9, model_version="rf-v1.0.0")
    assert r.severity == "high"
