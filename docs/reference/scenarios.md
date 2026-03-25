# Scenarios

This page describes the scenario layer as it exists today.

## Terms

- `scenario`: a repo-owned executable description of a concrete engineering
  situation
- `knowledge units`: small labels that identify the key ideas a scenario is
  exercising
- `scenario set`: a small group of related scenarios

## Current scenario sets

Scenario set directories:

```text
scenarios/dependency-maintenance/
scenarios/security-policy/
```

Current scenarios:

- `python-uv-lock-maintenance`
- `python-audit-policy`
- `java-gradle-maintenance`

## Root tasks

The repository currently exposes:

```bash
task scenarios:python-maintenance
task scenarios:python-audit-policy
task scenarios:java-maintenance
task scenarios:verify
```

These tasks extend the normal task workflow.

They do not replace `task ci`.

## Scenario manifest fields

Current manifests are JSON objects with fields such as:

- `name`
- `scenario_set`
- `intent`
- `language`
- `workspace`
- `runtime_guidance`
- `knowledge_units`
- `commands`
- `follow_on_commands`
- `artifacts`

Artifact entries may currently check:

- file existence
- exact JSON field values
- presence of selected JSON paths

## Scenario runner

Current runner:

```text
scripts/run_scenario.py
```

The runner:

- executes the listed commands in the target workspace
- checks the configured artifacts
- writes JSON and Markdown scenario results

## Result artifacts

Root result directory:

```text
.artifacts/scenarios/
```

Current output files:

- `python-uv-lock-maintenance.json`
- `python-uv-lock-maintenance.md`
- `python-audit-policy.json`
- `python-audit-policy.md`
- `java-gradle-maintenance.json`
- `java-gradle-maintenance.md`

## Current proving workspaces

Python audit-policy scenario workspace:

```text
examples/python-example/
```

Python scenario workspace:

```text
examples/python-maintenance-example/
```

Java scenario workspace:

```text
examples/java-maintenance-example/
```

Each workspace continues to write its own dependency and security artifacts
under `.artifacts/scans/`.

## Runtime documentation

Runtime page:

```bash
man polyglot-scenarios
```

Related pages:

- `man polyglot`
- `man polyglot-python`
- `man polyglot-java`
- `man polyglot-deps`
- `man polyglot-security`
