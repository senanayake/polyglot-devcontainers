# java-maintenance-example

`java-maintenance-example` is a slightly richer Gradle-first Java workspace
that consumes the published image
`ghcr.io/senanayake/polyglot-devcontainers-java:main` directly.

It exists to pressure-test the Phase 9b dependency evidence and planning flow on
something more realistic than the minimal math example while still remaining
small enough to understand quickly.

After opening the example in a devcontainer, run:

```bash
task deps:inventory
task deps:plan
task upgrade
task ci
```
