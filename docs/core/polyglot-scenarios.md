---
title: polyglot-scenarios
section: 7
header: Polyglot Devcontainers
footer: Runtime Documentation
---

# NAME

polyglot-scenarios - executable scenario proving slices for the repo and starters

# PURPOSE

This page explains the executable scenarios currently shipped in the repository
and in the `python-node-secure` starter.

# WHEN TO USE

Read this page when you want a runnable pattern that ties runtime guidance,
task execution, evidence artifacts, and verification together.

# PRIMARY COMMANDS

```bash
# repository root
task scenarios:python-maintenance
task scenarios:python-audit-policy
task scenarios:java-maintenance
task scenarios:verify

# python-node-secure starter
task scenarios:starter-health
task scenarios:security-evidence
task scenarios:non-git-scan-fallback
task scenarios:verify
```

# WORKFLOW

The current scenario surface stays deliberately small.

Repository root proving slices:

- Python dependency maintenance with the `uv-lock` strategy
- Python audit-policy review for structured package-audit decisions
- Java dependency maintenance with the Gradle-first update path

Starter-local proving slices in `python-node-secure`:

- starter health through the standard task contract
- security evidence review
- non-git secret-scan fallback

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
- `.artifacts/scenarios/python-audit-policy.json`
- `.artifacts/scenarios/python-audit-policy.md`
- `.artifacts/scenarios/java-gradle-maintenance.json`
- `.artifacts/scenarios/java-gradle-maintenance.md`
- `.artifacts/scenarios/starter-health.json`
- `.artifacts/scenarios/starter-health.md`
- `.artifacts/scenarios/security-evidence.json`
- `.artifacts/scenarios/security-evidence.md`
- `.artifacts/scenarios/non-git-scan-fallback.json`
- `.artifacts/scenarios/non-git-scan-fallback.md`

Underlying scenario workspaces still write their normal artifacts under:

```text
.artifacts/scans/
```

# COMMON FAILURES

- Running the scenario outside the maintainer container.
- Treating scenarios as a replacement for `task ci`.
- Expecting the current scenarios to apply to arbitrary downstream repos.
- Ignoring the underlying dependency artifacts after the scenario passes.
- Hard-coding a scenario to today's advisory count instead of stable artifact
  structure.
- Treating the non-git starter scenario as if it proved the repo-root
  maintainer path.

# GUIDANCE

- Use the current scenarios as executable examples of the `evidence -> plan ->
  execution` model.
- Start with the maintenance examples when you are working on the repository
  itself.
- Use the Python audit-policy scenario when you want the repo-owned review path
  for `pip-audit-policy.json` and `pip-audit-policy.md`.
- In `python-node-secure`, use the starter-local scenarios when you want proof
  inside the user container rather than the maintainer repo fixture.
- Treat `task upgrade` as the follow-on execution step after you have inspected
  the scenario evidence.
- Keep the scenario layer small until a few slices prove useful in practice.

# SEE ALSO

- `polyglot(7)`
- `polyglot-python(7)`
- `polyglot-java(7)`
- `polyglot-deps(7)`
- `polyglot-task-contract(7)`
