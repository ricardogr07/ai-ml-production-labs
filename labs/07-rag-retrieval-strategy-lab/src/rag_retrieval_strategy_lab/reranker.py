"""Cross-encoder reranker for the RAG retrieval strategy lab."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from sentence_transformers import CrossEncoder

_MODEL_NAME = "cross-encoder/ms-marco-MiniLM-L-6-v2"


class Reranker:
    def __init__(self, model_name: str = _MODEL_NAME) -> None:
        from sentence_transformers import CrossEncoder

        self._model: CrossEncoder = CrossEncoder(model_name)

    def score(self, query: str, documents: list[str]) -> list[float]:
        pairs = [(query, doc) for doc in documents]
        return [float(s) for s in self._model.predict(pairs)]  # type: ignore[no-matching-overload]
