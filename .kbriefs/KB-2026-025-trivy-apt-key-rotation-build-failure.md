---
id: KB-2026-025
type: failure-mode
status: active
created: 2026-04-17
updated: 2026-04-17
tags: [trivy, ci, maintainer-image, java-template, apt, keyring, upstream-drift, kbpd]
related: [KB-2026-003, KB-2026-004, KB-2026-005]
---

# Trivy APT Key Rotation Broke Maintainer Image Builds

## Context

This repository treats the maintainer container as the source of truth for
validation. That makes the maintainer image build a critical path for every
push to `main`.

On 2026-04-17, a push that only added a K-Brief triggered CI failure in the
root image build. The content change was not the cause; an external toolchain
installer drifted underneath the repository.

## System/Component

- `features/java-engineering/install.sh`
- `templates/java-secure/.devcontainer/Containerfile`
- the maintainer/root devcontainer image build in GitHub Actions
- the published Java devcontainer image validation path
- Trivy Debian repository bootstrap

## Failure Description

### Symptoms

Observable signs of failure:
- GitHub Actions `ci` failed in `Build root image`
- the build stopped while installing Trivy during feature setup
- logs showed `sha256sum: WARNING: 1 computed checksum did NOT match`

### Failure Scenario

Conditions that trigger the failure:
- CI rebuilds the maintainer/root image or the published Java image
- the installer downloads a mutable Trivy public key blob
- the downloaded key file bytes no longer match the repository-pinned SHA-256

### Impact

Consequences of the failure:
- unrelated changes cannot merge because the image build is red
- CI trust is reduced because the visible warning points at Node 20 while the
  actual failure is elsewhere
- repository maintenance depends on a mutable upstream blob outside a release
  artifact contract
- engineers lose time investigating false leads instead of the actual break

## Root Cause

### Primary Cause

The repository pinned the SHA-256 of a downloaded Trivy public key file and
treated any byte-level change in that file as a hard failure. Upstream rotated
or changed the served key file bytes, so the checksum gate failed before APT
could use the keyring.

### Contributing Factors

Additional factors that enable or worsen the failure:
- the stale bootstrap logic existed in two paths, not one: the shared Java
  feature and the published Java template image
- the install path used `https://get.trivy.dev/deb/...` instead of the current
  Debian repository path documented by Trivy
- the checksum validated the raw downloaded blob, not a stable repository
  contract such as a documented fingerprint or the package manager trust flow
- no scheduled maintainer-image canary existed to catch upstream installer
  drift before an unrelated push
- the run also emitted a Node 20 deprecation warning, which made the failing
  signal noisier to interpret

### Failure Mechanism

How the failure propagates through the system:
```text
upstream key file changes -> pinned blob checksum fails -> Trivy install aborts
-> image build fails -> repository CI fails on unrelated changes
```

## Evidence

Data demonstrating this failure mode:
- GitHub Actions run `24591323208`, job `71912489801`
- failing log lines:
  - `/tmp/gradle.zip: OK`
  - `sha256sum: WARNING: 1 computed checksum did NOT match`
  - `/tmp/trivy.key: FAILED`
- the same stale bootstrap existed in both
  `features/java-engineering/install.sh` and
  `templates/java-secure/.devcontainer/Containerfile`
- Trivy's current official Debian instructions use keyring import from
  `https://aquasecurity.github.io/trivy-repo/deb/public.key` and do not
  document raw blob checksum pinning
- maintainer-container validation after the fix succeeded with
  `task image:build`

## Reproduction

### Minimal Reproduction Case

Simplest way to trigger the failure:
```bash
docker build -f .devcontainer/Containerfile .
docker build -f templates/java-secure/.devcontainer/Containerfile .
```

with the pre-fix Trivy bootstrap and a changed upstream key file.

### Conditions Required

Prerequisites for reproduction:
- network access to the Trivy Debian repo
- a CI or local image build that runs the Java engineering feature or Java
  template image build
- a stale repository-pinned checksum for the downloaded key file

## Prevention

### Design Changes

Architectural changes to prevent the failure:
- follow Trivy's current official Debian install flow: import the repo key into
  a dedicated keyring and let APT enforce package signature trust
- avoid pinning raw bytes for mutable installer metadata unless upstream
  publishes that exact checksum as a supported contract
- centralize third-party installer trust strategy by classifying each dependency
  as `release-checksum`, `package-signature`, or `key-fingerprint` verified

### Operational Controls

Operational practices to avoid the failure:
- run a scheduled maintainer-image canary build so upstream installer drift is
  detected before unrelated pushes hit `main`
- surface the failing step and stderr in CI summaries so warning noise does not
  misdirect triage
- review third-party install scripts for undocumented checksum pinning and
  prefer upstream-supported verification methods

### Monitoring

How to detect conditions that lead to failure:
- nightly or weekly build of `.devcontainer/Containerfile`
- alert on installer-step failures for `curl`, `sha256sum`, `gpg`, and
  `apt-get update`
- periodic audit of external install URLs used by repo-owned features and
  templates

## Detection

### Early Warning Signs

Indicators that failure is imminent:
- upstream installation docs change paths or commands
- installer URLs return different content without a repository change
- checksum failures appear on key, repo, or bootstrap assets rather than
  versioned release artifacts

### Detection Methods

How to identify the failure:
- automated detection via scheduled image canary builds
- manual inspection of the failed feature-install step in Actions logs
- comparison of repo installer logic against current upstream docs

## Mitigation

### Immediate Response

What to do when failure occurs:
1. Inspect the failed image-build step, not just terminal warnings in the job.
2. Identify whether the failure is on a mutable metadata asset or a versioned
   release artifact.
3. Replace brittle verification with the upstream-supported trust mechanism and
   rebuild the affected image paths.

### Recovery Procedure

How to recover from the failure:
1. Update the Trivy installer to use the official Debian keyring/repo flow.
2. Patch every repo-owned image path that duplicated the stale bootstrap.
3. Validate the full image build flow inside the maintainer container path.
4. Push the fix to `main` and confirm the CI run turns green.

### Graceful Degradation

How to limit impact:
- keep tool installation steps isolated enough that the failing component is
  obvious in logs
- use scheduled canaries to shift failures away from feature or documentation
  pushes

## Testing

### Test Cases

Tests that verify prevention/detection:
```bash
podman exec <maintainer-container> bash -lc "cd /workspaces/polyglot-devcontainers && task image:build"
gh run view <run-id> --job <job-id> --log-failed
```

### Chaos Engineering

How to test resilience:
- replace a bootstrap asset with changed bytes and verify the canary fails in a
  dedicated toolchain signal
- rotate repository metadata inputs in a non-production mirror and confirm the
  installer still succeeds when the package-signing trust root is unchanged

## Recommendation

The best end-to-end improvement is to treat external installer trust as a
first-class repository system rather than letting each image path improvise its
own bootstrap logic.

Recommended next step:
- create one repo-owned third-party installer policy inventory that records,
  for each tool, the upstream install contract, the verification mode
  (`release-checksum`, `package-signature`, or `key-fingerprint`), and the
  authoritative source URL
- require new features and templates to reuse that policy instead of embedding
  ad hoc checksum gates in multiple files
- add a scheduled maintainer-image canary workflow so upstream drift is caught
  before unrelated pushes hit `main`
- keep the main CI path strict, but move early warning for mutable upstream
  bootstrap assets into the canary lane

## Related Failure Modes

Similar or cascading failures:
- stale release checksum pins for downloaded binaries
- repo URL migrations for third-party package feeds
- GPG key expiration or trust-store path regressions in image builds

## Lessons Learned

Key insights from this failure mode:
- checksum pinning is strongest when the checksum is attached to a versioned
  release artifact, not a mutable repository bootstrap file
- maintainer-image dependencies need their own early-warning loop because they
  can fail independently of product changes
- noisy CI warnings should not be allowed to obscure the actual failing step

## Applicability

### This Failure Mode Applies To

- external package repositories added during image builds
- bootstrap keys, repo metadata, and installer scripts fetched at build time
- maintainer-container and devcontainer image pipelines

### This Failure Mode Does Not Apply To

- versioned release artifacts with published upstream checksums
- tools installed only from distro-native repositories already trusted by the
  base image
- purely local scripts with no network-fetched bootstrap material

## Status

Current state of this failure mode:
- [x] Documented
- [x] Prevention implemented
- [ ] Detection implemented
- [x] Mitigation tested
- [ ] Monitoring in place

## Related Knowledge

- `KB-2026-003`
- `KB-2026-004`
- `KB-2026-005`
- Trivy installation docs: <https://trivy.dev/docs/latest/getting-started/installation/>
