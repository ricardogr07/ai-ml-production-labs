"""Integration tests for the full eval lifecycle against the CosmosDB emulator."""

from __future__ import annotations

import uuid

import pytest
from cosmosdb_llm_eval_store.cosmos_repository import CosmosDBEvalStoreRepository
from cosmosdb_llm_eval_store.schemas import (
    EvaluationScore,
    Experiment,
    ModelResponse,
    PromptRun,
)


def _uid() -> str:
    return str(uuid.uuid4())


@pytest.mark.integration
def test_full_eval_lifecycle(cosmos_repo: CosmosDBEvalStoreRepository) -> None:
    exp_id = _uid()

    exp = Experiment(id=exp_id, experiment_id=exp_id, name="Lifecycle Test", description="e2e")
    cosmos_repo.save_experiment(exp)

    run = PromptRun(
        id=_uid(),
        experiment_id=exp_id,
        prompt="Summarize the document.",
        model_name="claude-sonnet-4-6",
        model_version="20250101",
    )
    cosmos_repo.save_prompt_run(run)

    resp = ModelResponse(
        id=_uid(),
        experiment_id=exp_id,
        prompt_run_id=run.id,
        response_text="The document covers AI trends.",
        latency_ms=210.0,
        token_count=42,
    )
    cosmos_repo.save_response(resp)

    cosmos_repo.save_score(
        EvaluationScore(
            id=_uid(),
            experiment_id=exp_id,
            response_id=resp.id,
            metric_name="faithfulness",
            score=0.95,
        )
    )
    cosmos_repo.save_score(
        EvaluationScore(
            id=_uid(),
            experiment_id=exp_id,
            response_id=resp.id,
            metric_name="relevance",
            score=0.88,
        )
    )

    assert len(cosmos_repo.list_prompt_runs(exp_id)) == 1
    assert len(cosmos_repo.list_responses(exp_id)) == 1
    scores = cosmos_repo.list_scores(exp_id)
    assert len(scores) == 2
    metric_names = {s.metric_name for s in scores}
    assert metric_names == {"faithfulness", "relevance"}


@pytest.mark.integration
def test_archive_experiment(cosmos_repo: CosmosDBEvalStoreRepository) -> None:
    exp_id = _uid()
    exp = Experiment(id=exp_id, experiment_id=exp_id, name="Archive Test", description="arch")
    cosmos_repo.save_experiment(exp)

    retrieved = cosmos_repo.get_experiment(exp_id)
    assert retrieved is not None
    assert retrieved.status == "active"

    archived = exp.model_copy(update={"status": "archived"})
    cosmos_repo.save_experiment(archived)

    updated = cosmos_repo.get_experiment(exp_id)
    assert updated is not None
    assert updated.status == "archived"


@pytest.mark.integration
def test_get_missing_experiment(cosmos_repo: CosmosDBEvalStoreRepository) -> None:
    result = cosmos_repo.get_experiment("nonexistent-" + _uid())
    assert result is None


@pytest.mark.integration
def test_multi_experiment_isolation(cosmos_repo: CosmosDBEvalStoreRepository) -> None:
    exp_a = _uid()
    exp_b = _uid()

    for exp_id in (exp_a, exp_b):
        cosmos_repo.save_experiment(
            Experiment(id=exp_id, experiment_id=exp_id, name=exp_id, description="iso")
        )
        run = PromptRun(
            id=_uid(),
            experiment_id=exp_id,
            prompt="hello",
            model_name="m",
            model_version="v",
        )
        cosmos_repo.save_prompt_run(run)
        cosmos_repo.save_score(
            EvaluationScore(
                id=_uid(),
                experiment_id=exp_id,
                response_id=_uid(),
                metric_name="quality",
                score=0.7,
            )
        )

    assert len(cosmos_repo.list_prompt_runs(exp_a)) == 1
    assert len(cosmos_repo.list_prompt_runs(exp_b)) == 1
    assert len(cosmos_repo.list_scores(exp_a)) == 1
    assert len(cosmos_repo.list_scores(exp_b)) == 1
