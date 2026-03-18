---
title: polyglot-troubleshooting
section: 7
header: Polyglot Devcontainers
footer: Runtime Documentation
---

# NAME

polyglot-troubleshooting - common failures in the container workflow

# PURPOSE

This page captures common failure patterns and the preferred recovery path.

# WHEN TO USE

Read this page when the validated starter workflow is blocked.

# COMMON FAILURES

## `task ci` fails unexpectedly

Recommended response:

- identify the failing stage: init, lint, test, or scan
- inspect the related artifacts under `.artifacts/scans/`
- fix the real contract failure before widening the scope

## dependency report output looks incomplete

Recommended response:

- inspect `dependency-inventory.json`
- inspect `dependency-plan.json`
- confirm the path supports `deps:report`

## the host run behaves differently from the container

Recommended response:

- treat the container as the source of truth
- rerun inside the container before drawing conclusions

## a starter is too experimental for the job

Recommended response:

- move back to the relevant starter template
- use proving fixtures only when you need the extra maintenance workflow

# GUIDANCE

- prefer narrowing the problem before expanding the toolchain
- keep the validated task contract as the anchor
- use local runtime docs first, then deeper repository docs if needed

# SEE ALSO

- `polyglot(7)`
- `polyglot-task-contract(7)`
- `polyglot-starters(7)`
- `polyglot-agents(7)`
