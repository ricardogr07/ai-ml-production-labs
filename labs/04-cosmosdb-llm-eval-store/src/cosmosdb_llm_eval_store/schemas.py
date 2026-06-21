"""Pydantic document models for the LLM evaluation store."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Literal

from pydantic import BaseModel, Field


class Experiment(BaseModel):
    id: str
    experiment_id: str
    name: str
    description: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    status: Literal["active", "archived"] = "active"


class PromptRun(BaseModel):
    id: str
    experiment_id: str
    prompt: str
    model_name: str
    model_version: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class ModelResponse(BaseModel):
    id: str
    experiment_id: str
    prompt_run_id: str
    response_text: str
    latency_ms: float
    token_count: int
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class EvaluationScore(BaseModel):
    id: str
    experiment_id: str
    response_id: str
    metric_name: str
    score: float = Field(ge=0.0, le=1.0)
    evaluator: Literal["auto", "human"] = "auto"
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
