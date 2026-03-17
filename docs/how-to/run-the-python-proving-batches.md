# Run the Python Proving Batches

This guide describes how to run the Phase 9b Python dependency-maintenance
experiment against real public repositories in small batches.

The point of this exercise is not to prove that every Python project can be
upgraded automatically.

The point is to test whether the current workflow:

`inventory -> plan -> upgrade -> verify`

remains useful and honest across a representative set of real repository
shapes.

## Start with batches, not a giant sweep

Run a small batch first, update the hypothesis, then decide whether the next
batch is worth the added complexity.

Recommended batch order:

### Batch 1: Common application and library shapes

- `requests`
- `urllib3`
- `click`
- `pytest`
- `pydantic`
- `fastapi`
- `flask`
- `django`

Use this batch to test whether workflow detection and plan artifacts are useful
across common Python repository shapes without immediately adding the
scientific-stack complexity.

### Batch 2: Tooling and optional-dependency pressure

- `httpx`
- `rich`
- `typer`
- `sqlalchemy`
- `alembic`
- `celery`
- `black`
- `ruff`

Use this batch to test whether the current workflow still feels simpler than
repository-specific scripts when optional dependencies, tooling repos, and
plugin-style surfaces become more common.

### Batch 3: Large dependency graphs and compiled ecosystems

- `pandas`
- `numpy`
- `scipy`
- `matplotlib`
- `scikit-learn`
- `jupyterlab`

Use this batch to test the current approach against larger graphs and stricter
compatibility surfaces.

### Batch 4: Packaging and dependency-tooling repos

- `sphinx`
- `mkdocs`
- `poetry`
- `pip-tools`
- `uv`
- `pre-commit`

Use this batch to test whether the model remains useful on repositories that
themselves encode packaging and dependency-management edge cases.

### Batch 5: Complexity and scale

- `apache-airflow`
- `ansible`
- `django-rest-framework`
- `scrapy`
- `ray`
- `kedro`

Treat this as a late-stage stress test only after the earlier batches have
already shown useful signal.

## What to record for each repository

For each repository, record:

- repository name and commit or tag sampled
- dependency workflow shape detected
- manifest files present
- lockfiles present or absent
- whether `deps:inventory` produced useful evidence
- whether `deps:plan` produced useful planning output
- whether `upgrade` was supported by the detected strategy
- whether post-upgrade verification succeeded
- failure classification when verification failed
- whether the batch changed the current hypothesis

## Current working hypothesis updates

Update the hypothesis after each batch instead of waiting for a single large
summary.

Recommended hypothesis progression:

- After Batch 1:
  workflow detection is good enough for common library and framework repos
- After Batch 2:
  strategy detection plus plan artifacts improve operator understanding across
  a wider set of real packaging styles
- After Batch 3:
  the workflow remains useful under larger dependency graphs and compiled
  ecosystems
- After Batch 4:
  the approach still stays simpler than bespoke wrappers on tooling-centric
  repositories
- After Batch 5:
  the system is either ready for broader validation or should narrow back to
  the smaller shapes it can justify

## Initial execution recommendation

Start with this reduced first wave if time is limited:

- `requests`
- `pytest`
- `pydantic`
- `fastapi`
- `flask`
- `django`
- `pandas`
- `numpy`

That set gives broad coverage early:

- foundational libraries
- modern typed application libraries
- web frameworks
- scientific-stack pressure tests

## Keep the experiment honest

Do not mark the experiment successful just because detection ran.

The current phase only earns more investment if:

- the detected strategy is accurate often enough to trust
- the artifacts improve understanding versus raw tool output
- supported upgrade paths remain ecosystem-native
- verification still works often enough to justify the added workflow

If the results show that most repositories fall into unsupported or
repository-specific flows, narrow the scope instead of adding abstraction too
quickly.

## Current execution signal

Current temporary proving runs under
`C:\dev\polyglot-devcontainers\.tmp\python-proving-batch1` and
`C:\dev\polyglot-devcontainers\.tmp\python-proving-batch2` suggest:

- Batch 1 collapsed into three shapes: `uv-lock`, `plain-pyproject`, and
  `pyproject-exact-pins`
- `click`, `fastapi`, `flask`, and later `typer` all completed `upgrade` and
  still passed native `pytest` verification
- `urllib3` exposed a `uv-lock` resolver blocker caused by project-name
  shadowing
- `pydantic` exposed a `uv-lock` build-environment blocker caused by missing
  Rust/Cargo support
- `httpx` exposed a `pyproject-exact-pins` failure mode where exact-pin
  rewriting can create a dependency set that no longer satisfies the full
  declared `requires-python` range

Treat those results as the current hypothesis update:

- workflow detection is already useful on real public repositories
- `uv-lock` is the strongest currently supported upgrade path
- `pyproject-exact-pins` is still experimental and should not yet be treated as
  broadly safe without additional Python-version compatibility checks
