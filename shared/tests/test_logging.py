from __future__ import annotations

import pytest

from production_labs_shared.logging import configure_logging


@pytest.mark.unit
def test_configure_logging_runs_without_error() -> None:
    configure_logging("DEBUG")


@pytest.mark.unit
def test_configure_logging_invalid_level_falls_back() -> None:
    configure_logging("NOT_A_LEVEL")
