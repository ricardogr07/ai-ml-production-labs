# Claude Code Instructions — ai-ml-production-labs

## Commits and pull requests

- Never add `Co-Authored-By`, attribution lines, or any mention of Claude or AI to commit messages or PR bodies.
- Keep commit messages concise and in the imperative form (`chore:`, `feat:`, `fix:`, etc.).
- Never use em dashes in commit messages, PR titles, or PR bodies. Use a comma, a colon, or rephrase instead.

## Writing rules

- No em dashes anywhere: not in `.md` files, code comments, commit messages, PR bodies, or conversational output. Use a comma, a colon, a parenthetical, or rephrase.
- All `.md` files must be presented to Ricardo for review and explicit approval before staging with `git add`. Do not add any `.md` file to the index without sign-off.

## Tooling

- Type checker is **pyrefly** (not mypy). Run with `pyrefly check shared/src labs`.
- Infrastructure is **Terraform** (not Bicep). All infra lives in `main.tf` + `terraform.tfvars.example`.
- Package manager is **uv** with workspaces. Use `uv sync --all-packages` at the root.
- Test runner is **tox + tox-uv**. Standard gate: `tox -e lint,type,py312,security,audit`.

## Lab conventions

- Each lab lives under `labs/NN-lab-name/` with its own `pyproject.toml`, `src/`, `tests/`, `README.md`.
- The shared package (`shared/`) contains only infrastructure utilities, no lab-specific logic.
- Every lab must have at minimum: schema test, service test, smoke test, and a working README command.
- Infra templates go in `labs/NN-lab-name/infra/main.tf` for cloud-deployed labs.
