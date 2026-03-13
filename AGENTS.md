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

# 10. Agent Workflow Expectations

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

---

# 11. Repository Layout

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

# 12. What Agents Must Avoid

Agents must NOT:

- add large architectural layers prematurely
- implement unnecessary abstractions
- introduce enterprise-specific assumptions
- require host machine setup
- create overly complex container builds
- install excessive tooling

The system must remain **simple and maintainable**.

---

# 13. Development Philosophy

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

# 14. Contribution Expectations

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

# 15. Long Term Vision

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
