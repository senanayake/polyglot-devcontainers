---
id: KB-2026-053
type: standard
status: draft
created: 2026-05-01
updated: 2026-05-01
tags: [github-actions, docker, podman, ci, nested-builds, oci-runtime]
related:
  - KB-2026-035
  - KB-2026-049
  - KB-2026-050
---

# Hosted CI Should Force Docker for Docker-Owned Nested Image Builds

## Context

The repository can use either Podman or Docker through `scripts/oci_runtime.py`,
which prefers Podman when both runtimes are healthy. That flexibility is useful
locally, but hosted GitHub Actions workflows in this repository already build
their maintainer and validation images through Docker-native steps.

When those workflows later invoke nested image builds inside the maintainer
container, allowing the inner proof path to fall back to Podman creates a new
kind of drift: the workflow is nominally Docker-based, but the heavy nested
image work may actually execute on Podman.

## Decision

When a GitHub-hosted workflow builds or launches repository proof images through
Docker-owned paths, it should explicitly force nested image builds to use
Docker as well.

In practice this means:

- forward runtime-selection env vars through the maintainer wrapper
- set `POLYGLOT_OCI_RUNTIME=docker` for hosted CI steps that execute root
  `task ci` or other nested image-building proof paths
- pass the same runtime override into raw `docker run` workflow steps that
  execute repo tasks inside built images

## Why This Is The Right Standard Now

- it preserves one runtime contract across outer and inner hosted CI layers
- it avoids hosted-only Podman storage behavior becoming a hidden variable in
  Docker-owned workflows
- it aligns with `KB-2026-035`, which already showed that runtime/store
  mismatches are CI control-path bugs rather than product bugs

## Evidence

- GitHub Actions run `25243644910` failed during nested `task image:build`
  while building the `diagram-secure` verify image.
- The uploaded nested pre-build diagnostic snapshot showed:
  - `POLYGLOT_CONTAINER_RUNTIME=null`
  - `POLYGLOT_OCI_RUNTIME=null`
  - selected inner runtime: `podman`
- The outer job itself was explicitly Docker-oriented:
  - workflow job env set `POLYGLOT_CONTAINER_RUNTIME=docker`
  - root image was built with `docker build`
  - maintainer container control path used Docker
- `scripts/run_in_maintainer_container.py` previously forwarded only
  `POLYGLOT_CONTAINER_ROLE`, so nested proof commands lost the hosted runtime
  preference unless they exported it manually

## Implications

- Hosted CI workflows should be explicit about runtime choice when nested image
  builds are part of the proof bar.
- Local repository use can still keep flexible runtime preference when no hosted
  Docker-owned artifact chain is involved.
- Future free-tier optimization work should compare like with like by keeping
  the nested runtime fixed while evaluating disk behavior.

## Recommendations

- Keep Docker pinned for Docker-owned GitHub Actions proof paths.
- Preserve Podman-vs-Docker flexibility for local workflows unless the user or
  workflow explicitly constrains it.
- Treat future hosted Podman use as an intentional, separately proven choice,
  not as the default result of runtime preference order.

## Applicability

### This Standard Applies To

- `.github/workflows/ci.yml`
- `.github/workflows/maintainer-image.yml`
- `.github/workflows/release-images.yml`
- maintainer-container proof lanes that build nested verify images in hosted CI

### This Standard Does Not Apply To

- local developer workflows where Docker-owned outer artifacts are not the
  controlling constraint
- single-runtime hosts where only one healthy OCI runtime exists
