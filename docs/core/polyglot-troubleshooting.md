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

## `gh` says you are not logged in inside the maintainer container

Recommended response:
- use `task maintainer:gh -- ...` instead of opening an interactive `gh auth login`
- supply `GH_TOKEN` or `GITHUB_TOKEN` on the host, or rely on the host Git
  credential store for the repository HTTPS remote
- treat any plan to write credentials into the repository or container home as
  a bug

## `task` says there is no Taskfile in a published starter image

Recommended response:

- confirm the image is a published starter image and the workspace is mounted
- if the workspace is empty, run `task init`
- use `man polyglot` and `man polyglot-starters` before inventing a custom
  bootstrap path

## `task init` installs many Python or Node packages

Recommended response:

- treat this as expected starter bootstrap behavior
- distinguish between image-level tooling and project-local dependencies
- let `task init` finish before evaluating the starter workspace

## `task scan` reports Git repository discovery errors in a fresh workspace

Recommended response:

- use a starter image version that falls back cleanly outside Git repositories
- initialize Git later if your project needs it
- treat Git as optional for starter bootstrap, not a prerequisite

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

## `man polyglot` is missing in a starter image

Recommended response:

- use a starter image release that ships runtime docs in the image
- if you are validating the repository workspace itself, rebuild the docs with
  `python scripts/build_runtime_docs.py`
- treat missing runtime docs in a published starter image as a repository bug

# GUIDANCE

- prefer narrowing the problem before expanding the toolchain
- keep the validated task contract as the anchor
- use local runtime docs first, then deeper repository docs if needed

# SEE ALSO

- `polyglot(7)`
- `polyglot-task-contract(7)`
- `polyglot-starters(7)`
- `polyglot-agents(7)`
