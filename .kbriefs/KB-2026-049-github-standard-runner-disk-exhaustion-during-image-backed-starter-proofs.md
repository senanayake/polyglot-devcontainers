---
id: KB-2026-049
type: failure-mode
status: draft
created: 2026-05-01
updated: 2026-05-01
tags: [github-actions, runner-disk, docker, starter-proofing, ci]
related: [KB-2026-036, KB-2026-042]
---

# GitHub standard runner disk exhaustion during image-backed starter proofs

## Context

The starter-generator branch extends root `task ci` so CI now proves generated starters through an image-backed path. That improves coverage, but it also introduces a new storage failure mode on GitHub-hosted standard runners.

## System/Component

GitHub Actions `ci` workflow running on `ubuntu-latest` standard runners, specifically the `Run root workflow` step after the maintainer control-path fix.

## Failure Description

### Symptoms

Observable signs of failure:
- The `ci` job passes image build, metadata validation, and maintainer control-path smoke tests.
- The job then fails during `Run root workflow` with `System.IO.IOException: No space left on device`.
- The runner may fail while writing its own diagnostic log under `_diag/Worker_...log`, which can truncate the useful tail of the application log.

### Failure Scenario

Conditions that trigger the failure:
- CI runs on a GitHub-hosted standard Ubuntu runner.
- Root `task ci` reaches `task starters:verify:image-backed`.
- That path runs `task image:build`, which builds four OCI images and exports them as tar archives.
- The work happens inside the maintainer container, so nested container storage is accumulated on top of the outer runner's own image and layer usage.

### Impact

Consequences of the failure:
- The PR check fails even though the earlier privileged-runtime failure is already fixed.
- The runner can stop logging before the exact last application command is emitted.
- The branch is blocked from merge by infrastructure capacity rather than functional correctness.

## Root Cause

### Primary Cause

The workflow exceeds the disk budget of a standard GitHub-hosted Ubuntu runner while executing an image-heavy nested proof path.

### Contributing Factors

Additional factors that enable or worsen the failure:
- The workflow first builds the maintainer image on the host runner, then starts the maintainer container and performs additional image builds inside that environment.
- `task image:build` retains both image layers and exported tarballs for `maintainer`, `java`, `diagrams`, and `python-node` verify images.
- The maintainer image itself is tool-heavy: Docker, Podman, Node.js, GitHub CLI, Java, Trivy, and multiple repo-owned feature installs.
- GitHub's standard Ubuntu runner storage budget is small enough that moderate layer duplication and archive exports become significant.

### Failure Mechanism

How the failure propagates through the system:
```
standard runner disk budget
-> outer maintainer image build consumes local Docker storage
-> inner image-backed proof builds additional images in nested runtime storage
-> same images are exported to tar archives under .artifacts/images
-> runner root filesystem reaches ENOSPC
-> runner fails while writing _diag/Worker_*.log
```

## Evidence

Data demonstrating this failure mode:
- GitHub Actions run `25239181369` for PR `#25` fails in `Run root workflow` after the maintainer control-path fix.
- The runner-level failure message is `System.IO.IOException: No space left on device : '/home/runner/actions-runner/cached/2.334.0/_diag/Worker_20260502-003428-utc.log'`.
- GitHub docs state standard Ubuntu-hosted runners provide `14 GB` SSD storage: <https://docs.github.com/en/actions/reference/runners/github-hosted-runners>.
- GitHub docs state Ubuntu larger runners at `4 CPU / 16 GB RAM` provide `150 GB` SSD storage: <https://docs.github.com/en/actions/reference/runners/larger-runners>.
- GitHub docs recommend larger runners when standard runners return memory or disk errors: <https://docs.github.com/en/actions/concepts/runners/larger-runners>.
- GitHub community and runner-images reports show the same class of failure, including exact `_diag/Worker_*.log` ENOSPC symptoms:
  - <https://github.com/orgs/community/discussions/25678>
  - <https://github.com/actions/runner-images/issues/9494>
  - <https://github.com/actions/runner-images/issues/7969>
- Repository evidence:
  - `.github/workflows/ci.yml` builds `polyglot-devcontainers-maintainer:ci` before running root `task ci`.
  - `Taskfile.yml` `starters:verify:image-backed` calls `task image:build`.
  - `Taskfile.yml` `image:build` builds and saves four verify images to `.artifacts/images/*.tar`.

## Reproduction

### Minimal Reproduction Case

Simplest way to trigger the failure:
```
1. Run the CI workflow on a GitHub-hosted standard Ubuntu runner.
2. Build the maintainer image.
3. Enter the maintainer control path.
4. Execute root `task ci` until it reaches `task starters:verify:image-backed`.
5. Build and export the four verify images.
6. Observe runner disk exhaustion before or during completion of the proof lane.
```

### Conditions Required

Prerequisites for reproduction:
- Standard GitHub-hosted Ubuntu runner.
- Root workflow includes image-backed starter verification.
- Nested OCI runtime is available inside the maintainer container.
- Verify images are exported as tar archives instead of using layer-only validation.

## Prevention

### Design Changes

Architectural changes to prevent the failure:
- Split image-backed starter proofing into a separate job or lane with a larger runner.
- Avoid exporting verify images to tar archives in the same lane unless downstream steps truly require them.
- Reconsider whether all four verify images need to be built in the PR gate.

### Operational Controls

Operational practices to avoid the failure:
- Add explicit `df -h` and `docker system df` checkpoints before and after image-heavy steps.
- Prune nested image state aggressively after proofs if the lane must stay on standard runners.
- Prefer larger runners or self-hosted runners for image-heavy proof paths instead of treating standard runners as elastic.

### Monitoring

How to detect conditions that lead to failure:
- Record free disk before `Build root image`, before `Run root workflow`, and after `task image:build`.
- Flag free space below a low-water mark before entering image-backed proofing.
- Emit artifact summaries of image sizes and tar sizes for each verify image.

## Detection

### Early Warning Signs

Indicators that failure is imminent:
- Large verify-image exports accumulating under `.artifacts/images`.
- Rapid growth in Docker layer storage during nested builds.
- Runner warnings about low free disk, or sharp drops in `df -h` before proofing completes.

### Detection Methods

How to identify the failure:
- Automated detection via explicit disk checks in workflow steps.
- Manual inspection of workflow logs and task topology.
- Correlating the failing step with GitHub runner ENOSPC exceptions.

## Mitigation

### Immediate Response

What to do when failure occurs:
1. Confirm the job got past the earlier privileged-runtime failure and isolate the remaining blocker as disk exhaustion.
2. Inspect the proof lane for image builds, archives, and nested runtime storage.
3. Move the lane to a higher-capacity runner or reduce storage pressure in the lane.

### Recovery Procedure

How to recover from the failure:
1. Change the workflow or task graph to reduce storage demand, or switch to a larger runner.
2. Re-run the PR workflow.
3. Verify the job completes `Run root workflow` and reaches artifact upload.

### Graceful Degradation

How to limit impact:
- Keep lightweight validation on standard runners and isolate image-backed proofing in a separate capacity-aware lane.
- Allow starter validation and source-based proofing to continue even if image-backed proofing must temporarily move off the default lane.

## Testing

### Test Cases

Tests that verify prevention/detection:
```
- Add a workflow step that captures `df -h` and `docker system df` before and after `task image:build`.
- Run the lane on a standard runner and verify it either stays above a chosen free-space threshold or fails early with a clear diagnostic.
- Run the same lane on a 150 GB larger runner and verify the disk failure disappears.
```

### Chaos Engineering

How to test resilience:
- Inject an artificial free-space threshold guard before image-backed proofing and verify the workflow exits with an actionable explanation.
- Prune or disable tar exports in a trial branch and measure the delta in consumed storage.

## Related Failure Modes

Similar or cascading failures:
- Maintainer control-path drift causing unprivileged nested Docker failure.
- Runner image growth reducing practical build headroom for container-heavy workflows.
- Truncated failure logs when the runner itself cannot write to `_diag`.

## Lessons Learned

Key insights from this failure mode:
- The maintainer control-path fix exposed a second, independent CI boundary: disk capacity.
- Image-backed proofing is not just CPU-time expensive; it is storage-amplifying when it combines image layers and tar exports.
- Standard GitHub-hosted runners are a poor default for nested, multi-image proof lanes unless disk use is explicitly budgeted.

## Applicability

### This Failure Mode Applies To

- GitHub-hosted standard Ubuntu runners
- PR lanes that build multiple OCI images
- Nested Docker or Podman workflows inside maintainer containers
- Repositories that export image tarballs as part of validation

### This Failure Mode Does Not Apply To

- Lightweight source-only validation lanes
- Self-hosted runners sized for image-heavy workloads
- Larger runners with materially higher disk budgets when the workload has been validated against that capacity

## Status

Current state of this failure mode:
- [x] Documented
- [ ] Prevention implemented
- [ ] Detection implemented
- [ ] Mitigation tested
- [ ] Monitoring in place

## Related Knowledge

- `KB-2026-036-maintainer-control-path-drift-breaks-image-backed-proofs.md`
- `KB-2026-042-image-backed-starter-proof-should-use-branch-local-verify-images.md`
- `.github/workflows/ci.yml`
- `Taskfile.yml`
