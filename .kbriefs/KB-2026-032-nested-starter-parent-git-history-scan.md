---
id: KB-2026-032
type: failure-mode
status: draft
created: 2026-04-26
updated: 2026-04-26
tags: [starters, gitleaks, git, nested-workspace, python-node, proof]
related: [KB-2026-009, KB-2026-031]
---

# Nested Starter Falls Back To Parent Git History Scan

## Context

The first starter-catalog proof slice generated a `python-node-secure` starter
under the repository's `.tmp/` directory and then ran `task ci` inside that
generated workspace.

The proof failed even though the starter files themselves were valid because the
secret-scan path detected the parent repository's Git history and switched into
Git-history scan mode.

## System/Component

Affected component:

- `templates/python-node-secure/tasks.py`

Affected behavior:

- gitleaks mode selection during `task scan`

## Failure Description

### Symptoms

Observable signs of failure:

- a generated starter nested under another Git repository reports secret leaks
  unrelated to the generated starter files
- `task ci` fails in the generated starter during the gitleaks step
- the failure disappears when the same starter is moved outside the parent Git
  repository

### Failure Scenario

Conditions that trigger the failure:

- generate or copy `python-node-secure` into a directory that is inside another
  Git working tree
- run `task ci` or `task scan`
- the task logic detects "inside a Git work tree" and uses `gitleaks git`

### Impact

Consequences of the failure:

- starter-local validation is contaminated by unrelated parent-repo history
- generated-starter proofs produce false negatives
- users cannot trust secret-scan failures in nested starter workspaces

## Root Cause

### Primary Cause

The previous `in_git_repo()` implementation only asked Git whether the current
directory was inside any work tree:

- `git rev-parse --is-inside-work-tree`

That test returns true for nested directories inside a parent repository even
when the starter workspace does not own that repository.

### Contributing Factors

Additional factors that enable or worsen the failure:

- generated starter proofs were placed under repo-owned `.tmp/`
- `gitleaks git <path>` operates on the containing repository history rather
  than only on the nested directory contents
- the fallback `dir` scan path is already available, so the incorrect Git mode
  selection was avoidable

### Failure Mechanism

How the failure propagates through the system:

```
starter nested under parent repo -> inside-work-tree check returns true ->
Git mode selected -> parent repo history scanned -> unrelated leaks reported ->
starter proof fails
```

## Evidence

Data demonstrating this failure mode:

- the first `task starters:prove -- --all` run passed for `python-secure` and
  failed for `python-node-secure`
- the failure occurred during the gitleaks Git-mode scan inside the generated
  `python-node-secure` workspace
- the generated workspace path was under
  `/workspaces/polyglot-devcontainers/.tmp/starter-proving/python-node-secure`

## Reproduction

### Minimal Reproduction Case

Simplest way to trigger the failure:

```bash
task starters:prove -- --starter python-node-secure
```

when the proof workspace is created under the repository root and the starter's
Git detection only checks "inside a work tree".

### Conditions Required

Prerequisites for reproduction:

- a parent Git repository exists
- the generated starter is nested inside it
- the starter scan logic uses Git-mode scanning when any parent Git repo exists

## Prevention

### Design Changes

Architectural changes to prevent the failure:

- only use Git-mode scanning when the starter workspace itself is the Git
  top-level directory
- otherwise fall back to directory-mode scanning

### Operational Controls

Operational practices to avoid the failure:

- avoid relying on parent-repo Git context when proving starter-local behavior
- keep generated starter proofs explicit about whether they are validating
  repo-owned or standalone behavior

## Detection

### Detection Methods

How to identify the failure:

- compare reported secret leaks with files present in the generated workspace
- inspect whether `git rev-parse --show-toplevel` equals the starter root
- confirm whether `gitleaks-mode.json` reports `git` or `dir`

## Mitigation

### Immediate Response

What to do when failure occurs:

1. confirm whether the starter is nested under a parent repository
2. switch secret scanning to directory mode unless the starter owns the Git root
3. rerun the starter proof

## Lessons Learned

Key insights from this failure mode:

- "inside a Git work tree" is too weak as a starter-local ownership test
- generated-starter proofs can expose behavioral mismatches that template-local
  repo validation does not reveal
- nested starter workspaces are a useful KBPD probe because they surface hidden
  parent-context assumptions

## Applicability

### This Failure Mode Applies To

- generated `python-node-secure` starters
- starter proofs run inside a parent repository
- any starter workflow that switches behavior based only on
  `--is-inside-work-tree`

### This Failure Mode Does Not Apply To

- starter workspaces that own their own Git root
- `python-secure`, which currently uses directory-mode gitleaks scanning in its
  standalone task contract

## Related Knowledge

- `KB-2026-009-scenario-adoption-barriers.md`
- `KB-2026-031-starter-generator-knowledge-gaps-and-learning-cycles.md`
