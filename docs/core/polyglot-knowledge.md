---
title: polyglot-knowledge
section: 7
header: Polyglot Devcontainers
footer: Runtime Documentation
---

# NAME

polyglot-knowledge - curated engineering and security guidance

# PURPOSE

This page provides a compact baseline of engineering judgment for humans and
agents working inside the container.

It adapts durable ideas from strong software engineering and security sources
into practical guidance for this environment.

# WHEN TO USE

Read this page when a task requires judgment rather than just mechanics.

# GUIDANCE

## Principle: verify through the real workflow

Why it matters:

Changes are only trustworthy when they pass through the same workflow the
environment expects.

How it applies here:

- use the container
- use the task contract
- treat `task ci` as the default proof bar

Failure mode:

- code appears correct in an ad hoc run but fails in the validated workflow

Recommended behavior:

- verify with the real task path before declaring success

## Principle: keep the source of truth explicit

Why it matters:

Ambiguous state leads to fragile automation and risky edits.

How it applies here:

- Python uses `pyproject.toml` plus `uv.lock`
- dependency artifacts live under `.artifacts/scans/`
- runtime docs should explain the supported workflow locally

Failure mode:

- tooling guesses intent from partial or stale information

Recommended behavior:

- prefer explicit manifests, lockfiles, and stable artifact conventions

## Principle: security belongs in the normal loop

Why it matters:

Security work fails when it is treated as a separate phase with weak feedback.

How it applies here:

- scans are part of `task ci`
- dependency and secret findings should be inspected as normal engineering work

Failure mode:

- teams test and lint regularly but only scan sporadically

Recommended behavior:

- keep scan output in the standard loop and inspect the artifacts

## Principle: start simple, then evolve

Why it matters:

Overbuilt systems become harder to trust and harder to maintain.

How it applies here:

- prefer the smallest working starter
- add helper flows only when they remove real friction
- keep experiments thin until they prove their value

Failure mode:

- architecture expands faster than the evidence that justifies it

Recommended behavior:

- evolve from working systems instead of designing abstraction first

## Principle: make decisions inspectable

Why it matters:

Humans and agents both make better decisions when the evidence is visible.

How it applies here:

- use structured dependency reports
- keep artifact paths stable
- prefer explicit guidance over hidden assumptions

Failure mode:

- a result depends on private context or unrecorded reasoning

Recommended behavior:

- leave behind artifacts, reports, and local runtime guidance that others can
  inspect

# SEE ALSO

- `polyglot-agents(7)`
- `polyglot-security(7)`
- `polyglot-deps(7)`
- `polyglot-troubleshooting(7)`
