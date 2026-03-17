# Run the Security Workflow

The repository integrates security into the default engineering loop.

## Run all checks

```bash
task scan
```

## Run the dependency upgrade workflow

Where implemented, use:

```bash
task upgrade
```

This performs the ecosystem-specific dependency upgrade workflow and then
re-verifies the workspace.

Where implemented, you can also inspect the dependency evidence and plan before
mutating the workspace:

```bash
task deps:inventory
task deps:plan
```

For Python, these artifacts now include a `strategy_detection` section that
records the detected workflow shape, such as:

- `uv-lock`
- `pip-tools`
- `pyproject-exact-pins`
- `plain-pyproject`

Current scope:

- Python templates and published-image examples detect the repository workflow
  shape and currently treat `uv-lock` as the first-class upgrade path
- Python compatibility workflows such as `pip-tools` and
  `pyproject-exact-pins` may still produce evidence and limited upgrade support,
  but they are no longer equal-priority optimization targets
- Java templates and published-image examples generate a Gradle dependency
  update report, apply stable version updates, refresh lockfiles, and rerun the
  relevant verification steps

## Find the artifacts

Python example artifacts are written to:

- `examples/python-example/.artifacts/scans/pip-audit.json`
- `examples/python-example/.artifacts/scans/gitleaks.sarif`

Node template artifacts are written to:

- `.artifacts/scans/pnpm-audit.json`
- `.artifacts/scans/gitleaks.sarif`

Python upgrade artifacts are written to:

- `.artifacts/scans/dependency-inventory.json`
- `.artifacts/scans/dependency-plan.json`
- `.artifacts/scans/pypi-upgrades.json`

Java upgrade artifacts are written to:

- `.artifacts/scans/dependency-inventory.json`
- `.artifacts/scans/dependency-plan.json`
- `.artifacts/scans/gradle-dependency-updates.json`

## Interpret the results

- `pip-audit.json` and `pnpm-audit.json` contain dependency findings.
- `dependency-inventory.json` records the currently declared or locked
  dependencies used as the basis for later planning.
- `dependency-plan.json` records the currently known update candidates before
  any files are changed, including the detected workflow strategy where
  available.
- `pypi-upgrades.json` records the current and latest Python package versions
  considered by the upgrade workflow.
- `gradle-dependency-updates.json` records the dependency update report produced
  before Java upgrades are applied.
- `gitleaks.sarif` is suitable for code scanning tools and editors that support
  SARIF.
