"""Statistical drift detection between reference and current datasets."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from scipy import stats


@dataclass
class FeatureDriftResult:
    feature: str
    ks_statistic: float
    p_value: float
    drift_detected: bool
    reference_mean: float
    current_mean: float


def detect_drift(
    reference: dict[str, list[float]],
    current: dict[str, list[float]],
    p_threshold: float = 0.05,
) -> list[FeatureDriftResult]:
    """Run KS test on each feature and return drift results."""
    results: list[FeatureDriftResult] = []
    for feature in reference:
        ref_vals = np.array(reference[feature])
        cur_vals = np.array(current.get(feature, []))
        if len(cur_vals) == 0:
            continue
        stat, p_value = stats.ks_2samp(ref_vals, cur_vals)
        results.append(
            FeatureDriftResult(
                feature=feature,
                ks_statistic=round(float(stat), 4),
                p_value=round(float(p_value), 4),
                drift_detected=p_value < p_threshold,
                reference_mean=round(float(ref_vals.mean()), 4),
                current_mean=round(float(cur_vals.mean()), 4),
            )
        )
    return results
