# python-image-example

`python-image-example` is a minimal Python workspace that consumes the
published image `ghcr.io/senanayake/polyglot-devcontainers-python-node:main`
directly.

Use it when you want to validate the stable Python image-consumption path in VS
Code without building a local devcontainer definition first.

This example now uses `uv` and a checked-in `uv.lock` file for its Python
environment bootstrap.

What it teaches:

- consuming the published Python and Node image directly in VS Code
- the standard Python task contract
- `uv` and `uv.lock` as the default Python workflow
- runtime guidance through `man`
- security artifacts under `.artifacts/scans/`

After opening the example in a devcontainer, start with:

```bash
man polyglot
man polyglot-python
```

Then run:

```bash
task ci
```

Key implemented features:

- `task init|lint|test|scan|ci`
- `uv sync --frozen --extra dev`
- `ruff`, `mypy`, and `pytest`
- `pip-audit` and `gitleaks`
- in-container runtime docs
