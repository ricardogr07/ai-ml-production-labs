from __future__ import annotations

import pytest

from production_labs_shared.telemetry import timed_operation


@pytest.mark.unit
def test_timed_operation_completes_without_error() -> None:
    with timed_operation("test_op", env="test"):
        result = 1 + 1

    assert result == 2


@pytest.mark.unit
def test_timed_operation_propagates_exceptions() -> None:
    with pytest.raises(ValueError, match="boom"), timed_operation("failing_op"):
        raise ValueError("boom")
