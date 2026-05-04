---
id: KB-2026-067
type: failure-mode
status: active
created: 2026-05-03
updated: 2026-05-04
tags:
  - maintainer-image
  - full-release
  - local-proof
  - cache
  - podman
  - kbpd
related:
  - KB-2026-058
  - KB-2026-063
---

# Cached Maintainer Main Reuse Can Block Local Full-Release Proof

## Context

The repository prefers the published maintainer image as the control path for
local maintainer and agent workflows.

That preference depends not only on the published image being correct, but also
on the local control path actually refreshing a moving tag such as `:main`.

## System/Component

- `ghcr.io/senanayake/polyglot-devcontainers-maintainer:main`
- `python scripts/run_in_maintainer_container.py exec -- task ci:full-release`
- Podman-backed local devcontainer reuse

## Failure Description

### Symptoms

- local full-release proof on `main` commit `6bf92f0` failed before any
  heavyweight image build or scan work completed
- failure occurred in `task ci:repo-core`
- failing path was `examples/diagram-image-example` lint

### Failure Mechanism

Inside the locally reused maintainer container, the diagram lint path attempted
to run:

```text
d2 fmt --check ...
```

and failed with:

```text
bash: line 2: d2: command not found
```

## Initial Hypothesis

The first hypothesis was that the published maintainer image on GHCR was
behind current `main`.

## What Was Tested

1. Local full-release proof was attempted:

```bash
python scripts/run_in_maintainer_container.py exec -- task ci:full-release
```

2. The reused local maintainer container was inspected and showed no `d2` or
   `diagram` binary.
3. A fresh pull of `ghcr.io/senanayake/polyglot-devcontainers-maintainer:main`
   was performed with Podman.
4. Running the freshly pulled image directly showed both binaries:

```text
/usr/local/bin/d2
/usr/local/bin/diagram
```

5. The old maintainer container was removed and recreated, after which direct
   maintainer-container probes also showed both binaries.

## Root Cause

The local proof path was using a stale cached/reused `:main` maintainer image
and container state, not the current GHCR image contents.

The moving tag `ghcr.io/...:main` had advanced, but the local Podman-backed
maintainer workflow continued to reuse older local state until a manual pull
and container recreation occurred.

## Evidence

- before refresh:
  - `podman exec <old-container> command -v d2` returned nothing
  - `podman exec <old-container> command -v diagram` returned nothing
- after `podman pull ghcr.io/senanayake/polyglot-devcontainers-maintainer:main`:
  - image digest resolved to
    `ghcr.io/senanayake/polyglot-devcontainers-maintainer@sha256:833dc3cc9a6e0dec01ebb07f86a357b2189180fcf507c50c59876ffb1b74d6a3`
  - direct image run showed:
    - `/usr/local/bin/d2`
    - `/usr/local/bin/diagram`
- after removing the old container, a new maintainer container also showed both
  binaries

## Implications

- local authoritative proof on a moving maintainer tag is vulnerable to stale
  cache/container reuse
- a local failure against `ghcr.io/...:main` does not, by itself, prove that
  the currently published GHCR image is wrong
- "prefer the published maintainer image" remains correct, but local proof on a
  moving tag needs an explicit refresh/recreation policy

## Recommendations

- treat local maintainer proof on a moving tag as requiring:
  - explicit pull freshness
  - or container recreation
  - or a digest/scoped immutable tag instead of `:main`
- when debugging local maintainer proof failures, distinguish:
  - stale local cache/container reuse
  - from actual GHCR publication defects

## Applicability

- Applies to: local maintainer-container proof paths using a moving image tag
  such as `:main`
- Does not apply to: hosted GitHub Actions lanes that rebuild the image from
  source in the workflow

## Related Knowledge

- [KB-2026-058](KB-2026-058-full-release-validation-and-release-publication-still-need-a-single-build-gate.md)
- [KB-2026-063](KB-2026-063-image-release-gating-implementation-plan.md)
