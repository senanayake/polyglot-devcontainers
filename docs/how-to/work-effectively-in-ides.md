# Work Effectively in IDEs

The active templates are tuned to feel usable in the IDE immediately after the
container starts.

## VS Code

Each template recommends extensions and settings through its
`.devcontainer/devcontainer.json`.

Current focus areas:

- Python templates: interpreter selection, pytest discovery, Ruff and MyPy
- Node templates: ESLint, Prettier, TypeScript SDK, and Vitest
- Java template: Java extension pack, Gradle integration, and format-on-save

Open the repository or copied template folder, then use `Dev Containers: Reopen
in Container`.

## JetBrains IDEs

The repository does not maintain a separate JetBrains-specific environment
definition.

Use the same containerized workspace principles:

- keep project tooling in the container
- keep the repository task contract unchanged
- treat the container as the source of truth for build, test, and scan

## Keep the contract central

IDE settings are there to make editing smoother, but the authoritative workflow
remains:

```bash
task init
task lint
task test
task scan
task ci
```

If an IDE customization conflicts with that workflow, the task contract wins.
