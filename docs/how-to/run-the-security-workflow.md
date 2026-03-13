# Run the Security Workflow

The repository integrates security into the default engineering loop.

## Run all checks

```bash
task scan
```

## Find the artifacts

Python example artifacts are written to:

- `examples/python-example/.artifacts/scans/pip-audit.json`
- `examples/python-example/.artifacts/scans/gitleaks.sarif`

Node template artifacts are written to:

- `.artifacts/scans/pnpm-audit.json`
- `.artifacts/scans/gitleaks.sarif`

## Interpret the results

- `pip-audit.json` and `pnpm-audit.json` contain dependency findings.
- `gitleaks.sarif` is suitable for code scanning tools and editors that support
  SARIF.
