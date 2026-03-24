---
title: polyglot-python
section: 7
header: Polyglot Devcontainers
footer: Runtime Documentation
---

# NAME

polyglot-python - Python starter and maintenance workflow

# PURPOSE

This page explains the supported Python workflow in polyglot-devcontainers.

# WHEN TO USE

Read this page when working in Python starters or Python proving paths.

# PRIMARY COMMANDS

```bash
task init
task ci
uv sync --frozen --extra dev
uv lock --upgrade
```

# WORKFLOW

The repository now treats `uv` and `uv.lock` as the first-class Python path.

In maintained Python paths:

- `pyproject.toml` describes intent
- `uv.lock` describes the resolved environment
- `task init` uses `uv sync --frozen --extra dev`

In the published `python-node` starter image:

- the image already contains Python, Node, `uv`, `pnpm`, and the scanner
  toolchain
- `task init` still installs the project-local Python and Node dependencies
  into the mounted workspace
- this is expected because `.venv` and `node_modules` belong to the project
  contract, not the image base layer
- when the workspace is not yet a Git repository, the secret scan falls back to
  starter source files instead of scanning dependency directories like
  `node_modules` and `.venv`

Safe default workflow:

1. open the container
2. run `task init`
3. do the work
4. run `task ci`

Dependency-oriented workflow:

1. inspect `task deps:inventory`
2. inspect `task deps:plan`
3. inspect `task deps:report`
4. use `task upgrade` only when the path supports it
5. rerun `task ci`

Repository-owned scenario slice:

- from the repository root, run `task scenarios:python-maintenance`
- inspect `.artifacts/scenarios/python-uv-lock-maintenance.md`
- treat `task upgrade` in `examples/python-maintenance-example` as the manual
  follow-on execution step after reading the evidence

# OUTPUTS / ARTIFACTS

Python paths may write:

- `pip-audit.json`
- `gitleaks.sarif`
- `dependency-inventory.json`
- `dependency-plan.json`
- `dependency-report.json`
- `dependency-report.md`
- `pypi-upgrades.json`

# COMMON FAILURES

- Editing dependencies without updating `uv.lock`.
- Expecting `task init` in a fresh starter workspace to skip local dependency
  installation.
- Using a loose `pip install` flow in a maintained `uv` path.
- Treating compatibility workflows as equal to the `uv-lock` path.

# GUIDANCE

- Prefer `uv` operations over ad hoc Python package commands.
- Keep `uv.lock` checked in and aligned with `pyproject.toml`.
- Use `task ci` after dependency changes.

# SEE ALSO

- `polyglot(7)`
- `polyglot-task-contract(7)`
- `polyglot-deps(7)`
- `polyglot-scenarios(7)`
- `polyglot-security(7)`
- `polyglot-knowledge(7)`
