"""LangGraph state definition for the project agent."""

from __future__ import annotations

from pydantic import BaseModel


class ProjectState(BaseModel):
    """Typed state flowing through the project analysis graph."""

    project_idea: str = ""
    project_type: str = ""
    thesis_score: float = 0.0
    missing_artifacts: list[str] = []
    implementation_plan: str = ""
    scorecard: dict[str, object] = {}
