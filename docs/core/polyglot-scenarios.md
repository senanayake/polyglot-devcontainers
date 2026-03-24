---
title: polyglot-scenarios
section: 7
header: Polyglot Devcontainers
footer: Runtime Documentation
---

# NAME

polyglot-scenarios - repo-owned executable scenario proving slices

# PURPOSE

This page explains the first executable scenarios shipped in the repository.

# WHEN TO USE

Read this page when you want a runnable pattern that ties runtime guidance,
task execution, evidence artifacts, and verification together.

# PRIMARY COMMANDS

```bash
task scenarios:python-maintenance
task scenarios:java-maintenance
task scenarios:verify
```

# WORKFLOW

The current scenario slice stays deliberately small.

It uses two repo-owned maintenance examples:

- Python dependency maintenance with the `uv-lock` strategy
- Java dependency maintenance with the Gradle-first update path

Each scenario:

1. runs through existing task commands in the proving workspace
2. checks the expected evidence and report artifacts
3. writes a scenario result artifact under `.artifacts/scenarios/`

The scenarios are thin wrappers over the existing task contract.

They are not a new workflow system.

# OUTPUTS / ARTIFACTS

Scenario run artifacts:

- `.artifacts/scenarios/python-uv-lock-maintenance.json`
- `.artifacts/scenarios/python-uv-lock-maintenance.md`
- `.artifacts/scenarios/java-gradle-maintenance.json`
- `.artifacts/scenarios/java-gradle-maintenance.md`

Underlying scenario workspaces still write their normal artifacts under:

```text
.artifacts/scans/
```

# COMMON FAILURES

- Running the scenario outside the maintainer container.
- Treating scenarios as a replacement for `task ci`.
- Expecting the current scenarios to apply to arbitrary downstream repos.
- Ignoring the underlying dependency artifacts after the scenario passes.

# GUIDANCE

- Use the current scenarios as executable examples of the `evidence -> plan ->
  execution` model.
- Start with the maintenance examples because they are the current proving set.
- Treat `task upgrade` as the follow-on execution step after you have inspected
  the scenario evidence.
- Keep the scenario layer small until a few slices prove useful in practice.

# SEE ALSO

- `polyglot(7)`
- `polyglot-python(7)`
- `polyglot-java(7)`
- `polyglot-deps(7)`
- `polyglot-task-contract(7)`
