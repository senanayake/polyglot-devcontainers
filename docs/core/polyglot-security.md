---
title: polyglot-security
section: 7
header: Polyglot Devcontainers
footer: Runtime Documentation
---

# NAME

polyglot-security - security checks and artifact expectations

# PURPOSE

This page explains the security-first operating model of the starters.

# WHEN TO USE

Read this page when you need to understand scans, artifacts, or the repository
security baseline.

# PRIMARY COMMANDS

```bash
task scan
task ci
```

# WORKFLOW

Security checks are part of the standard workflow, not an optional afterthought.

At minimum, supported paths should include:

- dependency vulnerability scanning
- secret scanning
- secure default tooling

Some paths also include:

- Java filesystem vulnerability scanning
- dependency evidence and reporting

# OUTPUTS / ARTIFACTS

Common artifacts:

- `pip-audit.json`
- `trivy-java.json`
- `gitleaks.sarif`

# COMMON FAILURES

- Running tests without scans and assuming the environment is healthy.
- Treating vulnerability output as self-explanatory without checking the
  related report artifacts or task context.

# GUIDANCE

- Security checks belong in the normal development loop.
- Use structured artifacts when available.
- Prefer the container-validated workflow over host-local shortcuts.

# SEE ALSO

- `polyglot-task-contract(7)`
- `polyglot-deps(7)`
- `polyglot-knowledge(7)`
