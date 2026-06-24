from __future__ import annotations

import pytest
from cosmosdb_llm_eval_store.repository import InMemoryEvalStoreRepository
from cosmosdb_llm_eval_store.schemas import (
    EvaluationScore,
    Experiment,
    ModelResponse,
    PromptRun,
)
from pydantic import ValidationError


@pytest.fixture
def repo() -> InMemoryEvalStoreRepository:
    return InMemoryEvalStoreRepository()


@pytest.mark.unit
def test_save_and_retrieve_experiment(repo: InMemoryEvalStoreRepository) -> None:
    exp = Experiment(
        id="e1", experiment_id="exp-001", name="Test", description="A test experiment."
    )
    repo.save_experiment(exp)

    retrieved = repo.get_experiment("exp-001")
    assert retrieved is not None
    assert retrieved.name == "Test"


@pytest.mark.unit
def test_list_scores_by_experiment(repo: InMemoryEvalStoreRepository) -> None:
    score = EvaluationScore(
        id="s1",
        experiment_id="exp-001",
        response_id="r1",
        metric_name="faithfulness",
        score=0.9,
    )
    repo.save_score(score)

    scores = repo.list_scores("exp-001")
    assert len(scores) == 1
    assert scores[0].metric_name == "faithfulness"


@pytest.mark.unit
def test_list_scores_filters_by_experiment(repo: InMemoryEvalStoreRepository) -> None:
    repo.save_score(
        EvaluationScore(
            id="s1", experiment_id="exp-001", response_id="r1", metric_name="m", score=0.8
        )
    )
    repo.save_score(
        EvaluationScore(
            id="s2", experiment_id="exp-002", response_id="r2", metric_name="m", score=0.7
        )
    )

    assert len(repo.list_scores("exp-001")) == 1
    assert len(repo.list_scores("exp-002")) == 1


@pytest.mark.unit
def test_get_experiment_missing(repo: InMemoryEvalStoreRepository) -> None:
    assert repo.get_experiment("does-not-exist") is None


@pytest.mark.unit
def test_save_and_list_prompt_runs(repo: InMemoryEvalStoreRepository) -> None:
    run = PromptRun(
        id="r1",
        experiment_id="exp-001",
        prompt="What is 2+2?",
        model_name="gpt-4",
        model_version="1.0",
    )
    repo.save_prompt_run(run)

    runs = repo.list_prompt_runs("exp-001")
    assert len(runs) == 1
    assert runs[0].prompt == "What is 2+2?"
    assert repo.list_prompt_runs("exp-002") == []


@pytest.mark.unit
def test_save_and_list_responses(repo: InMemoryEvalStoreRepository) -> None:
    response = ModelResponse(
        id="resp1",
        experiment_id="exp-001",
        prompt_run_id="r1",
        response_text="4",
        latency_ms=120.5,
        token_count=3,
    )
    repo.save_response(response)

    responses = repo.list_responses("exp-001")
    assert len(responses) == 1
    assert responses[0].response_text == "4"
    assert repo.list_responses("exp-999") == []


@pytest.mark.unit
def test_document_type_defaults() -> None:
    exp = Experiment(id="e1", experiment_id="exp-001", name="x", description="y")
    run = PromptRun(id="r1", experiment_id="exp-001", prompt="p", model_name="m", model_version="v")
    resp = ModelResponse(
        id="resp1",
        experiment_id="exp-001",
        prompt_run_id="r1",
        response_text="t",
        latency_ms=10.0,
        token_count=1,
    )
    score = EvaluationScore(
        id="s1", experiment_id="exp-001", response_id="resp1", metric_name="f", score=0.5
    )

    assert exp.document_type == "experiment"
    assert run.document_type == "prompt_run"
    assert resp.document_type == "model_response"
    assert score.document_type == "evaluation_score"


@pytest.mark.unit
def test_score_validation_bounds() -> None:
    with pytest.raises(ValidationError):
        EvaluationScore(
            id="s1",
            experiment_id="exp-001",
            response_id="r1",
            metric_name="faithfulness",
            score=1.1,
        )
