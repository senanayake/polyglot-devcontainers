---
id: KB-2026-038
type: failure-mode
status: active
created: 2026-05-16
updated: 2026-05-16
tags: [trivy, apt, keyring, upstream-drift, java-template, image-build, kbpd]
related: [KB-2026-025]
---

# Trivy Public Key Checksum Drift Recurred in Image Build

## Context

While adding the research-runner and LaTeX images, the full published-image
build failed before reaching the new image paths. The failing component was the
existing Trivy APT key bootstrap in Java image installation logic.

## System/Component

- `features/java-engineering/install.sh`
- `templates/java-secure/.devcontainer/Containerfile`
- `task image:build`

## Failure Description

### Symptoms

`task maintainer:task -- image:build` failed when checking `/tmp/trivy.key`
against the pinned SHA-256 in the Java feature and Java template image.

### Failure Scenario

The image build downloaded the current Trivy repository public key. The served
key bytes no longer matched the repository-pinned value.

### Impact

- New image work was blocked by an unrelated existing image path.
- Full image verification could not proceed until the Java install path was
  updated.

## Root Cause

The repository still depended on a mutable upstream key blob checksum. This is
the same class of failure described by KB-2026-025: raw public-key byte pinning
is brittle when upstream rotates or republishes the key material.

## Evidence

- Rebuilding all images inside the maintainer container failed at the Trivy key
  checksum step.
- Updating the pinned key hash in both affected paths to the newly downloaded
  SHA-256 allowed `task maintainer:task -- image:build` to complete.
- This recurrence happened on 2026-05-16 while adding unrelated image features.

## Prevention

### Design Changes

- Replace raw key blob checksum pinning with an upstream-supported trust model
  where possible.
- If a raw checksum remains necessary, centralize the value so all image paths
  fail and update together.
- Add a scheduled image-build canary so upstream key drift is found before
  feature work depends on full image validation.

### Operational Controls

- Treat checksum drift in third-party key material as upstream residual
  maintenance, not as a reason to fork or repackage the tool.
- Update all duplicated installation paths in one change.

## Recommendation

The next hardening step is to remove duplicate Trivy key bootstrap logic from
the Java feature and Java image template, then validate a single shared trust
path through `task image:build`.
