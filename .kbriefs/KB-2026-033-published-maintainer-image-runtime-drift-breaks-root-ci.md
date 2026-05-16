---
id: KB-2026-033
type: failure-mode
status: validated
created: 2026-04-24
updated: 2026-04-24
tags: [maintainer-image, runtime-drift, failure-mode, ci, diagrams]
related: [KB-2026-032]
---

# Published Maintainer Image Runtime Drift Breaks Root CI

## Context

The repository tells agents to trust the maintainer container as the source of
truth for validation. That makes published-image drift a correctness problem,
not just an operational inconvenience.

## System/Component

- published maintainer image
- root `task ci` workflow
- diagram example lint path

## Failure Description

### Symptoms

- root `task ci` fails in the default published maintainer container
- `examples/diagram-image-example` lint exits with `d2: command not found`
- the failure happens even though the repo-owned maintainer `Containerfile`
  installs `features/diagram-rendering`

### Failure Scenario

- maintainer image contents lag the repo's current feature contract
- root `task ci` reaches the diagram example lint step
- the published container lacks `d2`, so the diagram lint path cannot execute

### Impact

- repo-level validation is blocked in the default maintainer path
- agents can no longer treat published maintainer behavior as equivalent to repo
  source intent
- task-contract confidence drops because the default maintainer image and the
  repo's own workflows disagree

## Root Cause

### Primary Cause

The published maintainer image drifted behind the repo's declared maintainer
feature set.

### Contributing Factors

- root CI depends on diagram tooling indirectly through the example lint path
- the maintainer image is consumed by tag, so stale published contents can
  persist after repo changes
- the failure only becomes visible when the full root workflow is exercised

### Failure Mechanism

```text
published image missing d2 -> diagram lint step starts -> shell cannot find d2 -> root task ci fails
```

## Evidence

- `python scripts/run_in_maintainer_container.py exec -- bash -lc 'cd /workspaces/polyglot-devcontainers-testing-framework && task ci'`
- failure excerpt: `bash: line 2: d2: command not found`
- repo source evidence: [Containerfile](C:/dev/polyglot-devcontainers-testing-framework/.devcontainer/Containerfile:53) runs `features/diagram-rendering/install.sh`

## Reproduction

### Minimal Reproduction Case

```bash
python scripts/run_in_maintainer_container.py up
python scripts/run_in_maintainer_container.py exec -- bash -lc 'cd /workspaces/polyglot-devcontainers-testing-framework && task -t examples/diagram-image-example/Taskfile.yml lint'
```

### Conditions Required

- use the default published maintainer image
- run the diagram example lint or root `task ci`
- rely on the maintainer container contents instead of a rebuilt local image

## Prevention

### Design Changes

- keep the published maintainer image aligned with the repo-owned feature set
- validate maintainer image contents, not just source `Containerfile` intent
- treat missing repo-required tools in the published maintainer image as a
  release-blocking defect

### Operational Controls

- rebuild and validate a local maintainer image when maintainer-tooling drift is
  suspected
- release maintainer-image refreshes promptly after feature changes
- include diagram example lint in published-image verification paths

### Monitoring

- add or preserve a smoke check that asserts `d2 --version` in the maintainer
  image
- keep root `task ci` in the maintainer image validation path

## Detection

### Early Warning Signs

- root lint fails only in the default published maintainer image
- diagram example commands pass in rebuilt local images but fail in the
  published image
- maintainer image release timing lags repo feature changes

### Detection Methods

- run root `task ci` in the published maintainer image
- run `which d2` or `d2 --version` in the maintainer container
- compare published-image behavior with a locally rebuilt maintainer image

## Mitigation

### Immediate Response

1. confirm the missing tool in the published maintainer image
2. rebuild the maintainer image from repo source
3. rerun root validation against the rebuilt image

### Recovery Procedure

1. build a local maintainer image from `.devcontainer/Containerfile`
2. set `POLYGLOT_MAINTAINER_IMAGE` to that image tag
3. rerun `python scripts/run_in_maintainer_container.py exec -- task ci`
4. refresh the published maintainer image through the normal release path

### Graceful Degradation

- validate starter-scoped workflows independently while maintainer-image repair
  is in progress
- record the drift as a failure mode so it is not mistaken for a starter bug

## Testing

### Test Cases

- root `task ci` passes in a rebuilt maintainer image
- `task -t examples/diagram-image-example/Taskfile.yml lint` passes in the
  rebuilt maintainer image
- `d2 --version` succeeds in the maintainer container used for validation

## Lessons Learned

- maintainer-image drift can invalidate otherwise-correct repo work
- repo-level validation needs at least one content smoke check for every tool
  that root workflows depend on
- published-image correctness is part of the task contract, not separate from it

## Applicability

- Applies to: maintainer image refreshes, repo-level validation, toolchain-heavy examples
- Does not apply to: starter-only validation inside purpose-built starter images
