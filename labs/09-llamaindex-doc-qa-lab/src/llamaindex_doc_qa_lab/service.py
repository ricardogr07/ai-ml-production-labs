from __future__ import annotations

from llama_index.core import VectorStoreIndex

from llamaindex_doc_qa_lab import embeddings, llm, vector_store
from llamaindex_doc_qa_lab.schemas import QueryRequest, QueryResponse, SourceChunk


class QueryService:
    def query(self, request: QueryRequest) -> QueryResponse:
        index = VectorStoreIndex.from_vector_store(
            vector_store.get_vector_store(),
            embed_model=embeddings.get_embedding_model(),
        )
        query_engine = index.as_query_engine(
            llm=llm.get_llm(),
            similarity_top_k=request.top_k,
        )
        response = query_engine.query(request.question)

        sources = [
            SourceChunk(
                content=node.node.get_content(),
                source=node.node.metadata.get("source", "unknown"),
                score=node.score or 0.0,
            )
            for node in response.source_nodes
        ]
        return QueryResponse(answer=str(response), sources=sources)
