---
id: KB-2026-048
type: failure-mode
status: published
created: 2026-05-01
updated: 2026-05-01
tags: [starters, public-service, ci, tempfile, failure-mode, kbpd]
related:
  - KB-2026-046-public-starter-downloads-should-come-from-released-snapshots.md
  - KB-2026-047-public-starter-deployment-should-wait-until-local-contract-is-stable.md
---

# Public Validator Must Create Its Temp Root Before Using `TemporaryDirectory`

## Context

The hardened public starter API added a maintainer-container validation lane in
`task starters:validate:public`. GitHub CI later failed on that lane even
though the validator had passed in local development.

## Failure Description

### Symptoms

- `task starters:validate:public` exits with `FileNotFoundError`
- the traceback points at `tempfile.TemporaryDirectory(..., dir=ROOT / ".tmp")`
- the parent `task starters:verify` and root `task ci` fail immediately after
  the public validator starts

### Failure Scenario

This failure occurs when:

- the validator asks `TemporaryDirectory` to create its workspace under
  `ROOT / ".tmp"`
- that `.tmp` directory has not already been created by a prior local workflow
- the CI job runs in a clean checkout where no previous task populated `.tmp`

### Impact

- public starter contract validation fails before any API assertions run
- `task starters:verify` fails even when the service logic itself is correct
- GitHub CI reports the branch as failed for an environment-precondition bug

## Root Cause

### Primary Cause

`tempfile.TemporaryDirectory(dir=...)` requires the parent directory to already
exist. The validator assumed `.tmp` existed because local runs often inherited
it from prior host activity.

### Contributing Factors

- local development state masked the missing-directory assumption
- the validator used an explicit temp root but did not create it
- CI starts from a cleaner filesystem than the host workflow

### Failure Mechanism

```
clean checkout -> missing ROOT/.tmp -> TemporaryDirectory(dir=ROOT/.tmp) ->
FileNotFoundError -> starters:validate:public fails -> starters:verify fails
```

## Evidence

- GitHub CI failed with:
  - `FileNotFoundError: [Errno 2] No such file or directory: '/workspaces/polyglot-devcontainers/.tmp/starter-public-api-...'`
- the failing code path was in `scripts/validate_public_starter_api.py`
- after creating `ROOT / ".tmp"` explicitly, maintainer validation passed:
  - `task maintainer:task -- starters:validate:public`

## Prevention

### Design Changes

- create the explicit temp parent before calling `TemporaryDirectory`
- treat clean-checkout execution as the default validation environment
- keep validator temp roots repo-local but self-initializing

### Operational Controls

- keep `task starters:validate:public` in the maintainer verification path
- validate new temp-root assumptions in clean container runs, not only host
  runs

## Testing

### Test Cases

- run `task maintainer:task -- starters:validate:public` from a clean checkout
- verify the validator succeeds without pre-creating `.tmp`

## Lessons Learned

- CI-only filesystem assumptions are product bugs, not incidental flakiness
- repository-local temp roots are acceptable only when the owning workflow
  creates them explicitly

## Applicability

### This Failure Mode Applies To

- starter public API validation
- any repository task that passes a custom `dir=` path into `tempfile`

### This Failure Mode Does Not Apply To

- `TemporaryDirectory` calls that rely on the default system temp root
- workflows that create their own parent temp directories before use
