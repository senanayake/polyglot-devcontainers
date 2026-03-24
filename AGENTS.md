# AGENTS.md

This file defines the **operating rules for AI coding agents** working in this repository.

Agents must read and follow this file before making changes.

The goal of this repository is to build **polyglot devcontainers that enable secure, reproducible, high-performance software engineering workflows** for both humans and AI coding agents.

---

# 1. Project Purpose

`polyglot-devcontainers` provides:

- reusable development container configurations
- DevSecOps-ready engineering environments
- reproducible development tooling
- security-first workflows
- environments usable by both IDE users and AI agents

The repository prioritizes:

- reproducibility
- simplicity
- security
- composability
- minimal maintenance burden

---

# 2. Architectural Principles

## Follow Gall's Law

Start with the **simplest working system** and evolve.

Do not design a complex system from scratch.

Complex systems must grow from simple working ones.

Initial scope should remain small and practical.

---

## Prefer Composition Over Reinvention

When adding capabilities:

1. Prefer **existing Dev Container Features**
2. Prefer **existing devcontainer templates**
3. Only implement **custom Features** when necessary

Do not re-implement common installation logic.

Investigate:

https://github.com/devcontainers/features

before writing custom tooling.

---

## Security Is Job 0

Security must be integrated into the default development workflow.

Security checks must not be optional.

Security tasks must run as part of the standard workflow.

Required security categories include:

- dependency vulnerability scanning
- secret scanning
- container scanning where appropriate
- secure defaults

---

## Devcontainers Define the Environment

The development container must contain:

- the task runner
- language runtime
- security tools
- linting tools
- test tools

Host machines should require **minimal setup**.

When container tooling is available, agents must prefer a **container-first
workflow** for implementation and validation.

Do not rely on host-installed language runtimes or host package state to prove
the task contract works.

Use the base container environment first, then validate:

```bash
task init
task lint
task test
task scan
task ci
```

inside the container.

The repository must remain **machine agnostic** across Windows, macOS, and
Linux by treating the Linux container as the source of truth.

Agents must prefer:

- container-local tooling over host tooling
- project-local state over host-global state
- portable paths and commands over host-specific shell assumptions

For this repository, agent execution must use the maintainer container as the
source of truth.

Hard constraint:

- agents must run repository maintenance, validation, image-refresh, security,
  and release-preparation workflows inside the maintainer container
- agents must not treat host execution as valid proof for this repository
- the host may only provide the container runtime and the control entry point
  needed to start or attach to the maintainer container
- the default maintainer container entry point for this repository is the
  published GHCR image `ghcr.io/senanayake/polyglot-devcontainers-maintainer:main`
- the default maintainer control path is the official Dev Containers CLI
  targeting `.devcontainer/devcontainer.json`
- when a standalone `devcontainer` binary is unavailable, agents may invoke the
  pinned `@devcontainers/cli` package through the repository wrapper instead of
  relying on a host-global install
- agents should prefer the published maintainer image over rebuilding the
  maintainer image on the host
- if a workflow cannot run inside the maintainer container, agents must treat
  that as a repository bug and fix the maintainer environment before relying on
  host-local fallbacks
- DevPod remains a valid IDE consumption path for downstream image users, but
  maintainer and agent workflows should use the maintainer devcontainer control
  path instead of treating DevPod as the automation interface
- on Windows, container-authoritative Git in worktrees requires
  `git worktree add --relative-paths` so the Dev Containers CLI can mount the
  worktree common dir correctly; otherwise agents should use a normal clone or
  a WSL-backed checkout

On Windows, agents should prefer a **WSL-first** workflow when using VS Code
and devcontainers.

---

# 3. Task Runner Contract

All repositories using these devcontainers must expose the following commands.

These commands must run inside the container.

```bash
task init
task lint
task test
task scan
task ci
```

Definitions:

| command | purpose |
|------|------|
| init | bootstrap development environment |
| lint | run code quality checks |
| test | run tests |
| scan | run security checks |
| ci | run lint + test + scan |

Agents should consider a task complete only when:
```bash
task ci
```

succeeds.

---

# 4. Language Support Strategy

The repository will eventually support multiple ecosystems.

Initial implementation must start small.

Phase 1 language support:

- Python

Future support (later phases):

- Node / TypeScript
- Go
- Rust
- Java

Do not implement additional languages until the initial Python system works well.

---

# 5. Devcontainer Strategy

Devcontainers should be built using:

1. official devcontainer images
2. devcontainer Features
3. minimal custom configuration

Avoid large custom Dockerfiles initially.

Preferred base images:
```bash
mcr.microsoft.com/devcontainers/python
```

or equivalent official templates.

---

# 6. Feature Strategy

When installing tools:

1. Check if an official Feature exists
2. Use the Feature if maintained
3. Only write custom Features when necessary

Custom Features should focus on:

- DevSecOps workflows
- security baseline tooling
- agent-friendly workflows
- opinionated engineering standards

Possible future custom Features:
security-baseline
python-engineering
node-engineering
agent-runtime


---

# 7. Security Tooling Expectations

Baseline security tools may include:

Python ecosystem:

- pip-audit
- safety (optional)

General:

- Gitleaks
- Trivy (later)
- dependency scanning

Security tooling must be:

- open source
- free
- well maintained
- compatible with CI pipelines

For third-party security or maintenance tools that this repository installs as
released binaries, agents must stay on the latest upstream-supported release
that is available through the repository workflow.

Agents must NOT:

- self-build, fork, patch, or privately repackage third-party tools such as
  `trivy`, `gitleaks`, or `task` only to suppress scanner findings unless a
  human explicitly directs that work
- replace an upstream-supported release artifact with a repository-specific
  derivative build as an automatic remediation step

When image scans still report findings in the latest upstream-supported binary
release, agents must classify those findings as upstream residual risk,
document them in the generated security artifacts, and wait for a new upstream
release rather than leaving the monitored ecosystem.

---

# 8. Code Quality Tooling

Preferred tools for Python:

ruff
pytest


Preferred tools for JavaScript/TypeScript (future):

eslint
prettier
typescript


Avoid installing overlapping tools when one tool can replace many.

Example:

Ruff replaces:

- flake8
- isort
- several other Python linters.

---

# 9. CI Strategy

CI pipelines must mirror the local workflow.

CI should run:
```bash
task ci
```

The CI pipeline must not contain special logic that bypasses local workflows.

---

# 10. Dev Container Image Compliance

When this repository builds or publishes an OCI image intended for devcontainer
use, that image must remain compliant with the dev container specification's
image metadata model.

Agents must ensure:

- built images embed repo-owned devcontainer metadata in the
  `devcontainer.metadata` image label
- the embedded metadata matches the source `devcontainer.json` for all
  image-storable properties used by the repository
- published images do not rely on downstream repositories to re-declare
  required defaults like `remoteUser`, lifecycle commands, or editor
  customizations
- image validation checks inspect the final built image labels, not only the
  source JSON files
- changes to a devcontainer definition are mirrored in the image build path so
  the image and `devcontainer.json` do not drift apart

At minimum, agents must review whether the image needs to embed values such as:

- `remoteUser`
- lifecycle commands like `onCreateCommand`, `updateContentCommand`,
  `postCreateCommand`, `postStartCommand`, and `postAttachCommand`
- `customizations`
- `containerEnv` or `remoteEnv` when they define required behavior for image
  consumers
- any other devcontainer properties the specification allows to be stored in
  image metadata and that this repository depends on

If an image is intended to be consumed directly through an `"image"` reference,
agents must treat missing or stale `devcontainer.metadata` as a correctness bug.

---

# 11. Agent Workflow Expectations

Agents should follow this development loop:

1. understand task
2. modify code
3. run lint
4. run tests
5. run security scans
6. fix failures
7. repeat

Example loop:
```bash
task lint
task test
task scan
```

Agents must not declare tasks complete if these fail.

Agents must also fail fast when these workflows are run outside the maintainer
container. Task and script guards should enforce this rule so host execution is
not silently accepted.

---

# 12. Repository Layout

Preferred repository layout:
polyglot-devcontainers
│
├─ README.md
├─ AGENTS.md
├─ ROADMAP.md
├─ Taskfile.yml
│
├─ examples
│ └─ python-example
│
├─ templates
│
├─ features
│
└─ .github
└─ workflows


Do not introduce unnecessary directories.

---

# 13. What Agents Must Avoid

Agents must NOT:

- add large architectural layers prematurely
- implement unnecessary abstractions
- introduce enterprise-specific assumptions
- require host machine setup
- create overly complex container builds
- install excessive tooling

The system must remain **simple and maintainable**.

---

# 14. Development Philosophy

The project draws inspiration from:

- Google SRE practices
- DevSecOps shift-left security
- reproducible engineering environments
- high-performance developer workflows

The system must remain:

- small
- practical
- secure
- composable

---

# 15. Contribution Expectations

Changes should:

- improve reproducibility
- reduce complexity
- improve security posture
- increase usability for both humans and AI agents

Avoid changes that:

- increase maintenance burden
- duplicate existing ecosystem tools
- introduce unnecessary dependencies

---

# 16. Long Term Vision

The repository may eventually provide:

- polyglot devcontainer templates
- secure engineering environments
- standardized DevSecOps workflows
- AI-agent-compatible development environments

But the system must evolve **incrementally** from the

simplest working implementation.
simple → working → evolved → complex

not complex → broken

---

End of AGENTS.md
