# ROADMAP.md

This roadmap describes the evolution of `polyglot-devcontainers`.

The project follows Gall's Law:

> A complex system that works is invariably found to have evolved from a simple system that worked.

Phases 0 through 4 are now implemented. Phases 5 through 7 remain future work.

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

## Future Work

### Phase 5 - Polyglot Devcontainers

Planned:

- support shared development environments for common multi-language workflows
- begin with a small set of validated language combinations instead of a universal all-in-one container
- prioritize combinations with clear engineering value, starting with Python plus Node / TypeScript
- preserve the standard task contract across polyglot templates
- continue using composable Features and minimal container configuration
- use additional service containers only when needed for dependencies such as databases or message brokers

Guiding approach:

- polyglot support should expand incrementally from proven single-language templates
- the default should remain focused, maintainable environments rather than maximal images
- each polyglot template should represent a real workflow that benefits from multiple runtimes in one workspace

### Phase 6 - CI/CD and Image Distribution

Planned:

- published images
- container scanning
- registry distribution
- signing and supply-chain improvements

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
