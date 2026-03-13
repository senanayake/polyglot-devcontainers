# Create a Polyglot Workspace

This tutorial walks through the smallest supported polyglot setup in the
repository: Python plus Node / TypeScript.

## 1. Copy the template

Copy `templates/python-node-secure` into a new repository.

## 2. Reopen in a devcontainer

Open the repository in VS Code and reopen it in the devcontainer.

## 3. Bootstrap the environment

Run:

```bash
task init
```

This creates the Python virtual environment and installs Node dependencies with
`pnpm`.

## 4. Validate the workflow

Run:

```bash
task ci
```

This executes the standard lint, test, and scan workflow across both language
toolchains.
