# Task Verb System

## Overview

The task verb system is the stable execution surface for humans and agents.

The contract stays intentionally small:

- `task init`
- `task lint`
- `task test`
- `task scan`
- `task ci`

Focused verbs may extend that contract when the environment has a proven need.

## Core Rules

1. `task test` is the full automated regression bar, not a fast subset.
2. Focused test verbs narrow or accelerate the test surface without redefining
   `task test`.
3. Check verbs stay read-only by default.
4. Fix verbs remain explicit.

## Required Verbs

| Verb | Purpose |
| --- | --- |
| `task init` | Bootstrap the environment |
| `task lint` | Run code quality and static analysis checks |
| `task test` | Run the full automated test suite supported by the environment |
| `task scan` | Run security and supply-chain checks |
| `task ci` | Run the validated workflow end-to-end |

## Recommended Optional Verbs

### Testing

| Verb | Purpose |
| --- | --- |
| `task test:fast` | Fast inner-loop feedback, typically unit plus property tests |
| `task test:unit` | Unit tests only |
| `task test:property` | Property-based tests only |
| `task test:integration` | Integration tests only |
| `task test:acceptance` | Executable specification / BDD tests only |

### Fix And Maintenance

| Verb | Purpose |
| --- | --- |
| `task format` | Auto-fix formatting and auto-fixable style issues |
| `task deps:inventory` | Write normalized dependency inventory artifacts |
| `task deps:plan` | Write normalized dependency planning artifacts |
| `task deps:report` | Summarize dependency inventory and planning evidence |
| `task upgrade` | Apply a validated dependency update workflow |

## Test Hierarchy

Polyglot separates semantic test layers from execution amplifiers.

Semantic layers:

- unit
- property
- integration
- acceptance
- full regression

Execution amplifiers:

- coverage
- parallelism
- randomized order
- mutation testing

This prevents tools like coverage or parallel execution from distorting the
meaning of the task verbs themselves.

## Examples

### Python

- `task test` -> `pytest` across all supported test roots
- `task test:unit` -> `pytest tests/unit`
- `task test:property` -> `pytest tests/property`
- `task test:acceptance` -> `pytest` over `pytest-bdd` suites

### Java

- `task test` -> Gradle over all declared test suites
- `task test:unit` -> Gradle `test`
- `task test:property` -> Gradle `propertyTest`
- `task test:acceptance` -> Gradle `acceptanceTest`

## Why This Shape

This model aligns better with KBPD and modern testing practice:

- it preserves a clear completion bar
- it gives agents a predictable zoom-in surface
- it keeps TDD fast without weakening the full regression contract
- it keeps BDD and specification-by-example visible instead of implicit
