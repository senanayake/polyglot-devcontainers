# KB-2026-043: Security Remediation Demo — Integration Testing Gap and pip-audit Isolation Design

**Type:** Failure Analysis  
**Date:** 2026-05-12  
**Status:** Decision reached, implementing

---

## Problem Statement

The `security-remediation-demo` Python fixture crashed three times during container validation:

1. `cyclonedx.parser` ModuleNotFoundError — pip-audit version in venv had cyclonedx API mismatch
2. `requirements are unsatisfiable` — pip-audit requires `requests>=2.31.0` but fixture pins `requests==2.28.0`
3. `cyclonedx-python-lib>=5,<9` conflict — manually-added `--with` constraint was the wrong range

Each fix was deployed to the container without local validation. This is the root quality failure: **changes were not tested before asking the user to run them**.

---

## Gap 1: Wrong pip-audit invocation strategy

### What happened
After correctly isolating pip-audit into a `uv tool run` environment (fixing gap 2), the scan was invoked via:

```
uv tool run --from pip-audit==2.8.0 pip-audit --requirement frozen-requirements.txt
```

**The freeze file contains the project's own editable install entry:**
```
health-monitor @ file:///path/to/examples/security-remediation-demo
```

pip-audit with `--requirement` cannot audit local file-path entries. It either fails or silently skips them. Additionally, `uv pip freeze` emits editable install entries in a format that differs between uv versions, making any filter brittle.

### Decision
Use `pip-audit --path .venv` instead of `--requirement frozen-requirements.txt`.

`pip-audit --path /path/to/venv` reads installed packages directly from the venv's site-packages dist-info directories. This:
- Handles editable installs correctly (skips local packages)
- Audits all installed packages including transitives
- Requires no intermediate freeze file
- Is idiomatic — it is the documented way to audit a venv when pip-audit is not installed into it

```python
completed = run(
    [UV, "tool", "run", "--from", "pip-audit==2.8.0",
     "pip-audit", "--path", str(VENV_DIR),
     "--format", "json", "--output", str(audit_report)],
    check=False,
)
```

---

## Gap 2: No integration test harness

### What happened
Every code change was validated by:
1. Committing/copying to a devcontainer
2. Asking the user to run `task demo` or `task scan` manually
3. Waiting for crash output
4. Iterating

There was no automated path that could be run locally or in CI to verify that:
- `task scan` fails before upgrade (as designed)
- `task upgrade` actually rewrites the pins
- `task scan` passes after upgrade

### Decision
Create `scripts/test_security_remediation_demo.py` — an integration test harness that:

1. Saves pyproject.toml original content
2. Clears `.venv` and `.artifacts` for a clean run
3. Runs `python tasks.py init`
4. Runs `python tasks.py scan` — asserts `violations > 0`
5. Runs `python tasks.py upgrade` + `uv pip install` re-sync
6. Runs `python tasks.py scan` — asserts `violations == 0`
7. Validates all expected artifacts exist and have the right JSON shape
8. Always restores pyproject.toml to the vulnerable state on exit

Wire this as `task test:integration` in the fixture Taskfile.

---

## Gap 3: Demo is not idempotent

### What happened
`upgrade()` permanently rewrites pyproject.toml. Running `task demo` a second time starts in the post-upgrade state, so the "before" scan passes instead of failing. This breaks the demo story.

### Decision
The test harness saves and restores pyproject.toml unconditionally (in a `finally` block). The `demo:capture-before` task is designed to run on fresh checkout; the test harness makes it safe to run repeatedly.

---

## Lessons

- **Test before deploying.** Every shell command that touches uv or pip-audit must be validated in the target environment before asking the user to run it. When the target is a devcontainer and local execution is not possible, the test harness must capture the expected behaviour so that a single container run validates everything.
- **Favour `--path` over freeze files.** Freezing a venv to a text file and then passing that file to a tool introduces an intermediate layer with its own parsing hazards (editable entries, URL dependencies, VCS references). When a tool supports scanning a venv directly, prefer that.
- **Design for idempotency from the start.** Any demo that modifies source files (pyproject.toml, gradle.properties, etc.) must restore them. The test harness encodes that contract.
