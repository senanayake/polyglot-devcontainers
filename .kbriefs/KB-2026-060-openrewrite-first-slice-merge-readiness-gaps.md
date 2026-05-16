---
id: KB-2026-060
type: standard
status: active
created: 2026-05-03
updated: 2026-05-03
tags: [java, openrewrite, merge-readiness, validation, kbpd]
related: [KB-2026-021, KB-2026-059]
---

# OpenRewrite First Slice Merge Readiness Gaps

## Context

`feat/java-openrewrite` adds the first repository-sanctioned OpenRewrite slice
for Java:

- Gradle plugin integration in the Java template and examples
- explicit `rewrite:dry-run` and `rewrite:run` task entry points
- documentation describing when to use rewrite tasks versus `task upgrade`

KBPD requires separating what has been **implemented**, what has been
**demonstrated with evidence**, and what is still only **asserted**.

## Problem/Need

The branch is close to mergeable, but the current state still mixes:

- durable product changes
- process transcript artifacts
- manual proof claims that are not yet captured in repository-owned validation

Without closing these gaps, the feature can merge with incomplete proof and can
regress silently later.

## Standard/Pattern

### Description

A first-slice migration feature such as OpenRewrite is ready to merge only when
it meets all of the following:

1. product artifacts are clean and authoritative
2. docs match observed runtime behavior
3. at least one repository-owned automated proof exercises the new entry point
4. any remaining environment-specific limits are explicitly classified as either
   supported behavior or a deferred repository bug

### Key Principles

- Separate product truth from process history.
- Prefer durable proof over one-off manual validation.
- Treat documentation drift as a correctness issue when it affects user
  workflows.
- Record environmental boundaries explicitly rather than letting them remain
  ambiguous.

## Implementation

For `feat/java-openrewrite`, the merge bar was:

```text
Required before merge:
1. Remove TASK.md from the branch.
2. Add an automated non-mutating rewrite proof.
3. Correct docs/K-Brief output-path drift for rewriteDryRun.

Status after follow-up:
1. TASK.md removed.
2. Repo-owned proof added as task scenarios:java-openrewrite.
3. Docs and K-Briefs updated to the observed Gradle 9 patch path.

Strongly recommended before or immediately after merge:
4. Record or fix the Windows + Podman bind-mount Gradle/OpenRewrite boundary.
```

## Rationale

Why this approach is preferred:

- It keeps the first OpenRewrite slice small while still making it trustworthy.
- It avoids merging a feature whose only proof lives in an agent transcript.
- It protects future maintainers from silent regression when Gradle or the
  OpenRewrite plugin changes.

## Benefits

Advantages of following this standard:

- Higher confidence that the new tasks actually remain runnable.
- Lower documentation ambiguity for downstream users.
- Cleaner repository history with less process-noise churn.

## Constraints

Limitations or requirements:

- The current feature intentionally uses a single narrow recipe:
  `org.openrewrite.java.RemoveUnusedImports`.
- The feature is opt-in by design and must remain separate from `task ci` and
  `task upgrade`.
- Proof must remain container-authoritative.

## Alternatives Considered

### Merge As-Is

- Description: accept the current branch because the code change itself is
  small.
- Why not chosen: the branch still contains process noise and lacks durable
  automated proof.

### Block on Full Cross-Platform Hardening

- Description: require the Windows + Podman bind-mount issue to be fixed before
  any merge.
- Why not chosen: the observed failure appears to be an environment/storage
  boundary rather than evidence that the OpenRewrite feature itself is invalid.
  A repository-owned Linux/container proof lane is the higher-priority merge
  bar for this first slice.

## Evidence

Observed evidence for the feature:

- The Gradle plugin is wired into the Java template and both Java examples.
- `rewrite:dry-run` and `rewrite:run` task wrappers exist and are clearly
  labeled.
- In a maintainer-container validation sandbox under `/tmp`,
  `rewriteDryRun` detected an injected unused import and generated a patch.
- In the same sandbox, `rewriteRun` removed the unused import successfully.

Observed merge-readiness gaps before follow-up:

- `TASK.md` was a process transcript and drifted from implementation details by
  naming plugin version `7.32.0` while the branch and KB-2026-059 used `7.30.0`.
- No repository-owned validation lane exercised `rewrite:dry-run`.
- Documentation stated the dry-run patch path as
  `build/rewrite/rewrite.patch`, but observed Gradle 9 behavior wrote the patch
  to `build/reports/rewrite/rewrite.patch`.

Remaining deferred boundary:

- Workspace-mounted validation on this Windows + Podman host hit Gradle/project
  cache I/O errors, so the direct repository task path is not yet proven in
  this environment. The branch now uses a maintainer-container proof that runs
  against a disposable `/tmp` sandbox and captures artifacts under
  `.artifacts/scenarios/`.

## Anti-Patterns

Common mistakes to avoid:

- Merging process transcripts such as `TASK.md` as if they were product docs.
- Treating one successful manual run as equivalent to durable proof.
- Leaving user-facing command output paths wrong after runtime behavior has been
  observed directly.

## Verification

How to verify compliance:

- Confirm `TASK.md` is removed from the branch.
- Run `task scenarios:java-openrewrite` in the maintainer container.
- Confirm docs/K-Brief references use the observed dry-run patch location.
- Re-run `task scenarios:verify` or the CI lane that includes it.

## Migration

If replacing the current branch state:

- Move any durable rationale from `TASK.md` into K-Briefs or product docs.
- Add a non-mutating rewrite proof first; keep mutating proof optional or
  scenario-scoped.
- Leave broader recipe expansion for later slices after this merge bar is met.

## Exceptions

When it's acceptable to deviate:

- The Windows + Podman bind-mount issue may be deferred if:
  - the repository does not claim that exact host path as a merge gate for this
    feature, and
  - a container-authoritative automated proof exists elsewhere.

## Applicability

### Use This Standard When

- adding a new opt-in migration or refactoring tool
- merging a first-slice developer workflow feature
- deciding whether a feature has enough proof to land

### Don't Use This Standard When

- the change is documentation-only
- the feature already has mature, repository-owned proving lanes

## Maintenance

How this standard evolves:

- Revisit once a rewrite proof lane exists.
- Expand when future OpenRewrite slices add recipe libraries or broader recipe
  bundles.

## Related Knowledge

- KB-2026-021
- KB-2026-059
- `docs/core/polyglot-java.md`

## Success Metrics

How to measure adoption and effectiveness:

- `rewrite:dry-run` is exercised automatically in repository validation.
- No process transcript files are needed to understand the feature.
- Documentation and observed runtime behavior stay aligned.
