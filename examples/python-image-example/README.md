# python-image-example

`python-image-example` is a minimal Python workspace that consumes the
published image `ghcr.io/senanayake/polyglot-devcontainers-root:main`
directly.

Use it when you want to validate the stable Python image-consumption path in VS
Code without building a local devcontainer definition first.

This example now uses `uv` and a checked-in `uv.lock` file for its Python
environment bootstrap.

After opening the example in a devcontainer, run:

```bash
task ci
```
