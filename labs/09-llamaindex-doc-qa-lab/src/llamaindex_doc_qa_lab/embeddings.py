"""Embedding model factory, shared by ingestion and query."""

from __future__ import annotations

from functools import lru_cache

from llama_index.core.base.embeddings.base import BaseEmbedding

from llamaindex_doc_qa_lab.config import settings


@lru_cache(maxsize=1)
def get_embedding_model() -> BaseEmbedding:
    from llama_index.embeddings.huggingface import HuggingFaceEmbedding

    return HuggingFaceEmbedding(model_name=settings.embedding_model_name)
