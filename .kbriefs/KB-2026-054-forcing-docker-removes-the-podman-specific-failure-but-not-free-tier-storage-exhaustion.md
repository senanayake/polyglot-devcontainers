---
id: KB-2026-054
type: failure
status: draft
created: 2026-05-01
updated: 2026-05-01
tags: [github-actions, docker, podman, ci, disk-usage, nested-builds, free-tier]
related:
  - KB-2026-049
  - KB-2026-053
---

# Forcing Docker Removes the Podman-Specific Failure but Not Free-Tier Storage Exhaustion

## Context

PR `#25` on branch `codex/starter-generator` was failing in GitHub Actions
while running `task starters:verify:image-backed` from the root `task ci`
workflow.

An earlier run (`25243644910`) showed the nested proof lane selecting Podman
inside the maintainer container and then failing during the `diagram-secure`
image build with `No space left on device` from `dpkg` while unpacking
packages for the `diagram-rendering` feature.

That created a knowledge gap: was Podman itself the main problem, or was the
branch simply exceeding free-tier storage regardless of runtime?

## Experiment

Change set:

- forward `POLYGLOT_OCI_RUNTIME` and `POLYGLOT_CONTAINER_RUNTIME` through
  `scripts/run_in_maintainer_container.py`
- make the maintainer wrapper honor `POLYGLOT_OCI_RUNTIME` for its own outer
  runtime selection
- explicitly set `POLYGLOT_OCI_RUNTIME=docker` for the hosted root CI proof
  lane
- explicitly pass Docker runtime env vars into raw `docker run` workflow steps
  that execute repository tasks

Tested by GitHub Actions run `25244231575` on commit `e2260db`.

## Observation

The Docker-pinned run changed the failure mode materially:

- the nested pre-image-build diagnostic showed:
  - `runtime_env=docker`
  - `oci_env=docker`
  - selected OCI runtime: `docker`
- `diagram-secure` built successfully
- `diagram-secure` metadata validation succeeded
- `diagram-secure` tar export succeeded
- the run then advanced into the `python-node-secure` image build

The new failure happened later, during the `python-node-secure` build:

- Docker build reached `Step 17/20`
- the failing instruction was:
  - `COPY scripts/install_runtime_docs.sh /tmp/install_runtime_docs.sh`
- Docker returned:
  - `no space left on device`

The root workflow therefore ran substantially longer than the prior Podman
failure and died after more nested image work had completed.

## What We Learned

1. Forcing Docker does remove the specific hosted-CI Podman failure mode.
2. The branch still exceeds the free-tier storage budget even under Docker.
3. The remaining limit is now clearly aggregate image-build/storage pressure,
   not the original Podman-vs-Docker selection bug.
4. The full PR proof lane is still too heavy when it builds multiple verify
   images and exports tar archives inside the maintainer container.

## Implications

- Runtime pinning to Docker is worth keeping for Docker-owned hosted workflows.
- Runtime pinning alone is not enough to make this branch merge-ready on the
  free tier.
- The next remediation should target proof scope and artifact volume:
  - reduce which images are built in the PR profile
  - avoid tar export where the proof does not need it
  - split image-backed proof work so each job pays for less accumulated state

## Recommendation

Do not spend another iteration on runtime selection alone.

Treat the Docker pin as a successful narrowing step, then move on to a
free-tier scope reduction strategy for image-backed starter proofing.
