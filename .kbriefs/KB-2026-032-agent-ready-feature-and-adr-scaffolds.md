---
id: KB-2026-032
type: standard
status: validated
created: 2026-04-24
updated: 2026-04-24
tags: [scaffolding, features, adr, testing, traceability, agents]
related: [KB-2026-029, KB-2026-030, KB-2026-031]
---

# Agent-Ready Feature And ADR Scaffolds

## Context

The repository needed a repeatable way to scaffold new OCI features and
architecture decisions without losing testing intent, traceability, or KBPD
context.

## Problem/Need

Ad hoc scaffolding causes teams and agents to recreate the same structure from
memory, which weakens consistency and leaves requirements, decisions, and tests
disconnected.

## Standard/Pattern

### Description

Use explicit repository tasks to scaffold new features and ADRs:

```bash
task init:feature -- "<feature name>"
task init:adr -- "Short decision title"
```

### Key Principles

- scaffold requirements, executable specification, and traceability together
- make BDD artifacts first-class for externally visible behavior
- make ADRs first-class for durable architectural choices

### Implementation

- `task init:feature` creates feature metadata, installer stub, README,
  requirements, Gherkin acceptance spec, traceability map, and executable test
  placeholders
- `task init:adr` creates a numbered ADR in `docs/explanation/decisions/` and
  updates the index
- starter project scaffolding now creates `docs/explanation/decisions/` and
  teaches agents where ADRs belong

## Rationale

This approach is preferred because it encodes product-development knowledge in
the repository surface itself rather than expecting agents to infer it from
prior chats or maintainer memory.

## Benefits

- new features begin with a requirement/spec/test chain
- architectural decisions become discoverable and linkable
- agents get a consistent starting point for disciplined work

## Constraints

- scaffold output is intentionally incomplete and expects project-specific
  refinement
- generated install stubs and placeholder specs must be replaced before a new
  feature is production-ready

## Alternatives Considered

### Minimal Code-Only Scaffold

- creates less upfront structure
- was not chosen because it hides the testing and traceability intent

### Documentation-Only Guidance

- cheaper to publish
- was not chosen because it relies on humans or agents to remember the shape

## Evidence

- the repository now contains reusable scaffold assets under `assets/`
- root tasks expose stable entry points for feature and ADR creation
- starter conventions now include an ADR directory and guidance

## Anti-Patterns

- creating a feature with only `devcontainer-feature.json` and `install.sh`
- recording a major design choice only in a pull request description
- adding BDD, requirements, or traceability artifacts only after the feature is
  already implemented

## Verification

- `task init:feature` should create the full scaffolded directory shape
- `task init:adr` should create a numbered ADR and update the README index
- starter bootstrap should create the decisions directory in fresh workspaces

## Exceptions

- tiny private experiments may skip ADRs
- a feature can defer option-specific acceptance scenarios until it actually
  gains options

## Applicability

### Use This Standard When

- adding a new repository-owned feature
- introducing a durable architectural choice
- bootstrapping work that an AI agent will continue

### Don't Use This Standard When

- making a one-line typo fix
- recording ephemeral execution details that do not need a permanent home

## Maintenance

- review the scaffold whenever the task contract or testing taxonomy changes
- extend traceability assets only when the repository proves a new need

## Related Knowledge

- `docs/how-to/scaffold-a-feature.md`
- `docs/how-to/record-an-architecture-decision.md`
- `docs/reference/testing-taxonomy.md`

## Success Metrics

- new features include requirement/spec/test assets by default
- new ADRs are created through the scaffold instead of ad hoc files
- repo changes increasingly link decisions to K-Briefs and tests
