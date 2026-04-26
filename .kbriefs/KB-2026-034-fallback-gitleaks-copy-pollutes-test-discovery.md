---
id: KB-2026-034
type: failure-mode
status: draft
created: 2026-04-26
updated: 2026-04-26
tags: [starters, gitleaks, tmp, test-discovery, python-node, proof]
related: [KB-2026-032, KB-2026-033]
---

# Fallback Gitleaks Copy Pollutes Later Test Discovery

## Context

After fixing parent-Git ownership for `python-node-secure`, generated starter
proofs still showed an undesirable side effect during repeated `task ci` and
scenario runs.

The non-Git fallback scan copied starter files into `.tmp/gitleaks-source-scan`
inside the workspace and left that copy behind after the scan completed.

## System/Component

Affected component:

- `templates/python-node-secure/tasks.py`

Affected behavior:

- temporary workspace creation for `gitleaks dir` fallback mode

## Failure Description

### Symptoms

- later `vitest` runs see duplicate tests under `.tmp/gitleaks-source-scan`
- repeated starter-local proofs become noisier than expected
- temporary scan state becomes visible to tools that traverse the workspace

### Failure Scenario

- run `task scan` in non-Git fallback mode
- fallback copies a subset of the workspace into `.tmp/gitleaks-source-scan`
- run `task test`, `task ci`, or a scenario that repeats test discovery

### Impact

- duplicated test execution
- reduced confidence in repeatability of starter-local proofs
- avoidable workspace pollution from a temporary scan artifact

## Root Cause

### Primary Cause

The fallback scan tree was created at a stable path under the workspace and was
not removed after the gitleaks command completed.

### Failure Mechanism

```
fallback dir scan -> copied tree left under .tmp -> later test discovery sees
copied tests -> duplicate execution/noise
```

## Evidence

- generated `python-node-secure` proof runs showed `vitest` discovering copied
  tests under `.tmp/gitleaks-source-scan`
- switching the fallback tree to a temporary directory with explicit cleanup
  removed the duplicate discovery

## Prevention

### Design Changes

- create the fallback scan tree in a temporary directory
- clean it up in a `finally` block after gitleaks completes

## Lessons Learned

- starter-local fallback helpers should behave like ephemeral scratch space, not
  durable workspace content
- KBPD proof loops are useful for finding interactions between scans and later
  test discovery that template-local checks can miss

## Applicability

### This Failure Mode Applies To

- non-Git fallback scanning in `python-node-secure`
- repeated proof loops that rerun tests after fallback scans

### This Failure Mode Does Not Apply To

- Git-mode gitleaks scans
- starter tasks that do not materialize copied fallback trees inside the
  workspace

## Related Knowledge

- `KB-2026-032-nested-starter-parent-git-history-scan.md`
- `KB-2026-033-source-template-first-starter-generator-thin-slice.md`
