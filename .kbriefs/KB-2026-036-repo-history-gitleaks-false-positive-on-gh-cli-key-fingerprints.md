---
id: KB-2026-036
type: failure-mode
status: draft
created: 2026-04-26
updated: 2026-04-26
tags: [gitleaks, security, false-positive, history-scan, maintainer, ci]
related: [KB-2026-031]
---

# Repo-History Gitleaks False Positive On GH CLI Key Fingerprints

## Context

After starter validation and proving were wired into root `task ci`, the repo
contract still failed at the top-level `gitleaks git .` history scan. The
reported findings were not secrets. They were fixed GitHub CLI signing key
fingerprints embedded in the maintainer container build.

## System/Component

Affected components:

- repo-level `gitleaks git .` scan
- `.devcontainer/Containerfile`
- gitleaks default `generic-api-key` rule

## Failure Description

### Symptoms

- root `task ci` fails even though directory scans inside templates and starters
  report no leaks
- SARIF findings point to `.devcontainer/Containerfile` history rather than a
  live credential
- findings are stable across reruns because they come from committed history

### Failure Scenario

- run repo-level `task scan` or root `task ci`
- gitleaks scans Git history
- the default generic key heuristic matches the hard-coded GH CLI fingerprint
  arguments

### Impact

- false blocking failure in the main repository contract
- security signal is diluted by a deterministic non-secret match
- starter-generator work appears broken even when the underlying change is
  correct

## Root Cause

### Primary Cause

The default gitleaks heuristic treated the GH CLI signing key fingerprints as a
generic API key pattern.

### Failure Mechanism

```
history scan -> generic-api-key heuristic matches public fingerprint literal ->
repo-level scan fails -> root ci fails
```

## Evidence

- SARIF findings referenced commit `e05004879889f00c830f7385aada8aa523dac58d`
  and `.devcontainer/Containerfile`
- the matched values were `GH_CLI_KEY_FINGERPRINT_*` arguments, not credentials
- adding a path- and regex-scoped allowlist in `.gitleaks.toml` restored a
  green root `task ci`

## Prevention

### Design Changes

- keep a repo-owned `.gitleaks.toml` for bounded false-positive suppressions
- scope suppressions by rule, path, and regex so real secret detection remains
  intact

## Lessons Learned

- repo-history scans need explicit handling for public fingerprint material used
  in supply-chain verification
- starter-generator progress can expose unrelated repo-wide scan debt, and KBPD
  should capture that instead of treating it as incidental noise

## Applicability

### This Failure Mode Applies To

- repo-level Git history scans
- build metadata that embeds public signing fingerprints

### This Failure Mode Does Not Apply To

- actual credentials or tokens
- path-independent suppressions that would weaken unrelated secret detection

