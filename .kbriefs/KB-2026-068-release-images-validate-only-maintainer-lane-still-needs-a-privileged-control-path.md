---
id: KB-2026-068
type: failure-mode
status: active
created: 2026-05-03
updated: 2026-05-03
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

# Release-Images Validate-Only Maintainer Lane Still Needs A Privileged Control Path

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

## Implications

- `validate-only` semantics are now proven publish-free
- the hosted heavyweight proof path is still not green, because the maintainer
  target uses the wrong validation control path
- the workload-image release lanes and the maintainer-image release lane should
  no longer be treated as if they have the same runtime needs

## Recommendations

- keep the publish-free `validate-only` semantics; that part is correct
- adapt maintainer validation in `release-images` so it uses a maintainer-aware
  control path instead of raw `docker run` for root `task ci`
- alternatively, narrow what the maintainer lane proves so it does not invoke
  root `task ci` in a context that cannot satisfy nested runtime requirements
- treat this as a prerequisite before claiming the hosted full-release lane on
  `main` is proven

## Applicability

- Applies to: maintainer target validation inside `.github/workflows/release-images.yml`
- Does not apply to: workload-image validate-only lanes such as `java`,
  `python-node`, and `diagrams`, which succeeded in the same run

## Related Knowledge

- [KB-2026-036](KB-2026-036-maintainer-control-path-drift-breaks-image-backed-proofs.md)
- [KB-2026-058](KB-2026-058-full-release-validation-and-release-publication-still-need-a-single-build-gate.md)
- [KB-2026-063](KB-2026-063-image-release-gating-implementation-plan.md)
