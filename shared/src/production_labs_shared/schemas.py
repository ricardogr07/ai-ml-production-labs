from __future__ import annotations

from pydantic import BaseModel, Field


class ErrorResponse(BaseModel):
    """Standard error envelope returned by all lab APIs."""

    detail: str
    request_id: str = Field(default="")
