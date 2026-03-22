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
task maintainer:pull
task maintainer:task -- scan
task scan
task image:discover
task image:verify
task image:scan
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
- published image base refresh evidence
- published image tarball scanning

# OUTPUTS / ARTIFACTS

Common artifacts:

- `pip-audit.json`
- `trivy-java.json`
- `gitleaks.sarif`
- `base-image-report.json`
- `base-image-report.md`
- `image-security/trivy-maintainer.json`
- `image-security/trivy-java.json`
- `image-security/trivy-python-node.json`

# COMMON FAILURES

- Running tests without scans and assuming the environment is healthy.
- Treating vulnerability output as self-explanatory without checking the
  related report artifacts or task context.
- Refreshing a published image base without rebuilding and rescanning the
  published image set.

# GUIDANCE

- Security checks belong in the normal development loop.
- Use structured artifacts when available.
- Prefer the maintainer-container workflow over host-local shortcuts.
- Prefer the published GHCR maintainer image over rebuilding the maintainer image on the host.
- For published images, resolve and pin base digests before rebuilding and
  rescanning the published image set.

# SEE ALSO

- `polyglot-task-contract(7)`
- `polyglot-deps(7)`
- `polyglot-knowledge(7)`
