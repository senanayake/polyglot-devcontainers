---
id: KB-2026-069
type: limit
status: active
created: 2026-05-04
updated: 2026-05-04
tags:
  - windows
  - podman
  - gradle
  - starter-proof
  - full-release
  - kbpd
related:
  - KB-2026-058
  - KB-2026-067
---

# Windows Podman Bind Mounts Can Break Nested Gradle Starter Proofing

## Context

After refreshing the local maintainer `:main` image and recreating the local
maintainer container, local `task ci:full-release` progressed far beyond
repo-core and into the image-backed starter proof lane.

That exposed a second local-only boundary.

## System/Component

- Windows host
- Podman-backed maintainer container
- nested `scripts/smoke_test_published_starter.sh`
- Java published-image bootstrap proof

## Limit / Boundary

The local full-release proof on Windows + Podman can fail in nested Java
starter proofing even when the same image passes hosted CI.

The boundary appears when Gradle in the nested smoke container tries to set
daemon directory permissions on the bind-mounted starter workspace:

```text
Could not set file mode 700 on /workspaces/project/.gradle/daemon/9.1.0
```

## What Was Tested

After refreshing the local maintainer image, the following was rerun on current
`main` commit `6bf92f0`:

```bash
python scripts/run_in_maintainer_container.py exec -- task ci:full-release
```

Observed behavior:

- repo-core lint, test, scan, scenarios, and source starter proofing advanced
  successfully
- the run then reached `task starters:verify:image-backed`
- the failure occurred in the `java-secure` published-image bootstrap proof
- the nested smoke container retried twice and failed both times

## Findings

- the blocker is not the Java workload image itself, because hosted `main`
  integration publication already proved `medium / java` successfully on GitHub
- the blocker is not the maintainer image missing tooling anymore
- the failure is a local filesystem/permission boundary in the nested
  bind-mounted workspace under Windows + Podman

## Evidence

- local log:
  - `.artifacts/experiments/ci-full-release-main-6bf92f0-refresh.log`
- failing path:
  - `.tmp/starter-proving/published-image-bootstrap/java-secure/baseline`
- Gradle error:
  - `Could not set UNIX mode on /workspaces/project/.gradle/daemon/9.1.0`
  - `could not chmod file (errno 1: Operation not permitted)`

## Implications

- local full-release proof on Windows + Podman is not yet a stable authority
  for nested Java starter bootstrap validation
- hosted Linux proof remains the more trustworthy authority for this lane until
  the bind-mount permission behavior is adapted or worked around
- this is a local portability boundary, not evidence that the Java release lane
  itself is broken on GitHub-hosted Linux runners

## Recommendations

- treat this as a local environment boundary until proven otherwise
- when debugging release readiness, separate:
  - local Windows + Podman nested-proof failures
  - from hosted Linux workflow failures
- if local authoritative proof is required on Windows, the nested Java starter
  proof path likely needs a workspace strategy that avoids chmod-sensitive
  Gradle daemon paths on the bind mount

## Applicability

- Applies to: local Windows + Podman maintainer workflows that run nested Java
  published-image bootstrap proofing on bind-mounted workspaces
- Does not apply to: hosted Linux GitHub Actions validation that runs the same
  Java workload image successfully

## Related Knowledge

- [KB-2026-058](KB-2026-058-full-release-validation-and-release-publication-still-need-a-single-build-gate.md)
- [KB-2026-067](KB-2026-067-cached-maintainer-main-reuse-can-block-local-full-release-proof.md)
