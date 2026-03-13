# ROADMAP.md

This roadmap describes the evolution of `polyglot-devcontainers`.

The project follows Gall's Law:

> A complex system that works is invariably found to have evolved from a simple system that worked.

Phases 0 through 5 are now implemented. Phases 6 and 7 remain future work.

## Implemented

### Phase 0 - Seed System

Delivered:

- a Python devcontainer
- the standard `task` workflow
- integrated dependency and secret scanning
- a validated Python example project
- a CI workflow that runs `task ci` in the repository container

### Phase 1 - Harden the Python Environment

Delivered:

- Ruff lint and format checks
- MyPy type checking
- pre-commit hooks
- pinned Python developer tooling
- scan artifacts for `pip-audit` and `gitleaks`
- improved devcontainer defaults for Python editing

### Phase 2 - Introduce Devcontainer Templates

Delivered:

- `templates/python-secure`

This template includes the standard task contract, a Python sample project, and
local feature composition.

### Phase 3 - Introduce Node / TypeScript Support

Delivered:

- `templates/node-secure`

This template provides a minimal TypeScript starter with `pnpm`, ESLint,
Prettier, Vitest, and the standard task contract.

### Phase 4 - Feature Library

Delivered:

- `features/security-baseline`
- `features/python-engineering`
- `features/node-engineering`
- `features/agent-runtime`

These features are intentionally modular and composable.

### Phase 5 - Polyglot Devcontainers

Delivered:

- `templates/python-node-secure`

This template validates a focused Python plus Node / TypeScript workflow in one
container while preserving the standard task contract and feature composition.

## Future Work

### Phase 6 - CI/CD and Image Distribution

Planned:

- build validated OCI images for the repository root environment and selected templates
- publish public images to a free OCI registry using open standards
- run `task ci` inside the built container before publication
- add container image scanning as part of the standard release workflow
- sign published images and attach provenance attestations
- document supported tags, retention rules, and verification steps

Initial delivery target:

- publish the root repository image
- publish the Python plus Node / TypeScript polyglot image
- use GitHub Actions for CI and GHCR for public image hosting
- preserve the existing task contract as the single validation interface

Guiding approach:

- start with a small number of published images rather than every template
- keep CI behavior aligned with the local container-first workflow
- use free and open tooling for build, scan, signing, and verification
- prefer standard OCI-compatible outputs so registry choices can evolve later

### Phase 7 - Agent-Optimized Environments

Planned:

- richer structured outputs for scans
- more agent-focused helper tooling
- further startup and determinism improvements

## Non-goals

The repository still avoids:

- enterprise-specific assumptions
- large custom platform layers
- proprietary integrations
- support for every language at once
- a single universal container with every supported language and tool installed by default
- polyglot templates without a validated workflow need
- large custom Dockerfiles that replace feature composition
- combining unrelated runtimes in ways that increase maintenance burden without improving the development workflow
- publishing every template image before there is a clear maintenance and support model
- release pipelines that bypass `task ci`
- registry-specific build logic that makes migration difficult
- paid-only infrastructure requirements for the default open-source workflow
