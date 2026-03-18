# java-maintenance-example

`java-maintenance-example` is a slightly richer Gradle-first Java workspace
that consumes the published image
`ghcr.io/senanayake/polyglot-devcontainers-java:main` directly.

It exists to pressure-test the Phase 9b dependency evidence and planning flow on
something more realistic than the minimal math example while still remaining
small enough to understand quickly.

What it teaches:

- the richer Java dependency-maintenance path
- dependency inventory, plan, report, and upgrade artifacts
- the current Gradle-first evidence model

After opening the example in a devcontainer, start with:

```bash
man polyglot
man polyglot-java
man polyglot-deps
```

Then run:

```bash
task deps:inventory
task deps:plan
task deps:report
task upgrade
task ci
```

Key implemented features:

- `dependency-inventory.json`
- `dependency-plan.json`
- `dependency-report.json`
- `dependency-report.md`
- Gradle-based update planning
