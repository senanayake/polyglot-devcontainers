---
id: KB-2026-028
type: standard
status: validated
created: 2026-04-24
updated: 2026-04-24
tags: [kbpd, standard, testing, pytest, integration, templates, security, remediation]
related: [KB-2026-015, KB-2026-026, KB-2026-027]
---

# Fast Default and Opt-In Integration Test Lanes for Python Starters

## Context

Polyglot Python starters previously exposed a single `task test` path. That
worked for trivial examples, but it did not distinguish between fast local
checks and slower or externally coupled integration coverage.

## Problem/Need

The repository needed a standard test contract that:
- keeps `task test` fast enough for local iteration and CI defaults
- gives starters a first-class place for integration tests
- does not weaken meaningful starter coverage that already runs locally
- keeps security remediation workflows aligned with the default verification
  lane

## Standard/Pattern

### Description

For Polyglot Python starters:
- `task test` runs `pytest -m "not integration"`
- `task test:integration` runs `pytest -m integration`
- `task test:all` runs the full suite
- `pytest` markers declare the `integration` marker in `pyproject.toml`
- starter scaffolds include `tests/unit/`, `tests/integration/`, and
  `tests/conftest.py`
- meaningful local tests stay in the fast default lane instead of being
  replaced with placeholders
- remediation verification helpers use the fast lane, not the full suite

### Key Principles

- Fast feedback is the default contract.
- Integration coverage is explicit and opt-in.
- Security automation must verify against the same default lane users and CI run
  by default.

### Implementation

```bash
task test
task test:integration
task test:all
```

And in Python task runners:

```python
run([str(PYTHON), "-m", "pytest", "-q", "-s", "-m", "not integration"])
run([str(PYTHON), "-m", "pytest", "-q", "-s", "-m", "integration"])
run([str(PYTHON), "-m", "pytest", "-q", "-s"])
```

## Rationale

This approach is preferred because:
- it preserves the repo task contract while creating a clearer proving ladder
- it prevents future live integrations from silently slowing or destabilizing
  the default `task test` path
- it keeps automated remediation flows from accidentally depending on external
  systems just because markers were introduced

## Benefits

- Faster default feedback in local development and CI
- Cleaner separation between starter smoke coverage and live integrations
- Lower risk that `scan:auto` or similar workflows become flaky after new
  integration tests are added

## Constraints

- Starters must actually include at least one integration-marked example so the
  lane is visible and testable.
- Mixed-language starters may need template-specific adaptations; for example,
  Python integration markers do not automatically classify frontend test suites.

## Alternatives Considered

### Single Undifferentiated Test Lane

- Simpler on paper
- Rejected because it couples default verification to the slowest or most
  externally dependent tests

### Move All Existing Tests into Integration

- Would satisfy the new directory shape mechanically
- Rejected because it weakens the default starter proving path and hides real
  regressions from the fast lane

## Evidence

- `templates/python-api-secure/tests/test_api.py` already provided meaningful,
  local API coverage and belonged in the fast suite.
- Python remediation flows in `tasks.py` already rely on pytest-based
  verification, so marker adoption affects security automation as well as human
  workflows.
- `KB-2026-015` and `KB-2026-026` both reinforce that automated remediation is
  only credible when the verification path stays fast and stable.

## Anti-Patterns

- Introducing integration markers but leaving remediation helpers on raw
  unfiltered `pytest`
- Replacing meaningful starter tests with placeholder examples only
- Treating mixed-language starters as if every test framework shares the same
  marker model

## Verification

- `task test` excludes integration tests
- `task test:integration` runs only integration-marked Python tests
- `task test:all` runs the full suite
- repository `task ci` still uses the fast lane by default

## Applicability

### Use This Standard When

- a Python starter needs both fast checks and slower live integrations
- remediation or upgrade automation depends on the default verification lane
- the repository wants consistent task verbs across starters

### Don't Use This Standard When

- the environment has no meaningful distinction between local and integration
  tests
- the test runner does not support marker-based filtering without additional
  infrastructure
