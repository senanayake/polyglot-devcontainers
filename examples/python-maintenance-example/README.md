# python-maintenance-example

`python-maintenance-example` is a slightly richer Python workspace that consumes
the published image `ghcr.io/senanayake/polyglot-devcontainers-python-node:main`
directly.

It exists to pressure-test the Phase 9b dependency evidence and planning flow on
something more realistic than the minimal math example while still remaining
small enough to understand quickly.

The repo-owned maintenance fixture now also uses `uv` and a checked-in
`uv.lock` file as its default Python workflow.

What it teaches:

- the richer Python dependency-maintenance path
- dependency inventory, plan, report, and upgrade artifacts
- how the repository uses `uv-lock` as the first-class Python strategy

After opening the example in a devcontainer, start with:

```bash
man polyglot
man polyglot-python
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
- upgrade planning aligned with `uv lock --upgrade`
