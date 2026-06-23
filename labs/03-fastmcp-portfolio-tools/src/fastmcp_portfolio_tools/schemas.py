from __future__ import annotations

from typing import Literal

from pydantic import BaseModel


class ProjectScore(BaseModel):
    score: float
    criteria: dict[str, bool]
    recommendation: Literal["strong", "needs work"]
