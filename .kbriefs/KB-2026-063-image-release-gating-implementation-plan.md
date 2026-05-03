---
id: KB-2026-063
type: standard
status: active
created: 2026-05-03
updated: 2026-05-03
tags:
  - release
  - implementation-plan
  - github-actions
  - images
  - gating
  - kbpd
related:
  - KB-2026-038
  - KB-2026-058
  - KB-2026-062
  - KB-2026-064
---

# Image Release And Gating Implementation Plan

## Context

The repository now has a working free-tier branch CI model and a partially
modernized release path:

- feature-branch push runs `ci-repo-core` plus medium image fanout
- `cut-release` can compute and push semantic tags
- `release-images` can build, validate, publish, scan, sign, attest, and
  publish release-security docs

Two distinct gaps remain:

1. merged `main` does not yet feed a fast workload-image integration channel
2. release publication still happens without a final authoritative full-release
   gate and without guaranteed digest continuity

This plan now covers both channels together:

- a fast **mainline integration channel**
- a slower **release authority channel**

## Objective

Establish an image publication process in which:

1. merged `main` quickly produces integration-grade workload images after
   medium proof
2. a specific `main` commit is proven by a full-release validation lane before
   semver release publication
3. release publication is allowed only for a commit with successful evidence
4. release-scan success is defined by evidence generation and residual-risk
   classification, not by zero findings
5. digest continuity is improved after the mainline evidence gate exists

## Scope

### In Scope

- GitHub Actions workflow behavior for:
  - `.github/workflows/ci.yml`
  - `.github/workflows/release-images.yml`
  - `.github/workflows/cut-release.yml`
- mainline medium-validated workload-image publication
- commit-scoped full-release validation on `main`
- evidence recording and eligibility checks
- operator-facing release semantics and docs

### Out Of Scope For The First Slice

- changing residual-risk policy from `KB-2026-038`
- redesigning the free-tier branch CI lanes
- introducing a large staging registry architecture before the evidence gate
  exists
- solving every future digest-promotion detail up front

## Target End State

The desired operator model has two channels.

### Mainline Integration Channel

1. merge to `main`
2. run repo-core plus medium image proof
3. publish moving integration images
4. use those images for fast downstream integration testing

### Release Authority Channel

1. choose a target commit on `main`
2. run a heavyweight full-release validation lane for that commit
3. review the evidence bundle
4. cut a release only if that commit has successful evidence
5. publish release images and release assets

The important process change is:

- merged `main` becomes quickly consumable for integration
- semver release remains gated by heavyweight proof

## Implementation Plan

### Phase 1: Make Validation And Publication Semantics Explicit

#### Goal

Remove ambiguous workflow meanings before adding stronger gates.

#### Changes To Make

- redefine `release-images` modes so they are semantically true:
  - `validate-only` means no GHCR push, no moving tags, no release note updates
  - `full-release` means publish and release-side effects are allowed
- ensure manual validation on `main` cannot update moving `main` image tags
- make workflow summaries state clearly whether the run is:
  - validation-only
  - release publication

#### Why First

The current `validate-only` mode is not actually publish-free. Until that is
fixed, the repo has no safe manual path for authoritative mainline validation.

#### Acceptance Criteria

- a manual validation run on `main` performs no image publication
- no GHCR tags move during validation-only runs
- operator summary text matches real workflow behavior

### Phase 2: Establish A Mainline Integration Image Channel

#### Goal

Make merged `main` quickly consumable as workload images without waiting for
full-release publication.

#### Changes To Make

- allow the medium image matrix to run on `main`
- after successful medium proof on `main`, publish integration-grade workload
  images
- use channel semantics from `KB-2026-064`:
  - moving `main` tag
  - immutable commit-scoped SHA tag
  - no semver tag
  - no `latest` tag
  - no release notes or release-security docs
- keep the integration publication path separate from semver release
  publication

#### Why Here

This solves the fast-loop requirement directly and keeps it independent from the
heavier release-authority work.

#### Acceptance Criteria

- a successful medium-proof run on `main` publishes workload images for fast
  integration use
- the published tags are clearly integration-grade, not release-grade
- `latest` does not move as a side effect of this channel

### Phase 3: Establish A Dedicated Mainline Full-Release Validation Lane

#### Goal

Create an authoritative heavyweight proof path for a specific `main` commit.

#### Changes To Make

- add a dedicated workflow or a clearly separated `release-images` mode for
  mainline full-release validation
- run the full image matrix using the existing `full-release` profile shape:
  - build
  - metadata validation
  - starter smoke where relevant
  - in-image `task ci`
  - saved image artifact or equivalent evidence
  - Trivy summary generation
  - residual-risk classification
- key all evidence to the target commit SHA

#### Notes

- This lane should be allowed on explicit dispatch first.
- Running it automatically on every `main` push is a later policy choice, not a
  prerequisite for the first implementation.

#### Acceptance Criteria

- one workflow run can produce full-release evidence for a specific `main`
  commit without publishing images
- evidence artifacts are downloadable and clearly linked to the target SHA
- scan success is defined by completed scan artifacts and residual-risk output

### Phase 4: Record Commit-Scoped Release Eligibility

#### Goal

Make release readiness queryable and machine-checkable.

#### Changes To Make

- define the evidence bundle contract for a validated commit
- choose a lightweight evidence source of truth, for example:
  - workflow conclusion plus named artifacts
  - a generated JSON summary artifact keyed by commit SHA
  - optionally a commit status/check name dedicated to full-release readiness
- make the evidence include:
  - target SHA
  - image matrix
  - per-image validation results
  - scan summary locations
  - residual-risk report location

#### Why Before `cut-release` Changes

`cut-release` cannot gate reliably until there is something stable to check.

#### Acceptance Criteria

- the repo can answer "does commit `<sha>` have successful full-release
  evidence?"
- the answer does not depend on reading free-form logs manually

### Phase 5: Gate `cut-release` On Existing Full-Release Evidence

#### Goal

Move semantic tag creation behind proven commit readiness.

#### Changes To Make

- update `cut-release` so it checks the target commit for successful
  full-release evidence before pushing a semantic tag
- fail fast with a clear message if the target commit has not passed the
  authoritative lane
- keep `cut-release` as the human-facing release entry point

#### Why This Is The Core Process Shift

This is the moment where the repo stops treating release as "tag then hope" and
 starts treating it as "prove then tag."

#### Acceptance Criteria

- `cut-release` refuses to tag an unproven commit
- `cut-release` can successfully tag and continue only after the evidence gate
  passes

### Phase 6: Strengthen Artifact Continuity

#### Goal

Reduce or eliminate the gap between the validated artifact and the published
digest.

#### Candidate Approaches

- acceptable intermediate state:
  - keep rebuild-on-publish, but record that digest continuity remains open
- stronger state:
  - validate local built image, then retag and push that exact image
- strongest state:
  - build candidate digest once, validate it, then promote that exact digest

#### Recommendation

Do this **after** the commit-scoped evidence gate exists. The evidence gate is
the more important process fix; digest promotion is the stronger second step.

#### Acceptance Criteria

- release docs and workflow summaries make artifact identity explicit
- either:
  - the exact validated artifact is published
  - or the remaining rebuild drift is explicitly recorded as an accepted gap

### Phase 7: Normalize Release Docs And Operator Guidance

#### Goal

Make the release process understandable and reproducible for humans and agents.

#### Changes To Make

- update `docs/how-to/release-images.md`
- document:
  - how the mainline integration channel works
  - how to run the authoritative mainline validation
  - what counts as a successful release scan
  - how `cut-release` checks eligibility
  - what evidence humans should review

#### Acceptance Criteria

- a maintainer can explain the release process without reading workflow YAML
- docs match actual workflow behavior

## Recommended Rollout Order

1. Phase 1: true validate-only semantics
2. Phase 2: mainline integration image channel
3. Phase 3: authoritative mainline full-release validation lane
4. Phase 4: commit-scoped evidence bundle
5. Phase 5: `cut-release` eligibility gate
6. Phase 7: docs normalization
7. Phase 6: artifact continuity strengthening

This ordering is intentional:

- first create a safe validation path
- then make merged `main` useful for fast integration loops
- then create heavyweight release evidence
- then enforce the release gate
- then strengthen artifact continuity

## Validation Strategy

### For Workflow Semantics

- run manual validation against `main`
- verify no image publication occurs
- verify no moving tags are changed

### For Mainline Integration Publication

- merge or simulate a `main` commit that changes one or more workload images
- confirm medium proof passes
- confirm integration-grade `main` and SHA image tags publish
- confirm `latest` does not move

### For Mainline Full-Release Proof

- run the authoritative lane on a known `main` commit
- confirm all expected evidence artifacts exist
- confirm scan summaries and residual-risk outputs are present

### For `cut-release` Gating

- attempt a release from a commit without evidence and confirm fail-fast
- attempt a release from a commit with evidence and confirm success

### For Artifact Continuity

- compare validated artifact identity with published digest identity
- record whether the workflow is still rebuilding or truly promoting

## Risks And Mitigations

### Risk: Mainline Integration Publication Blurs Into Release Semantics

Mitigation:

- reserve semver and `latest` for the release channel
- document `main` and SHA tags as integration-grade

### Risk: Validation Lane Is Too Slow Or Expensive To Run Frequently

Mitigation:

- start with explicit dispatch on `main`
- decide later whether every `main` push, nightly, or pre-release only is the
  right trigger policy

### Risk: Evidence Source Is Hard To Query Reliably

Mitigation:

- keep the first evidence bundle simple and machine-readable
- prefer explicit artifacts or a dedicated status/check over log scraping

### Risk: Digest Continuity Delays The More Important Gate

Mitigation:

- treat digest promotion as Phase 5
- do not block the mainline evidence gate on solving promotion first

### Risk: Release Scan Semantics Regress To "Zero Findings"

Mitigation:

- keep `KB-2026-038` as the policy anchor
- define scan success in terms of evidence and classification, not absence of
  findings

## Open Questions

- should the integration channel publish all medium-lane images or only a
  curated subset
- should the integration channel run on every `main` push or only when image
  inputs change
- should downstream integration consumers use moving `main` tags or commit SHA
  tags by default
- Should authoritative full-release validation run:
  - only on manual dispatch
  - on every `main` push
  - on a scheduled cadence
  - or on some hybrid policy
- What is the lightest durable evidence source of truth:
  - workflow artifact
  - check run conclusion
  - generated JSON summary committed nowhere
- Is local-image retag-and-push good enough for artifact continuity, or is
  staged digest promotion worth the extra complexity for this repo

## Recommendations

- Implement the mainline integration channel and the mainline evidence gate as
  separate but coordinated workstreams.
- Do not treat the current `cut-release` tag-first flow as the final release
  authority model.
- Keep the first slices small and explicit:
  - publish-free full-release validation on `main`
  - medium-validated integration image publication on `main`
  - evidence keyed by commit SHA
  - then `cut-release` eligibility enforcement

## Applicability

- Applies to: image publication workflow design and rollout planning
- Does not apply to: feature-branch medium CI or dependency-maintenance flows

## Related Knowledge

- [KB-2026-038](KB-2026-038-release-image-scan-must-report-upstream-residual-risk-without-blocking-release.md)
- [KB-2026-058](KB-2026-058-full-release-validation-and-release-publication-still-need-a-single-build-gate.md)
- [KB-2026-062](KB-2026-062-mainline-full-release-evidence-should-gate-cut-release-and-publication.md)
- [KB-2026-064](KB-2026-064-mainline-medium-validated-images-should-feed-fast-integration-loops.md)
