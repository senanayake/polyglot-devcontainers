---
id: KB-2026-034
type: failure-mode
status: validated
created: 2026-04-25
updated: 2026-04-25
tags: [scan-auto, python, remediation, failure-mode, verification, fixtures]
related: [KB-2026-018]
---

# scan:auto Verification-Scope and Equivalent-Retry Drift

## Context

The Python remediation standard says `scan:auto` must verify each accepted
candidate with the real non-integration test loop and avoid redundant retries
after a candidate has already been proven unacceptable.

## System/Component

- `templates/python-secure/tasks.py`
- `templates/python-api-secure/tasks.py`
- `task scan:auto:fixtures`

## Failure Description

### Symptoms

- the rollback fixture reports accepted remediations even though a follow-up
  full test run fails
- the direct-dev fixture rolls back the same parent-upgrade command more than
  once under different vulnerable-package keys
- `task ci` fails at `task scan:auto:fixtures`

### Failure Scenario

- a guardrail test lives outside `tests/unit` and `tests/property`
- `scan:auto` applies a candidate and runs a narrower verification helper than
  the documented non-integration contract
- a second vulnerable package maps to the same transitive-parent `uv add`
  command after that command already failed once

### Impact

- remediation can report false acceptance
- fixture evidence no longer proves the standard described in KB-2026-018
- automation wastes time retrying equivalent failed upgrades

## Root Cause

### Primary Cause

The remediation helper drifted from the documented verification contract by
running only `tests/unit` and `tests/property` instead of the full
non-integration suite.

### Contributing Factors

- the preflight metadata still advertised the broader verification command,
  hiding the implementation drift
- remediation attempts were keyed by vulnerable package rather than by the
  equivalent upgrade command being proven

### Failure Mechanism

```text
narrow verification helper -> guardrail test not exercised -> bad upgrade accepted
equivalent parent command fails once -> retried under another package key -> duplicate rollback noise
```

## Evidence

- `task scan:auto:fixtures` on `codex/testing-taxonomy-scaffolds`
- failing fixtures: `python-secure-direct-dev`, `python-secure-rollback`
- rollback fixture post-test failure after accepted `python-jose` remediation

## Reproduction

### Minimal Reproduction Case

```bash
task scan:auto:fixtures
cat .artifacts/scans/python-scan-auto-fixtures.json
```

### Conditions Required

- run inside the maintainer container
- use the current Python remediation task runners
- include a guardrail test outside `tests/unit` and `tests/property`

## Prevention

### Design Changes

- keep remediation verification aligned with the documented non-integration test
  command
- collapse equivalent remediation attempts by command signature rather than only
  by vulnerable-package key

### Operational Controls

- keep `task scan:auto:fixtures` in root `task ci`
- treat fixture failures as contract regressions, not optional maintenance

### Monitoring

- watch for mismatches between `preflight.verification_command` and the helper
  implementation
- watch for duplicate exhausted candidates that share the same remediation
  command

## Detection

### Early Warning Signs

- a remediation report says `tests passed` but a follow-up `task test` fails
- a single parent dependency upgrade appears multiple times in rolled-back
  results

### Detection Methods

- run `task scan:auto:fixtures`
- inspect `.artifacts/scans/python-scan-auto-fixtures.json`
- inspect `.artifacts/scans/dependency-remediation-report.json` for repeated
  commands

## Mitigation

### Immediate Response

1. widen the verification helper to the full non-integration suite
2. deduplicate equivalent remediation attempts by command signature
3. rerun the fixture matrix and root `task ci`

## Testing

### Test Cases

- the rollback fixture must fail remediation and leave tests green after
  rollback
- the direct-dev fixture must record at most one rollback for the same
  `pip-audit` parent upgrade
- `task scan:auto:fixtures` must pass inside the maintainer container

## Lessons Learned

- verification scope drift is a correctness bug, not just a testing detail
- remediation attempts should be keyed by the evidence-producing command, not
  only by the vulnerable package that surfaced it

## Applicability

- Applies to: Polyglot Python remediation runners and their fixture matrix
- Does not apply to: templates that do not implement `scan:auto`
