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

## research-runner

Contains:

- devcontainer definition for the published research runner image
- Taskfile smoke checks for Python, Node.js, the pre-built research venv, and
  runtime documentation
- baseline guidance for LLM-assisted research artifacts

## solver-runner

Contains:

- devcontainer definition for the published solver runner image
- Taskfile smoke checks for Alloy/Kodkod, Z3, cvc5, SQLite, Postgres client
  tooling, Python, Node.js, and runtime documentation
- a small Alloy model and SMT-LIB probes for deterministic formal-tool receipts

## latex

Contains:

- devcontainer definition for the published LaTeX image
- Taskfile commands for `init`, `build`, `lint`, `test`, `scan`, and `ci`
- a minimal IEEE-style paper that verifies BibTeX, TikZ, tables, and PDF
  validation

## Consumption pattern

Use the templates when you want to author or evolve the container definition in
this repository.

Use `examples/java-image-example` when you want the stable Java image
consumption path based on `ghcr.io/senanayake/polyglot-devcontainers-java:main`.
