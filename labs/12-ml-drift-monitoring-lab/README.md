# Lab 12: ML Drift Monitoring Lab

## What this proves

ML systems decay after deployment because reality changes. This lab detects data drift between a reference dataset (training distribution) and a current dataset (simulated production shift) using the Kolmogorov-Smirnov test, producing a drift report that names which features shifted and by how much.

## Scope

- Capability: Detect and report feature-level data drift
- Input: reference dataset, current dataset (same schema)
- Output: drift report per feature (KS statistic, p-value, drift flag, mean shift)
- Deployment target: local script or scheduled job
- Non-goals: concept drift, model retraining, alerting infrastructure

## Architecture

```text
reference_data.csv → drift.py → FeatureDriftResult per feature
current_data.csv  ↗              ↓
                          drift_report.json
```

## Run locally

```bash
uv sync
uv run --package ml-drift-monitoring-lab python labs/12-ml-drift-monitoring-lab/scripts/generate_report.py
```

## Test

```bash
uv run --package ml-drift-monitoring-lab pytest labs/12-ml-drift-monitoring-lab/tests
```

## Tradeoffs

- KS test is distribution-free and works on any continuous feature; it does not detect label drift (concept drift).
- Threshold (`p < 0.05`) is a starting point; real production thresholds depend on business tolerance for false alarms.
- Simulated drift uses a mean shift; real drift can be subtler (variance change, tail behavior).
