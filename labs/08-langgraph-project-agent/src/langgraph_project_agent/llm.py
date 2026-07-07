"""LLM-backed node implementations sharing one structured-output code path."""

from __future__ import annotations

from functools import lru_cache
from typing import Literal

from langchain_core.language_models import LanguageModelInput
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.runnables import Runnable
from pydantic import BaseModel, Field

from langgraph_project_agent.config import settings
from langgraph_project_agent.state import ProjectState
from production_labs_shared.telemetry import timed_operation

_TYPE_LABELS = (
    "cloud_api",
    "ml_model",
    "rag_system",
    "agent_system",
    "observability",
    "general",
)

_REQUIRED_ARTIFACTS = ["README.md", "tests/", "pyproject.toml", "Dockerfile"]


@lru_cache(maxsize=1)
def get_chat_model() -> BaseChatModel:
    if settings.llm_provider == "ollama":
        from langchain_ollama import ChatOllama

        return ChatOllama(base_url=settings.ollama_base_url, model=settings.ollama_model)
    if settings.llm_provider == "anthropic":
        from langchain_anthropic import ChatAnthropic

        if settings.anthropic_api_key and settings.anthropic_api_key.get_secret_value():
            return ChatAnthropic(
                model_name=settings.anthropic_model,
                api_key=settings.anthropic_api_key,
                timeout=None,
                stop=None,
            )
        # falls back to ANTHROPIC_API_KEY from the process environment
        return ChatAnthropic(model_name=settings.anthropic_model, timeout=None, stop=None)
    raise ValueError(f"no chat model for provider {settings.llm_provider!r}")


def _structured(schema: type[BaseModel]) -> Runnable[LanguageModelInput, dict | BaseModel]:
    model = get_chat_model()
    if settings.llm_provider == "ollama":
        # ponytail: json_schema uses Ollama's constrained decoding, so small
        # models without tool-calling support (phi3.5 etc) still emit valid JSON
        return model.with_structured_output(schema, method="json_schema")
    return model.with_structured_output(schema)


class ClassifyResult(BaseModel):
    project_type: Literal[
        "cloud_api", "ml_model", "rag_system", "agent_system", "observability", "general"
    ]


class ThesisScoreResult(BaseModel):
    thesis_score: float = Field(ge=0.0, le=1.0)


class MissingArtifactsResult(BaseModel):
    missing_artifacts: list[str]


class PlanResult(BaseModel):
    implementation_plan: str


_CLASSIFY_PROMPT = (
    "Classify this software project idea into exactly one category from: "
    f"{', '.join(_TYPE_LABELS)}.\n\nProject idea: {{idea}}"
)

_SCORE_PROMPT = (
    "Score this project idea from 0.0 to 1.0 against a production AI/ML portfolio "
    "thesis. Award roughly 0.2 for each criterion met: mentions cloud deployment, "
    "mentions testing, mentions Docker, involves AI/ML, and is focused (a single "
    "clear capability rather than a sprawling platform).\n\nProject idea: {idea}"
)

_ARTIFACTS_PROMPT = (
    "A production-ready lab requires these artifacts: "
    f"{', '.join(_REQUIRED_ARTIFACTS)}. "
    "List which of them the project idea does NOT explicitly mention. Return only "
    "names from that list, verbatim.\n\nProject idea: {idea}"
)

_PLAN_PROMPT = (
    "Write a short numbered implementation plan (5 to 8 steps, one line each) for "
    "building this {project_type} project as a production lab: scaffold, core logic, "
    "schemas, tests, Dockerfile, CI, README.\n\nProject idea: {idea}"
)


def llm_classify(state: ProjectState) -> ProjectState:
    with timed_operation("llm_classify", provider=settings.llm_provider):
        result = _structured(ClassifyResult).invoke(
            _CLASSIFY_PROMPT.format(idea=state.project_idea)
        )
    assert isinstance(result, ClassifyResult)
    return state.model_copy(update={"project_type": result.project_type})


def llm_score(state: ProjectState) -> ProjectState:
    with timed_operation("llm_score", provider=settings.llm_provider):
        result = _structured(ThesisScoreResult).invoke(
            _SCORE_PROMPT.format(idea=state.project_idea)
        )
    assert isinstance(result, ThesisScoreResult)
    return state.model_copy(update={"thesis_score": round(result.thesis_score, 2)})


def llm_missing_artifacts(state: ProjectState) -> ProjectState:
    with timed_operation("llm_missing_artifacts", provider=settings.llm_provider):
        result = _structured(MissingArtifactsResult).invoke(
            _ARTIFACTS_PROMPT.format(idea=state.project_idea)
        )
    assert isinstance(result, MissingArtifactsResult)
    missing = [a for a in result.missing_artifacts if a in _REQUIRED_ARTIFACTS]
    return state.model_copy(update={"missing_artifacts": missing})


def llm_plan(state: ProjectState) -> ProjectState:
    with timed_operation("llm_plan", provider=settings.llm_provider):
        result = _structured(PlanResult).invoke(
            _PLAN_PROMPT.format(project_type=state.project_type, idea=state.project_idea)
        )
    assert isinstance(result, PlanResult)
    return state.model_copy(update={"implementation_plan": result.implementation_plan})
