---
id: KB-2026-066
type: failure-mode
status: active
created: 2026-05-03
updated: 2026-05-03
tags:
  - github-actions
  - ghcr
  - packages
  - permissions
  - images
  - kbpd
related:
  - KB-2026-065
---

# Mainline Integration Image Publication Requires Packages Write Permission

## Context

The repository added a new mainline integration channel in `.github/workflows/ci.yml`
that publishes medium-validated workload images on pushes to `main`.

The initial merge of that workflow failed in GitHub Actions run
`25290707821`.

## System/Component

- `.github/workflows/ci.yml`
- GHCR publication using `docker/login-action@v3`
- `docker/build-push-action@v6`

## Failure Description

### Symptoms

- `publish / diagrams` failed
- `publish / java` failed
- `publish / python-node` failed
- all three failed at `Build and push mainline integration image`

### Failure Mechanism

The workflow could authenticate to GHCR, but the token available to the
workflow did not have write permission for packages.

The log error was:

```text
failed to push ghcr.io/senanayake/polyglot-devcontainers-java:main:
denied: installation not allowed to Write organization package
```

## Root Cause

`ci.yml` did not declare `packages: write` in its workflow permissions.

On GitHub Actions, the default `GITHUB_TOKEN` permission set was therefore not
sufficient for GHCR push operations in the new mainline integration publish
jobs.

Other workflows that publish images in this repository, such as
`maintainer-image.yml` and `release-images.yml`, already declare package write
permission explicitly.

## Evidence

- GitHub Actions run `25290707821`
- failed jobs:
  - `publish / diagrams`
  - `publish / java`
  - `publish / python-node`
- successful prior steps:
  - `Log in to GHCR`
  - all medium validation jobs
- failing step:
  - `Build and push mainline integration image`

## Prevention

### Design Change

Any workflow that pushes to GHCR must declare:

```yaml
permissions:
  contents: read
  packages: write
```

### Operational Control

When adding new publish jobs, compare their permission block against known-good
publisher workflows in the same repository before merging.

## Recovery

1. Add `packages: write` to `.github/workflows/ci.yml`.
2. Push the fix.
3. Re-run the `main` workflow and confirm the `publish / ...` jobs succeed.

## Applicability

- Applies to: any GitHub Actions workflow in this repository that pushes to
  GHCR
- Does not apply to: validation-only workflows that build but do not push

## Related Knowledge

- [KB-2026-065](KB-2026-065-mainline-integration-publication-and-semver-release-should-use-separate-channels.md)
