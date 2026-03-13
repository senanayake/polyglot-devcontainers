# polyglot-devcontainers

`polyglot-devcontainers` now delivers the roadmap through Phase 5:

- a hardened Python baseline
- reusable Python and Node/TypeScript templates
- a focused Python and Node/TypeScript polyglot template
- a composable feature library
- documentation organized using the Diataxis model

Every environment in this repository follows the same task contract:

```bash
task init
task lint
task test
task scan
task ci
```

Open the repository in the devcontainer, then run `task ci`.

GitHub Actions validates the same image definition by building
`.devcontainer/Containerfile` and running `task ci` inside that container.

Phase 6 infrastructure is prepared for publishing a small set of validated
OCI images to GHCR with Trivy scanning, Cosign signing, and provenance
attestations.

## Documentation

The documentation is organized with the Diataxis approach:

- [Tutorials](./docs/tutorials/README.md)
- [How-to guides](./docs/how-to/README.md)
- [Reference](./docs/reference/README.md)
- [Explanation](./docs/explanation/README.md)
- [Documentation home](./docs/README.md)

## Delivered Phases

- Phase 1: hardened Python tooling with Ruff formatting, MyPy, pre-commit, and scan artifacts
- Phase 2: reusable `templates/python-secure`
- Phase 3: reusable `templates/node-secure`
- Phase 4: composable features under `features/`
- Phase 5: reusable `templates/python-node-secure`

## Machine-Agnostic Contract

This repository is designed to work across Windows, macOS, and Linux by making
the devcontainer the primary execution environment.

The supported contract is:

- the host only needs a container runtime and VS Code support for devcontainers
- the project tooling lives inside the container
- `task ci` is validated inside the container, not on the host

Host-specific package installs should not be required to prove the workflow
works.

## Repository Structure

- `examples/python-example`: the validated reference implementation
- `templates/`: starter repositories built on the task contract
- `features/`: reusable devcontainer Features
- `docs/`: Diataxis documentation set

## Host Guidance

- Linux: open the repository and reopen in container
- macOS: open the repository and reopen in container
- Windows: prefer a WSL-based workflow, then reopen in container from VS Code

For Windows, the recommended flow is:

1. clone the repository inside WSL
2. open the WSL folder in VS Code
3. use `Dev Containers: Reopen in Container`
4. run `task ci` inside the container terminal

This avoids common Windows mount and image-store issues with Podman and
devcontainers.
