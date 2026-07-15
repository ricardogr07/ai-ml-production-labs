from __future__ import annotations

from llama_index.core import VectorStoreIndex
from qdrant_client.http.exceptions import ResponseHandlingException, UnexpectedResponse

from llamaindex_doc_qa_lab import embeddings, llm, readiness, vector_store
from llamaindex_doc_qa_lab.config import settings
from llamaindex_doc_qa_lab.errors import GenerationError, NotReadyError
from llamaindex_doc_qa_lab.schemas import QueryRequest, QueryResponse, SourceChunk


class QueryService:
    def query(self, request: QueryRequest) -> QueryResponse:
        # Preflight the deterministic failure modes so an unseeded/stale Qdrant or
        # an unreachable/unpulled LLM returns an actionable 503, not a bare 500.
        readiness.check_qdrant()
        readiness.check_llm()

        # Readiness passed, but the preflight is not atomic: Qdrant can drop or
        # change between the check and the work below, and building the vector
        # store, index, and query engine all touch Qdrant. Wrap the whole
        # retrieve-and-generate span so a Qdrant fault maps to 503 (retry the
        # dependency) and any other fault to 424 (generation), never a bare 500.
        try:
            index = VectorStoreIndex.from_vector_store(
                vector_store.get_vector_store(),
                embed_model=embeddings.get_embedding_model(),
            )
            query_engine = index.as_query_engine(
                llm=llm.get_llm(),
                similarity_top_k=request.top_k,
            )
            response = query_engine.query(request.question)
        except (UnexpectedResponse, ResponseHandlingException) as exc:
            raise NotReadyError(f"Qdrant became unavailable during retrieval: {exc}") from exc
        except Exception as exc:  # anything left is a generation-side fault
            raise GenerationError(
                f"Generation failed for provider {settings.llm_provider!r}: {exc}"
            ) from exc

        sources = [
            SourceChunk(
                content=node.node.get_content(),
                source=node.node.metadata.get("source", "unknown"),
                score=node.score or 0.0,
            )
            for node in response.source_nodes
        ]
        return QueryResponse(answer=str(response), sources=sources)
