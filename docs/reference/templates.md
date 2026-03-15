# Templates

## python-secure

Contains:

- Python devcontainer definition
- Taskfile
- Python sample package and tests
- pinned developer tooling
- pre-commit configuration

## node-secure

Contains:

- Node/TypeScript devcontainer definition
- Taskfile
- TypeScript sample module and tests
- ESLint, Prettier, Vitest, and TypeScript configuration
- pinned `pnpm` workflow

## python-node-secure

Contains:

- Python-based devcontainer definition with official Node Feature composition
- unified Taskfile and orchestration script for Python and Node workflows
- Python sample package and tests under `backend/`
- TypeScript sample module and tests under `frontend/`
- pinned Python developer tooling, pinned `pnpm`, and pre-commit configuration

## java-secure

Contains:

- Java devcontainer definition based on the official Java devcontainer image
- Taskfile using a Gradle-first workflow
- sample Java library and JUnit tests
- Spotless formatting checks
- SpotBugs with FindSecBugs
- Trivy-based dependency vulnerability auditing

## Consumption pattern

Use the templates when you want to author or evolve the container definition in
this repository.

Use `examples/java-image-example` when you want the stable Java image
consumption path based on `ghcr.io/senanayake/polyglot-devcontainers-java:main`.
