"""CLI entry point and smoke test for the project agent graph.

Usage:
  uv run python -m langgraph_project_agent "A FastAPI RAG service on Azure"

Runs end to end with LLM_PROVIDER=none (default) and no external services.
Set LLM_PROVIDER=ollama or LLM_PROVIDER=anthropic to use real LLM nodes.
"""

from __future__ import annotations

import json
import sys

import structlog

from langgraph_project_agent.config import settings
from langgraph_project_agent.graph import compiled_graph
from langgraph_project_agent.state import ProjectState
from production_labs_shared.logging import configure_logging
from production_labs_shared.telemetry import timed_operation

_SCORECARD_KEYS = {
    "project_type",
    "thesis_score",
    "missing_artifacts",
    "implementation_plan",
    "recommendation",
}


def main(argv: list[str]) -> int:
    configure_logging(settings.log_level)
    log = structlog.get_logger("langgraph_project_agent")

    idea = argv[0] if argv else "A FastAPI RAG service on Azure with pytest and Docker"
    log.info("run_started", provider=settings.llm_provider, project_idea=idea)

    with timed_operation("project_agent_run", provider=settings.llm_provider):
        result = compiled_graph.invoke(ProjectState(project_idea=idea))

    scorecard = result["scorecard"]
    missing_keys = _SCORECARD_KEYS - scorecard.keys()
    if missing_keys:
        log.error("scorecard_incomplete", missing_keys=sorted(missing_keys))
        return 1

    print(json.dumps(scorecard, indent=2))
    log.info("run_completed", recommendation=scorecard["recommendation"])
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
