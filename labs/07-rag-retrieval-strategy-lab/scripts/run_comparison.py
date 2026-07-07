#!/usr/bin/env python3
"""
Run all retrieval strategies over the golden query set and print a metrics
comparison table.

Usage:
  docker compose -f labs/07-rag-retrieval-strategy-lab/docker-compose.yml up -d
  uv run python labs/07-rag-retrieval-strategy-lab/scripts/run_comparison.py
"""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any

import structlog
from qdrant_client import QdrantClient
from rag_retrieval_strategy_lab.config import settings
from rag_retrieval_strategy_lab.metrics import mean_reciprocal_rank, recall_at_k
from rag_retrieval_strategy_lab.repository import QdrantVectorStoreRepository
from rag_retrieval_strategy_lab.reranker import Reranker
from rag_retrieval_strategy_lab.schemas import Document, RetrievalResult
from rag_retrieval_strategy_lab.strategies import (
    expanded_query_search,
    metadata_filtered_search,
    naive_search,
    reranked_search,
)

from production_labs_shared.logging import configure_logging

_CORPUS_PATH = Path(__file__).parent.parent / "data" / "wikipedia_corpus.json"
_QUERIES_PATH = Path(__file__).parent.parent / "data" / "golden_queries.json"
_VECTOR_SIZE = 384
_TOP_K = 3
_CANDIDATE_K = 10
_STRATEGIES = ["naive", "metadata_filtered", "reranked", "expanded_query"]


def _build_client() -> QdrantClient:
    if settings.qdrant_url:
        return QdrantClient(url=settings.qdrant_url)
    return QdrantClient(":memory:")


def _record(
    bucket: dict[str, list[float]],
    results: list[RetrievalResult],
    relevant_ids: set[str],
    latency_ms: float,
) -> None:
    bucket["recall"].append(recall_at_k(results, relevant_ids, k=_TOP_K))
    bucket["mrr"].append(mean_reciprocal_rank(results, relevant_ids))
    bucket["latency_ms"].append(latency_ms)
    bucket["token_count"].append(sum(len(r.content.split()) for r in results))


def _print_table(aggregate: dict[str, dict[str, list[float]]]) -> None:
    print(f"{'strategy':<20}{'recall@3':>10}{'mrr':>10}{'latency_ms':>14}{'tokens':>10}")
    for name in _STRATEGIES:
        metrics = aggregate[name]
        n = len(metrics["recall"])
        recall = sum(metrics["recall"]) / n
        mrr = sum(metrics["mrr"]) / n
        latency = sum(metrics["latency_ms"]) / n
        tokens = sum(metrics["token_count"]) / n
        print(f"{name:<20}{recall:>10.3f}{mrr:>10.3f}{latency:>14.2f}{tokens:>10.1f}")


def main() -> int:
    configure_logging()
    log = structlog.get_logger()

    corpus: list[dict[str, Any]] = json.loads(_CORPUS_PATH.read_text(encoding="utf-8"))
    queries: list[dict[str, Any]] = json.loads(_QUERIES_PATH.read_text(encoding="utf-8"))

    log.info("comparison.loading_models")
    from sentence_transformers import SentenceTransformer

    model = SentenceTransformer("all-MiniLM-L6-v2")
    reranker = Reranker()

    def embed_fn(text: str) -> list[float]:
        return model.encode([text], normalize_embeddings=True).tolist()[0]  # type: ignore[no-any-return]

    client = _build_client()
    repo = QdrantVectorStoreRepository(
        client, settings.qdrant_collection or "documents", vector_size=_VECTOR_SIZE
    )

    texts = [doc["content"] for doc in corpus]
    embeddings = model.encode(texts, normalize_embeddings=True).tolist()
    for doc, embedding in zip(corpus, embeddings, strict=True):
        repo.add(
            Document(
                id=doc["id"], content=doc["content"], category=doc["category"], embedding=embedding
            )
        )
    log.info("comparison.corpus_seeded", count=len(corpus))

    aggregate: dict[str, dict[str, list[float]]] = {
        name: {"recall": [], "mrr": [], "latency_ms": [], "token_count": []} for name in _STRATEGIES
    }

    for q in queries:
        query_text = q["query"]
        relevant_ids = set(q["relevant_doc_ids"])
        query_embedding = embed_fn(query_text)

        start = time.perf_counter()
        naive_results = naive_search(repo, query_embedding, top_k=_TOP_K)
        _record(
            aggregate["naive"], naive_results, relevant_ids, (time.perf_counter() - start) * 1000
        )

        start = time.perf_counter()
        filtered_results = metadata_filtered_search(
            repo, query_embedding, "category", q["category"], top_k=_TOP_K
        )
        _record(
            aggregate["metadata_filtered"],
            filtered_results,
            relevant_ids,
            (time.perf_counter() - start) * 1000,
        )

        start = time.perf_counter()
        reranked_results = reranked_search(
            repo,
            query_text,
            query_embedding,
            reranker.score,
            top_k=_TOP_K,
            candidate_k=_CANDIDATE_K,
        )
        _record(
            aggregate["reranked"],
            reranked_results,
            relevant_ids,
            (time.perf_counter() - start) * 1000,
        )

        start = time.perf_counter()
        expanded_results = expanded_query_search(repo, query_text, embed_fn, top_k=_TOP_K)
        _record(
            aggregate["expanded_query"],
            expanded_results,
            relevant_ids,
            (time.perf_counter() - start) * 1000,
        )

        log.info("comparison.query_done", query=query_text)

    _print_table(aggregate)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
