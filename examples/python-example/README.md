# python-example

This example is the minimal Phase 0 Python project used to validate the shared
task workflow.

It now uses `uv` and a checked-in `uv.lock` file as the Python dependency
source of truth for the repository-owned path.

Use it when you want the smallest repository-owned Python example that still
shows the standard task contract.

After opening the repository root devcontainer, start with:

```bash
man polyglot
man polyglot-python
task ci
```
