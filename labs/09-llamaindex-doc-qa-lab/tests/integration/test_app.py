from __future__ import annotations

from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient
from llamaindex_doc_qa_lab.app import app
from llamaindex_doc_qa_lab.schemas import QueryResponse, SourceChunk

_PATCH_TARGET = "llamaindex_doc_qa_lab.app._service.query"


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


@pytest.mark.integration
def test_health(client: TestClient) -> None:
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["service"] == "llamaindex-doc-qa-lab"
    assert "version" in data
    assert "timestamp_utc" in data


@pytest.mark.integration
def test_query_success(client: TestClient) -> None:
    mock_resp = QueryResponse(
        answer="Paris is the capital of France.",
        sources=[SourceChunk(content="France is a country.", source="France", score=0.9)],
    )
    with patch(_PATCH_TARGET, return_value=mock_resp):
        response = client.post(
            "/query", json={"question": "What is the capital of France?", "top_k": 2}
        )
    assert response.status_code == 200
    data = response.json()
    assert data["answer"] == "Paris is the capital of France."
    assert len(data["sources"]) == 1


@pytest.mark.integration
def test_query_rejects_empty_question(client: TestClient) -> None:
    response = client.post("/query", json={"question": ""})
    assert response.status_code == 422


@pytest.mark.integration
def test_query_rejects_top_k_out_of_range(client: TestClient) -> None:
    response = client.post("/query", json={"question": "hello", "top_k": 0})
    assert response.status_code == 422
