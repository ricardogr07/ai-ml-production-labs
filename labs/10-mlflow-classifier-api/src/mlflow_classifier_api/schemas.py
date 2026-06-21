from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class IncidentFeatures(BaseModel):
    service_name: str
    error_count: int = Field(ge=0)
    latency_p95_ms: float = Field(ge=0.0)
    failed_jobs: int = Field(ge=0)
    deployment_recent: bool


class SeverityResponse(BaseModel):
    severity: Literal["low", "medium", "high", "critical"]
    confidence: float = Field(ge=0.0, le=1.0)
    model_version: str
