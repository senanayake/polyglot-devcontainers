---
id: KB-2026-061
type: standard
status: active
created: 2026-05-03
updated: 2026-05-03
tags: [agents, aider-relay, process, merge-readiness, kbpd]
related: [KB-2026-059, KB-2026-060]
---

# Aider-Relay First Slice Process Learnings

## Context

`feat/java-openrewrite` was initially produced through an aider-relay workflow.
The relay left three kinds of evidence:

- session metadata in `.aider-relay/session.json`
- generated patch mail files
- the resulting branch contents

This brief captures what the process did well, where it drifted, and what
guardrails are needed when using the same workflow again.

## Problem/Need

The relay produced a useful first slice, but it also mixed:

- product changes
- process transcript artifacts
- proof claims that were not yet encoded in repository-owned validation

Without recording the pattern, future relay-driven work is likely to repeat the
same cleanup cycle.

## Standard/Pattern

### Description

Use aider-relay for **narrow implementation slices with explicit task specs**,
but require a human or second agent to perform a merge-readiness pass before the
branch is considered done.

### Key Principles

- Relay is good at bounded code generation and local consistency work.
- Relay output is not the same as repository-integrated proof.
- Process artifacts must not be merged as product artifacts.
- "BUILD SUCCESSFUL" claims need durable repo-owned validation, not just a task
  transcript.

## Evidence

Observed from this run:

- The relay had a strong task spec with concrete deliverables, proof paths, and
  non-goals in `.aider-relay/session.json`.
- The generated patch set was narrow and coherent: OpenRewrite plugin wiring,
  task wrappers, docs, and a K-Brief.
- The relay also produced `TASK.md`, a process transcript that duplicated the
  task brief and drifted from the actual implementation.
- The first patch mail claimed plugin version `7.32.0`, while the actual branch
  and later K-Brief settled on `7.30.0`.
- The relay declared proof complete, but no repository-owned validation lane was
  added, so the feature was still vulnerable to silent regression.
- The relay did not fully reconcile observed runtime behavior with docs: the
  actual Gradle 9 dry-run patch location was `build/reports/rewrite/rewrite.patch`,
  not the documented `build/rewrite/rewrite.patch`.
- The relay session ended with handoff reason `exhausted`, which matches the
  pattern that bounded implementation succeeded but final integration hygiene
  remained unfinished.

## What Worked Well

- The task spec quality was high enough to keep scope tight.
- The relay respected the desired architecture:
  - Gradle-first integration
  - no CLI binary
  - tasks separate from `ci` and `upgrade`
- The first recipe choice was disciplined and low risk.
- Patch artifacts made it easy to inspect exactly what was proposed.

## What Did Not Get Closed

- Product-vs-process separation
- Durable proof in repository task surfaces
- Final documentation alignment with observed behavior
- Environment boundary classification

## Anti-Patterns

- Treating a relay-maintained `TASK.md` as shippable documentation
- Treating patch-mail claims as authoritative after implementation diverges
- Accepting "all proof paths passed" without repository-owned regression hooks

## Verification

A relay-produced feature is ready only after a follow-up pass confirms:

- no process transcript artifacts remain
- docs match observed runtime behavior
- at least one repository-owned validation path exercises the new feature
- remaining host/runtime failures are explicitly deferred or fixed

## Applicability

### Use This Standard When

- the task is a small, well-scoped feature slice
- the acceptance criteria are concrete
- a follow-up integration pass is available

### Don't Use This Standard When

- the task spans multiple architectural layers without a narrow proof target
- the branch needs immediate "merge-ready in one pass" confidence

## Success Metrics

- relay branches require only small merge-readiness cleanup
- no process transcript files merge
- feature proof moves from transcript claims into repository automation
