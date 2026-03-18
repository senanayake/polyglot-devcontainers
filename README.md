# polyglot-devcontainers

`polyglot-devcontainers` now delivers the roadmap through the initial starter
runtime-documentation slice:

- a hardened Python baseline
- reusable Python and Node/TypeScript templates
- a reusable Java template with a Gradle-first workflow
- a focused Python and Node/TypeScript polyglot template
- a composable feature library
- improved IDE-first devcontainer defaults across the active templates
- initial dependency upgrade workflows for Python and Java
- in-container runtime documentation available through `man`
- documentation organized using the Diataxis model

Every environment in this repository follows the same task contract:

```bash
task init
task lint
task test
task scan
task ci
```

Some environments also expose an optional:

```bash
task upgrade
```

when they provide a validated dependency-upgrade workflow.

Some Python and Java proving paths also expose:

```bash
task deps:report
```

to turn the existing dependency inventory and plan artifacts into a compact
JSON and Markdown report for humans and automation.

For Python environments, `uv` and `uv.lock` are now the first-class dependency
maintenance path in this repository. The maintained Python examples and
templates now ship with checked-in `uv.lock` files and bootstrap with
`uv sync --frozen`. Other Python workflow shapes are still detected so the
artifacts stay honest, but they are compatibility lanes rather than
equal-priority upgrade targets.

Open the repository in the devcontainer, then run `task ci`.

The root, Python starter, and Java starter environments also install a local
runtime help system. Start with:

```bash
man polyglot
```

Then follow the top-down guide to:

- choose the correct starter workflow
- understand the task contract
- find dependency and security artifacts
- recover agent-specific operating guidance
- read the curated "Knowledge" guidance for stronger engineering and security
  decisions

GitHub Actions validates the same image definition by building
`.devcontainer/Containerfile` and running `task ci` inside that container.

Validated OCI images are published to GHCR with Trivy scanning, Cosign signing,
and provenance attestations.

Current published images:

- `ghcr.io/senanayake/polyglot-devcontainers-root`
- `ghcr.io/senanayake/polyglot-devcontainers-java`
- `ghcr.io/senanayake/polyglot-devcontainers-python-node`

The root image is now the repository validation image, so it includes the
Python, Node, and Java toolchains needed to execute the maintained repo task
contract.

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
- Phase 6: validated and published OCI images
- Phase 7: reusable `templates/java-secure`
- Phase 8: IDE-first devcontainer customizations across active templates
- Phase 9b: dependency-upgrade proof and container-backed root CI validation
- Phase 9c: repo-owned Python paths standardized on `uv` and `uv.lock`
- Phase 9d (runtime-doc MVP): `man`-based runtime guidance installed in the root, Python, and Java starter environments

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
- `examples/python-image-example`: a Python workspace that consumes the published GHCR root image directly
- `examples/python-maintenance-example`: a richer Python proving fixture for dependency evidence and upgrade experiments
- `examples/java-image-example`: a Java workspace that consumes the published GHCR image directly
- `examples/java-maintenance-example`: a richer Java proving fixture for dependency evidence and upgrade experiments
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
