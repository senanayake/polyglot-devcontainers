# Run the Scenario Proving Set

Use this guide when you want to execute the current repo-owned scenarios and
inspect the results.

## Prerequisites

- work from the repository root
- use the maintainer container
- start Docker inside that container if your current session needs image-backed
  tooling

The runtime docs for this flow are:

```bash
man polyglot
man polyglot-scenarios
man polyglot-deps
man polyglot-security
```

## Run a single scenario

Python:

```bash
task scenarios:python-maintenance
```

Python audit policy:

```bash
task scenarios:python-audit-policy
```

Java:

```bash
task scenarios:java-maintenance
```

## Run the full proving set

```bash
task scenarios:verify
```

## Inspect the results

Scenario summaries are written to:

```text
.artifacts/scenarios/
```

Current result files:

- `python-uv-lock-maintenance.json`
- `python-uv-lock-maintenance.md`
- `python-audit-policy.json`
- `python-audit-policy.md`
- `java-gradle-maintenance.json`
- `java-gradle-maintenance.md`

The underlying workspace artifacts remain in the proving paths:

- `examples/python-example/.artifacts/scans/`
- `examples/python-maintenance-example/.artifacts/scans/`
- `examples/java-maintenance-example/.artifacts/scans/`

## Use the follow-on execution path

The scenarios are intentionally evidence-first.

After reading the scenario output, the next manual step is usually:

Python audit policy:

```bash
cat examples/python-example/.artifacts/scans/pip-audit-policy.md
```

Python:

```bash
cd examples/python-maintenance-example
task upgrade
task ci
```

Java:

```bash
cd examples/java-maintenance-example
task upgrade
task ci
```

## Troubleshooting

- If the scenario fails immediately, verify you are inside the maintainer
  container.
- If a scenario artifact is missing, inspect the corresponding
  `.artifacts/scans/` directory in the target workspace first.
- If a dependency plan changes shape, update the scenario manifest rather than
  bypassing the artifact check.
