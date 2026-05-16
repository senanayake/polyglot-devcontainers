# Scaffold A Feature

Use the repository scaffold when you want to add a new OCI devcontainer feature
without rebuilding the layout from memory.

## Command

```bash
task init:feature -- pandoc
```

Example:

```bash
task init:feature -- diagram-rendering
```

Use a stable feature id or working title as the input. A slug is the simplest
task-shell input, and the scaffold also accepts quoted working titles when you
need them. It always turns the input into a repository-safe slug for the
generated directory.

## What It Creates

The scaffold writes a new `features/<id>/` directory with:

- `devcontainer-feature.json`
- `install.sh`
- `README.md`
- `specs/requirements.md`
- `specs/acceptance.feature`
- `specs/traceability.md`
- `test/test.sh`
- `test/scenarios.json`

## Why The Extra Files Exist

The scaffold is intentionally test-first and traceability-aware.

- requirements capture the contract
- the Gherkin file captures externally visible behavior in a form that humans
  and agents can read quickly
- traceability maps requirements to automated checks
- `test/test.sh` is the executable proving entry point for feature behavior

## Typical Follow-Up

1. Replace the placeholder install logic in `install.sh`.
2. Fill in the real feature metadata and options.
3. Tighten the requirements and acceptance examples.
4. Update `test/test.sh` so the checks prove the documented behavior.
5. Record the architectural choice with `task init:adr -- decision-slug` when the
   feature introduces a durable design decision.
