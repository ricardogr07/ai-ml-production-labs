from __future__ import annotations

from datetime import UTC, datetime
from typing import Literal

from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    status: Literal["ok"] = "ok"
    service: str
    version: str
    timestamp_utc: datetime = Field(default_factory=lambda: datetime.now(UTC))
