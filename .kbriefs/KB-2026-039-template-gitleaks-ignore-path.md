---
id: KB-2026-039
type: failure-mode
status: active
created: 2026-05-16
updated: 2026-05-16
tags: [gitleaks, secret-scanning, template, history-scan, false-positive, kbpd]
related: [KB-2026-035]
---

# Template Gitleaks Scan Missed Root Ignore File

## Context

The repository has a root `.gitleaksignore` for two known historical public
GitHub signing-key fingerprint false positives. A full `task image:verify`
still failed in the nested maintainer `task ci` path while scanning
`templates/python-node-secure`.

## System/Component

- `templates/python-node-secure/tasks.py`
- root `.gitleaksignore`
- `task image:verify`

## Failure Description

### Symptoms

The root scan had an ignore file, but the template scan reported the same two
historical `generic-api-key` findings from commit
`e05004879889f00c830f7385aada8aa523dac58d`.

### Failure Scenario

`templates/python-node-secure/tasks.py` ran `gitleaks git` with `cwd` set to
the template directory. Gitleaks defaults `--gitleaks-ignore-path` to `.`, so
it looked for `.gitleaksignore` in the template directory rather than the
repository root.

### Impact

Full image verification failed after image builds and starter smokes succeeded,
blocking unrelated image feature validation.

## Root Cause

The scan target lived inside a larger Git worktree, but the task did not pass
the repository-level ignore path explicitly.

## Evidence

- `task maintainer:task -- image:verify` failed in
  `templates/python-node-secure/tasks.py scan`.
- The generated SARIF contained the two fingerprints listed in the root
  `.gitleaksignore`.
- After adding explicit `--gitleaks-ignore-path <git-root>/.gitleaksignore`,
  `task maintainer:task -- -t templates/python-node-secure/Taskfile.yml scan`
  passed with `no leaks found`.

## Prevention

- Template-local gitleaks history scans should resolve the Git top-level path
  and pass the root ignore file when it exists.
- Keep fallback `dir` scans independent so non-Git starter validation does not
  depend on repository history or root-only files.

## Recommendation

When a task scans a subdirectory as a Git repository member, pass repository
policy files explicitly instead of relying on tool defaults relative to `cwd`.
