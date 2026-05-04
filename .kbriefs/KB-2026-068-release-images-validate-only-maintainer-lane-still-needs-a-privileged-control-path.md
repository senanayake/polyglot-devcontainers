---
id: KB-2026-068
type: failure-mode
status: active
created: 2026-05-03
updated: 2026-05-04
tags:
  - release-images
  - validate-only
  - maintainer
  - nested-docker
  - github-actions
  - kbpd
related:
  - KB-2026-036
  - KB-2026-058
  - KB-2026-063
---

# Release-Images Maintainer Validation Requires A Privileged Control Path

## Context

The repository introduced `release-images` manual `validate-only` mode so a
specific `main` commit can be validated without publishing release artifacts.

That mode was expected to become the first hosted proof of the heavyweight
release path on `main`.

## System/Component

- `.github/workflows/release-images.yml`
- manual `workflow_dispatch` with `release_mode=validate-only`
- maintainer matrix entry in the release-image matrix

## Failure Description

### Symptoms

- `release-images` run `25294168787` on `main` finished `failure`
- `python-node`, `java`, and `diagrams` validate-only lanes succeeded
- the failing lane was:
  - `publish (maintainer, polyglot-devcontainers-maintainer, ...)`

### Failure Mechanism

The maintainer lane built the maintainer image successfully and then failed in
`Run task ci inside built image`.

Inside that container, root `task ci` reached `task ci:medium`, which reached
`task starters:verify:image-backed`, which requires nested container runtime.

The release workflow executes the built maintainer image through raw
`docker run`, not through the privileged maintainer control path. Nested
`dockerd` therefore failed with the familiar iptables/NAT-chain error:

```text
failed to start daemon: Error initializing network controller:
failed to create NAT chain DOCKER: iptables ... Permission denied
```

## Root Cause

`release-images` validate-only mode is publish-free, but its maintainer lane
still validates the maintainer image by running root `task ci` inside an
unprivileged raw Docker container.

That execution model is incompatible with the current root task contract,
because root `task ci` now includes image-backed starter proofing that needs a
privileged nested OCI runtime.

This is the same control-path class of problem previously identified for raw
container execution in CI, but now reproduced in the maintainer lane of
`release-images`.

## What Was Tested

On 2026-05-03, `release-images` was triggered manually against `main`:

```text
workflow_dispatch
release_mode=validate-only
```

Run URL:

- `https://github.com/senanayake/polyglot-devcontainers/actions/runs/25294168787`

Observed result:

- validate-only semantics were correct:
  - GHCR login skipped
  - push skipped
  - SBOM/sign/attest/Trivy/release-note jobs skipped
- maintainer lane still failed during validation

## Evidence

- run `25294168787`
- failing job:
  - `74150282962`
- failing step:
  - `Run task ci inside built image`
- successful publish-free evidence:
  - `Log in to GHCR` skipped
  - `Build and push image` skipped
  - release-side jobs skipped:
    - `publish-release-notes`
    - `prepare-release-security`
    - `publish-release-security-docs`
    - `publish-release-security`
    - `update-readme-recent-releases`

## Resolution And Follow-Up Proof

On 2026-05-04, branch `codex/full-release-proof-main` changed
`.github/workflows/release-images.yml` so the matrix uses two distinct
validation paths:

- maintainer target:
  - `docker run --rm --privileged ... task ci`
- workload targets:
  - existing unprivileged raw `docker run`

That branch was then proven with a manual hosted run:

- run `25295665680`
- ref `codex/full-release-proof-main`
- mode `validate-only`

Observed result:

- overall workflow conclusion: `success`
- workload-image lanes still succeeded:
  - `java`
  - `python-node`
  - `diagrams`
- maintainer lane also succeeded:
  - `Run maintainer task ci inside built image`
- publish-side steps and release-side jobs remained skipped as intended

## Implications

- `validate-only` semantics are proven publish-free
- maintainer validation in `release-images` is compatible with root `task ci`
  when it uses the privileged path
- workload-image lanes and maintainer-image lanes have distinct runtime needs
  and should keep distinct validation steps
- the remaining release-work gaps have moved upstream to:
  - merging this control-path fix to `main`
  - proving the hosted heavyweight lane on `main`
  - commit-scoped release evidence
  - `cut-release` gating
  - digest continuity

## Recommendations

- keep the publish-free `validate-only` semantics; that part is correct
- keep maintainer validation in `release-images` on the privileged path
- keep workload-image validation on the lighter unprivileged path
- treat this K-Brief as the failure-mode and remediation record for future
  regressions

## Applicability

- Applies to: maintainer target validation inside `.github/workflows/release-images.yml`
- Does not apply to: workload-image validate-only lanes such as `java`,
  `python-node`, and `diagrams`, which succeeded in the same run

## Related Knowledge

- [KB-2026-036](KB-2026-036-maintainer-control-path-drift-breaks-image-backed-proofs.md)
- [KB-2026-058](KB-2026-058-full-release-validation-and-release-publication-still-need-a-single-build-gate.md)
- [KB-2026-063](KB-2026-063-image-release-gating-implementation-plan.md)
