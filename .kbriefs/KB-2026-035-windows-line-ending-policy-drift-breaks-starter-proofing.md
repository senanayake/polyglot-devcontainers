---
id: KB-2026-035
type: failure-mode
status: draft
created: 2026-04-26
updated: 2026-04-26
tags: [windows, line-endings, starters, ci, formatting, proof]
related: [KB-2026-033]
---

# Windows Line-Ending Policy Drift Breaks Starter Proofing

## Context

The starter catalog thin slice was initially proven in a Windows-hosted clone
that had broad CRLF checkout behavior. Once starter proofing expanded to include
`java-secure` and repo-level `task ci`, generated starter workspaces started to
inherit line endings that disagreed with the template formatters and checkers.

## System/Component

Affected components:

- repository line-ending policy in `.gitattributes`
- generated starter workspaces copied from repo templates
- formatter and lint gates in Java, Node, and documentation surfaces

## Failure Description

### Symptoms

- generated starter proofs fail on formatting or check steps even when source
  content is semantically unchanged
- Windows worktrees show large numbers of modified files after starter work
- the repo contract passes on one host state and fails on another because line
  endings drift before generation

### Failure Scenario

- expand the starter catalog and prove generated starters from a Windows clone
- copy template files into generated workspaces
- run container-authoritative checks that expect LF-normalized sources

### Impact

- false-negative starter proofs
- noisy diffs that hide real product changes
- lower confidence that generated starters are deterministic across host
  platforms

## Root Cause

### Primary Cause

The repository did not declare LF policy for several file types that now
participate directly in starter generation and proofing.

### Failure Mechanism

```
Windows CRLF checkout -> generated starter copies CRLF files -> formatter/check
expects LF -> starter proof fails or produces noisy drift
```

## Evidence

- extending `.gitattributes` to cover starter-relevant file types removed the
  newline-policy ambiguity
- after the LF policy update, maintainer-container `task starters:verify` and
  full root `task ci` both passed

## Prevention

### Design Changes

- declare LF policy for starter-relevant text file types in `.gitattributes`
- treat generated starter proofing as a cross-platform newline-policy check, not
  only a template correctness check

## Lessons Learned

- starter generation turns repository checkout policy into product behavior
- container-authoritative proofing is still sensitive to host-side text
  normalization when generation begins from a host worktree

## Applicability

### This Failure Mode Applies To

- Windows-hosted clones used to generate starter workspaces
- starter proof loops that copy template files before container validation

### This Failure Mode Does Not Apply To

- purely container-authored files created after generation
- starter proofing paths that no longer depend on host checkout state

