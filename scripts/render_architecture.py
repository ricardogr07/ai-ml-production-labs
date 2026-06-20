#!/usr/bin/env python3
"""Print a quick summary of all labs and their contract status."""

from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent


def lab_status(lab_path: Path) -> str:
    has_docker = (lab_path / "Dockerfile").exists()
    has_infra = (lab_path / "infra" / "main.bicep").exists()
    has_tests = (lab_path / "tests" / "unit").is_dir()
    has_readme = (lab_path / "README.md").exists()

    flags = []
    if has_readme:
        flags.append("README")
    if has_tests:
        flags.append("tests")
    if has_docker:
        flags.append("Docker")
    if has_infra:
        flags.append("infra")

    return ", ".join(flags) if flags else "scaffold only"


def main() -> int:
    labs_dir = REPO_ROOT / "labs"
    if not labs_dir.exists():
        print("No labs/ directory found.", file=sys.stderr)
        return 1

    print(f"{'Lab':<50} {'Artifacts'}")
    print("-" * 80)

    for lab_path in sorted(p for p in labs_dir.iterdir() if p.is_dir()):
        status = lab_status(lab_path)
        print(f"{lab_path.name:<50} {status}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
