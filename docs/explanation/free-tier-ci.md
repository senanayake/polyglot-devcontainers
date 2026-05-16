# Free-Tier CI Architecture

The repository now treats CI as a layered evidence system rather than one
monolithic job.

## Why The CI Shape Changed

The earlier starter-generator work added image-backed starter proofing to the
default CI path. That improved coverage, but it also collapsed too much work
onto one GitHub-hosted runner:

- multiple nested image builds
- starter bootstrap smoke proofs
- release-oriented artifact behavior

On GitHub's free standard runners, that shape exhausted storage and made the
default development loop too slow and fragile.

The repository now solves that by separating:

- core repository proof
- default published-image proof
- heavyweight release proof

## The Three Lanes

### `ci:repo-core`

This is the core repository lane.

It proves:

- the maintainer image can be built
- the maintainer image metadata is valid
- the maintainer control path works
- the repository-wide `init`, `lint`, `test`, and `scan` contract works
- source-template starter proofs and repo scenarios still pass

It does **not** prove the published workload images.

### `ci:medium`

This is the default branch confidence lane.

Root `task ci` now maps to this lane.

It keeps `ci:repo-core` as one parallel job and fans published-image work out
by image target. Each medium image job:

- builds exactly one published image
- validates that image's devcontainer metadata
- runs the medium smoke path for that image
- runs starter-proof follow-up only if that image publishes a starter contract

Today the default medium matrix covers:

- `diagrams`
- `java`
- `python-node`

That means the branch loop validates all default published workload images
without forcing one runner to carry all image state at once.

### `ci:full-release`

This is the heavyweight lane.

It is intended to do the strongest local image validation bar:

- build every published image
- validate metadata
- run smoke proofs
- save image tar archives
- run in-image `task ci`
- run local image scans

This lane exists, but it has **not** yet been re-proven end to end after the
free-tier CI restructuring. That gap is intentional to defer pre-merge scope
growth, and it is tracked in the repository knowledge base.

## Why The Medium Lane Uses A Matrix

The scaling primitive is the image, not the workflow.

The planner in
[`scripts/published_image_pipeline.py`](../../scripts/published_image_pipeline.py)
reads
[`published-image-catalog.toml`](../../published-image-catalog.toml)
and emits the matrix for a named profile.

For `medium`, that gives one job per image target instead of one job for the
entire image inventory.

That matters because:

- each GitHub Actions job gets a fresh runner
- local Docker state is not shared across jobs
- parallel jobs use the free-tier concurrency budget better than one huge job
- storage pressure is contained to one image at a time

## Why `ci:repo-core` Still Builds The Maintainer Image

The maintainer image is not optional infrastructure. It is the repository's
authoritative execution environment.

So the core lane must still prove:

- the maintainer image builds
- its embedded devcontainer metadata is correct
- repository tasks can run through the official maintainer control path

That is why the lane is called `repo-core`, not just `lint-and-test`.

## Branch Pushes, Mainline Pushes, And PR Runs

The default free-tier CI now runs on pushes, not only on PRs.

On non-`main` branches, it provides development proof:

- `ci-repo-core`
- medium image validation jobs

On `main`, it provides the same proof and then publishes integration-grade
workload images for fast downstream testing.

The workflow also uses GitHub Actions concurrency cancellation so a new push
replaces an older in-flight run on the same branch.

## Mainline Integration Publication

When the same workflow runs on `main`, a follow-on publish job pushes
integration-grade workload images after medium proof succeeds.

That channel is intentionally separate from semver release publication:

- it publishes moving `main` tags
- it publishes immutable SHA tags
- it does not publish `latest`
- it does not create release notes
- it does not generate release-security docs

This keeps merged `main` quickly consumable without collapsing release-grade
evidence into the fast loop.

## Local Command Mapping

The GitHub checks map to local maintainer-container commands:

```bash
task ci
task ci:repo-core
task image:build -- --profile medium --image diagrams
task image:build -- --profile medium --image java
task image:build -- --profile medium --image python-node
task starters:verify:image-backed -- --profile medium --skip-build --image java
task starters:verify:image-backed -- --profile medium --skip-build --image python-node
```

The mainline publication job then rebuilds from the same commit and pushes the
medium-validated image set as integration images. That publication step exists
only on `main`.

Targeted work can stay narrower:

```bash
task image:build -- --profile fast --image python-node
task image:build -- --profile medium --image python-node
task image:verify -- --image python-node
```

## What Is Proven Today

The following has been proven in the free-tier CI model:

- `ci-repo-core`
- `medium / diagrams`
- `medium / java`
- `medium / python-node`

Those successful runs establish the new default branch-development model.

The next proven addition is the `main` integration publication model, where the
same medium-validated image set becomes available under moving `main` and SHA
tags for downstream integration loops.

## What Is Still A Knowledge Gap

The remaining gap is not default branch CI. It is release-grade proof and
release gating.

In particular:

- the heavyweight `full-release` path has not yet been re-run end to end after
  the branch-CI restructuring
- the release workflow still validates one build and then performs a separate
  build-and-push step

That means the release process still needs a stronger single-build or
promotion-style gate before it should be treated as the final release evidence
model.

See:

- [KB-2026-055](../../.kbriefs/KB-2026-055-free-tier-image-validation-should-use-fast-medium-and-full-release-lanes.md)
- [KB-2026-057](../../.kbriefs/KB-2026-057-default-free-tier-ci-should-run-on-branch-push-and-fan-out-medium-image-builds.md)
- [KB-2026-058](../../.kbriefs/KB-2026-058-full-release-validation-and-release-publication-still-need-a-single-build-gate.md)
- [KB-2026-063](../../.kbriefs/KB-2026-063-image-release-gating-implementation-plan.md)
- [KB-2026-064](../../.kbriefs/KB-2026-064-mainline-medium-validated-images-should-feed-fast-integration-loops.md)
