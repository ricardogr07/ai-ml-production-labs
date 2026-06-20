from __future__ import annotations

import pytest

from production_labs_shared.schemas import ErrorResponse


@pytest.mark.unit
def test_error_response_with_detail() -> None:
    err = ErrorResponse(detail="something went wrong")

    assert err.detail == "something went wrong"
    assert err.request_id == ""


@pytest.mark.unit
def test_error_response_with_request_id() -> None:
    err = ErrorResponse(detail="not found", request_id="req-123")

    assert err.request_id == "req-123"


@pytest.mark.unit
def test_error_response_serializes() -> None:
    err = ErrorResponse(detail="bad input", request_id="req-abc")
    data = err.model_dump()

    assert data == {"detail": "bad input", "request_id": "req-abc"}
