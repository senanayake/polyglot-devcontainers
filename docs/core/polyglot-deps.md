---
title: polyglot-deps
section: 7
header: Polyglot Devcontainers
footer: Runtime Documentation
---

# NAME

polyglot-deps - dependency evidence, planning, reporting, and upgrade flow

# PURPOSE

This page explains the dependency-maintenance helper workflow.

# WHEN TO USE

Read this page when you want to inspect dependency state before mutating the
workspace.

# PRIMARY COMMANDS

```bash
task deps:inventory
task deps:plan
task deps:report
task upgrade
```

# WORKFLOW

The current helper flow is:

1. `deps:inventory`
2. `deps:plan`
3. `deps:report`
4. `upgrade`
5. `task ci`

`deps:report` is the compressed operator-facing view over the underlying
inventory and plan artifacts.

# OUTPUTS / ARTIFACTS

Common files:

- `dependency-inventory.json`
- `dependency-plan.json`
- `dependency-report.json`
- `dependency-report.md`

At the repository root, `task deps:report` also produces an aggregate report
over the Python and Java proving paths.

# COMMON FAILURES

- Reading only the raw scanner output and ignoring the normalized report.
- Treating `upgrade` as safe without inspecting the plan first.

# GUIDANCE

- Use `deps:report` when you want the shortest useful view.
- Use `dependency-plan.json` when you need the detailed machine artifact.
- Prefer the normalized report over ad hoc interpretation of mixed tool output.

# SEE ALSO

- `polyglot-security(7)`
- `polyglot-python(7)`
- `polyglot-java(7)`
- `polyglot-task-contract(7)`
