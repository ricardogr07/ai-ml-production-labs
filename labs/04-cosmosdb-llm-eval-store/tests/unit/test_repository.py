from __future__ import annotations

import pytest

from cosmosdb_llm_eval_store.repository import InMemoryEvalStoreRepository
from cosmosdb_llm_eval_store.schemas import Experiment, EvaluationScore, ModelResponse, PromptRun


@pytest.fixture
def repo() -> InMemoryEvalStoreRepository:
    return InMemoryEvalStoreRepository()


@pytest.mark.unit
def test_save_and_retrieve_experiment(repo: InMemoryEvalStoreRepository) -> None:
    exp = Experiment(id="e1", experiment_id="exp-001", name="Test", description="A test experiment.")
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
    repo.save_score(EvaluationScore(id="s1", experiment_id="exp-001", response_id="r1", metric_name="m", score=0.8))
    repo.save_score(EvaluationScore(id="s2", experiment_id="exp-002", response_id="r2", metric_name="m", score=0.7))

    assert len(repo.list_scores("exp-001")) == 1
    assert len(repo.list_scores("exp-002")) == 1
