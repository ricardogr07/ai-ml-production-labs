from __future__ import annotations

import pytest
from rag_retrieval_strategy_lab.metrics import mean_reciprocal_rank, recall_at_k
from rag_retrieval_strategy_lab.schemas import RetrievalResult


def _results(*ids: str) -> list[RetrievalResult]:
    return [RetrievalResult(doc_id=i, content="", score=1.0) for i in ids]


@pytest.mark.unit
def test_recall_at_k_perfect() -> None:
    assert recall_at_k(_results("a", "b", "c"), {"a", "b"}, k=3) == 1.0


@pytest.mark.unit
def test_recall_at_k_partial() -> None:
    assert recall_at_k(_results("a", "x", "y"), {"a", "b"}, k=3) == 0.5


@pytest.mark.unit
def test_recall_at_k_empty_relevant() -> None:
    assert recall_at_k(_results("a"), set(), k=3) == 0.0


@pytest.mark.unit
def test_mrr_first_is_relevant() -> None:
    assert mean_reciprocal_rank(_results("a", "b"), {"a"}) == 1.0


@pytest.mark.unit
def test_mrr_second_is_relevant() -> None:
    assert mean_reciprocal_rank(_results("x", "a"), {"a"}) == 0.5


@pytest.mark.unit
def test_mrr_none_relevant() -> None:
    assert mean_reciprocal_rank(_results("x", "y"), {"a"}) == 0.0
