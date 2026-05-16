---
id: KB-2026-064
type: design-space
status: active
created: 2026-05-03
updated: 2026-05-03
tags:
  - images
  - release
  - integration
  - main
  - ci
  - kbpd
related:
  - KB-2026-055
  - KB-2026-057
  - KB-2026-063
---

# Mainline Medium-Validated Images Should Feed Fast Integration Loops

## Context

The repository now has a strong free-tier development lane:

- feature-branch push runs `ci-repo-core`
- feature-branch push fans out medium image validation in parallel

That solves developer feedback speed on branches. It does **not** yet provide a
fast-moving published image channel built from merged `main` commits for use in
downstream integration testing.

At the same time, the heavyweight release lane is intentionally slower and more
expensive:

- full image build matrix
- in-image `task ci`
- scan summaries and residual-risk reporting
- release notes, release security docs, signing, provenance, immutable semver

Those two use cases should not be forced into one channel.

## Problem Statement

Should the repository publish images from merged `main` commits after
medium-level proof so they are available quickly for integration-test loops,
while reserving heavyweight scans and semver publication for the full release
process?

## Short Answer

Yes. That split makes sense and matches the repo's free-tier agility goals.

The correct shape is:

- **integration channel**: moving `main`/commit-scoped images published after
  medium proof on `main`
- **release channel**: semver and `latest` images published only after the
  authoritative full-release gate

## Why This Split Is Valuable

### Fast Integration Loops Need Availability More Than Release-Grade Evidence

If a downstream system just wants to integration-test against the newest merged
image, waiting for full release behavior is unnecessary latency.

Medium proof already gives useful confidence:

- image builds successfully
- metadata is correct
- starter smoke works where relevant
- selected image-backed scenarios run

That is a strong bar for a moving integration target.

### Full Release Needs Stronger Evidence

Release images have a different job:

- immutable distribution
- longer-lived consumer expectations
- release notes
- release security docs
- semver commitments

That is where heavyweight proof and release-security publication belong.

### One Channel Cannot Optimize Both Objectives Well

If every published image must wait for full-release proof:

- integration loops get slower
- merges to `main` become less useful as a fast staging surface

If every published image is treated as release-grade:

- the release concept becomes watered down
- `latest` and semver channels lose meaning

## Current State

The repo already has one working example of this pattern:

- `.github/workflows/maintainer-image.yml` publishes the maintainer image on
  `main` after validation, using moving `main` and `sha` tags

The published workload images do **not** yet have an equivalent mainline
integration channel.

Also, `.github/workflows/ci.yml` currently ignores `main` pushes entirely, so
merged workload-image changes are not automatically re-proven at medium level
on `main`.

## Design Space

### Option A: Publish Only Full Releases

**Characteristics**

- no moving published workload-image channel
- only semver release tags produce published images

**Pros**

- simplest mental model
- least registry churn

**Cons**

- poor support for fast downstream integration loops
- merged `main` is not quickly consumable as an image channel

### Option B: Publish Mainline Medium-Validated Images And Separate Full Releases

**Characteristics**

- publish moving integration images from `main`
- keep semver/`latest` publication behind full-release gating

**Pros**

- best balance of speed and evidence
- preserves a meaningful release bar
- makes merged `main` immediately useful for integration

**Cons**

- introduces two image channels to explain
- requires careful tag semantics

### Option C: Publish Every Branch

**Characteristics**

- publish images from feature branches too

**Pros**

- maximum availability

**Cons**

- too much churn for this repo
- weakens the role of merged `main`
- likely too noisy and expensive

## Recommended Channel Model

### 1. Mainline Integration Channel

Published after successful medium proof on `main`.

Recommended properties:

- moving `main` tag
- immutable commit-scoped `sha` tag
- no semver tag
- no `latest` tag
- no release notes or release-security docs
- no claim of full-release readiness

Purpose:

- fast downstream integration testing
- quick human or agent consumption of the newest merged image set

### 2. Release Channel

Published only after authoritative full-release validation and release gating.

Recommended properties:

- immutable semver tag
- moving `latest` tag
- signing
- provenance
- release notes
- release-security docs
- full-release evidence

Purpose:

- stable distribution
- user-facing release consumption
- audited release history

## Tagging Guidance

To keep the two channels understandable:

- integration channel:
  - `main`
  - `sha-<commit>` or the existing metadata-action SHA tag
- release channel:
  - `vX.Y.Z`
  - `latest`

Do **not** let medium-proof publication move `latest`.

That preserves the meaning of `latest` as "latest full release," not "latest
merged mainline image."

## Interaction With Release Gating

This integration channel does **not** replace the full-release gate from
`KB-2026-063`.

Instead:

- the integration channel optimizes feedback speed on merged `main`
- the release gate optimizes trust for semver publication

These are complementary, not competing, goals.

## Implementation Direction

The likely workflow shape is:

1. on push to `main`, run the medium image matrix
2. after successful medium proof, publish moving integration tags for the
   workload images
3. keep full-release validation and semver publication as a separate process

The maintainers should think of this as:

- **mainline image availability workflow**
- **release publication workflow**

not one giant pipeline.

## Risks And Controls

### Risk: Users Confuse `main` Images With Release Images

Control:

- keep semver and `latest` reserved for full releases
- document `main` images as integration-grade, not release-grade

### Risk: `main` Pushes Become Too Slow

Control:

- reuse the medium proof shape rather than the heavyweight release lane
- keep image fanout parallel

### Risk: Channel Semantics Drift

Control:

- make workflow summaries and docs explicitly label the channel:
  - integration
  - release

## Open Questions

- should the integration channel publish all medium-lane images or only a
  curated subset
- should the integration channel run on every `main` push or only when image
  inputs change
- should downstream integration consumers use the moving `main` tag or commit
  SHA tags by default

## Recommendations

- Publish workload images from merged `main` after medium proof.
- Treat those images as an integration channel, not as releases.
- Keep full-release scans, release docs, semver tags, and `latest` in the
  heavier release workflow.
- Fold this channel into the release implementation plan as a parallel fast
  path, not as a substitute for release gating.

## Applicability

- Applies to: workload-image publication strategy after merge to `main`
- Does not apply to: feature-branch publication or semver release authority

## Related Knowledge

- [KB-2026-055](KB-2026-055-free-tier-image-validation-should-use-fast-medium-and-full-release-lanes.md)
- [KB-2026-057](KB-2026-057-default-free-tier-ci-should-run-on-branch-push-and-fan-out-medium-image-builds.md)
- [KB-2026-063](KB-2026-063-image-release-gating-implementation-plan.md)
