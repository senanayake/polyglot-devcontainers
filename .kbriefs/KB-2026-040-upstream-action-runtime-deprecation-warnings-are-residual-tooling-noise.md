---
id: KB-2026-040
type: standard
status: published
created: 2026-04-28
updated: 2026-04-28
tags: [github-actions, release, warnings, upstream, residual-risk]
related:
  - KB-2026-038-release-image-scan-must-report-upstream-residual-risk-without-blocking-release.md
  - KB-2026-039-retry-upstream-binary-downloads-in-image-builds.md
---

# Upstream Action Runtime Deprecation Warnings Are Residual Tooling Noise

## Context

After the `v0.0.27` main release path was repaired and re-run successfully, the
remaining workflow annotations were Node 20 deprecation warnings emitted by
third-party GitHub Actions in the Docker and artifact upload stack.

## Standard/Pattern

Treat these warnings as upstream residual tooling noise once three conditions
are true:

- repository-pinned actions are already on the latest compatible major versions
- repo-owned action usage has been updated where newer majors exist
- the warnings do not block the required CI or release workflows

## Why This Is The Right Standard Now

- the warnings are outside repo-owned application logic
- forcing local workarounds would add maintenance burden without improving the
  shipped starter or image contracts
- KBPD favors closing the learning loop once the remaining issue is clearly
  external and non-blocking

## Evidence

- branch validation run `25034936434` passed after repo-owned warning cleanup
- remaining deprecation annotations came from upstream action internals in the
  Docker build/login/metadata/buildx stack and artifact/cache helpers
- the repaired `main` release completed successfully for tag `v0.0.27`

## Operational Rule

- update to newer upstream action majors when they exist and are compatible
- do not block merge or release on these annotations once the repo-controlled
  upgrades have been exhausted
- record the residue in a K-Brief rather than reopening release-fix work

## Applicability

### This Standard Applies To

- GitHub Actions runtime deprecation warnings originating inside third-party
  actions
- release and branch validation runs that are otherwise green

### This Standard Does Not Apply To

- warnings caused by repo-authored composite actions or workflow logic
- deprecated action majors that the repository has not yet upgraded
- warnings that correlate with failing jobs or broken release outputs
