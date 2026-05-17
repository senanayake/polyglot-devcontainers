---
id: KB-2026-071
type: failure-mode
status: active
created: 2026-05-17
updated: 2026-05-17
tags:
  - windows
  - podman
  - disk-usage
  - image-validation
  - maintainer-container
  - kbpd
related:
  - KB-2026-027
  - KB-2026-049
  - KB-2026-055
  - KB-2026-069
---

# Windows Podman Image Validation Can Exhaust User Profile Storage

## Context

The repository correctly treats container-first validation as the source of
truth. That validation model becomes expensive when local development repeatedly
builds and tests published devcontainer images, especially on Windows hosts
where Podman stores Linux container state under the user's profile.

This failure was discovered during local work on the research-runner and LaTeX
published images. Windows reported critically low disk space after several
image build, smoke-test, and inner-`task ci` cycles.

## System/Component

- Windows host storage
- Podman Desktop / Windows Podman machine storage
- `C:\Users\chris\.local\share\containers`
- maintainer-container image validation workflow
- `task image:build`, `task image:verify`, and targeted published-image smoke
  tests

## Failure Description

### Symptoms

- Windows reports critically low disk space.
- `Get-PSDrive C` initially reports only about `0.02 GB` free.
- `fsutil volume diskfree c:` later reports only about `27.5 GB` free on a
  `1.8 TB` volume.
- `podman system df` and `podman system prune -a --volumes --force` hang or do
  not provide timely recovery.
- `C:\Users\chris\.local\share\containers` accounts for roughly `916 GB`.
- Deleting the containers directory frees the machine to about `943 GB` free.

### Failure Scenario

- A Windows host uses Podman as the local OCI runtime.
- Repository work repeatedly runs image-heavy validation paths.
- The validation path builds large images such as LaTeX / TeX Live images.
- The workflow runs nested validation through the maintainer container.
- Podman accumulates image layers, build cache, volumes, and temporary runtime
  state in the user's profile.
- Standard Podman cleanup commands become slow or stuck once storage pressure is
  severe.

### Impact

- The host becomes unstable for ordinary development.
- Repository validation can no longer run reliably because the container runtime
  itself becomes unhealthy.
- Diagnostic commands hang, which makes the failure harder to triage under
  time pressure.
- The user may be forced into manual storage deletion instead of normal runtime
  cleanup.

## Root Cause

### Primary Cause

Local Windows Podman storage grew without a guardrail while image-heavy
validation repeatedly built and tested published devcontainer images.

### Contributing Factors

- Large image content, especially LaTeX / TeX Live package layers.
- Repeated local verification of multiple images during conflict resolution and
  feature validation.
- Nested maintainer-container workflows that correctly prove the repository
  contract but amplify local storage use.
- Build, smoke, inner-CI, and scan loops that retain useful evidence while also
  retaining image state.
- No preflight disk-budget check before image-heavy tasks.
- No automatic post-run storage report or cleanup guidance for Windows Podman
  hosts.
- Late detection: the issue was noticed after Windows reported a critical disk
  warning, not while the workflow still had comfortable headroom.

### Failure Mechanism

```text
repeated local image validation
-> Podman stores image layers/cache/volumes under user profile
-> large TeX Live and polyglot images compound over multiple runs
-> C:\Users\chris\.local\share\containers grows to about 916 GB
-> C: approaches zero free space
-> Podman diagnostics and prune operations hang
-> manual deletion of container storage becomes the practical recovery path
```

## Evidence

Observed local measurements:

```text
C:\Users                     1654.05 GB
C:\Users\chris\.local          916.95 GB
C:\Users\chris\.local\share    916.47 GB
C:\Users\chris\.local\share\containers 915.81 GB
```

After deleting the containers directory:

```text
Total free bytes: 1,012,600,913,920 (943.1 GB)
Used bytes:        980,741,033,984 (913.4 GB)
```

Other local container/VM stores were materially smaller:

```text
Docker docker_data.vhdx     39.07 GB
Ubuntu ext4.vhdx            28.35 GB
Rancher Desktop ext4.vhdx    9.26 GB
```

The dominant storage consumer was therefore Windows Podman container storage,
not hibernation, Docker Desktop, WSL Ubuntu, or Rancher Desktop.

## KBPD Analysis

### Knowledge Gap

The original learning question was framed as whether the new images could be
built and validated. The hidden knowledge gap was:

> What is the local storage cost and failure behavior of repeated published
> image validation on Windows Podman?

That gap mattered because the repository's container-first principle is only
effective if the local control path remains operational.

### Activities That Caused Or Exposed The Failure

- Building new published images locally.
- Rebuilding large LaTeX layers after bootstrap changes.
- Running metadata validation, starter smoke tests, and inner `task ci`.
- Running validation through the maintainer container as required by the
  repository contract.
- Repeating the loop during conflict resolution and debugging.
- Attempting broad image workflows before the local storage budget was known.

### What Could Have Been Done Differently

- Run the narrowest possible image target first:
  `task image:build -- --image latex` or
  `task image:build -- --image research-runner`.
- Defer full-release or multi-image validation until the final evidence step.
- Add an explicit free-space check before image-heavy tasks, especially on
  Windows.
- Add disk snapshots before and after image builds so storage growth becomes
  visible as evidence.
- Use a Linux-native development environment for repeated image work.
- Treat Windows Podman as a valid consumer path but not the cheapest
  high-frequency image-build environment.
- Clean or rotate local OCI storage after heavy validation runs, while keeping
  source artifacts and scan outputs in the repository workspace.

## Prevention

### Design Changes

- Add a repository disk preflight helper for image-heavy tasks.
- Fail fast when free disk falls below a conservative threshold, such as
  `100 GB` for targeted builds and `200 GB` for full-release validation.
- Record image-build disk deltas in `.artifacts/` so future work can compare
  storage costs across targets.
- Keep `fast`, `medium`, and `full-release` lanes distinct; do not collapse
  local development back into one monolithic image workflow.
- Consider a Windows-specific cleanup task that prints the relevant Podman
  storage paths and safe cleanup sequence instead of silently pruning.

### Operational Controls

- Before local image work on Windows, inspect:

```powershell
fsutil volume diskfree c:
Get-ChildItem "$env:USERPROFILE\.local\share" -Force -Directory
```

- During heavy image work, periodically inspect:

```powershell
Get-ChildItem "$env:USERPROFILE\.local\share\containers" -Force |
    Select-Object Name, FullName
```

- Prefer targeted builds:

```bash
task image:build -- --profile fast --image latex --smoke --inner-ci
task image:build -- --profile fast --image research-runner --smoke --inner-ci
```

- Reserve:

```bash
task image:verify
task ci:full-release
```

for final release evidence or hosted validation with an explicit disk budget.

### Environment Strategy

The user's plan to move regular development to a dual-boot Ubuntu installation
is aligned with this finding. Native Linux removes the Windows Podman machine
layer and gives more predictable container storage behavior.

That does not remove the need for disk budgeting. Large image workflows can
still consume hundreds of GB on Linux if cache and layer growth are not
monitored.

## Detection

### Early Warning Signs

- `.local\share\containers` grows faster than expected.
- `podman system df` becomes slow.
- `podman system prune` hangs.
- Dev Containers CLI starts reporting runtime health or temp-file failures
  after heavy image work.
- Windows low-disk warnings appear while the repository itself is not large.

### Detection Methods

- Automated preflight checks before image-heavy tasks.
- Disk snapshots before and after `task image:build`.
- Periodic local reports that identify top user-profile directories by size.
- Runtime health checks that distinguish Podman machine failure from
  repository validation failure.

## Mitigation

### Immediate Response

1. Confirm whether the dominant storage consumer is
   `C:\Users\<user>\.local\share\containers`.
2. Stop or close Podman/Dev Containers processes where practical.
3. Prefer normal Podman cleanup first if it responds.
4. If Podman cleanup hangs and the storage path is confirmed disposable,
   remove the container storage directory.
5. Recreate or repair the Podman machine before treating future validation
   failures as repository failures.

### Recovery Procedure

```powershell
fsutil volume diskfree c:
Get-ChildItem "$env:USERPROFILE\.local\share" -Force -Directory
Get-ChildItem "$env:USERPROFILE\.local\share\containers" -Force
```

If `containers` is confirmed as the dominant disposable container store and
Podman cleanup is not responding, remove only that container state. Do not
delete the whole `.local` directory because it can also contain unrelated tool
state.

## Testing

### Test Cases

- Run a targeted LaTeX image build and record disk before and after.
- Run a targeted research-runner image build and record disk before and after.
- Run a full-release validation lane on native Linux and compare peak storage
  with Windows Podman.
- Verify the disk preflight fails before entering image builds when free space
  is below threshold.

### Evidence To Capture Next Time

- `fsutil volume diskfree c:` before and after each image-heavy task.
- `podman system df` when responsive.
- Size of `C:\Users\chris\.local\share\containers`.
- Which image targets were built in the session.
- Whether tar archives under `.artifacts/images` were created.

## Lessons Learned

- This was a disk-capacity failure, not a RAM or hibernation-file issue.
- Container-first validation remains the right correctness model, but image
  validation needs a storage budget.
- Windows Podman is a useful local path, but high-frequency image builds can
  make it operationally fragile without measurement and cleanup.
- The expensive activity is not one command; it is the learning loop of
  repeated build, smoke, inner-CI, and scan cycles.
- KBPD should treat local infrastructure capacity as part of the experiment
  design, not as background plumbing.

## Applicability

### This Failure Mode Applies To

- Windows hosts using Podman for devcontainer and image validation workflows
- Large published image builds, especially LaTeX / TeX Live images
- Maintainer-container workflows that perform nested image builds
- Local release-readiness proofing

### This Failure Mode Does Not Apply To

- Source-only repository lint/test/scan workflows
- Hosted Linux validation with an explicit disk budget
- Native Linux development where this exact Windows profile path does not exist

## Status

- [x] Documented
- [ ] Prevention implemented
- [ ] Detection implemented
- [x] Immediate mitigation tested through container storage deletion
- [ ] Monitoring in place

## Related Knowledge

- [KB-2026-027](KB-2026-027-windows-podman-machine-control-path-failure.md)
- [KB-2026-049](KB-2026-049-github-standard-runner-disk-exhaustion-during-image-backed-starter-proofs.md)
- [KB-2026-055](KB-2026-055-free-tier-image-validation-should-use-fast-medium-and-full-release-lanes.md)
- [KB-2026-069](KB-2026-069-windows-podman-bind-mounts-can-break-nested-gradle-starter-proofing.md)
