---
id: KB-2026-043
type: standard
status: published
created: 2026-04-29
updated: 2026-04-29
tags: [starters, ui, service, generator, kbpd]
related:
  - KB-2026-030-starter-generator-service-design-space.md
  - KB-2026-031-starter-generator-knowledge-gaps-and-learning-cycles.md
  - KB-2026-041-generated-starter-scenario-proof-should-run-in-the-generated-workspace.md
---

# Minimal Local Starter UI Should Stay Thin Over The Catalog

## Context

Once the starter catalog and proof lanes were working, the next step was a
local website. The main risk was rebuilding generation logic inside the UI
layer before the catalog contract was stable enough to deserve multiple
implementations.

## Decision

Make the first local website a thin control plane over the existing catalog
module.

The UI may:

- list starters, profiles, modes, and published image metadata
- choose an output directory
- submit generation requests

The UI should not:

- duplicate starter resolution logic
- invent a second starter schema
- become the authoritative place for proof orchestration

## Why This Is The Right Standard Now

- it keeps the learning loop focused on the catalog contract
- it makes the UI cheap to change while the starter surface is still evolving
- it leaves room to publish the same service later without rewriting starter
  behavior

## Evidence

- `scripts/starter_site.py` serves catalog metadata and generation through a
  minimal stdlib HTTP service
- `starters/site/` contains a small local web UI that consumes those endpoints
- generation requests still route through the same `starter_catalog` functions
  used by the CLI

## Applicability

### This Standard Applies To

- the first local starter website
- future hosted starter sites that can reuse the same service contract

### This Standard Does Not Yet Apply To

- rich asynchronous proof dashboards
- hosted multi-user workflow orchestration
- server-side state beyond catalog reads and generation requests
