# Run the First Scenarios

This tutorial walks through the first executable scenarios in the repository.

## Goal

Run the Python and Java dependency-maintenance scenarios from the repository
root and inspect the resulting artifacts.

## Before you begin

Use the maintainer container for this flow.

Inside the container, start with:

```bash
man polyglot
man polyglot-scenarios
```

## Steps

1. From the repository root, run:

   ```bash
   task scenarios:python-maintenance
   ```

2. Read the generated scenario summary:

   ```bash
   cat .artifacts/scenarios/python-uv-lock-maintenance.md
   ```

3. Inspect the underlying Python maintenance artifacts:

   ```bash
   cat examples/python-maintenance-example/.artifacts/scans/dependency-report.md
   ```

4. Run the Java scenario:

   ```bash
   task scenarios:java-maintenance
   ```

5. Read the generated Java summary:

   ```bash
   cat .artifacts/scenarios/java-gradle-maintenance.md
   ```

6. Inspect the underlying Java maintenance artifacts:

   ```bash
   cat examples/java-maintenance-example/.artifacts/scans/dependency-report.md
   ```

7. Run the combined proving set:

   ```bash
   task scenarios:verify
   ```

## What happened

- the Python scenario ran the existing `uv-lock` maintenance path in
  `examples/python-maintenance-example`
- the Java scenario ran the existing Gradle-first maintenance path in
  `examples/java-maintenance-example`
- both scenarios stayed inside the existing task contract
- both scenarios checked for the expected evidence and planning artifacts
- both scenarios wrote a compact result into `.artifacts/scenarios/`

## Next steps

- Use [Run the Scenario Proving Set](../how-to/run-the-scenario-proving-set.md)
  when you want the operational version of this flow.
- Read [Executable Scenarios](../explanation/executable-scenarios.md) when you
  want the rationale.
- Read [Scenarios](../reference/scenarios.md) for the current file layout,
  tasks, and manifest fields.
