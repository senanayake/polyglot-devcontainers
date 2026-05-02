---
id: KB-2026-050
type: design-space
status: active
created: 2026-05-01
updated: 2026-05-02
tags: [github-actions, free-tier, ci, starters, images, kbpd]
related:
  - KB-2026-028
  - KB-2026-029
  - KB-2026-031
  - KB-2026-042
  - KB-2026-049
  - KB-2026-058
---

# Free-Tier CI Knowledge Gaps for Image-Backed Starter Proofing

## Context

The starter-generator branch now includes image-backed starter proofing in the
root PR workflow. That raised coverage, but it also exhausted the disk budget
of GitHub's free standard Ubuntu runner.

The project wants to stay on the free tier. That means the next step is not
"buy more runner" but "rethink the proof contract so the free tier remains
credible."

## Problem Statement

What knowledge gaps must be closed before changing the starter proof strategy
so the repository can:

- stay on GitHub's free standard runner tier
- keep meaningful branch confidence
- preserve container-authoritative proofing
- avoid silently weakening the published task contract

## Resolution Snapshot

Most of the original free-tier branch-CI questions in this brief are now
substantially resolved:

- disk attribution was captured with targeted diagnostics
- tar export was removed from the medium branch lane
- the proof scope was reduced to per-image matrix jobs
- the default gate placement converged on:
  - `ci-repo-core`
  - `medium / <image>`
- the standard runner is now viable for the default branch lane
- failure observability improved through preserved disk and starter-proof
  artifacts

The remaining major open question is no longer whether free-tier branch CI is
possible. It is whether the heavyweight `full-release` lane and the
`release-images` workflow provide a strong enough release gate for published
digests. That follow-on gap is now tracked separately in `KB-2026-058`.

## What Is Already Known

These are hard facts, not open questions:

- The repository is public and owned by a user account, not an organization.
- GitHub-hosted larger runners are not available to the current repo ownership
  model and would be paid even if they were.
- Standard public `ubuntu-latest` runners currently provide `14 GB` SSD.
- Current run `25239181369` passed the maintainer control-path fix and then
  failed with runner-level `No space left on device`.
- `starters:verify:image-backed` currently calls `task image:build`.
- `task image:build` currently builds four verify images and saves four tar
  archives.
- The actual image-backed starter proof only exercises two starter paths:
  `java-secure` and `python-node-secure`.
- Existing repo knowledge already favors explicit heavy lanes over silently
  bloating default lanes:
  - `KB-2026-028` favors fast defaults and opt-in heavier lanes
  - `KB-2026-031` favors explicit contract names over ambiguous defaults
  - `KB-2026-029` treats the free baseline as non-negotiable

## Design Space Dimensions

Key variables that define the solution space:

- Free-tier compatibility
- Branch-level confidence
- Task-contract clarity
- CI runtime and disk footprint
- Maintenance complexity

## Options in the Space

### Option A: Keep the current required PR lane and trim it until it fits

**Position in space:**
- Free-tier compatibility: unknown
- Branch-level confidence: high
- Task-contract clarity: high
- Runtime and disk footprint: currently failing
- Maintenance complexity: medium

**Characteristics:**
- Preserves today's required signal if it can be made small enough
- Risks repeated tuning against an extremely small storage budget
- Depends on learning which parts of the lane are essential versus accidental

### Option B: Keep full image-backed proofing, but move it out of the default PR gate

**Position in space:**
- Free-tier compatibility: likely high
- Branch-level confidence: medium
- Task-contract clarity: unknown
- Runtime and disk footprint: low for PRs, high elsewhere
- Maintenance complexity: medium

**Characteristics:**
- Makes the default PR lane cheaper immediately
- Requires an explicit policy for when the heavy lane runs
- Risks discovering branch/image drift later unless another compensating signal exists

### Option C: Replace the heavy PR proof with a lighter equivalent signal

**Position in space:**
- Free-tier compatibility: likely high
- Branch-level confidence: unknown
- Task-contract clarity: medium-high if named clearly
- Runtime and disk footprint: low-medium
- Maintenance complexity: high until equivalence is proven

**Characteristics:**
- Most aligned with the free-tier goal if equivalence can be shown
- Requires evidence that lighter checks still catch the important regressions
- May reveal that some current proof work is redundant

### Option D: Layered lane model

**Position in space:**
- Free-tier compatibility: high
- Branch-level confidence: high if designed well
- Task-contract clarity: medium unless named carefully
- Runtime and disk footprint: low for default lane, high for explicit heavy lane
- Maintenance complexity: medium-high

**Characteristics:**
- Keeps a fast required lane plus an explicit heavier verification lane
- Matches prior repo knowledge about fast defaults and opt-in heavy proof
- Requires the repository to define exactly what "merge-ready" means

## Design Space Map

| Option | Free tier | Confidence | Contract clarity | Viable now? |
|--------|-----------|------------|------------------|-------------|
| A | Unknown | High | High | Maybe |
| B | High | Medium | Unknown | Maybe |
| C | High | Unknown | Medium-High | Maybe |
| D | High | High | Medium | Strong candidate |

## Dominated Solutions

Options that are strictly worse than others:

- Use GitHub-hosted larger runners for this repo in its current form.
  This is dominated by the stated free-tier constraint and by the current
  user-owned public repo shape.
- Keep the current all-in-one PR lane unchanged.
  This is dominated by observed failure on the free standard runner.

## Constraints That Narrow the Space

Hard constraints that eliminate options:

- The solution must stay on free GitHub-hosted standard runners.
- The maintainer container remains the source of truth for repository proof.
- The repository should not silently weaken `task ci` semantics without
  replacing lost meaning with explicit task structure.
- Branch-local image-backed proof should use branch-local verify images when the
  goal is current-branch correctness.

## Prioritized Knowledge Gaps

### Gap 1: Disk Attribution Gap

**Unknown**

Which storage consumers dominate the failing lane:

- host maintainer image layers
- nested runtime image layers
- tar exports under `.artifacts/images`
- Trivy or package caches
- some combination

**Why it matters**

Without attribution, free-tier remediation will be guesswork.

**Learning cycle**

Instrument the workflow with:

- `df -h`
- host `docker system df`
- nested-runtime `docker system df` or equivalent
- `du -sh .artifacts/images`

at three checkpoints:

- before `Build root image`
- before `task image:build`
- after `task image:build`

**Success signal**

One or two dominant storage sources explain most of the runner exhaustion.

### Gap 2: Tar Export Necessity Gap

**Unknown**

Does the image-backed starter proof actually need exported image tarballs, or
are those only needed by image-scan and release-style workflows?

**Why it matters**

If tar export is accidental baggage in the PR lane, removing it may recover a
large amount of disk without reducing proof coverage.

**Learning cycle**

Split `task image:build` conceptually into:

- build-only for starter proofing
- save/export only for scanning workflows

Then prove whether `starters:verify:image-backed` still works with build-only
images present in the local runtime.

**Success signal**

The starter proof lane passes without `oci_runtime.py save` steps.

### Gap 3: Proof Scope Gap

**Unknown**

What is the minimum image set required for the starter proof lane?

Current build scope includes:

- maintainer
- java
- diagrams
- python-node

Current image-backed starter proofs appear to use:

- java
- python-node

**Why it matters**

The lane may be paying to build and archive images that are not part of the
required proof signal.

**Learning cycle**

Map each built image to a specific consumer in the PR workflow.

**Success signal**

Every built image in the PR lane has a direct proof purpose, or the unused
images are removed from that lane.

### Gap 4: Unique Coverage Gap

**Unknown**

Which regressions are caught only by the image-backed proof path and not by:

- source-template starter proof
- published image smoke tests
- template-local `task ci`

**Why it matters**

The free-tier strategy depends on understanding the marginal value of the
expensive lane.

**Learning cycle**

Catalog recent starter regressions by bug class:

- bootstrap contract drift
- published image drift
- branch-local image drift
- scenario/workspace drift

Then mark which verification lane would have caught each bug.

**Success signal**

The team can name the unique bug classes protected by image-backed branch proof.

### Gap 5: PR Gate Placement Gap

**Unknown**

Does image-backed starter proof need to block every PR, or is it enough for it
to run:

- manually
- on merge to `main`
- nightly
- before release
- on selected path changes only

**Why it matters**

This is the main policy choice that determines whether the free-tier PR lane
must absorb the full cost.

**Learning cycle**

Compare risk by change type:

- starter catalog edits
- template devcontainer edits
- bootstrap script edits
- docs-only changes
- unrelated repo changes

**Success signal**

A rule exists for when heavy proof is required and when it is not.

### Gap 6: Task Contract Scope Gap

**Unknown**

Should image-backed starter proof live inside root `task ci`, or should it be
an explicit stronger lane such as a release or full-proof verb?

**Why it matters**

The repo already has prior knowledge favoring explicit heavy lanes and clear
contracts. Free-tier pressure may be revealing that `task ci` has grown beyond
its sustainable default role.

**Learning cycle**

Define candidate task shapes and evaluate them against:

- published contract clarity
- contributor expectations
- agent predictability
- free-tier sustainability

**Success signal**

One task naming model keeps `task ci` useful and explicit without hiding the
existence of stronger proof.

### Gap 7: Standard-Runner Viability Gap

**Unknown**

After removing accidental baggage, can a meaningful image-backed starter proof
still fit inside the free standard runner?

**Why it matters**

This determines whether Option A or D remains viable at all.

**Learning cycle**

Run a reduction matrix:

- no tar exports
- only starter-relevant images
- no diagrams image
- one starter at a time
- pruning between image builds if safe

**Success signal**

At least one meaningful branch-proof slice completes within the standard runner
disk budget.

### Gap 8: Failure Observability Gap

**Unknown**

How should the workflow fail early enough to preserve useful diagnostics before
the runner itself stops writing logs?

**Why it matters**

Low-space failures currently destroy the very evidence needed for debugging.

**Learning cycle**

Add low-water-mark checks before image-heavy steps and fail with a custom
message if free space falls below a threshold.

**Success signal**

The next free-tier failure explains the dominant storage pressure instead of
ending in a runner `_diag` ENOSPC crash.

## Evidence

Data supporting this design space mapping:

- `.github/workflows/ci.yml`
- `Taskfile.yml`
- `scripts/starter_catalog.py`
- `KB-2026-028-fast-default-and-opt-in-integration-test-lanes-for-python-starters.md`
- `KB-2026-029-free-local-baseline-vs-robust-remote-control-plane.md`
- `KB-2026-031-full-test-bar-vs-fast-default-feedback-loop.md`
- `KB-2026-042-image-backed-starter-proof-should-use-branch-local-verify-images.md`
- `KB-2026-049-github-standard-runner-disk-exhaustion-during-image-backed-starter-proofs.md`

## Insights

Key learnings from mapping the space:

- The expensive part is not merely "starter proofing"; it is the combination of
  nested image builds plus exported image artifacts inside the default PR lane.
- The repo already has philosophical precedent for keeping heavy coverage
  explicit rather than silently making the default lane slower and more fragile.
- The most important unknown is not "how do we buy more headroom" but "what is
  the smallest credible free-tier signal for branch confidence."

## Decision Guidance

### Narrowing the Space

How to progressively eliminate options:

1. Treat paid larger runners as out of scope for this repo's current operating
   model.
2. Measure disk attribution so optimization targets are real.
3. Remove accidental baggage before weakening proof scope.
4. Only then decide whether the heavy proof belongs in the default PR gate.

### Convergence Strategy

When and how to commit to a solution:

- If build-only plus reduced image scope fits the free runner and preserves the
  important coverage, keep a trimmed PR lane.
- If it still does not fit, move to a layered model with an explicit heavier
  proof lane and a lighter required PR lane.
- Do not weaken proof placement until the unique coverage gap is understood.

## Implications

What this design space means for:

- Architecture: starter proof tasks may need clearer separation by purpose
- Roadmap: CI contract work is now part of the starter product work
- Risk: weakening PR gates without coverage attribution would be guesswork
- Cost strategy: free-tier viability depends more on proof design than on YAML
  tweaking alone

## Recommendations

Suggested path forward:

- Explore Gap 1 and Gap 2 first because they can expose easy storage wins.
- Explore Gap 3 immediately after, because current build scope appears broader
  than current proof use.
- Delay any decision to move the heavy lane out of PR until Gap 4 and Gap 5 are
  answered.
- Keep the free baseline as the primary design constraint, not an afterthought.

## Applicability

Where this design space applies:

- Applies to: PR CI design, starter proof placement, free-tier workflow design,
  image-backed branch validation
- Does not apply to: paid org-only runner strategies, enterprise runner groups,
  or non-container-authoritative shortcuts

## Related Knowledge

- `KB-2026-028-fast-default-and-opt-in-integration-test-lanes-for-python-starters.md`
- `KB-2026-029-free-local-baseline-vs-robust-remote-control-plane.md`
- `KB-2026-031-full-test-bar-vs-fast-default-feedback-loop.md`
- `KB-2026-042-image-backed-starter-proof-should-use-branch-local-verify-images.md`
- `KB-2026-049-github-standard-runner-disk-exhaustion-during-image-backed-starter-proofs.md`
