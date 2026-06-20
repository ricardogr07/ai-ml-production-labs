from __future__ import annotations

import pytest
from pydantic import ValidationError

from portfolio_ai_production_capstone.schemas import AnalyzeRequest, AnalyzeResponse


@pytest.mark.unit
def test_analyze_request_valid() -> None:
    req = AnalyzeRequest(project_idea="A FastAPI ML service with tests and Docker.")
    assert len(req.project_idea) > 0


@pytest.mark.unit
def test_analyze_request_rejects_empty() -> None:
    with pytest.raises(ValidationError):
        AnalyzeRequest(project_idea="")


@pytest.mark.unit
def test_analyze_response_serializes() -> None:
    resp = AnalyzeResponse(
        project_type="cloud_api",
        thesis_score=0.8,
        missing_artifacts=[],
        implementation_plan="1. scaffold",
        recommendation="build it",
    )
    data = resp.model_dump()
    assert data["thesis_score"] == 0.8
