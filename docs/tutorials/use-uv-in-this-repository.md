# Use uv in This Repository

This tutorial explains the Python dependency workflow that
`polyglot-devcontainers` now treats as first-class.

## Goal

Understand what `uv` does, how the repository uses it, and how to perform the
common dependency tasks without leaving the validated task contract behind.

## What `uv` is doing

In this repository, `uv` is used for three related jobs:

1. Resolve Python dependencies into a checked-in `uv.lock` file.
2. Create or update the local project environment from that lockfile.
3. Run ecosystem-native dependency maintenance through `uv lock --upgrade`.

That gives the repository a clear source of truth:

- `pyproject.toml` describes intent
- `uv.lock` records the resolved environment
- `uv sync --frozen` recreates that exact environment

## Step 1: Open a maintained Python path

Use one of the repository-owned Python paths:

- `examples/python-example`
- `examples/python-image-example`
- `examples/python-maintenance-example`
- `templates/python-secure`
- `templates/python-node-secure`

Open the repository in the devcontainer first. The container is the canonical
environment for the task contract.

## Step 2: Inspect the source of truth

Look at:

- `pyproject.toml`
- `uv.lock`

`pyproject.toml` holds the declared dependencies and metadata.

`uv.lock` holds the exact resolved versions used by the maintained workflow.

That is why the repository can use a stricter bootstrap command than a loose
`pip install -e .[dev]` flow.

## Step 3: Recreate the environment

From one of the maintained Python paths, run:

```bash
uv sync --frozen --extra dev
```

What this does:

- creates `.venv` if needed
- installs the locked dependency set
- includes the optional `dev` dependency group
- fails if the lockfile and manifest no longer agree

In the repository task contract, this is what `task init` now does for the
maintained Python paths.

## Step 4: Run commands inside the environment

Use:

```bash
uv run pytest -q
uv run ruff check .
uv run mypy src tests tasks.py
```

`uv run` executes commands inside the environment described by the current
project configuration.

In this repository, the task files still call the `.venv` Python directly for
the stable task contract, but `uv run` remains useful when you are working
interactively.

## Step 5: Change dependencies

When you need to add a dependency, use:

```bash
uv add httpx
uv add --dev pytest
```

When you need to remove one, use:

```bash
uv remove httpx
```

These commands update both:

- `pyproject.toml`
- `uv.lock`

That is one of the main reasons `uv` became the default path here: the manifest
and lockfile stay in sync through a native workflow.

## Step 6: Refresh the lockfile deliberately

To refresh resolved versions while keeping the same declared intent, use:

```bash
uv lock
```

To ask for newer resolved versions where the declared constraints allow them,
use:

```bash
uv lock --upgrade
```

That command is the basis for the repository's preferred Python upgrade path.

In the maintained dependency-maintenance fixtures, the planning and upgrade
workflow treats `uv lock --upgrade` as the first-class native mutation step.

## Step 7: Re-verify the repository contract

After dependency changes, run the validated workflow:

```bash
task ci
```

If the path supports dependency-maintenance helpers, you can also inspect:

```bash
task deps:inventory
task deps:plan
task upgrade
```

For repo-owned Python paths, `uv-lock` is now the default workflow behind that
upgrade path.

## Additional `uv` capabilities worth knowing

`uv` can do more than this repository currently standardizes on.

Useful commands include:

```bash
uv tree
uv export --format requirements-txt
uv python list
uv python install 3.12
```

How they fit here:

- `uv tree` is useful for understanding dependency shape during debugging
- `uv export` can help when another tool still needs requirements-style output
- `uv python list` and `uv python install` can help in local experimentation,
  though the repository's canonical environment is still the devcontainer

The repository does not require every `uv` feature to be part of the formal
task contract. The important point is narrower:

- repo-owned Python paths should have a checked-in `uv.lock`
- bootstrap should use `uv sync --frozen`
- upgrades should prefer `uv lock --upgrade`
- final verification should still run through `task ci`

## What changed in repository policy

The earlier Python compatibility lanes were useful for evidence, but not
equally safe as default mutation paths.

The proving work showed:

- `plain-pyproject` was honest but too weak for safe auto-upgrade
- `pyproject-exact-pins` needed extra compatibility guards and still remained
  risky
- `pip-tools` stayed valid, but not simpler than `uv-lock`

That is why the repository now standardizes on `uv` for its own maintained
Python paths while still detecting other shapes honestly.

## Next steps

- Read [Python Dependency Workflows](../explanation/python-dependency-workflows.md)
  for the design rationale.
- Follow [Create a Python Workspace](./create-a-python-workspace.md) for the
  smallest end-to-end path.
- Use [Run the Security Workflow](../how-to/run-the-security-workflow.md) when
  you need the dependency evidence and upgrade artifacts.
