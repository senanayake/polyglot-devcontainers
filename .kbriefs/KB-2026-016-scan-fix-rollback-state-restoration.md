---
id: KB-2026-016
type: failure-mode
status: validated
created: 2026-04-07
updated: 2026-04-07
tags: [scan-fix, security, python, uv, rollback, failure-mode, kbpd]
related: [KB-2026-011, KB-2026-015]
---

# scan:fix Rollback State Restoration

## Context

The first `scan:fix` implementation could apply `uv add`, but it did not
restore the full project state when verification failed. That is dangerous for
an interactive remediation loop because a rejected fix should leave the
repository exactly where it started.

## System/Component

- `templates/python-secure/tasks.py`
- `templates/python-api-secure/tasks.py`
- Polyglot-standard Python templates using `uv.lock` and `pyproject.toml`

## Failure Description

### Symptoms

- a failed fix left `pyproject.toml` mutated even when the lockfile was rolled
  back
- `pytest`, `pip-audit`, and other dev tools disappeared after rollback
- later `task test` or `task scan` runs broke or behaved inconsistently

### Failure Scenario

- `scan:fix` applied a candidate update with `uv add`
- verification failed or the resolver errored
- rollback restored only `uv.lock`
- the active environment no longer matched the original dev workflow

### Impact

- the project could drift into a half-reverted state
- later scans and tests were no longer trustworthy
- users would need manual cleanup after a rejected fix

## Root Cause

### Primary Cause

Rollback was too narrow: it treated `uv.lock` as the only mutable state, even
though `uv add` also mutates `pyproject.toml` and the active environment.

### Contributing Factors

- the dev environment is not preserved by `uv add`
- the task runner originally restored with `uv sync --frozen` instead of the
  full dev sync command
- verification and rollback happened after the manifest had already changed

### Failure Mechanism

```text
uv add candidate fix
-> pyproject.toml and uv.lock change
-> verification fails
-> only uv.lock restored
-> manifest/env drift remains
```

## Evidence

Controlled Polyglot-standard validation:

- `rollback-test-failure` deliberately made the fix fail with a test asserting
  `python-jose==3.3.0`
- after the rollback fix, `task test` passed again and `task scan` returned the
  original vulnerable state
- post-run manifest and lockfile stayed on `python-jose==3.3.0` in
  both the project manifest and lockfile

## Reproduction

### Minimal Reproduction Case

```bash
cd /workspaces/eval-main/lab/standard-variants/rollback-test-failure
task init
printf 'y\n' | task scan:fix
task test
task scan
```

### Conditions Required

- Polyglot-standard Python template
- a direct vulnerable dependency
- a test that intentionally fails after the proposed upgrade

## Prevention

### Design Changes

- back up both `pyproject.toml` and `uv.lock` before applying a fix
- restore both files on failure
- re-sync the full dev environment with `uv sync --frozen --extra dev`

### Operational Controls

- validate rollback with an intentionally failing test case
- verify both `task test` and `task scan` after a rejected fix

### Monitoring

- diff the manifest after a rejected fix
- verify the dev tools still exist after rollback

## Detection

### Early Warning Signs

- post-fix `task test` fails because `pytest` is missing
- `task scan` behavior changes without a successful fix being accepted
- the manifest shows a fixed version even though the user rejected or failed it

### Detection Methods

- inspect `pyproject.toml` and `uv.lock` after a failed fix
- re-run `task test`
- re-run `task scan`

## Mitigation

### Immediate Response

1. Restore `pyproject.toml` from backup.
2. Restore `uv.lock` from backup.
3. Re-sync the dev environment with `uv sync --frozen --extra dev`.

### Recovery Procedure

1. Re-run `task test`.
2. Re-run `task scan`.
3. Confirm the vulnerable baseline is back in place before trying another fix.

### Graceful Degradation

- fail the current candidate fix but keep the project usable
- leave the vulnerability visible rather than partially applying a broken fix

## Testing

### Test Cases

```bash
cd /workspaces/eval-main/lab/standard-variants/rollback-test-failure
printf 'y\n' | task scan:fix
task test
task scan
```

Expected behavior:
- the fix attempt fails
- the manifest and lockfile return to their original values
- `task test` and `task scan` still work afterwards

## Lessons Learned

- `uv add` mutates more than the lockfile, so rollback has to cover manifest
  and environment state as well
- rollback is not complete until the dev toolchain is restored
- a controlled failure variant is the fastest way to validate rollback logic

## Applicability

### This Failure Mode Applies To

- Polyglot Python templates using `uv add` inside `scan:fix`
- workflows where remediation is accepted or rejected based on test results

### This Failure Mode Does Not Apply To

- read-only scans
- repositories that never mutate the manifest during remediation

## Status

- [x] Documented
- [x] Prevention implemented
- [ ] Detection implemented
- [x] Mitigation tested
- [ ] Monitoring in place

## Related Knowledge

- `KB-2026-011-scan-fix-dispatch-and-direct-dependency-boundary.md`
- `KB-2026-015-scan-fix-standard-python-remediation-loop.md`
