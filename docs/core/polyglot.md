---
title: polyglot
section: 7
header: Polyglot Devcontainers
footer: Runtime Documentation
---

# NAME

polyglot - top-level runtime guide for polyglot-devcontainers

# PURPOSE

This page is the starting point for humans and agents working inside a
polyglot-devcontainers environment.

Use it to discover:

- which starter or workspace you are in
- how to bootstrap an empty workspace from a published starter image
- the task contract
- where to find Python or Java guidance
- where security and dependency artifacts are written
- where to find stronger agent and engineering guidance

# WHEN TO USE

Read this page first when you enter a container and do not yet know the local
workflow.

# PRIMARY COMMANDS

```bash
man polyglot-starters
man polyglot-task-contract
man polyglot-python
man polyglot-java
man polyglot-scenarios
man polyglot-troubleshooting
man polyglot-agents
man polyglot-knowledge
```

# WORKFLOW

1. If you opened a published starter image into an empty workspace, run
   `task init` to scaffold the starter.
2. Identify whether you are in the repository root, a Python / Node starter,
   or a Java starter.
3. Read the starter-specific page.
4. Follow the task contract.
5. Use the scenarios page when you want a repo-owned executable pattern rather
   than only read-only guidance.
6. Use the security and dependency pages when you need artifacts or upgrade
   guidance.
7. Use the troubleshooting, agents, and knowledge pages when you need stronger
   operating guidance.

# OUTPUTS / ARTIFACTS

Most engineering and security artifacts are written under:

```text
.artifacts/scans/
```

Examples include:

- `pip-audit.json`
- `trivy-java.json`
- `gitleaks.sarif`
- `dependency-inventory.json`
- `dependency-plan.json`
- `dependency-report.json`
- `dependency-report.md`

# COMMON FAILURES

- Running on the host instead of inside the container.
- Expecting starter project dependencies to be baked into the image.
- Treating an empty non-Git workspace as if it were already a repository.
- Guessing commands instead of using the task contract.
- Treating examples, templates, and proving fixtures as the same thing.
- Ignoring artifacts after a scan or dependency operation.

# GUIDANCE

- Prefer container-first execution.
- In published starter images, use `task init` to materialize the starter into
  the mounted workspace before expecting `task ci` to work.
- Treat `task ci` as the completion bar unless you are explicitly doing
  exploratory work.
- Use the local runtime docs before relying on memory or assumptions.
- Follow the validated starter workflow rather than inventing a custom one too
  early.

# SEE ALSO

- `polyglot-starters(7)`
- `polyglot-task-contract(7)`
- `polyglot-python(7)`
- `polyglot-java(7)`
- `polyglot-scenarios(7)`
- `polyglot-security(7)`
- `polyglot-deps(7)`
- `polyglot-troubleshooting(7)`
- `polyglot-agents(7)`
- `polyglot-knowledge(7)`
