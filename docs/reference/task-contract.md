# Task Contract

Every supported repository in this project family must expose these commands:

```bash
task init
task lint
task test
task scan
task ci
```

Some repositories may also expose optional helper tasks such as:

```bash
task format
task deps:inventory
task deps:plan
task upgrade
```

These helpers must extend the standard workflow rather than replace it.

## Meanings

- `init`: bootstrap the development environment
- `lint`: run code quality and type checks
- `test`: run automated tests
- `scan`: run security checks
- `ci`: run the full workflow
- `deps:inventory` (optional): write normalized dependency inventory artifacts
- `deps:plan` (optional): write normalized dependency update planning artifacts
- `upgrade` (optional): run a validated dependency-upgrade workflow and
  re-verify the repository

For Python, the dependency helpers now also emit strategy detection metadata so
the evidence path can distinguish between workflows such as:

- `uv-lock`
- `pip-tools`
- `pyproject-exact-pins`
- `plain-pyproject`

## Phase 1 Python behavior

In the root repository:

- `lint` runs Ruff and MyPy
- `test` runs Pytest with coverage
- `scan` runs `pip-audit` and Gitleaks with artifact output
