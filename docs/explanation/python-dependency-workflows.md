# Python Dependency Workflows

The Python dependency maintenance experiment cannot assume that every repository
uses the same packaging workflow.

The current evidence path therefore starts by detecting the repository shape
before it tries to plan or apply upgrades.

## Why detection comes first

Recent repository sampling showed at least four recurring workflow shapes:

- `uv-lock`
- `pip-tools`
- `pyproject-exact-pins`
- `plain-pyproject`

Those shapes imply different sources of truth:

- `uv-lock`: `uv.lock` is the resolved dependency state
- `pip-tools`: `requirements.in` is intent and compiled `requirements.txt` is
  the pinned output
- `pyproject-exact-pins`: exact pins in `pyproject.toml` can be compared
  directly against PyPI
- `plain-pyproject`: the repository has a manifest but no clear lockfile-based
  upgrade strategy

Treating all of those as one workflow would produce misleading evidence and
unsafe upgrade behavior.

## Evidence from real repositories

The experiment sampled real public repositories and found:

- `pallets/itsdangerous`: `uv-lock`
- `cookiecutter/cookiecutter`: `uv-lock`
- `jazzband/pip-tools`: `pip-tools`
- `pypa/sampleproject`: `plain-pyproject`

Additional ecosystem sampling across projects such as NumPy, pandas, Flask,
FastAPI, Celery, SQLAlchemy, Requests, Django, matplotlib, and scikit-learn
showed that:

- `pyproject.toml` is now common
- dependency groups and optional dependencies are common
- lockfiles are common in some workflows, but not universal
- requirements files often remain in use for docs, CI, or compile-based flows

## Current adapter boundary

The current Python evidence path supports:

- `uv-lock`
- `pip-tools`
- `pyproject-exact-pins`

It detects but does not auto-upgrade:

- `plain-pyproject`

That boundary is intentional. The experiment should only automate workflows
that it can represent honestly.

## What the artifacts mean

`dependency-inventory.json` records:

- the detected strategy
- the files that define dependency intent and lock state
- the currently declared or locked dependencies used as evidence

`dependency-plan.json` records:

- the detected strategy
- the current and target versions the adapter can actually justify
- whether a change would be applied by the current adapter

`pypi-upgrades.json` records:

- the concrete changes applied by the current adapter
- the files updated as part of that workflow

## Why this matters

The point of the current phase is not to build a universal Python upgrader.

The point is to prove that:

- the repository can detect real Python workflow shapes
- the evidence path can stay honest about what it knows
- upgrade automation can remain native to the workflow instead of inventing a
  fake abstraction too early
