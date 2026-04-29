---
id: KB-2026-045
type: standard
status: published
created: 2026-04-29
updated: 2026-04-29
tags: [starters, hosting, deployment, public-service, kbpd]
related:
  - KB-2026-030-starter-generator-service-design-space.md
  - KB-2026-029-free-local-baseline-vs-robust-remote-control-plane.md
  - KB-2026-043-minimal-local-starter-ui-should-stay-thin-over-the-catalog.md
  - KB-2026-044-local-starter-site-should-use-explicit-host-lifecycle-tasks.md
---

# Public Starter Service Should Launch With A Hosted Derivative

## Context

The local starter website is now useful for host-side testing, but it still
inherits the trust assumptions of a maintainer workstation. The next question
was how to publish a public starter surface that can promote adoption without
exposing the local generation model directly to the internet.

## Decision

Launch a hosted derivative of the starter service rather than publishing the
local site implementation as-is.

Recommended deployment order:

1. `Cloud Run` generation API
2. `Cloudflare Pages` public UI
3. `Cloudflare R2` downloadable artifact storage
4. Later convergence toward `Cloudflare Workers + R2` if generation logic is
   lightweight enough to justify a runtime rewrite

## Why This Is The Right Standard Now

- it preserves the current Python generator and avoids an early rewrite
- it creates a credible public product quickly
- it isolates internet-facing concerns from maintainer-container proof paths
- it keeps the public contract centered on released catalog snapshots and
  downloadable artifacts

## Evidence

- the current local website only exposes catalog read and generation endpoints
  from `scripts/starter_site.py`
- the current generator writes local workspaces and assumes trusted filesystem
  access through `scripts/starter_catalog.py`
- Cloudflare offers a cheap static edge path and low-cost object storage
- Cloud Run is a strong fit for the current Python service shape with a generous
  request-based free tier
- GitHub Pages is explicitly a poor fit for a SaaS-style generator surface

## Applicability

### This Standard Applies To

- the first public deployment of the starter generator
- hosted starter-download experiences that expose released starter artifacts

### This Standard Does Not Mean

- the local site should be discarded
- public proof orchestration should be added immediately
- the repository must commit to a single vendor forever
