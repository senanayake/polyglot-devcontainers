---
id: KB-2026-039
type: standard
status: published
created: 2026-04-26
updated: 2026-04-26
tags: [images, reliability, curl, retries, external-dependencies]
related:
  - KB-2026-025-trivy-apt-key-rotation-build-failure.md
  - KB-2026-038-release-image-scan-must-report-upstream-residual-risk-without-blocking-release.md
---

# Retry Upstream Binary Downloads In Image Builds

## Context

Published images and maintainer images fetch release artifacts from external services during `Containerfile` builds. Those downloads are outside repository control and occasionally return transient `5xx` responses even when the requested version is valid.

## Problem/Need

Without retries, image builds fail nondeterministically during release preparation and CI. A transient upstream failure should not be indistinguishable from a persistent checksum mismatch or a broken URL.

## Standard/Pattern

### Description

All release-time `curl` downloads for upstream binaries and repository keys inside maintained `Containerfile` builds and feature install scripts should use retry-aware flags.

### Key Principles

- Preserve checksum verification after download.
- Retry only transport-layer failures, not logical validation failures.
- Keep retries small and deterministic so failures still surface promptly.

### Implementation

```bash
curl --retry 5 --retry-all-errors --retry-delay 2 -fsSLo <output> <url>
```

Apply this to:

- GitHub release binary downloads
- checksum file downloads
- repository signing key downloads used during image builds

## Rationale

- transient upstream `502` errors are an operational reality, not a code signal
- retrying download steps is cheaper than re-running full image builds
- checksum validation still provides the integrity boundary after a successful retry

## Benefits

- fewer nondeterministic release failures caused by temporary upstream outages
- better signal separation between transport errors and true package integrity failures
- lower operator burden during image refresh and release workflows

## Constraints

- this standard applies only to network fetches whose content is validated afterward
- retries do not replace checksum validation or version pinning
- persistent failures should still fail the build

## Alternatives Considered

### No Retries

- simplest implementation
- rejected because a single transient upstream error aborts long-running image builds

### Mirror All Artifacts Internally

- stronger control over availability
- rejected for now because it increases maintenance burden and diverges from the repository's upstream-first policy

## Evidence

- local `task image:build` failed during `python-node` image construction on `curl: (22) The requested URL returned error: 502`
- the failure occurred during upstream artifact fetch, not during checksum validation or package installation
- similar external-dependency failure patterns already exist in the K-Brief history for image maintenance

## Anti-Patterns

- using naked `curl -fsSLo` for critical release-time binary fetches
- retrying checksum mismatches or signature validation failures
- masking repeated failures with unbounded retry loops

## Examples

### Good Example

```bash
curl --retry 5 --retry-all-errors --retry-delay 2 -fsSLo "${tmpdir}/${task_archive}" \
  "https://github.com/go-task/task/releases/download/v${TASK_VERSION}/${task_archive}"
```

### Bad Example

```bash
curl -fsSLo "${tmpdir}/${task_archive}" \
  "https://github.com/go-task/task/releases/download/v${TASK_VERSION}/${task_archive}"
```

## Verification

- review maintained `Containerfile` and feature install scripts for retry-aware `curl`
- rebuild affected images after introducing retries
- confirm checksum verification still runs after successful download

## Migration

- update maintained image `Containerfile` fetch steps first
- update shared feature install scripts next
- keep existing version pins and checksums unchanged during the retry migration

## Exceptions

- local file copies or repo-local `COPY` operations
- package-manager downloads already wrapped by the package manager's own retry logic

## Applicability

### ✅ Use This Standard When

- a build downloads upstream release artifacts directly with `curl`
- a download is followed by checksum or signature validation
- the build runs in CI or release automation

### ❌ Don't Use This Standard When

- the fetched content is not version-pinned or integrity-checked
- the operation is not part of a maintained image or feature install path
- the upstream client already includes appropriate retries

## Maintenance

- review retry settings when the build fleet or upstream behavior changes
- extend the pattern to new maintained image builds as they are added
- revisit if the repository later adopts a mirrored artifact strategy

## Related Knowledge

- `.devcontainer/Containerfile`
- `templates/*/.devcontainer/Containerfile`
- `features/diagram-rendering/install.sh`

## Success Metrics

- fewer image build failures caused by transient upstream HTTP errors
- fewer manual rebuild attempts during release preparation
- stable checksum validation despite transient fetch retries
