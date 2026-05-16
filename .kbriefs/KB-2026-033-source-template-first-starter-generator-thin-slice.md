---
id: KB-2026-033
type: standard
status: draft
created: 2026-04-26
updated: 2026-04-26
tags: [starters, generator, standard, proof, kbpd, source-template]
related: [KB-2026-030, KB-2026-031, KB-2026-032]
---

# Source-Template-First Starter Generator Thin Slice

## Context

The repository needed a first implementation slice for a future starter
generator service inspired by `start.spring.io`, but the design space still had
open questions around starter metadata, bootstrap semantics, proof contracts,
and thin image-backed generation.

Rather than building a service or UI first, this experiment implemented the
smallest end-to-end path that could be generated and proven through the
maintainer container.

## Problem

What should the first generator/proof slice look like so that it produces
useful evidence without overcommitting to unresolved product and runtime
contracts?

## Decision

Use a **source-template-first** starter generator thin slice.

The first slice should:

- define a small starter catalog
- generate source-complete workspaces from curated templates
- stamp generated workspaces with machine-readable starter metadata
- prove generated starters headlessly through the task contract
- defer thin image-backed generation as a metadata-only concern until the
  workspace bootstrap contract is broadened

## Why This Works

### Existing Contracts Already Support It

The repository already knows how to validate the curated templates:

- `python-secure`
- `python-node-secure`

Those templates already carry the task contract and, in the case of
`python-node-secure`, starter-local scenarios.

### It Produces Real Evidence

The thin slice proves that one catalog entry can drive:

- starter selection
- workspace generation
- headless execution
- artifact validation

without requiring a web UI, IDE opening, or a new remote control plane.

### It Avoids Premature Convergence

Thin image-backed generation remains partially unresolved because the current
published-image bootstrap path expects an almost-empty workspace. That contract
is narrower than a user-facing starter product and should not be silently
promoted as the general default.

## Evidence

Implemented artifacts:

- `starters/catalog.toml`
- `starters/README.md`
- `scripts/starter_catalog.py`
- root `Taskfile.yml` starter tasks

Validated proof path:

- `task starters:list`
- `task starters:show -- --starter python-secure`
- `task starters:prove -- --all`

Validated starters:

- `python-secure`
- `python-node-secure`

Validated commands:

- generated `python-secure`: `task ci`
- generated `python-node-secure`: `task ci`, `task scenarios:verify`

Related failure discovered during the experiment:

- nested generated starters can accidentally inherit parent Git history scan
  mode if Git ownership checks are too weak
- captured in `KB-2026-032`

## Implications

- The starter catalog can now be treated as a real product surface instead of a
  documentation-only idea.
- Headless proving is viable and should remain the primary correctness contract.
- Thin image-backed starter generation should stay explicitly experimental until
  the workspace bootstrap contract supports a richer initial workspace.

## Recommendations

- Extend the catalog cautiously, one curated starter at a time.
- Keep generation modes explicit in metadata rather than inferred.
- Prefer source-template generation as the default until image-backed starters
  can prove a broader workspace contract.
- Build any future local service or website on top of this proven catalog and
  proof path rather than bypassing it.

## Applicability

Applies to:

- first-class starter generation for curated Polyglot starters
- agentic proof of starter contracts
- local CLI and future service-backed generation

Does not yet apply to:

- arbitrary feature composition
- rich thin image-backed starter products
- hosted UI-first workflows that bypass headless proof
