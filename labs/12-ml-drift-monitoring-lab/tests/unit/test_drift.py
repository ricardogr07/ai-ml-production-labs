from __future__ import annotations

import pytest
from ml_drift_monitoring_lab.drift import detect_drift


@pytest.mark.unit
def test_no_drift_identical_data() -> None:
    data = {"error_count": list(range(100))}
    results = detect_drift(data, data)

    assert len(results) == 1
    assert results[0].drift_detected is False


@pytest.mark.unit
def test_drift_detected_on_shifted_data() -> None:
    reference = {"error_count": [float(i) for i in range(100)]}
    current = {"error_count": [float(i + 50) for i in range(100)]}

    results = detect_drift(reference, current)

    assert results[0].drift_detected is True
    assert results[0].current_mean > results[0].reference_mean


@pytest.mark.unit
def test_returns_one_result_per_feature() -> None:
    reference = {"a": [1.0, 2.0, 3.0], "b": [4.0, 5.0, 6.0]}
    current = {"a": [1.0, 2.0, 3.0], "b": [4.0, 5.0, 6.0]}

    results = detect_drift(reference, current)

    assert len(results) == 2
