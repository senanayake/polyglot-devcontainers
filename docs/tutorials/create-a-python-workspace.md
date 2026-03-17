# Create a Python Workspace

This tutorial walks through the smallest useful Python workflow in the
repository.

## Goal

Start from the repository checkout, open the root devcontainer, and run the
validated Python workflow.

## Steps

1. Open the repository in VS Code.
2. Reopen it in the devcontainer.
3. Wait for `postCreateCommand` to finish.
4. Run `task ci`.

## What happened

- `task init` used `uv sync --frozen --extra dev` to create the example
  virtual environment from the checked-in `uv.lock` file.
- `task lint` ran Ruff and MyPy.
- `task test` ran Pytest with coverage output.
- `task scan` wrote dependency and secret scan artifacts.

## Next steps

- Follow [Use uv in This Repository](./use-uv-in-this-repository.md) to learn
  the Python workflow the repository now standardizes on.
- Explore [Reference](../reference/README.md) to understand the task contract.
- Copy `templates/python-secure` when you need a starter repository.
