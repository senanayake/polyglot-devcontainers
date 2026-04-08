---
id: KB-2026-015
type: standard
status: validated
created: 2026-04-07
updated: 2026-04-07
tags: [scan-fix, security, python, uv, kbpd, standard, template-validation]
related: [KB-2026-010, KB-2026-011, KB-2026-016, KB-2026-017]
---

# scan:fix Standard Remediation Loop for Polyglot Python Templates

## Context

`scan:fix` exists to turn `task scan` findings into a guided remediation path
for Polyglot Python templates. After fixing the dispatch bug in `KB-2026-011`,
the next question was whether the mechanism actually works on repositories that
match the Polyglot task contract instead of arbitrary public projects.

## Problem/Need

We needed a validated standard for how `scan:fix` should behave on a
Polyglot-standard Python project:
- direct vulnerable dependencies should be offered as fix candidates
- transitive-only findings should remain visible but skipped
- the dev environment should survive remediation so tests and later scans still
  work
- successful fixes should leave the manifest and lockfile updated in place

## Standard/Pattern

### Description

For Polyglot Python templates, `scan:fix` should:
- load a fresh `pip-audit` report for the active environment
- map findings back to declared dependencies only
- apply fixes with `uv add` using the original declaration shape and scope
- immediately re-sync the dev environment with `uv sync --frozen --extra dev`
- verify the candidate fix with a direct `pytest -q -x` subprocess that does
  not inherit the task runner's temp-directory overrides
- keep transitive findings as manual Phase 1 items

### Key Principles

- Remediate only declared dependencies in Phase 1.
- Preserve the Polyglot dev toolchain before and after each fix attempt.
- Verify with the real project test loop before accepting a fix.

### Implementation

Core task-runner changes:

```python
def sync_dev_environment() -> None:
    run([UV, "sync", "--frozen", "--extra", "dev"])

def run_verification_tests() -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    env.pop("TMP", None)
    env.pop("TEMP", None)
    env.pop("TMPDIR", None)
    return subprocess.run(
        [str(PYTHON), "-m", "pytest", "-q", "-x"],
        cwd=ROOT,
        check=False,
        text=True,
        env=env,
    )
```

## Rationale

This approach is preferred because:
- `uv add` alone can rewrite the environment away from the dev extras required
  by `pytest`, `pip-audit`, and related tooling
- using declared dependency specifiers preserves optional-group and exact-pin
  intent
- a direct subprocess for verification avoids false failures caused by the
  task wrapper's temp-environment settings

## Benefits

- Direct runtime and dev vulnerabilities can now be remediated end-to-end on
  Polyglot-standard templates.
- Successful fixes leave the repository in a runnable and scannable state.
- Transitive-only vulnerabilities stay visible without widening the manifest.

## Constraints

- This standard applies only to declared dependencies in Polyglot-standard
  Python templates.
- Remaining transitive findings are not automatically remediated in Phase 1.
- The project still needs a satisfiable `requires-python` range; see
  `KB-2026-017`.

## Alternatives Considered

### Fix All Audited Packages

- Treat every vulnerable `pip-audit` package as editable.
- Not chosen because it promotes transitive packages into direct dependencies.

### Verify Inside the Generic Task Wrapper

- Reuse the same temp-wrapper logic used for scans.
- Not chosen because controlled validation showed false verification failures
  after `uv add` and `uv sync`.

## Evidence

Validated with a controlled Polyglot-standard variant matrix in the maintainer
container:

- Control case: `base-transitive-only` skipped both `pygments` and `requests`
  without mutating the manifest.
- Direct runtime remediation: `runtime-direct-vuln` upgraded
  `python-jose[cryptography]==3.3.0` to `==3.4.0`, then `task test` and
  `task scan` passed with only non-blocking transitive findings remaining.
- Direct dev remediation: `dev-direct-vuln` upgraded `pygments==2.19.1` to
  `==2.20.0`, then `task test` and `task scan` passed.

## Anti-Patterns

- Running `uv add` and then testing without restoring the dev extras.
- Building fix commands from raw audit package names instead of declared
  dependency entries.
- Treating transitive findings as safe automatic edits.

## Verification

Use the maintainer container and run:

```bash
cd /workspaces/eval-main/lab/standard-variants/runtime-direct-vuln
task init
printf 'y\n' | task scan:fix
task test
task scan
```

Expected behavior:
- the direct dependency is offered as a fix candidate
- tests pass after the fix
- the manifest and lockfile stay updated
- only transitive leftovers remain

## Exceptions

- Projects with a broken or overly broad `requires-python` declaration are out
  of scope for this standard; see `KB-2026-017`.
- Repositories without the Polyglot task contract are out of scope for this
  standard.

## Applicability

### Use This Standard When

- the repository follows the Polyglot Python template shape
- vulnerabilities exist on declared runtime or dev dependencies
- the maintainer container is the source of truth

### Don't Use This Standard When

- the only findings are transitive and you do not want manifest widening
- the project does not expose the Polyglot task contract
- the project is already outside its declared Python support boundary

## Related Knowledge

- `KB-2026-010-interactive-fix-workflow-design.md`
- `KB-2026-011-scan-fix-dispatch-and-direct-dependency-boundary.md`
- `KB-2026-016-scan-fix-rollback-state-restoration.md`
- `KB-2026-017-scan-fix-requires-python-resolution-boundary.md`

## Success Metrics

- Direct vulnerable dependencies can move from failing `task scan` to passing
  `task test` plus improved `task scan` in one interactive loop.
- Post-fix projects remain re-runnable with `task test` and `task scan`.
- Transitive findings remain skipped instead of becoming new direct
  dependencies.
