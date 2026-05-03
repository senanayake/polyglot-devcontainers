---
id: KB-2026-062
type: design-space
status: active
created: 2026-05-03
updated: 2026-05-03
tags:
  - release
  - full-release
  - main
  - gating
  - publication
  - digests
  - kbpd
related:
  - KB-2026-038
  - KB-2026-058
---

# Mainline Full-Release Evidence Should Gate Cut-Release And Publication

## Context

The repository now has an effective free-tier development loop:

- medium-profile image validation runs on feature-branch push
- `ci-repo-core` runs in parallel with the medium image fanout
- the heavyweight `full-release` path is still separate and more expensive

The next problem is not branch CI anymore. The next problem is release process
shape: how to make image publication depend on proven mainline full-release
evidence.

## Problem Statement

What release process should this repository use so that:

- heavyweight full-release validation happens on the intended `main` commit
- the commit is known-good **before** a versioned image release is cut
- release-scan success is defined consistently with residual-risk policy
- image publication uses the validated artifact or an explicit promotion of it

## Design Space Dimensions

- Strength of the commit-to-release evidence chain
- Strength of digest continuity
- Cost and latency on the free tier
- Operator clarity
- Reversibility of failure points

## Candidate Process Shapes

### Option A: Current Tag-First Release Orchestration

**Flow**

1. Push semantic tag.
2. Run full release workflow from the tag.
3. Build, validate, publish, scan, sign, and document.

**Pros**

- simple to operate
- release remains a single visible action

**Cons**

- version tag exists before heavyweight proof is complete
- publication can still happen before scan evidence exists
- digest continuity is weak when validation and push use separate builds

### Option B: Commit-Scoped Mainline Validation Before Tag Cut

**Flow**

1. Choose a target commit on `main`.
2. Run a dedicated full-release validation workflow on that commit with **no**
   image publication and **no** moving tags.
3. Record evidence keyed by commit SHA.
4. Allow `cut-release` only for commits with successful evidence.
5. Perform publication afterward.

**Pros**

- strongest near-term process improvement for the least conceptual change
- keeps release candidate selection explicit
- makes failure reversible before a semantic tag is created

**Cons**

- still leaves digest continuity unresolved if publication rebuilds
- requires evidence lookup by commit SHA

### Option C: Candidate Digest Build, Validate, Then Promote

**Flow**

1. Build candidate digests once.
2. Validate those exact digests.
3. Publish/promote those exact digests after success.

**Pros**

- strongest artifact continuity
- release evidence points directly at the published digest

**Cons**

- more orchestration complexity
- introduces staging or promotion mechanics that do not exist yet

### Option D: Release-Candidate Tag Or Channel Before Final Tag

**Flow**

1. Publish to an RC tag or staging namespace.
2. Validate there.
3. Promote to final semver tag after success.

**Pros**

- makes pre-release vs final release explicit
- can keep final tags clean

**Cons**

- extra naming and lifecycle complexity
- still needs a digest-promotion story

## What Is Already True

- The local `full-release` task contract already models the right proof shape:
  build, metadata validation, starter smoke where relevant, in-image `task ci`,
  saved tarball, Trivy summary, and residual-risk report.
- `KB-2026-038` already decided that release-scan success is **not** a
  zero-finding bar. It is an evidence-and-classification bar.
- Current `release-images` behavior still treats scan as post-push reporting,
  not as a pre-publication gate.

## Recommended Near-Term Process

The best next process to establish is **Option B**, with the release gate keyed
to a commit SHA on `main`.

### Phase 1: Mainline Full-Release Validation

Run an explicit heavyweight validation workflow on a specific `main` commit:

- full matrix
- no GHCR push
- no moving `main` tag updates
- no semver tag creation

This phase should produce a complete evidence bundle keyed by commit SHA.

### Phase 2: Evidence Bundle

Record release-readiness evidence for that exact commit:

- planned image matrix
- per-image build success
- metadata-validation success
- starter smoke results where relevant
- in-image `task ci` success
- scan summaries
- residual-risk report
- any future digest or manifest identifiers that will be needed for promotion

### Phase 3: Eligibility Gate

`cut-release` should refuse to proceed unless the selected target commit has a
successful, recent full-release evidence bundle.

That keeps semantic tag creation behind a proven gate rather than ahead of it.

### Phase 4: Publication

After commit eligibility is established, publish by one of two models:

- acceptable next step: rebuild and publish, while explicitly recording that
  digest continuity is not yet closed
- stronger next step: publish or promote the exact validated artifact

### Phase 5: Post-Publish Security And Release Docs

Keep the existing post-push security-document flow:

- SBOM generation
- signing
- provenance
- GitHub Release updates
- browser-viewable release security docs

Those are still valuable after publication even when pre-publication gating is
stronger.

## Definition Of A Successful Release Scan

For this repository, a successful release scan should mean:

1. Trivy completed for the target images.
2. Summary artifacts were produced.
3. Residual-risk classification completed.
4. Any `review_required` findings remain visible for human review.

It should **not** mean:

- zero HIGH/CRITICAL findings across all published images

That would contradict `KB-2026-038` and the repo's upstream residual-risk
policy.

## Why This Is The Right Next Learning Cycle

- It fixes the most important process flaw first: publication without prior
  mainline full-release evidence.
- It keeps the release process understandable for a small repo.
- It preserves future freedom to strengthen digest continuity later.
- It does not require redesigning the current release-security documentation
  model first.

## Unexplored Regions

- whether full-release validation should run on every `main` push, only on
  explicit dispatch, or on a scheduled cadence
- how to record and query commit-scoped evidence most cleanly
- whether staged digest promotion is worth the added operational complexity for
  this repository

## Recommendations

- Establish a commit-scoped full-release validation process on `main` before
  treating image release as authoritative.
- Keep publication behind that evidence gate.
- Treat digest-promotion continuity as the follow-on design decision after the
  commit-scoped evidence gate exists.

## Applicability

- Applies to: `main` release preparation, `cut-release`, `release-images`,
  release-security review
- Does not apply to: feature-branch medium CI or the default developer
  feedback loop

## Related Knowledge

- [KB-2026-038](KB-2026-038-release-image-scan-must-report-upstream-residual-risk-without-blocking-release.md)
- [KB-2026-058](KB-2026-058-full-release-validation-and-release-publication-still-need-a-single-build-gate.md)
