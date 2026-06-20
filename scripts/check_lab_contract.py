#!/usr/bin/env python3
"""Check that a lab meets the minimum contract defined in the blueprint."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent

REQUIRED_FILES = [
    "README.md",
    "pyproject.toml",
    ".env.example",
]

REQUIRED_DIRS = [
    "src",
    "tests/unit",
    "tests/integration",
]

OPTIONAL_BUT_NOTED = [
    "Dockerfile",
    "infra/main.bicep",
    "scripts/smoke_test.py",
]


def check_lab(lab_path: Path) -> list[str]:
    failures: list[str] = []

    for f in REQUIRED_FILES:
        if not (lab_path / f).exists():
            failures.append(f"Missing required file: {f}")

    for d in REQUIRED_DIRS:
        if not (lab_path / d).is_dir():
            failures.append(f"Missing required directory: {d}")

    readme = lab_path / "README.md"
    if readme.exists():
        content = readme.read_text()
        for section in ("## What this proves", "## Scope", "## Tradeoffs"):
            if section not in content:
                failures.append(f"README missing section: {section}")

    notes: list[str] = []
    for f in OPTIONAL_BUT_NOTED:
        if not (lab_path / f).exists():
            notes.append(f"Optional artifact not yet present: {f}")

    return failures


def main() -> int:
    parser = argparse.ArgumentParser(description="Check lab contract compliance.")
    parser.add_argument("labs", nargs="*", help="Lab folder names or paths (default: all labs)")
    args = parser.parse_args()

    labs_dir = REPO_ROOT / "labs"

    if args.labs:
        lab_paths = [Path(p) if Path(p).is_absolute() else labs_dir / p for p in args.labs]
    else:
        lab_paths = sorted(p for p in labs_dir.iterdir() if p.is_dir())

    exit_code = 0
    for lab_path in lab_paths:
        if not lab_path.exists():
            print(f"[ERROR] Lab not found: {lab_path}", file=sys.stderr)
            exit_code = 1
            continue

        failures = check_lab(lab_path)
        label = lab_path.name
        if failures:
            print(f"[FAIL] {label}")
            for f in failures:
                print(f"  - {f}")
            exit_code = 1
        else:
            print(f"[PASS] {label}")

    return exit_code


if __name__ == "__main__":
    sys.exit(main())
