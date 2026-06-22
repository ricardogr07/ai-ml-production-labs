from __future__ import annotations

from pydantic import BaseModel, Field


class ClassifyRequest(BaseModel):
    text: str = Field(min_length=1, max_length=10_000)


class ClassifyResponse(BaseModel):
    label: str
    confidence: float = Field(ge=0.0, le=1.0)
    model_version: str
