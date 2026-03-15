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

Current scope:

- Python templates and published-image examples update exact-pinned Python dev
  dependencies from PyPI, then rerun the task contract
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

- `.artifacts/scans/pypi-upgrades.json`

Java upgrade artifacts are written to:

- `.artifacts/scans/gradle-dependency-updates.json`

## Interpret the results

- `pip-audit.json` and `pnpm-audit.json` contain dependency findings.
- `pypi-upgrades.json` records the current and latest Python package versions
  considered by the upgrade workflow.
- `gradle-dependency-updates.json` records the dependency update report produced
  before Java upgrades are applied.
- `gitleaks.sarif` is suitable for code scanning tools and editors that support
  SARIF.
