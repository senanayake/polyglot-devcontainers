---
id: KB-2026-046
type: standard
status: published
created: 2026-04-30
updated: 2026-04-30
tags: [starters, public-service, releases, artifacts, kbpd]
related:
  - KB-2026-045-public-starter-service-should-launch-with-a-hosted-derivative.md
  - KB-2026-043-minimal-local-starter-ui-should-stay-thin-over-the-catalog.md
  - KB-2026-041-generated-starter-scenario-proof-should-run-in-the-generated-workspace.md
---

# Public Starter Downloads Should Come From Released Snapshots

## Context

Once the deployment brief was clear, the remaining contract gap was how the
internet-facing generator should choose its source of truth. The local site was
still reading live branch catalog state and writing local workspaces, which is
acceptable for host-side development but too loose for a public download
surface.

## Decision

Generate public starter downloads only from released catalog snapshots, and
serve them as versioned zip artifacts.

The public contract should:

- require `catalog_version`
- resolve starter/profile/mode only from a released snapshot
- return artifact metadata and a download URL
- reject arbitrary output paths and maintainer-local controls

## Why This Is The Right Standard Now

- it makes the public service reproducible across deployments
- it prevents branch drift from changing public downloads unexpectedly
- it keeps the local site useful for development without making it the public
  trust boundary
- it creates a clean handoff between release engineering and hosting

## Evidence

- `scripts/starter_catalog.py` now exports and loads released catalog snapshots
- `scripts/starter_catalog.py` now builds deterministic zip artifacts with
  embedded stable metadata
- `scripts/starter_site.py` now exposes `GET /api/public/catalog`,
  `GET /api/public/catalog/<version>`, `POST /api/public/generate`, and
  `GET /api/public/download/<version>/<artifact_id>`
- `scripts/validate_public_starter_api.py` proves:
  - valid source-template and image-backed requests succeed
  - unsupported request fields are rejected
  - missing catalog versions are rejected
  - download artifacts do not leak host filesystem paths

## Applicability

### This Standard Applies To

- hosted starter generator deployments
- downloadable starter artifacts published for users and agents

### This Standard Does Not Replace

- the live branch catalog used for local development
- maintainer-container proof workflows such as `task starters:prove`
