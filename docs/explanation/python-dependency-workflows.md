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

## Current repository policy

The experiment has now reached a stronger policy conclusion for repository-owned
Python paths:

- `uv` and `uv.lock` are the first-class Python dependency workflow in
  `polyglot-devcontainers`
- new Python examples, templates, and future hardening work should prefer
  `uv-lock`
- other detected shapes such as `pip-tools`, `pyproject-exact-pins`, and
  `plain-pyproject` remain compatibility and evidence paths rather than
  equal-priority targets for ongoing optimization

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

## Why the proving set is staged

The next step in Phase 9b is not a single "top Python projects" run.

It is a staged proving set that expands complexity batch by batch.

The staged approach is intentional:

- it keeps the experiment aligned with Gall's Law
- it lets the repository update the hypothesis after each batch
- it makes it easier to separate workflow-shape failures from scale failures
- it avoids overfitting the adapter set to one dramatic but noisy sweep

The current recommended proving batches are:

### Batch 1: Common application and library shapes

- `requests`
- `urllib3`
- `click`
- `pytest`
- `pydantic`
- `fastapi`
- `flask`
- `django`

### Batch 2: Tooling and optional-dependency pressure

- `httpx`
- `rich`
- `typer`
- `sqlalchemy`
- `alembic`
- `celery`
- `black`
- `ruff`

### Batch 3: Large dependency graphs and compiled ecosystems

- `pandas`
- `numpy`
- `scipy`
- `matplotlib`
- `scikit-learn`
- `jupyterlab`

### Batch 4: Packaging and dependency-tooling repos

- `sphinx`
- `mkdocs`
- `poetry`
- `pip-tools`
- `uv`
- `pre-commit`

### Batch 5: Complexity and scale

- `apache-airflow`
- `ansible`
- `django-rest-framework`
- `scrapy`
- `ray`
- `kedro`

The early batches are meant to answer a narrower question first:

can the repository detect real Python dependency workflow shapes and produce
useful plan artifacts on repositories that are important but still tractable?

Only after that is proven is it worth spending effort on the scientific stack,
tooling-heavy repos, or very large operational frameworks.

## Initial Batch 1 signal

An initial Batch 1 execution against these repositories:

- `requests`
- `urllib3`
- `click`
- `pytest`
- `pydantic`
- `fastapi`
- `flask`
- `django`

produced three important signals.

First, the batch collapsed into a small number of workflow shapes:

- `uv-lock`: `urllib3`, `click`, `pydantic`, `fastapi`, `flask`
- `plain-pyproject`: `pytest`, `django`
- `pyproject-exact-pins`: `requests`

Second, a real adapter bug surfaced early: environment-marked requirement
specifiers were initially being treated as package names. Fixing that bug
reclassified `pytest` and `django` from `pyproject-exact-pins` to the more
honest `plain-pyproject` path.

Third, the current `uv-lock` path appears promising but not universally
portable yet:

- `click`, `fastapi`, and `flask` produced real plan artifacts successfully
- `urllib3` failed because `uv lock --upgrade` ran into a self-shadowing
  resolution problem
- `pydantic` failed because the upgrade path required a Rust toolchain in the
  current environment

An initial deeper execution pass also showed that the path is not merely able
to plan changes:

- `click` completed `upgrade` and its native `pytest` suite still passed
- `fastapi` completed `upgrade` and its native `pytest` suite still passed
- `flask` completed `upgrade` and its native `pytest` suite still passed
- `requests` still had one failing TLS certificate-path test, but that happened
  with zero planned updates, so the result is evidence of an environment issue
  rather than an upgrade regression

That is still useful evidence.

It suggests the next hypothesis should be:

- workflow detection is already strong enough to classify common public Python
  repositories into a small number of real shapes
- the current `plain-pyproject` path is honest but intentionally low-action
- the current `uv-lock` path can produce useful plans on real repositories, but
  environment and resolver constraints still need to be characterized before it
  can be treated as broadly reliable

## Initial Batch 2 signal

An initial Batch 2 execution against these repositories:

- `httpx`
- `rich`
- `typer`
- `sqlalchemy`
- `alembic`
- `celery`
- `black`
- `ruff`

also collapsed into a small number of shapes:

- `uv-lock`: `typer`
- `plain-pyproject`: `rich`, `celery`, `ruff`
- `pyproject-exact-pins`: `httpx`, `sqlalchemy`, `alembic`, `black`

That is useful because the second batch broadened repository style without
exploding the number of strategies the experiment needs to reason about.

The initial Batch 2 execution also produced two important proving outcomes:

- `typer` completed `upgrade` and its native `pytest` suite still passed
- `httpx` completed the current `pyproject-exact-pins` rewrite, but native
  verification then failed during environment resolution because the updated
  exact pin on `click` no longer fit the repository's declared
  `requires-python` range

That result sharpens the current hypothesis:

- `uv-lock` remains the strongest currently supported upgrade path
- `plain-pyproject` is still honest but intentionally low-action
- `pyproject-exact-pins` can produce useful plans, but exact-pin rewriting is
  not yet safe enough to treat as a generally reliable upgrade path for
  multi-Python repositories

That is also enough to justify a repository-level default:

- standardize the repository's Python-first path around `uv` and `uv.lock`
- keep the other shapes detectable so the evidence path remains honest
- only broaden first-class support again if another workflow earns comparable
  proof

## Current adapter boundary

The current Python evidence path supports:

- `uv-lock`
- `pip-tools`
- `pyproject-exact-pins`

It detects but does not auto-upgrade:

- `plain-pyproject`

That boundary is intentional. The experiment should only automate workflows
that it can represent honestly.

But the support levels are no longer equal:

- `uv-lock` is the primary supported path going forward
- `pip-tools` and `pyproject-exact-pins` are compatibility paths
- `plain-pyproject` remains detect-only

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
- the experiment can update its own hypothesis as each proving batch reveals
  new workflow shapes and failure modes
