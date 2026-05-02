---
id: KB-2026-057
type: standard
status: active
created: 2026-05-02
updated: 2026-05-02
tags:
  - ci
  - github-actions
  - free-tier
  - images
  - parallelism
  - starters
related:
  - KB-2026-052
  - KB-2026-055
  - KB-2026-056
---

# Default Free-Tier CI Should Run on Branch Push and Fan Out Medium Image Builds

## Context

The repository now supports fast, medium, and full-release validation lanes. The free-tier default needs to give quick branch feedback, avoid duplicate GitHub Actions execution, and keep image validation scalable as the published image set grows.

## Problem/Need

The earlier workflow waited for pull-request execution and only fanned out the medium lane for the two starter-backed images. That left one published workload image (`diagrams`) outside the default branch feedback loop and forced the user to wait for PR-triggered CI even though the checks are commit-attached.

## Standard/Pattern

### Description

Use branch-push CI as the default free-tier execution path for non-`main` branches, and fan the medium image lane out across every published workload image that belongs in the default validation set. Keep `ci-repo-core` running in parallel with the medium image matrix. For starter-backed images, add a starter-proof follow-up after the medium build instead of rebuilding the image again.

### Key Principles

- Branch pushes should trigger the default free-tier feedback loop.
- Medium image validation should scale by image target, not by one monolithic job.
- Starter-proof follow-up should reuse the image already built in the medium lane.

### Implementation

```yaml
on:
  push:
    branches-ignore:
      - main

jobs:
  plan-medium-image-matrix:
    run: python3 scripts/published_image_pipeline.py matrix --profile medium

  ci-repo-core:
    run: task ci:repo-core

  ci-medium-image-backed:
    strategy:
      matrix: from planner output
    run: task image:build -- --profile medium --image <target>
    if starter-backed:
      run: task starters:verify:image-backed -- --profile medium --skip-build --image <target>
```

## Rationale

- Push-triggered CI gives immediate feedback on feature branches without waiting for PR-only execution.
- A per-image matrix keeps wall clock bounded by the slowest single image job instead of the full image inventory.
- Reusing the already-built image avoids redundant nested image builds in starter-backed matrix entries.

## Benefits

- Every default published workload image gets branch-time validation.
- Parallel image jobs preserve free-tier scalability as image count grows.
- The starter-proof follow-up stays targeted to only the images that actually publish starter contracts.

## Constraints

- This standard applies to the default free-tier workflow, not the full-release lane.
- `ci-repo-core` remains an independent wall-clock bottleneck until its own scope is reduced.
- The maintainer container is still built in each GitHub-hosted job because local Docker state is not shared across runners.

## Alternatives Considered

### PR-Only Execution

- Description: Run the default CI only on `pull_request`.
- Why not chosen: Delays feedback on branch pushes and adds workflow latency for the main development loop.

### Monolithic Medium Image Job

- Description: Build all medium images in one job.
- Why not chosen: Reintroduces the free-tier storage and runtime coupling that the matrix fanout was designed to remove.

### Rebuild Starter-Backed Images During Proof Follow-Up

- Description: Let `starters:verify:image-backed` rebuild the selected image again.
- Why not chosen: Wastes time and storage, and defeats the point of per-image medium jobs.

## Evidence

- The matrix-based fanout in `KB-2026-052` fixed the earlier storage coupling by isolating image work per job.
- The successful run after `KB-2026-056` showed medium starter proofs can reuse branch-local verify images once the smoke workspace contract is correct.
- `ci-repo-core` already runs in parallel with the medium matrix, so branch-push CI now benefits immediately from the existing parallel structure.

## Anti-Patterns

- Waiting for PR-only execution when the same checks can attach to the branch push commit.
- Packing all image validation into one free-tier job.
- Rebuilding an image in the starter-proof step when the current job already built it.

## Verification

- `python scripts/published_image_pipeline.py matrix --profile medium` includes every default medium image target.
- `task image:build -- --profile medium --image <target>` passes for each medium target.
- Starter-backed targets also pass `task starters:verify:image-backed -- --profile medium --skip-build --image <target>`.
- GitHub Actions on a non-`main` branch push creates `ci-repo-core` plus one `medium / <target>` job per medium target.

## Exceptions

- `main` can use other workflows or release-oriented lanes; this standard is about the default branch-development loop.
- Images that are intentionally excluded from the free-tier default can keep `medium_lane = false`.

## Related Knowledge

- [KB-2026-052](C:/dev/polyglot-devcontainers-starter-generator/.kbriefs/KB-2026-052-matrix-based-image-proof-fanout-for-free-tier-ci.md)
- [KB-2026-055](C:/dev/polyglot-devcontainers-starter-generator/.kbriefs/KB-2026-055-free-tier-image-validation-should-use-fast-medium-and-full-release-lanes.md)
- [KB-2026-056](C:/dev/polyglot-devcontainers-starter-generator/.kbriefs/KB-2026-056-published-image-smoke-workspace-overrides-need-permission-normalization.md)

## Success Metrics

- Branch pushes on non-`main` refs start CI immediately.
- The medium matrix includes all intended default published images.
- Starter-backed medium jobs do not perform a second image build before running the proof follow-up.
