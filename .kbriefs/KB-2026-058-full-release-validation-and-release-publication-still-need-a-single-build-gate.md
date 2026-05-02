---
id: KB-2026-058
type: design-space
status: active
created: 2026-05-02
updated: 2026-05-02
tags:
  - release
  - full-release
  - github-actions
  - images
  - gating
  - digests
  - kbpd
related:
  - KB-2026-038
  - KB-2026-055
  - KB-2026-057
---

# Full-Release Validation And Release Publication Still Need A Single-Build Gate

## Context

The repository now has a proven free-tier branch CI model:

- `ci-repo-core`
- `medium / diagrams`
- `medium / java`
- `medium / python-node`

That closes the default branch-confidence problem. It does **not** yet prove
the heavyweight `full-release` path end to end, and it does not yet guarantee
that the image digest which gets published to GHCR is the exact build artifact
that passed heavyweight validation.

## Problem Statement

How should the repository adapt the `full-release` and `release-images`
workflow so that:

- the heavyweight release process is explicitly proven after the lane split
- release publication is gated on a successful heavyweight build
- the pushed digest is demonstrably the validated artifact, not a later rebuild

## Design Space Dimensions

- Evidence strength for the published digest
- Workflow complexity
- Release latency and cost
- Reuse of current build tooling
- Human confidence at release time

## Current State

The branch CI and release workflow now share the same image planner, but the
release workflow still has two important characteristics:

1. it has not been re-proven end to end after the branch-CI restructuring
2. it validates one build and then performs a separate build-and-push step

In `.github/workflows/release-images.yml` the current sequence is:

1. `Build image for validation`
2. validate metadata
3. smoke-test starter bootstrap where relevant
4. run `task ci` inside the built image
5. `Build and push image`

That means the image that is published can differ from the image that passed
validation, even if both are produced from the same sources and cache inputs.

## Options In The Space

### Option A: Keep The Current Two-Build Release Workflow

**Position in space:**
- Evidence strength: medium-low
- Complexity: low
- Release latency: medium

**Characteristics:**
- easiest to keep
- validates a pre-push build
- publishes a second rebuild
- leaves a proof gap between validated image and released digest

### Option B: Validate Then Push The Exact Local Validated Image

**Position in space:**
- Evidence strength: high
- Complexity: medium
- Release latency: medium-low

**Characteristics:**
- validate the locally built image
- retag and push the same local image after success
- reduces rebuild drift
- may constrain how SBOM, provenance, and signing integrate

### Option C: Build Once To A Staging Digest, Validate That Digest, Then Promote

**Position in space:**
- Evidence strength: very high
- Complexity: high
- Release latency: medium-high

**Characteristics:**
- create a candidate digest first
- validate the pulled candidate digest
- publish or retag only after that digest passes
- strongest evidence chain, but more orchestration

### Option D: Split Full-Release Validation From Publication And Gate Publish On Recorded Evidence

**Position in space:**
- Evidence strength: high
- Complexity: high
- Release latency: high

**Characteristics:**
- make heavyweight validation its own explicit workflow or mode
- publish only when a matching commit/tag already has successful full-release evidence
- strongest process separation
- requires additional coordination and state lookup

## Design Space Map

| Option | Evidence strength | Complexity | Drift risk | Viable next step? |
|--------|-------------------|------------|------------|-------------------|
| A | Low-Med | Low | High | Weak |
| B | High | Med | Low | Strong |
| C | Very High | High | Very Low | Strong |
| D | High | High | Low | Strong |

## Constraints That Narrow The Space

- The merge candidate should not be blocked on redesigning release publication.
- The maintainer/container-first validation model remains the source of truth.
- The release workflow still needs metadata validation, smoke proof where
  relevant, in-image `task ci`, signing, provenance, and Trivy reporting.
- Any chosen gate needs to stay understandable for a small repo operating on a
  free-tier development model.

## Unexplored Regions

- exact wall-clock and storage profile of the current `full-release` path after
  the branch-CI refactor
- whether the current GitHub-hosted runner budget is sufficient for the full
  matrix without additional shaping
- the best artifact-promotion mechanism for preserving digest identity between
  validation and publication

## Evidence

- push run `25252816203` proved the branch CI restructuring, not the release
  workflow
- `.github/workflows/release-images.yml` currently contains separate
  `Build image for validation` and `Build and push image` steps
- `KB-2026-038` already establishes that release policy depends on structured
  release-security evidence after publication

## Insights

- The free-tier branch CI problem is largely solved; the remaining uncertainty
  has moved to release-grade evidence.
- Sharing the same matrix planner across CI and release prevents image-list
  drift, but does not by itself guarantee digest-level proof continuity.
- The next meaningful learning cycle is about release gating, not branch CI
  parallelism.

## Recommendations

- Do not redesign the release workflow before merging the current CI work.
- After merge, run an explicit heavyweight `full-release` validation exercise
  on a non-release ref to measure runtime, storage, and failure behavior.
- Then choose a release-gating model that proves the published digest is the
  validated artifact or a gated promotion of it.
- Prefer options that make the validated artifact identity explicit in logs and
  release evidence.

## Applicability

- Applies to: `.github/workflows/release-images.yml`, heavyweight image
  validation, release publication policy
- Does not apply to: the proven free-tier branch CI lane or source-template
  starter proofing

## Related Knowledge

- [KB-2026-038](C:/dev/polyglot-devcontainers-starter-generator/.kbriefs/KB-2026-038-release-image-scan-must-report-upstream-residual-risk-without-blocking-release.md)
- [KB-2026-055](C:/dev/polyglot-devcontainers-starter-generator/.kbriefs/KB-2026-055-free-tier-image-validation-should-use-fast-medium-and-full-release-lanes.md)
- [KB-2026-057](C:/dev/polyglot-devcontainers-starter-generator/.kbriefs/KB-2026-057-default-free-tier-ci-should-run-on-branch-push-and-fan-out-medium-image-builds.md)
