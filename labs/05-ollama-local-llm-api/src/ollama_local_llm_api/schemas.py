from __future__ import annotations

from pydantic import BaseModel, Field


class SummarizeRequest(BaseModel):
    text: str = Field(min_length=1, max_length=50_000)
    model: str = Field(default="phi3.5")
    max_tokens: int = Field(default=256, ge=1, le=2048)


class SummarizeResponse(BaseModel):
    summary: str
    model: str
    latency_ms: float
