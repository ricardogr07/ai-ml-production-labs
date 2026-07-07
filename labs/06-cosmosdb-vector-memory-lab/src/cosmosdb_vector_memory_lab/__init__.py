"""Lab 06: Cosmos DB Vector Memory Lab."""

from cosmosdb_vector_memory_lab.config import Settings, settings
from cosmosdb_vector_memory_lab.cosmos_repository import CosmosDBVectorStoreRepository
from cosmosdb_vector_memory_lab.repository import (
    InMemoryVectorStoreRepository,
    VectorStoreRepository,
)
from cosmosdb_vector_memory_lab.schemas import Document, SearchResult

__all__ = [
    "CosmosDBVectorStoreRepository",
    "Document",
    "InMemoryVectorStoreRepository",
    "SearchResult",
    "Settings",
    "VectorStoreRepository",
    "settings",
]
