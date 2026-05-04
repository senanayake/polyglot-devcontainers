---
id: KB-2026-058
type: design-space
status: active
created: 2026-05-02
updated: 2026-05-04
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
  - KB-2026-062
---

# Full-Release Validation And Release Publication Still Need A Single-Build Gate

## Context

The repository now has a proven free-tier branch CI model:

- `ci-repo-core`
- `medium / diagrams`
- `medium / java`
- `medium / python-node`

That closes the default branch-confidence problem. It does **not** yet prove
that release publication happens only after full-release evidence exists, and it
does not yet guarantee that the digest which gets published to GHCR is the
exact artifact that passed heavyweight validation.

## Problem Statement

How should the repository adapt the `full-release`, `release-images`, and
`cut-release` path so that:

- full-release validation is an explicit authoritative gate
- release publication happens only after that gate passes
- the pushed digest is demonstrably the validated artifact, not a later rebuild
- release-scan success is defined consistently with the repository's residual
  risk policy

## Design Space Dimensions

- Evidence strength for the published digest
- Irreversibility point in the release flow
- Workflow complexity
- Release latency and cost
- Human confidence at release time

## Current State

The `main` branch release surface is now more capable than the earlier branch
CI work assumed:

1. `.github/workflows/cut-release.yml` exists and can compute the next semantic
   tag, push it, dispatch `release-images`, and wait for the downstream run.
2. `.github/workflows/release-images.yml` now supports manual
   `workflow_dispatch` with `release_mode=validate-only` or
   `release_mode=full-release`.
3. `validate-only` is now publish-free, and moving `main` tags for workload
   images are owned by the separate `main` integration channel rather than the
   release workflow.
4. `scripts/published_image_pipeline.py` already defines a local
   `full-release` profile that means:
   - build the image
   - validate devcontainer metadata
   - run starter smoke proof where relevant
   - run `task ci` inside the built image
   - save the image tarball
   - scan the saved tarball and summarize residual risk in a separate step
5. branch `codex/full-release-proof-main` has now proven that
   `release-images` `validate-only` can complete successfully for the full
   release matrix in hosted Linux when the maintainer target uses a privileged
   validation path.

Those improvements still leave several release-gating gaps.

### Gap 1: Scan Evidence Is Post-Push And Non-Blocking

The release workflow still scans only after the digest has already been pushed.
Both Trivy steps run against the published digest and use `exit-code: 0`.

That behavior is correct for `KB-2026-038`, which established that upstream
residual findings must be reported rather than blindly blocking release. It
also means the current workflow does **not** yet enforce a pre-publication scan
gate.

### Gap 2: Version Tagging Happens Before Heavyweight Proof Completes

`cut-release` pushes the semantic version tag before the downstream
`release-images` workflow finishes. If the downstream full release fails, the
repository is left with a version tag that did not complete a successful full
release.

### Gap 3: Release Trigger Semantics Are Still Ambiguous

`release-images` runs on semantic version tag pushes, and `cut-release` also
dispatches `release-images` manually after pushing the tag.

The workflow definitions therefore permit overlapping trigger paths for the
same release tag unless some outside condition prevents one of them from
running. That ambiguity should be removed before the release process is treated
as settled.

## What Was Tested

### Local Single-Image Full-Release Slice

On 2026-05-03, a single-image local heavyweight proof was run from the
maintainer container using the repository task contract:

```bash
python scripts/run_in_maintainer_container.py exec -- \
  task image:build -- --profile full-release --image diagrams \
  --disk-label-prefix local-full-release-diagrams-task

python scripts/run_in_maintainer_container.py exec -- \
  task image:scan -- --image diagrams
```

Observed behavior:

- the run succeeded when invoked through `task image:build`
- the same pipeline failed when invoked directly through
  `published_image_pipeline.py build` because that bypassed
  `_require_image_runtime`
- the successful task-based run produced:
  - a validated local image `polyglot-devcontainers-diagrams:verify`
  - starter smoke proof success
  - in-image `task ci` success
  - a saved tarball at `.artifacts/images/diagrams.tar`
  - Trivy summary artifacts under `.artifacts/scans/image-security/`
  - residual-risk artifacts under `.artifacts/scans/image-security/`

### Local Evidence Snapshot

From that local slice:

- `.artifacts/images/diagrams.tar` was about `1.3 GiB`
- `trivy-diagrams-summary.md` reported:
  - `Critical: 2`
  - `High: 15`
- `residual-risk.md` classified both critical findings as
  `upstream_residual`

That confirms the local `full-release` path already encodes the right policy
shape for a release gate:

- proof first
- scan completion second
- residual-risk classification third

It does **not** require zero findings to count as a successful scan.

### Local Full-Release Task Proof On Current Main

On 2026-05-03, local heavyweight proof was then attempted on current `main`
commit `6bf92f0` from a clean clone using the repo-owned top-level task:

```bash
python scripts/run_in_maintainer_container.py exec -- task ci:full-release
```

Observed behavior in the first pass:

- the run failed before heavyweight image verification started
- the failure happened inside `task ci:repo-core`
- `examples/diagram-image-example` lint failed with:
  - `bash: line 2: d2: command not found`

Additional investigation showed that this first local blocker came from stale
cached/reused maintainer `:main` state, not from the current GHCR image
contents. After a fresh pull and container recreation, local proof progressed
far beyond repo-core and into image-backed starter proofing.

Observed behavior in the second pass after refresh:

- repo-core proof advanced successfully
- the run then failed in `task starters:verify:image-backed`
- the specific failing nested proof was Java published-image bootstrap
- Gradle failed in the nested smoke container with:
  - `Could not set file mode 700 on /workspaces/project/.gradle/daemon/9.1.0`

That second blocker looks like a Windows + Podman local-environment boundary,
not evidence that the hosted Linux release workload lanes are broken.

### Hosted Release-Images Validate-Only Proof On Current Main

On 2026-05-03, `release-images` was run manually on `main` with:

- `release_mode=validate-only`

Run:

- `25294168787`

Observed behavior:

- publish-free semantics were proven:
  - GHCR login skipped
  - image push skipped
  - SBOM/sign/attest/Trivy/release-security steps skipped
  - release-note and release-doc publication jobs skipped
- workload-image validation succeeded for:
  - `python-node`
  - `java`
  - `diagrams`
- the overall run still failed in the `maintainer` matrix entry

The maintainer failure occurred because `release-images` validates the built
maintainer image by running root `task ci` inside raw `docker run`, which is
not compatible with the current root task contract once that contract reaches
`task starters:verify:image-backed`.

### Hosted Release-Images Validate-Only Proof With Maintainer Fix

On 2026-05-04, branch `codex/full-release-proof-main` was validated with:

- `release_mode=validate-only`

Run:

- `25295665680`

Observed behavior:

- overall workflow conclusion: `success`
- workload-image validation succeeded for:
  - `python-node`
  - `java`
  - `diagrams`
- maintainer validation also succeeded after switching that matrix entry to:
  - `docker run --rm --privileged ... task ci`
- publish-side steps and release-side jobs remained skipped

That run proves the hosted Linux maintainer-lane control-path issue is solved
by the workflow change. It does **not** yet prove the same behavior on `main`
until the fix is merged and rerun there.

## Options In The Space

### Option A: Keep The Current Two-Build, Tag-First Release Workflow

**Position in space:**
- Evidence strength: low-medium
- Complexity: low
- Drift risk: high

**Characteristics:**
- validates one build
- publishes a separate rebuild
- pushes the release tag before full-release success is known

### Option B: Separate Mainline Full-Release Validation From Publication

**Position in space:**
- Evidence strength: high
- Complexity: medium
- Drift risk: medium

**Characteristics:**
- create explicit full-release evidence on a target `main` commit first
- allow `cut-release` only for commits with successful recorded evidence
- still leaves digest continuity unresolved if publication rebuilds

### Option C: Validate Then Push The Exact Local Validated Image

**Position in space:**
- Evidence strength: high
- Complexity: medium
- Drift risk: low

**Characteristics:**
- validate the local built image
- retag and push the same local image after success
- reduces rebuild drift substantially

### Option D: Build Once To A Candidate Digest, Validate That Digest, Then Promote

**Position in space:**
- Evidence strength: very high
- Complexity: high
- Drift risk: very low

**Characteristics:**
- build candidate digest once
- validate the candidate digest
- promote that exact digest after success
- strongest chain of custody for the released artifact

## Design Space Map

| Option | Evidence strength | Complexity | Tag timing risk | Digest drift risk |
|--------|-------------------|------------|-----------------|-------------------|
| A | Low-Med | Low | High | High |
| B | High | Med | Low | Med |
| C | High | Med | Med | Low |
| D | Very High | High | Low | Very Low |

## Constraints That Narrow The Space

- `KB-2026-038` already decided that release scans should report upstream
  residual risk instead of hard-failing on every finding.
- The repository wants a release process that stays understandable for a small
  free-tier project.
- The maintainer/container-first validation model remains the source of truth.
- The authoritative proof path has to stay within the repo task contract, not
  ad hoc host-side shell steps.

## Unexplored Regions

- exact wall-clock and storage profile of the **full four-image** mainline
  `full-release` matrix after the CI split
- whether `cut-release` has already exercised both release trigger paths for
  the same tag in practice
- the best mechanism for preserving digest identity between validation and
  publication
- how maintainer-target validation in `release-images` should satisfy the root
  task contract now that root `task ci` requires image-backed starter proofing

## Evidence

- `.github/workflows/release-images.yml` currently contains separate
  `Build image for validation` and `Build and push image` steps
- `.github/workflows/release-images.yml` scans the published digest with Trivy
  after push using `exit-code: 0`
- `.github/workflows/release-images.yml` manual `validate-only` mode now skips
  image publication and release-side effects
- local maintainer-container proof on 2026-05-03 showed:
  - `task ci:full-release` on current `main` was first blocked locally by stale
    cached/reused maintainer `:main` state
  - after refresh, the same proof advanced into nested Java starter proofing
    and then hit a Windows + Podman chmod boundary
- hosted manual `release-images` run `25294168787` showed:
  - `validate-only` is publish-free in practice
  - workload-image validate-only lanes can pass
  - the maintainer lane still fails because raw `docker run` cannot satisfy the
    nested runtime needs of root `task ci`
- `.github/workflows/cut-release.yml` pushes the semantic tag before waiting
  for downstream full-release completion
- public GitHub Actions workflow pages show:
  - `release-images` manual runs on `main`
  - `release-images` tag-triggered runs on `v*.*.*`
  - `cut-release` runs on `main`
- local maintainer-container proof on 2026-05-03 showed the task-based
  `full-release` slice for `diagrams` succeeded and produced both scan and
  residual-risk artifacts

## Insights

- The free-tier branch CI problem is largely solved; the remaining uncertainty
  has moved to release-grade evidence and release orchestration.
- The repository already has a good **workload-image** heavyweight proof shape,
  but there are now two distinct blockers before full hosted release proof can
  be considered settled:
  - local maintainer proof on a moving `:main` tag can be distorted by stale
    cached/reused local image and container state
  - local Windows + Podman proof can hit nested Gradle chmod boundaries that do
    not necessarily reflect hosted Linux behavior
  - hosted maintainer validation in `release-images` originally used a raw
    container execution model that could not satisfy the current root
    `task ci` contract
  - branch `codex/full-release-proof-main` now proves the privileged-path
    remediation in hosted Linux, but that proof still needs to land on `main`
- A successful release scan in this repo must mean:
  - the scan ran successfully
  - the summary artifacts exist
  - residual risk was classified
  - humans can review the result
  It does **not** mean zero findings.

## Recommendations

- Treat the current tag-first `cut-release` flow as a learning artifact, not
  yet the final release-evidence model.
- Treat "publish-free validate-only semantics" as proven.
- Treat "authoritative full-release validation on current main" as still
  unproven until the maintainer-lane fix is merged and rerun on `main`.
- Use the next learning cycle to define a process where:
  - full-release evidence is created for a specific `main` commit first
  - release publication happens only after that evidence exists
  - the final published digest is the validated artifact or a gated promotion
    of it
- Prefer future gates that make both the commit SHA and digest identity explicit
  in the release evidence.

## Applicability

- Applies to: `.github/workflows/cut-release.yml`,
  `.github/workflows/release-images.yml`, heavyweight image validation, release
  publication policy
- Does not apply to: the proven free-tier branch CI lane or source-template
  starter proofing

## Related Knowledge

- [KB-2026-038](KB-2026-038-release-image-scan-must-report-upstream-residual-risk-without-blocking-release.md)
- [KB-2026-055](KB-2026-055-free-tier-image-validation-should-use-fast-medium-and-full-release-lanes.md)
- [KB-2026-057](KB-2026-057-default-free-tier-ci-should-run-on-branch-push-and-fan-out-medium-image-builds.md)
- [KB-2026-062](KB-2026-062-mainline-full-release-evidence-should-gate-cut-release-and-publication.md)
- [KB-2026-067](KB-2026-067-cached-maintainer-main-reuse-can-block-local-full-release-proof.md)
- [KB-2026-068](KB-2026-068-release-images-validate-only-maintainer-lane-still-needs-a-privileged-control-path.md)
- [KB-2026-069](KB-2026-069-windows-podman-bind-mounts-can-break-nested-gradle-starter-proofing.md)
