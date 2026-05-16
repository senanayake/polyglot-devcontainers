---
id: KB-2026-035
type: failure-mode
status: validated
created: 2026-04-25
updated: 2026-04-25
tags: [oci-runtime, docker, podman, ci, devcontainer-metadata, failure-mode]
related: [KB-2026-033]
---

# Runtime Preference vs Image Store Mismatch

## Context

The repository supports both Podman and Docker, but some workflows build images
with Docker-specific actions while repo scripts independently select a
"preferred" healthy runtime.

## System/Component

- `scripts/validate_devcontainer_metadata.py`
- `scripts/run_in_maintainer_container.py`
- `.github/workflows/ci.yml`
- `.github/workflows/maintainer-image.yml`
- `.github/workflows/release-images.yml`

## Failure Description

### Symptoms

- GitHub Actions builds `polyglot-devcontainers-maintainer:ci` successfully
- metadata validation fails immediately after the build
- later maintainer-container smoke steps are at risk of failing against the
  same image for the same reason

### Failure Scenario

- the runner has both Podman and Docker CLIs available
- Docker owns the just-built image because the workflow used `docker build` or
  `docker/build-push-action` with `load: true`
- a repo script chooses Podman because it is healthy and preferred
- Podman tries to inspect or run an image that only exists in the Docker image
  store

### Impact

- CI reports a devcontainer metadata regression even though the image build
  succeeded
- the maintainer-container control path can fail before `task ci` starts
- workflow results depend on host runtime topology rather than on repository
  correctness

## Root Cause

### Primary Cause

Runtime selection was based on generic runtime health instead of on which
runtime actually owns the image artifact under test.

### Contributing Factors

- workflows used Docker-native build steps without pinning repo scripts to the
  same runtime
- the metadata validator assumed the healthy preferred runtime could always
  inspect the target image
- the maintainer wrapper used the same preference order independently

### Failure Mechanism

```text
docker build/load -> image exists only in Docker store
preferred runtime probe -> Podman selected because it is healthy
podman inspect/run -> image missing in Podman store -> false CI failure
```

## Evidence

- GitHub Actions run `24935245806`, job `73019591268`
- failing step: `Validate root image devcontainer metadata`
- traceback from `scripts/validate_devcontainer_metadata.py` shows:
  `podman image inspect polyglot-devcontainers-maintainer:ci` exited `125`

## Reproduction

### Minimal Reproduction Case

```bash
docker build --file .devcontainer/Containerfile --tag polyglot-devcontainers-maintainer:ci .
python3 scripts/validate_devcontainer_metadata.py \
  --image polyglot-devcontainers-maintainer:ci \
  --devcontainer-json .devcontainer/devcontainer.json
```

### Conditions Required

- both Docker and Podman installed
- Podman healthy enough to win the default runtime preference
- image built only into the Docker store

## Prevention

### Design Changes

- allow metadata validation to inspect with an explicit runtime
- fall back across healthy runtimes when the image is not present in the first
  runtime inspected
- pin GitHub Actions workflows to Docker when the build artifact is Docker-owned

### Operational Controls

- keep workflow runtime selection explicit when using Docker-native actions
- treat runtime/store mismatches as control-path bugs, not as image metadata
  bugs

### Monitoring

- watch for `image inspect` failures immediately after successful builds
- watch for steps that build with Docker but invoke repo wrappers without a
  runtime override

## Detection

### Early Warning Signs

- a workflow log shows a successful `docker build` followed by a failed
  `podman image inspect`
- maintainer smoke steps fail before entering the container even though the
  image tag was built earlier in the same job

### Detection Methods

- inspect failed GitHub Actions job logs
- compare the build tool in the workflow with the runtime selected by repo
  scripts

## Mitigation

### Immediate Response

1. pin workflow runtime selection to Docker for Docker-owned image builds
2. let metadata validation inspect with an explicit runtime or a runtime-aware
   fallback path
3. rerun CI on the repaired branch

## Testing

### Test Cases

- validate metadata for an image built through Docker-native workflow steps
- validate metadata for an image built through the repo runtime wrapper
- smoke test maintainer-container entry with the same runtime that built the
  image

## Lessons Learned

- "healthy runtime" and "runtime that owns this artifact" are different facts
- multi-runtime repositories need explicit artifact/runtime binding in CI

## Applicability

- Applies to: mixed Podman/Docker environments, especially GitHub-hosted Linux
  runners
- Does not apply to: single-runtime hosts where build and inspect always use
  the same engine
