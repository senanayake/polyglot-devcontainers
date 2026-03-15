# ROADMAP.md

This roadmap describes the evolution of `polyglot-devcontainers` and the
broader Polyglot ideas it may evaluate over time.

This repository hosts the substrate first:

- devcontainer environments
- reusable features and templates
- published OCI images
- the repository task contract

It may evaluate broader Polyglot interface ideas later, but the repository does
not currently commit to a separate CLI or parallel workflow contract.

The project follows Gall's Law:

> A complex system that works is invariably found to have evolved from a simple
> system that worked.

The system evolves in layers:

Devcontainer environments
-> engineering capability layer
-> automation and modernization

Early phases focus on practical developer environments that work locally in
IDEs and in CI.

Later phases introduce broader workflow standardization, security automation,
and agent-compatible interfaces.

---

# Guiding Axioms

The project is guided by several assumptions about the future of software
engineering.

### Portable development environments

Development environments will increasingly be defined as portable
infrastructure artifacts rather than manually configured machines.

Devcontainers allow environments to be defined declaratively and reproduced
across machines and CI systems.

### Deterministic environments enable automation

Automation systems, CI pipelines, and development tooling require deterministic
environments.

Containerized development environments provide consistency across developers and
automation systems.

### Security remediation will become increasingly automated

Dependency vulnerabilities and insecure code patterns will increasingly be
addressed through automated detection, safe upgrades, and targeted
modernization.

### Software systems remain polyglot

Real-world systems combine multiple languages and ecosystems.

Development environments must support this reality.

### Developer tools must remain simple

Developer platforms succeed when their surface area remains simple and proven by
use:

- `task init`
- `task lint`
- `task test`
- `task scan`
- `task ci`

### Learn through small working systems

The repository should use a small number of working environments to test the
larger ideas before broadening the platform.

---

# Core Architectural Concepts

Polyglot distinguishes between:

`intent -> capability -> tool adapter`

Example:

`dependency_vulnerability_audit`
-> Python: `pip-audit`
-> Node: `pnpm audit` or `npm audit`
-> Java: `OWASP Dependency-Check`

This prevents the architecture from being tightly coupled to specific tools.

The current repository contract remains the source of truth for local and CI
validation:

- `task init`
- `task lint`
- `task test`
- `task scan`
- `task ci`

Any future higher-level interface should only be introduced if it removes
concrete friction that the task contract does not already solve.

---

# Capability Model

The platform defines portable engineering capabilities.

Tools implement these capabilities within specific ecosystems.

| Capability | Description |
|---|---|
| build | compile or package the system |
| test | run automated tests |
| lint | enforce code quality |
| format | enforce code formatting |
| type_analysis | semantic correctness checks |
| dependency_vulnerability_audit | detect vulnerable dependencies (CVEs) |
| static_security_analysis | detect insecure coding patterns (CWEs) |
| secret_scan | detect embedded secrets |
| dependency_upgrade | update dependencies safely |
| code_modernization | refactor code for new APIs or safer patterns |
| sbom_generation | produce a software bill of materials |

---

# Target Capability Mappings

These are target capability mappings for the first three ecosystems the project
wants to exercise. They are not a claim that every adapter below is already
implemented in this repository.

| Capability | Python | Node / TypeScript | Java |
|---|---|---|---|
| build | packaging tools | `tsc` / bundlers | Maven / Gradle |
| test | `pytest` | Vitest / Jest | Maven Surefire / Gradle test |
| lint | Ruff | ESLint | Checkstyle |
| format | Ruff / Black | Prettier | Spotless |
| type_analysis | MyPy / Pyright | TypeScript compiler | compiler checks / Error Prone class tools later |
| dependency_vulnerability_audit | `pip-audit` | `pnpm audit` / `npm audit` | OWASP Dependency-Check |
| static_security_analysis | Bandit / Semgrep | Semgrep / eslint security rules | SpotBugs / Semgrep |
| secret_scan | `gitleaks` | `gitleaks` | `gitleaks` |
| dependency_upgrade | `pip` / `uv` / Poetry workflows | `npm` / `pnpm` update workflows | Maven Versions Plugin / Gradle versions tooling |
| code_modernization | codemods where available | codemods | OpenRewrite |
| sbom_generation | CycloneDX | CycloneDX | CycloneDX |

---

# Implemented Phases

## Phase 0 - Seed System

Delivered:

- Python devcontainer
- standard `task` workflow
- dependency vulnerability auditing
- secret scanning
- example Python project
- CI workflow running `task ci`

Outcome:

Minimal secure Python development environment.

## Phase 1 - Harden Python Environment

Delivered:

- Ruff lint and format
- MyPy type checking
- pre-commit hooks
- pinned developer tooling
- improved IDE defaults

Outcome:

High-quality Python engineering baseline.

## Phase 2 - Devcontainer Templates

Delivered:

- `templates/python-secure`

Outcome:

Reusable secure Python project template.

## Phase 3 - Node / TypeScript Support

Delivered:

- `templates/node-secure`

Includes:

- pnpm
- ESLint
- Prettier
- Vitest
- standard task lifecycle

Outcome:

Validated TypeScript development environment.

## Phase 4 - Feature Library

Delivered:

- `features/security-baseline`
- `features/python-engineering`
- `features/node-engineering`
- `features/agent-runtime`

Features remain:

- modular
- composable
- minimal

Outcome:

Composable engineering capability modules.

## Phase 5 - Polyglot Devcontainers

Delivered:

- `templates/python-node-secure`

Outcome:

Validated polyglot development workflow.

## Phase 6 - CI/CD and Image Distribution

Delivered:

- image validation pipelines
- OCI image publication
- Trivy scanning
- Cosign signing
- provenance attestations

Published images:

- `ghcr.io/senanayake/polyglot-devcontainers-root`
- `ghcr.io/senanayake/polyglot-devcontainers-python-node`

Outcome:

Secure development environment artifacts.

## Phase 7 - Java Engineering Environment

Delivered:

- `templates/java-secure`
- `features/java-engineering`
- a Gradle-first Java path
- Java dependency vulnerability auditing and static security analysis inside the
  standard task contract

Outcome:

A practical Java environment now exercises the next set of polyglot ideas
inside this repository.

## Phase 8 - IDE-First Experience

Delivered:

- improved VS Code devcontainer customizations for Python, Node, Java, and the
  repository root workspace
- stronger test discovery and formatter defaults in active templates
- Java and IDE usage documentation additions in the existing Diataxis structure

Outcome:

The active templates are more usable as daily-driver environments in the IDE
without changing the task contract.

---

# Future Work

## Phase 9 - Dependency Detection and Safe Upgrades

Delivered initial slice:

- Python dependency upgrade tasks for `templates/python-secure` and
  `examples/python-image-example`
- Java dependency upgrade tasks for `templates/java-secure` and
  `examples/java-image-example`
- upgrade artifacts written into `.artifacts/scans/`

Objective:

Automate dependency-oriented detection and safe upgrade workflows before taking
on broader CWE remediation.

Capabilities:

- dependency vulnerability auditing
- secret scanning
- safe dependency upgrade workflows

Automation flow:

`scan -> identify -> upgrade -> test -> propose changes`

Scope:

- dependency vulnerability auditing
- dependency upgrade workflows
- repository verification after upgrades
- implementation should extend the existing task-based workflow rather than
  introduce a new required command layer

Non-scope for this phase:

- automated source-code rewriting for CWE remediation

Outcome:

Repositories gain safer automated dependency maintenance with a constrained,
testable scope.

## Phase 10 - Static Security Analysis and CWE Remediation

Objective:

Add code-oriented security analysis and targeted remediation workflows after
dependency upgrade automation is working well.

Capabilities:

- static security analysis
- targeted code modernization workflows

Examples:

- Semgrep-based detection
- Java modernization via OpenRewrite
- targeted codemods for safer APIs and framework migrations

Outcome:

The project expands from dependency hygiene into code-level remediation and
modernization.

## Phase 11 - Expand Diataxis Coverage

Objective:

Expand existing Diataxis documentation coverage for the broader Polyglot ideas
now being incubated here.

Priority areas:

- capability model
- Java environment setup and operation
- dependency detection and safe upgrade workflows
- CWE remediation and modernization workflows

Documentation forms:

- tutorials
- how-to guides
- explanations
- reference material

Outcome:

The repository documentation keeps pace with the evolving substrate and remains
usable for both contributors and consumers.

## Phase 12 - Agent-Compatible Environments

Objective:

Add structured metadata for automation tools and coding agents.

Examples:

- `.devcontainer/agent.json`
- contract-aware command discovery
- more structured scan outputs

Outcome:

Deterministic environments become easier to use from non-human tooling without
changing the core task contract.

## Phase 13 - Environment Catalog and Release Channels

Objective:

Clarify consumption modes and release channels for stable reuse.

The project should support both:

- templates and features for authoring and experimentation
- published images for stable consumption

Potential catalog targets:

- `polyglot/python`
- `polyglot/node`
- `polyglot/java`
- `polyglot/python-node`
- later combinations justified by validated workflows

Near-term implementation should evolve from the existing GHCR-published images
and release workflow rather than introducing a wholly separate distribution
model.

Potential release channels:

- stable
- candidate
- nightly

Outcome:

The repository can serve both environment authors and downstream consumers with
clearer freshness and stability expectations.

## Phase 14 - Upgrade Recipes

Objective:

Introduce reusable modernization recipes once the capability and contract layers
have proven useful.

Examples:

- Python runtime upgrades
- Node ecosystem migrations
- Java framework upgrades

Inspired by:

- OpenRewrite
- codemod frameworks

Outcome:

Automated codebase modernization becomes more repeatable and portable.

## Potential Future Idea - Polyglot Interface Layer

The repository may later evaluate a higher-level Polyglot interface such as a
CLI or machine-readable contract if real usage shows that the existing task
contract is not enough.

That idea should only move forward if it clearly removes concrete friction such
as:

- cross-repository environment startup
- cross-ecosystem capability resolution
- agent-oriented command discovery beyond task names alone
- external tooling that cannot cleanly integrate with the current task contract

Until that need is proven, `task` remains the primary contract and the simpler
working system.

---

# Non-goals

The repository intentionally avoids:

- enterprise-specific assumptions
- proprietary integrations
- large platform frameworks before the substrate is proven
- supporting every language at once
- universal containers containing every runtime
- complex orchestration systems
- platform lock-in
- release pipelines that bypass `task ci`
- broad abstractions that replace concrete working environments too early

---

# Long-Term Vision

`polyglot-devcontainers` aims to provide portable, secure, and automated
development environments that work consistently across local machines, CI
systems, and automated tooling.

If the broader Polyglot interface and contract ideas prove useful, they can
be evaluated here later, but they are not part of the committed near-term
execution plan.
