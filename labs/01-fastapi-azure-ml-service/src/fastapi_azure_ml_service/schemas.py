from __future__ import annotations

from pydantic import BaseModel, Field


class PredictRequest(BaseModel):
    text: str = Field(min_length=1, max_length=10_000)


class PredictResponse(BaseModel):
    label: str
    confidence: float = Field(ge=0.0, le=1.0)
    model_version: str
