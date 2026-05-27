---
title: polyglot-solver-runner
section: 7
header: Polyglot Devcontainers
footer: Runtime Documentation
---

# NAME

polyglot-solver-runner - solver execution image for data-modeling correctness experiments

# PURPOSE

This page explains the supported workflow for the solver runner image.

# WHEN TO USE

Use this image when a project needs deterministic formal-methods tooling next
to Python and Node.js harnesses. It is intended for data-modeling correctness
experiments, model translation checks, solver receipts, and database-modeling
fixtures.

# PRIMARY COMMANDS

```bash
task init
task test
task test:alloy
task test:smt
task ci
```

# WORKFLOW

The image extends the Python-Node image and adds:

- Java runtime for Alloy and JVM-based solver integrations
- Alloy 6.2.0 with the upstream distribution jar installed at `/opt/alloy`
- an `alloy` command wrapper that executes the pinned jar
- Z3 and cvc5 for SMT-LIB checks
- MiniSat for direct CNF/SAT experiments
- SQLite and Postgres client tooling for schema and data-modeling probes

The image is not a Sententia-specific solver service. It is a reusable execution
surface for projects that need to run formal checks and keep receipts.

# OUTPUTS / ARTIFACTS

Solver projects should write generated models, solver outputs, receipts, and
reports under project-owned paths such as:

- `.artifacts/`
- `results/`
- `runs/`
- `receipts/`

Do not commit transient solver output unless it is intentionally part of a
review artifact.

# COMMON FAILURES

- Treating the image as a complete domain translator. Projects must still own
  their mappings from domain semantics into Alloy, SMT-LIB, SQL, or another
  formal representation.
- Comparing solver outputs without recording solver name, version, scope, and
  command-line options.
- Depending on one solver result without an independent small smoke check for
  the modeling language or theory fragment being exercised.

# GUIDANCE

- Keep project-specific theories, translators, and fixtures in the consuming
  repository.
- Use `task ci` for deterministic no-network checks.
- Preserve executable receipts whenever a result informs a product decision.
- Prefer small solver probes that isolate one semantic claim at a time.
- Escalate ambiguous or under-specified model semantics to review instead of
  hiding them in image-level defaults.

# SEE ALSO

- `polyglot(7)`
- `polyglot-python(7)`
- `polyglot-task-contract(7)`
- `polyglot-security(7)`
