# Create a Node Workspace

This tutorial introduces the Node/TypeScript template added in Phase 3.

## Goal

Start a new Node workspace from `templates/node-secure` and run the standard
task workflow.

## Steps

1. Copy `templates/node-secure` into a new repository or working directory.
2. Open that directory in a devcontainer-compatible editor.
3. Reopen the directory in the container.
4. Run `task ci`.

## What happened

- `task init` installed pinned `pnpm` dependencies.
- `task lint` ran ESLint, Prettier, and the TypeScript compiler.
- `task test` ran Vitest.
- `task scan` produced `pnpm audit` JSON and a Gitleaks SARIF report.

## Next steps

- Read [Use the Node and Python templates](../how-to/use-the-templates.md).
- Read [Templates](../reference/templates.md) for the exact contents of each
  starter.
