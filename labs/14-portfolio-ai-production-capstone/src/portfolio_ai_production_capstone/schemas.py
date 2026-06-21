from __future__ import annotations

from pydantic import BaseModel, Field


class AnalyzeRequest(BaseModel):
    project_idea: str = Field(min_length=1, max_length=5000)


class AnalyzeResponse(BaseModel):
    project_type: str
    thesis_score: float
    missing_artifacts: list[str]
    implementation_plan: str
    recommendation: str
    request_id: str = ""
