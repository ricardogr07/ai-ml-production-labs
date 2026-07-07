from __future__ import annotations

import pytest
from cosmosdb_vector_memory_lab.schemas import Document, SearchResult
from pydantic import ValidationError


@pytest.mark.unit
def test_document_defaults() -> None:
    doc = Document(id="1", content="hello")
    assert doc.embedding == []
    assert doc.metadata == {}
    assert doc.source == ""


@pytest.mark.unit
def test_search_result_score_bounds() -> None:
    with pytest.raises(ValidationError):
        SearchResult(document=Document(id="1", content="x"), score=1.1)


@pytest.mark.unit
def test_search_result_score_lower_bound() -> None:
    with pytest.raises(ValidationError):
        SearchResult(document=Document(id="1", content="x"), score=-1.1)


@pytest.mark.unit
def test_document_roundtrip() -> None:
    doc = Document(id="42", content="text", source="s3", embedding=[0.1, 0.2], metadata={"k": "v"})
    reconstructed = Document(**doc.model_dump())
    assert reconstructed == doc
