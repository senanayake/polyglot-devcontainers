---
title: polyglot-task-contract
section: 7
header: Polyglot Devcontainers
footer: Runtime Documentation
---

# NAME

polyglot-task-contract - the validated workflow contract

# PURPOSE

This page defines the standard task workflow used by the repository and its
starters.

# WHEN TO USE

Read this page whenever you need to know the supported commands or the
completion bar.

# PRIMARY COMMANDS

```bash
task init
task lint
task test
task scan
task ci
```

Optional helpers may also exist:

```bash
task format
task deps:inventory
task deps:plan
task deps:report
task upgrade
```

# WORKFLOW

- `task init`
  Bootstrap the local environment.
- `task lint`
  Run code quality and type checks.
- `task test`
  Run automated tests.
- `task scan`
  Run security checks and write artifacts.
- `task ci`
  Run the full validated workflow.

# OUTPUTS / ARTIFACTS

The main artifact convention is:

```text
.artifacts/scans/
```

Dependency-maintenance paths may also write:

- `dependency-inventory.json`
- `dependency-plan.json`
- `dependency-report.json`
- `dependency-report.md`

# COMMON FAILURES

- Declaring work complete after `lint` or `test` without running `scan`.
- Using helper tasks as a replacement for `task ci`.

# GUIDANCE

- The safe default completion bar is `task ci`.
- Use helper tasks to inspect or prepare changes, not to bypass verification.
- Keep artifact locations stable and inspectable.

# SEE ALSO

- `polyglot(7)`
- `polyglot-security(7)`
- `polyglot-deps(7)`
- `polyglot-agents(7)`
