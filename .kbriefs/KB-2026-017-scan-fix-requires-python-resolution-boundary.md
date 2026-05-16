---
id: KB-2026-017
type: limit
status: validated
created: 2026-04-07
updated: 2026-04-07
tags: [scan-fix, python, uv, requires-python, limit, kbpd]
related: [KB-2026-014, KB-2026-015, KB-2026-016]
---

# scan:fix requires-python Resolution Boundary

## Context

Even in a Polyglot-standard project, `scan:fix` depends on `uv add` being able
to resolve the updated dependency graph across the repository's declared
`requires-python` range. We needed to know whether that boundary still exists
in the standard template shape.

## Question

Can `scan:fix` remediate a direct vulnerability when the project's declared
`requires-python` range is broader than what the dependency graph actually
supports?

## Experiment

Controlled variant:
- copied the `python-secure` template into a dedicated variant
- changed `requires-python` from `>=3.12` to `>=3.8.1`
- added direct dev vulnerability `pygments==2.19.1`
- ran `uv lock`, `task init`, `printf 'y\n' | task scan:fix`, and `task scan`
  inside the maintainer container

## Findings

### The Limit

`scan:fix` cannot cross a project-level Python support inconsistency. When the
declared `requires-python` range includes interpreters unsupported by the
dependency graph, `uv add` fails before the fix can be applied.

### Behavior Before Limit

Within a satisfiable `requires-python` range, direct runtime and dev fixes work
end-to-end; see `KB-2026-015`.

### Behavior At/Beyond Limit

Once the project claims unsupported Python versions:
- `uv lock` fails for the broader range
- `task init` may still work from an existing lock on the active interpreter
- `scan:fix` proposes the direct dependency upgrade, but `uv add` fails and the
  candidate must be rolled back

## Evidence

- the validation run recorded the
  `uv add --optional dev pygments==2.20.0` failure
- the resolver error explicitly cited `mypy==1.17.1` requiring `Python>=3.9`
  while the project declared `>=3.8.1`
- post-failure `task scan` still ran successfully, showing rollback preserved a
  usable project state
- the manifest remained unchanged at `pygments==2.19.1`

## Implications

- `scan:fix` is not a substitute for correcting an invalid `requires-python`
  declaration
- a Polyglot-standard repo must stay internally consistent across its claimed
  Python support range if automated remediation is expected to work
- this remains a product boundary even after the direct-remediation loop is
  validated

## Recommendations

### Within Limit

- keep `requires-python` aligned with the actual dependency graph
- validate lock resolution whenever the supported Python range changes

### Approaching Limit

- treat `uv lock` failures as a project correctness bug, not a scan-fix bug
- narrow `requires-python` before expecting automated upgrades to succeed

### Beyond Limit

- fix the project support range first
- then re-run `task init`, `task scan`, and `task scan:fix`

## Applicability

- Applies to: Polyglot Python templates using `uv` and a declared
  `requires-python` range
- Does not apply to: projects whose declared Python range is already
  satisfiable for their dependency graph

## Related Knowledge

- `KB-2026-014-scan-fix-cross-python-resolution-boundary.md`
- `KB-2026-015-scan-fix-standard-python-remediation-loop.md`
- `KB-2026-016-scan-fix-rollback-state-restoration.md`
