---
id: KB-2026-065
type: standard
status: active
created: 2026-05-03
updated: 2026-05-03
tags:
  - images
  - release
  - integration
  - github-actions
  - ci
  - kbpd
related:
  - KB-2026-038
  - KB-2026-063
  - KB-2026-064
---

# Mainline Integration Publication And Semver Release Should Use Separate Channels

## Context

The repository needs two different kinds of image availability:

- fast-moving images from merged `main` for downstream integration loops
- slower, stronger semver releases with heavyweight proof and release-security
  evidence

Trying to satisfy both goals in one image-publication channel weakens one of
them:

- either fast loops become too slow
- or release semantics become too loose

## Decision

Use two separate channels.

### Mainline Integration Channel

Owned by `.github/workflows/ci.yml` on pushes to `main`.

Properties:

- medium proof is the publication gate
- publishes workload images only
- publishes moving `main` tags
- publishes immutable SHA tags
- does not publish `latest`
- does not create release notes
- does not create release-security docs

### Release Channel

Owned by `.github/workflows/release-images.yml` and `.github/workflows/cut-release.yml`.

Properties:

- full-release proof is the publication gate
- publishes semver tags
- publishes `latest`
- runs release-side effects such as release notes and release-security docs
- remains the channel for signed, attested, semver image releases

## Implementation

### `ci.yml`

- now runs on branch pushes including `main`
- keeps the existing repo-core plus medium matrix proof shape
- on `main`, adds a follow-on `publish / <image>` matrix job
- publishes `main` and SHA tags for the medium-lane workload images

### `release-images.yml`

- `validate-only` is now truly publish-free
- `release-images` no longer owns moving `main` tags
- release publication remains attached to `full-release` mode and semver tags

## Why This Is The Preferred Standard

- merged `main` becomes immediately useful for downstream integration testing
- semver release keeps a stronger trust boundary
- `latest` retains clear meaning as "latest full release"
- release-security evidence remains attached to the release process instead of
  slowing down the fast loop

## Evidence

- workflow updates in:
  - `.github/workflows/ci.yml`
  - `.github/workflows/release-images.yml`
- documentation updates in:
  - `docs/how-to/release-images.md`
  - `docs/explanation/free-tier-ci.md`
- YAML parse validation on 2026-05-03 succeeded for both workflows
- the medium planner still resolves the expected workload images:
  - `diagrams`
  - `java`
  - `python-node`

## Consequences

### Positive

- fast integration loops no longer have to wait for semver release publication
- release workflows no longer need to carry moving `main` tag semantics
- the repo can evolve release gating independently from fast mainline image
  availability

### Trade-Offs

- the workload images now have two distinct publication channels to explain
- medium-proof publication still rebuilds in its publish job rather than
  promoting an already validated artifact
- full-release gating and digest continuity remain separate follow-on work

## Applicability

- Applies to: published workload-image channel design in this repository
- Does not apply to: the maintainer image workflow, which already had a
  dedicated `main` publication path

## Related Knowledge

- [KB-2026-038](KB-2026-038-release-image-scan-must-report-upstream-residual-risk-without-blocking-release.md)
- [KB-2026-063](KB-2026-063-image-release-gating-implementation-plan.md)
- [KB-2026-064](KB-2026-064-mainline-medium-validated-images-should-feed-fast-integration-loops.md)
