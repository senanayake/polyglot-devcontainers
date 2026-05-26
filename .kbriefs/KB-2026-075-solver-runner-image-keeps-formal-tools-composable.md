---
id: KB-2026-075
type: standard
status: accepted
created: 2026-05-26
updated: 2026-05-26
tags:
  - published-images
  - formal-methods
  - solver-runner
related:
  - docs/core/polyglot-solver-runner.md
  - templates/solver-runner/README.md
  - published-image-catalog.toml
---

# Solver Runner Image Keeps Formal Tools Composable

## Context

Downstream projects such as Sententia need Alloy/Kodkod, SAT/SMT tools, and
database clients available in reproducible environments. The earlier pattern was
to extend the Java image privately and install Alloy in project-specific image
logic.

## Problem/Need

Private per-project solver installs make solver receipts harder to compare:
versions, command wrappers, database clients, and smoke checks can drift between
projects. Publishing many narrow solver images up front would create release and
security-maintenance overhead before the useful boundaries are proven.

## Standard/Pattern

Publish one `polyglot-devcontainers-solver-runner` image as the first shared
solver surface.

The first slice includes:

- the research runner's Python and Node harness surface
- Java runtime support
- pinned Alloy 6.2.0 distribution jar with SHA-256 verification
- Z3, cvc5, MiniSat, SQLite, and Postgres client packages from Debian
- deterministic `task ci` smoke checks for Alloy SAT/UNSAT receipts, SMT-LIB
  SAT/UNSAT probes, SQLite execution, and Postgres client availability

## Rationale

This keeps the first solver image broad enough for data-modeling correctness
experiments while staying small enough to validate through the existing
published-image pipeline. It also avoids baking any Sententia-specific
translator, theory, or domain semantics into Polyglot.

## Constraints

- The image is an execution substrate, not a domain-specific correctness engine.
- Solver package versions from Debian may lag upstream solver releases.
- Projects must record solver names, versions, scopes, and options in their own
  receipts when those results inform product decisions.

## Alternatives Considered

### Many Solver-Specific Images

Separate Alloy, SMT, database-modeling, and proof-assistant images would reduce
per-image size, but would multiply CI, release, scan, and documentation work
before the recurring boundaries are understood.

### Sententia-Only Private Image

A private image would move fastest for Sententia, but would keep the core
execution evidence outside the reusable Polyglot image contract.

### Add Solvers To The Java Image

The Java image should remain a JVM engineering base. Adding SAT/SMT/database
tooling there would make a common base image heavier for unrelated Java users.

## Verification

The image must pass:

- catalog validation through `scripts/published_image_pipeline.py`
- devcontainer metadata validation
- published-image smoke bootstrap
- `task ci` inside `templates/solver-runner`

## Related Knowledge

- [Polyglot Solver Runner Image](../docs/core/polyglot-solver-runner.md)
- [Solver Runner Template](../templates/solver-runner/README.md)
- [Published Image Catalog](../published-image-catalog.toml)

