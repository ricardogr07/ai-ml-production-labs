#!/usr/bin/env python3
"""Scaffold a new lab from the standard template."""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
LABS_DIR = REPO_ROOT / "labs"

LAB_DIRS = [
    "src/{package_name}",
    "tests/unit",
    "tests/integration",
    "tests/e2e",
    "infra",
    "scripts",
    "docs",
]

PYPROJECT_TEMPLATE = """\
[project]
name = "{lab_name}"
version = "0.1.0"
description = "TODO: one-sentence lab description."
readme = "README.md"
requires-python = ">=3.12"
dependencies = [
  "production-labs-shared",
  "pydantic>=2.7",
]

[project.optional-dependencies]
api = [
  "fastapi>=0.115",
  "uvicorn[standard]>=0.30",
]

[tool.uv.sources]
production-labs-shared = {{ workspace = true }}

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.hatch.build.targets.wheel]
packages = ["src/{package_name}"]
"""

README_TEMPLATE = """\
# Lab {number}: {title}

## What this proves

TODO

## Scope

- Capability:
- Input:
- Output:
- Deployment target:
- Non-goals:

## Architecture

```text
client -> service -> response
```

## Run locally

```bash
uv sync
uv run --package {lab_name} pytest
```

## Test

```bash
tox -e lint,type,py312
```

## Tradeoffs

TODO
"""

INIT_TEMPLATE = '"""Lab {number}: {title}."""\n'


def slugify(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", name.lower()).strip("_")


def main() -> int:
    parser = argparse.ArgumentParser(description="Scaffold a new lab.")
    parser.add_argument("number", help="Lab number, e.g. 15")
    parser.add_argument("name", help="Lab folder name, e.g. my-new-lab")
    parser.add_argument("--title", default="", help="Human-readable title")
    args = parser.parse_args()

    folder_name = f"{int(args.number):02d}-{args.name}"
    lab_dir = LABS_DIR / folder_name
    package_name = slugify(args.name)
    lab_name = args.name
    title = args.title or args.name.replace("-", " ").title()
    number = int(args.number)

    if lab_dir.exists():
        print(f"Error: {lab_dir} already exists.", file=sys.stderr)
        return 1

    for template in LAB_DIRS:
        path = lab_dir / template.format(package_name=package_name)
        path.mkdir(parents=True, exist_ok=True)

    (lab_dir / "src" / package_name / "__init__.py").write_text(
        INIT_TEMPLATE.format(number=number, title=title)
    )
    (lab_dir / "pyproject.toml").write_text(
        PYPROJECT_TEMPLATE.format(lab_name=lab_name, package_name=package_name)
    )
    (lab_dir / "README.md").write_text(
        README_TEMPLATE.format(number=number, title=title, lab_name=lab_name)
    )
    (lab_dir / ".env.example").write_text("ENVIRONMENT=local\nLOG_LEVEL=INFO\n")

    print(f"Created {lab_dir}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
