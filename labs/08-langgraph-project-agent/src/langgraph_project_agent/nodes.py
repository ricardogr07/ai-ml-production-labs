"""Node implementations for the project agent graph.

Each node dispatches on LLM_PROVIDER: "none" (default) runs the deterministic
heuristics below; "ollama" and "anthropic" route to the LLM-backed versions in
llm.py. Imports of llm.py are lazy so provider=none stays hermetic.
"""

from __future__ import annotations

from langgraph_project_agent.config import settings
from langgraph_project_agent.state import ProjectState

_TYPE_KEYWORDS: dict[str, list[str]] = {
    "cloud_api": ["fastapi", "api", "endpoint", "service", "rest"],
    "ml_model": ["sklearn", "model", "train", "classifier", "regression"],
    "rag_system": ["rag", "retrieval", "embedding", "vector", "chunk"],
    "agent_system": ["agent", "langgraph", "llamaindex", "tool", "graph"],
    "observability": ["otel", "trace", "metric", "log", "monitoring"],
}

_REQUIRED_ARTIFACTS = ["README.md", "tests/", "pyproject.toml", "Dockerfile"]


def classify_project_type(state: ProjectState) -> ProjectState:
    if settings.llm_provider != "none":
        from langgraph_project_agent.llm import llm_classify

        return llm_classify(state)
    text = state.project_idea.lower()
    for ptype, keywords in _TYPE_KEYWORDS.items():
        if any(kw in text for kw in keywords):
            return state.model_copy(update={"project_type": ptype})
    return state.model_copy(update={"project_type": "general"})


def score_against_portfolio_thesis(state: ProjectState) -> ProjectState:
    if settings.llm_provider != "none":
        from langgraph_project_agent.llm import llm_score

        return llm_score(state)
    text = state.project_idea.lower()
    criteria = {
        "has_cloud": any(kw in text for kw in ("azure", "aws", "gcp", "cloud", "deploy")),
        "has_tests": any(kw in text for kw in ("test", "pytest", "coverage")),
        "has_docker": "docker" in text,
        "has_ai_ml": any(kw in text for kw in ("ai", "ml", "llm", "model", "rag", "agent")),
        "is_focused": len(state.project_idea) < 300,
    }
    score = sum(criteria.values()) / len(criteria)
    return state.model_copy(update={"thesis_score": round(score, 2)})


def identify_missing_artifacts(state: ProjectState) -> ProjectState:
    if settings.llm_provider != "none":
        from langgraph_project_agent.llm import llm_missing_artifacts

        return llm_missing_artifacts(state)
    text = state.project_idea.lower()
    missing = [a for a in _REQUIRED_ARTIFACTS if a.lower().replace("/", "") not in text]
    return state.model_copy(update={"missing_artifacts": missing})


def generate_implementation_plan(state: ProjectState) -> ProjectState:
    if settings.llm_provider != "none":
        from langgraph_project_agent.llm import llm_plan

        return llm_plan(state)
    plan = (
        f"1. Scaffold {state.project_type} lab structure\n"
        "2. Implement core service logic\n"
        "3. Add Pydantic schemas\n"
        "4. Write unit and integration tests\n"
        "5. Add Dockerfile\n"
        "6. Add CI workflow\n"
        "7. Write README\n"
    )
    return state.model_copy(update={"implementation_plan": plan})


def return_scorecard(state: ProjectState) -> ProjectState:
    scorecard = {
        "project_type": state.project_type,
        "thesis_score": state.thesis_score,
        "missing_artifacts": state.missing_artifacts,
        "implementation_plan": state.implementation_plan,
        "recommendation": "build it" if state.thesis_score >= 0.6 else "refine the idea",
    }
    return state.model_copy(update={"scorecard": scorecard})
