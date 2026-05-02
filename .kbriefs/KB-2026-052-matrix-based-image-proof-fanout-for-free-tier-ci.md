---
id: KB-2026-052
type: design-space
status: draft
created: 2026-05-01
updated: 2026-05-01
tags: [github-actions, ci, matrix, starters, images, free-tier, scaling]
related:
  - KB-2026-031
  - KB-2026-037
  - KB-2026-049
  - KB-2026-050
  - KB-2026-051
---

# Matrix-Based Image-Proof Fanout for Free-Tier CI

## Context

The starter-generator branch has reached a point where image-backed starter
proofing is useful, but the current all-in-one PR lane does not scale on
GitHub's free standard hosted runners.

The immediate problem is not only total work. It is also work shape:

- one lane builds multiple images serially on one runner
- the same lane couples build, metadata validation, tar export, and proof
- every new image added to the repository threatens to make the single PR lane
  heavier and more fragile

The project needs a scaling pattern that allows the number of images to grow
without forcing one runner to carry the whole cost.

## Problem Statement

What CI structure should the repository use so that image-backed proofing can
scale to an arbitrary number of images while remaining:

- compatible with GitHub's free hosted standard runners
- explicit and reviewable
- aligned with starter and image metadata
- robust against per-runner disk limits

## Design Space Dimensions

Key variables that define the solution space:

- Per-runner disk pressure
- Total workflow parallelism
- Contract clarity
- Metadata reuse
- Scalability as the image count grows

## Options in the Space

### Option A: One monolithic image-proof job

**Position in space:**
- Per-runner disk pressure: worst
- Total workflow parallelism: low
- Contract clarity: medium
- Metadata reuse: low
- Scalability: weak

**Characteristics:**
- Simple YAML initially
- All image builds accumulate on one runner
- A growing image catalog grows one job's failure surface
- The current branch failure is evidence of this limit

### Option B: Manual per-image jobs in workflow YAML

**Position in space:**
- Per-runner disk pressure: good
- Total workflow parallelism: high
- Contract clarity: high
- Metadata reuse: low
- Scalability: medium

**Characteristics:**
- Split image proof into multiple jobs
- Each job gets a fresh runner and isolated Docker state
- Works for a small fixed image set
- Becomes repetitive and drift-prone as image count grows

### Option C: Parameterized matrix fanout by image target

**Position in space:**
- Per-runner disk pressure: good
- Total workflow parallelism: high
- Contract clarity: high
- Metadata reuse: medium-high
- Scalability: strong

**Characteristics:**
- A planner job defines the image-proof matrix
- Each matrix job builds only one image target and runs only proofs that depend
  on that image
- The workflow scales by adding matrix entries instead of more hand-written jobs
- Named profiles such as `pr`, `full`, or `release` can control which targets
  are included

### Option D: Starter-centric matrix fanout

**Position in space:**
- Per-runner disk pressure: medium
- Total workflow parallelism: high
- Contract clarity: high
- Metadata reuse: high
- Scalability: medium

**Characteristics:**
- Fan out by starter instead of by image
- Closer to user-facing proof intent
- Risks duplicate builds when multiple starters depend on the same image
- Better suited for source-template proof than shared-image proof

## Design Space Map

| Option | Disk pressure | Parallelism | Drift risk | Scales with image count? |
|--------|---------------|-------------|------------|---------------------------|
| A | High | Low | Medium | Poorly |
| B | Low | High | High | Moderately |
| C | Low | High | Low-Med | Well |
| D | Medium | High | Medium | Mixed |

## Dominated Solutions

Options that are strictly worse than others:

- Keeping one monolithic image-backed proof job as the image catalog grows.
  It is dominated by fanout approaches because it concentrates disk pressure
  and does not use the free parallelism that public GitHub-hosted runners allow.

## Constraints That Narrow the Space

Hard constraints that eliminate options:

- Standard GitHub-hosted runners on public repos remain the free execution
  tier.
- Each GitHub-hosted runner still has a fixed per-runner disk budget and cannot
  share local Docker images with another job.
- The matrix job count is capped at `256 jobs` per workflow run.
- GitHub Free allows `20` concurrent standard hosted jobs.
- Each hosted job can run for up to `6 hours`.
- Job outputs are limited to `1 MB` per job and `50 MB` total per workflow run.
- The repository should keep `task ci` semantically stable rather than making
  it a hidden function of workflow-only parameters.

## Evidence

Data supporting this design space mapping:

- The current branch hit runner disk exhaustion in run `25239181369` after the
  maintainer control-path fix, demonstrating the failure mode of concentrated
  image work on one runner.
- `Taskfile.yml` currently hard-codes `task image:build` as a full set build
  plus tar export path.
- `starters:verify:image-backed` currently uses only a subset of the built
  images, which shows that proof scope and build scope are not identical.
- `published-image-catalog.toml` already expresses the repository's published
  image inventory.
- `starters/catalog.toml` already expresses starter-level proof metadata.
- GitHub Actions docs confirm:
  - matrix jobs can fan out to multiple parallel jobs
  - `max-parallel` can throttle matrix concurrency
  - matrix size is capped at `256 jobs`
  - standard free hosted runners allow `20` concurrent jobs
  - each job runs on an isolated fresh runner

## Insights

Key learnings from mapping the space:

- The right primitive for scaling published-image proof is the image, not the
  monolithic workflow lane.
- The right API for selecting subsets is a named proof profile, not hidden
  environment-driven behavior in root `task ci`.
- Image-centric fanout avoids rebuilding the same image once per starter when
  multiple starters could depend on the same image in the future.
- Matrix fanout does not solve per-image oversize problems, but it prevents the
  total image set from collapsing onto one runner.

## Decision Guidance

### Narrowing the Space

How to progressively eliminate options:

1. Reject monolithic image-proof growth as the default scaling strategy.
2. Prefer image-centric rather than starter-centric fanout for published-image
   proof where starter-to-image relationships are many-to-one.
3. Prefer matrix-generated jobs over hand-written per-image jobs once the image
   catalog is expected to grow further.

### Convergence Strategy

When and how to commit to a solution:

- Use a planner job to emit a compact JSON matrix for a named profile such as
  `pr`, `full`, or `release`.
- Fan that matrix out into one image-proof job per image target.
- Keep scan and tar-export behavior profile-dependent so PR lanes can avoid
  release-only baggage.
- Reuse the same planner logic across PR CI and release workflows, while
  allowing them to choose different profiles.

## Proposed Pattern

Recommended scaling pattern:

1. **Planner job**
   - Reads repo metadata and selected profile.
   - Emits matrix entries such as:
     - image id
     - dockerfile
     - devcontainer metadata path
     - dependent starters
     - whether tar export is required
     - whether starter scenarios are required

2. **Image-proof matrix job**
   - Runs once per matrix entry on a fresh hosted runner.
   - Builds only the selected image.
   - Validates only that image's devcontainer metadata.
   - Runs only the starter proofs that depend on that image.
   - Skips tar export unless the selected profile requires scan artifacts.

3. **Optional downstream jobs**
   - Aggregate reports.
   - Upload artifacts.
   - Run release-only scans or publication steps.

## Why This Pattern Scales

- Adding a new image becomes metadata work plus a new matrix entry, not another
  hard-coded proof lane.
- The free tier's parallel job allowance can absorb growth better than a single
  runner's disk budget can.
- `max-parallel` provides a throttle when the image count grows faster than the
  account's practical concurrency budget.
- Fresh-runner isolation keeps each image job's failure localized.

## What This Pattern Does Not Solve

- It does not make an individual oversized image fit on a 14 GB runner.
- It does not allow one matrix job to reuse another job's local Docker images.
- It does not remove the need for explicit profile policy about what blocks PRs
  versus what runs in stronger lanes.

## GitHub Actions Limits That Matter

Relevant platform constraints:

- Matrix size: `256 jobs / workflow run`
- Standard GitHub-hosted runner concurrency on GitHub Free: `20 jobs`
- Hosted job execution time: `6 hours / job`
- Job outputs: `1 MB / job`
- Total workflow outputs: `50 MB / workflow run`
- Hosted runner storage is fixed per runner and cannot be increased by support

These limits mean:

- the planner output must stay compact
- the matrix should represent image targets, not individual files or tiny tasks
- `max-parallel` should be used to avoid self-inflicted queueing or resource spikes
- artifact- or tar-based image sharing between jobs is a poor default scaling mechanism

## Recommendations

Suggested path forward:

- Adopt image-centric matrix fanout as the long-term scaling pattern for
  published-image proof.
- Use named proof profiles to choose which image targets a workflow runs.
- Keep root `task ci` stable, and let workflows call stronger parameterized
  proof tasks explicitly.
- Separate build-only PR proof from build-plus-save scan or release workflows.
- Measure disk usage in the current lane before implementing the first profile
  split so the initial `pr` profile is evidence-driven.

## Applicability

Where this design space applies:

- Applies to: GitHub-hosted CI for starter image proof, growing published image
  catalogs, free-tier workflow design
- Does not apply to: single-image repos, paid larger-runner strategies, or
  self-hosted runners with shared local image caching

## Related Knowledge

- `KB-2026-031-full-test-bar-vs-fast-default-feedback-loop.md`
- `KB-2026-037-curated-composition-profiles-minimize-starter-compatibility-risk.md`
- `KB-2026-049-github-standard-runner-disk-exhaustion-during-image-backed-starter-proofs.md`
- `KB-2026-050-free-tier-ci-knowledge-gaps-for-image-backed-starter-proofing.md`
- `KB-2026-051-parameterized-image-proof-profiles-for-free-tier-ci.md`

## Sources

- GitHub Actions limits: <https://docs.github.com/en/actions/reference/limits>
- GitHub workflow syntax: <https://docs.github.com/en/actions/reference/workflows-and-actions/workflow-syntax>
- GitHub matrix jobs and shared matrix example: <https://docs.github.com/en/actions/using-jobs/using-a-matrix-for-your-jobs>
- GitHub concurrency model: <https://docs.github.com/en/actions/concepts/workflows-and-actions/concurrency>
- GitHub billing and usage: <https://docs.github.com/en/actions/concepts/billing-and-usage>
