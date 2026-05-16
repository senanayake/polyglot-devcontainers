---
id: KB-2026-056
type: failure-mode
status: active
created: 2026-05-02
updated: 2026-05-02
tags:
  - starters
  - ci
  - github-actions
  - docker
  - permissions
  - failure-mode
related:
  - KB-2026-042
  - KB-2026-055
---

# Published Image Smoke Workspace Overrides Need Permission Normalization

## Context

The free-tier CI split introduced per-image medium lanes that build one image at a time and then run published-image starter proofs against that image. Those proofs pass a pre-generated workspace into the smoke harness instead of letting the harness create its own temporary workspace.

## System/Component

- `scripts/smoke_test_published_starter.sh`
- `scripts/starter_catalog.py`
- medium image-backed GitHub Actions lanes

## Failure Description

### Symptoms

- `task starters:verify:image-backed -- --profile medium --image <target>` fails after the image build succeeds
- nested smoke container reaches `task init`
- scaffold copy operations fail with `cp: cannot create regular file ...: Permission denied`

### Failure Scenario

- the starter proof path generates a workspace before calling the smoke harness
- the smoke harness receives that path through `--workspace`
- the nested proof container tries to scaffold into the mounted workspace

### Impact

- free-tier medium per-image lanes look broken even though image builds are healthy
- the remaining failure obscures whether the lane split actually solved the disk-pressure problem
- published-image starter proofs cannot validate single-image workflows

## Root Cause

### Primary Cause

The smoke harness only normalized permissions for its internally created temporary workspace. It did not normalize permissions for caller-supplied workspaces passed through `--workspace`.

### Contributing Factors

- the new medium proof path reuses a pre-generated workspace instead of the harness creating one itself
- nested Docker bind mounts preserve host/container filesystem permissions
- `task init` needs write access to the mounted project root to scaffold starter files

### Failure Mechanism

```
pre-generated workspace -> mounted into nested proof container -> task init copies scaffold files
-> project root is not normalized for nested writes -> copy fails with Permission denied
```

## Evidence

- GitHub Actions run `25251611850`
- failing jobs: `medium / java` and `medium / python-node`
- both jobs completed the target image build and metadata validation before failing in `scripts/smoke_test_published_starter.sh`
- failure lines show `cp: cannot create regular file ...: Permission denied` immediately after `phase=task-init`
- post-fix targeted proofs passed locally inside the maintainer container for:
  - `java-secure` with `POLYGLOT_STARTER_PROOF_IMAGE_JAVA_SECURE=polyglot-devcontainers-java:verify`
  - `python-node-secure` with `POLYGLOT_STARTER_PROOF_IMAGE_PYTHON_NODE_SECURE=polyglot-devcontainers-python-node:verify`

## Reproduction

### Minimal Reproduction Case

```bash
task starters:verify:image-backed -- --profile medium --image java
task starters:verify:image-backed -- --profile medium --image python-node
```

### Conditions Required

- published-image starter proof path
- caller-supplied workspace via `--workspace`
- nested container write operations during `task init`

## Prevention

### Design Changes

- normalize permissions for caller-supplied smoke workspaces before bind-mounting them
- keep the normalization inside the smoke harness so all callers inherit the same behavior

### Operational Controls

- validate one medium image lane at a time after smoke-harness changes
- preserve starter proof artifacts in CI so permission failures are obvious

## Detection

### Early Warning Signs

- image build succeeds but starter proof fails almost immediately in `task init`
- proof workspace contains only `.devcontainer` inputs after failure

### Detection Methods

- GitHub Actions failed job logs
- starter proof markdown/json artifacts under `.artifacts/starters`

## Mitigation

### Immediate Response

1. Update the smoke harness to `chmod -R 0777` the caller-supplied workspace before launching the nested container.
2. Re-run the per-image medium lanes.
3. Confirm the failure moves past `task init`.

## Testing

### Test Cases

```bash
task starters:verify:image-backed -- --profile medium --image java
task starters:verify:image-backed -- --profile medium --image python-node
```

### Validation Evidence

The narrower published-image proof commands passed after the smoke-harness fix:

```bash
python scripts/starter_catalog.py prove --starter java-secure --mode published-image-bootstrap --profile baseline
python scripts/starter_catalog.py prove --starter python-node-secure --mode published-image-bootstrap --profile polyglot-default
```

## Lessons Learned

- free-tier fanout exposed a real proof-contract bug that the monolithic lane masked
- workspace lifecycle assumptions belong in the smoke harness, not in each caller

## Status

- [x] Documented
- [x] Prevention implemented
- [ ] Detection implemented
- [x] Mitigation tested
- [x] Monitoring in place
