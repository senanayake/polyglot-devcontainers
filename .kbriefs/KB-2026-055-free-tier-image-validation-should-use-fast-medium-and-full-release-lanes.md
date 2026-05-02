---
id: KB-2026-055
type: standard
status: draft
created: 2026-05-02
updated: 2026-05-02
tags: [github-actions, free-tier, ci, matrix, published-images, release, starter-proofs]
related:
  - KB-2026-049
  - KB-2026-050
  - KB-2026-051
  - KB-2026-052
  - KB-2026-053
  - KB-2026-054
---

# Free-Tier Image Validation Should Use Fast, Medium, and Full-Release Lanes

## Context

The repository originally treated published-image validation as one monolithic
lane:

- build every verify image
- save every image as a tar archive
- run image-backed starter proofs
- run image-local `task ci`
- run local image security scans

That made the default PR path too slow and too storage-heavy for GitHub-hosted
free-tier runners. It also made targeted local work inefficient, because even a
developer who only wanted to validate `python-node` had to pay for unrelated
image builds and the slowest validation steps.

## Decision

Published-image validation should be split into three named lanes:

1. `fast`
   - default for targeted local image work
   - build and validate selected images only
   - no tar export
   - no image smoke test
   - no in-image `task ci`

2. `medium`
   - default PR lane for published-image starter coverage
   - keep the fast repository lane separate from image-backed starter proofs
   - run image-backed starter proofs one image at a time
   - fan those proofs out as parallel GitHub matrix jobs on the free tier
   - skip tar export and other release-only steps

3. `full-release`
   - explicit slow lane for release-grade validation
   - build every published image
   - validate metadata
   - run smoke tests where relevant
   - save tar archives
   - run in-image `task ci`
   - run local image scans

## Standard

The repository should make image targets first-class data and use one planner to
drive both Taskfile entry points and GitHub Actions matrices.

That planner should support:

- selecting a single image by stable target id such as `python-node`
- selecting the default target set for a named lane
- toggling slow steps by profile instead of hard-coding one global behavior
- emitting a GitHub matrix for parallel fanout

## Why This Works On The Free Tier

- PR CI wall-clock time drops because Java and Python/Node starter-image proofs
  no longer wait on each other.
- Per-job storage pressure drops because each medium job builds only one image
  instead of accumulating the full image inventory.
- Local validation becomes practical for focused work:
  - `task image:build -- --image python-node`
  - `task image:build -- --profile full-release --image python-node`
- Full release coverage remains available as an explicit lane instead of being
  forced into every PR run.

## Implications

- `task ci` should map to the medium free-tier lane, not the heaviest possible
  release lane.
- `task ci:fast` should exist as a first-class repository lane for quick core
  validation.
- `task ci:full-release` should exist as a first-class explicit slow lane.
- Published-image starter proofs should run in their own matrix jobs in GitHub
  Actions.
- Release workflows should consume the same image planner as PR CI to avoid
  image-list drift.

## Applicability

### This Standard Applies To

- root `Taskfile.yml`
- `.github/workflows/ci.yml`
- `.github/workflows/release-images.yml`
- published image target metadata and matrix planning

### This Standard Does Not Apply To

- downstream consumer repositories that only pull one released image
- local workflows that intentionally choose a custom subset of slow steps
