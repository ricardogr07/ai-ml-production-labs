"""Readiness checks for the backing dependencies.

`/query` runs check_qdrant + check_llm as a preflight so the deterministic
failure modes (unseeded Qdrant, stale vector schema, empty collection,
unreachable Ollama, unpulled model, missing Anthropic key) return an actionable
503 instead of a bare 500. `/ready` reports the same checks without querying.
"""

from __future__ import annotations

import json
import urllib.request

from qdrant_client import QdrantClient

from llamaindex_doc_qa_lab import embeddings, vector_store
from llamaindex_doc_qa_lab.config import settings
from llamaindex_doc_qa_lab.errors import NotReadyError

_PROBE_TIMEOUT = 5


def check_qdrant() -> None:
    """Raise NotReadyError unless the collection exists, carries the named dense
    vector at the model's embedding dimension, and holds at least one point."""
    collection = settings.qdrant_collection
    # Every Qdrant call goes in the try: a transport error on any of them means
    # "not ready", not an opaque 500. The semantic checks below own the messages.
    try:
        client = QdrantClient(url=settings.qdrant_url, timeout=_PROBE_TIMEOUT)
        exists = client.collection_exists(collection)
        params = vector_store.named_vector(client, collection) if exists else None
        count = client.count(collection).count if params is not None else 0
    except Exception as exc:  # any client/transport error means not ready
        raise NotReadyError(f"Qdrant not reachable at {settings.qdrant_url}: {exc}") from exc

    if not exists:
        raise NotReadyError(
            f"Qdrant collection {collection!r} does not exist; run scripts/seed_data.py."
        )
    if params is None:
        raise NotReadyError(
            f"Qdrant collection {collection!r} has no named text-dense vector; "
            "re-seed with scripts/seed_data.py --recreate."
        )
    try:
        expected_dim = embeddings.embedding_dim()
    except Exception as exc:  # embedding model missing or failing to load
        raise NotReadyError(
            f"Embedding model {settings.embedding_model_name!r} failed to load: {exc}"
        ) from exc
    if params.size != expected_dim:
        raise NotReadyError(
            f"Qdrant collection {collection!r} has a text-dense vector of dim {params.size}, "
            f"but the embedding model produces {expected_dim}; "
            "re-seed with scripts/seed_data.py --recreate."
        )
    if count == 0:
        raise NotReadyError(f"Qdrant collection {collection!r} is empty; run scripts/seed_data.py.")


def check_llm() -> None:
    """Raise NotReadyError unless the selected generation provider is usable."""
    if settings.llm_provider == "ollama":
        try:
            # URL is the operator-configured ollama_base_url (http), not user input
            with urllib.request.urlopen(  # nosec B310
                f"{settings.ollama_base_url}/api/tags", timeout=_PROBE_TIMEOUT
            ) as resp:
                tags = json.load(resp)
        except OSError as exc:
            raise NotReadyError(
                f"Ollama not reachable at {settings.ollama_base_url}: {exc}"
            ) from exc
        available = {m["name"] for m in tags.get("models", [])}
        model = settings.ollama_model
        # A tagged config (llama3.2:1b) must match exactly; an untagged one
        # (llama3.2) matches any pulled tag of that base, since `ollama pull`
        # defaults to :latest.
        if ":" in model:
            pulled = model in available
        else:
            pulled = model in {name.split(":")[0] for name in available}
        if not pulled:
            raise NotReadyError(
                f"Ollama model {model!r} is not pulled; run: "
                f"docker compose exec ollama ollama pull {model}."
            )
    elif settings.llm_provider == "anthropic":
        if not (settings.anthropic_api_key and settings.anthropic_api_key.get_secret_value()):
            raise NotReadyError("Anthropic provider selected but ANTHROPIC_API_KEY is not set.")


def readiness() -> dict[str, str]:
    """Run every check and report per-dependency status: "ok" or the failure
    message. Never raises; callers decide the HTTP code from the values."""
    report: dict[str, str] = {}
    for name, check in (("qdrant", check_qdrant), ("llm", check_llm)):
        try:
            check()
            report[name] = "ok"
        except NotReadyError as exc:
            report[name] = str(exc)
    return report
