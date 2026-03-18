---
title: polyglot-java
section: 7
header: Polyglot Devcontainers
footer: Runtime Documentation
---

# NAME

polyglot-java - Java starter and maintenance workflow

# PURPOSE

This page explains the supported Java workflow in polyglot-devcontainers.

# WHEN TO USE

Read this page when working in Java starters or Java proving paths.

# PRIMARY COMMANDS

```bash
task init
task ci
task deps:plan
task deps:report
```

# WORKFLOW

The current Java path is Gradle-first.

Safe default workflow:

1. open the container
2. run `task init`
3. do the work
4. run `task ci`

Dependency-oriented workflow:

1. run `task deps:inventory`
2. run `task deps:plan`
3. run `task deps:report`
4. use `task upgrade` when you want the validated Gradle update path
5. rerun `task lint`, `task test`, and `task scan`

# OUTPUTS / ARTIFACTS

Java paths may write:

- `trivy-java.json`
- `gitleaks.sarif`
- `dependency-inventory.json`
- `dependency-plan.json`
- `dependency-report.json`
- `dependency-report.md`
- `gradle-dependency-updates.json`

# COMMON FAILURES

- Treating the raw Gradle updates plugin output as the only source of truth.
- Forgetting to rerun the full task workflow after version changes.
- Ignoring scan artifacts after a dependency update.

# GUIDANCE

- Let the task workflow drive Gradle operations unless you have a specific
  reason not to.
- Prefer normalized report artifacts when triaging multiple update candidates.
- Keep the verification loop intact after dependency changes.

# SEE ALSO

- `polyglot(7)`
- `polyglot-task-contract(7)`
- `polyglot-deps(7)`
- `polyglot-security(7)`
- `polyglot-knowledge(7)`
