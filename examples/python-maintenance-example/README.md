# python-maintenance-example

`python-maintenance-example` is a slightly richer Python workspace that consumes
the published image `ghcr.io/senanayake/polyglot-devcontainers-root:main`
directly.

It exists to pressure-test the Phase 9b dependency evidence and planning flow on
something more realistic than the minimal math example while still remaining
small enough to understand quickly.

The repo-owned maintenance fixture now also uses `uv` and a checked-in
`uv.lock` file as its default Python workflow.

After opening the example in a devcontainer, run:

```bash
task deps:inventory
task deps:plan
task upgrade
task ci
```
