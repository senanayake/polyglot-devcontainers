---
title: polyglot-agents
section: 7
header: Polyglot Devcontainers
footer: Runtime Documentation
---

# NAME

polyglot-agents - operating guidance for coding agents in the container

# PURPOSE

This page describes how an agent should behave inside polyglot-devcontainers.

# WHEN TO USE

Read this page before making changes or declaring work complete.

# PRIMARY COMMANDS

```bash
man polyglot
man polyglot-task-contract
task ci
```

# WORKFLOW

Agent defaults:

1. gather context from local runtime docs and the workspace
2. prefer container-first execution
3. follow the task contract
4. inspect artifacts when doing security or dependency work
5. use the smallest change that solves the real problem

# OUTPUTS / ARTIFACTS

Agents should treat `.artifacts/scans/` as a first-class source of evidence.

# COMMON FAILURES

- relying on memory instead of reading the local contract
- using host tooling as proof of success
- skipping `task ci`
- ignoring generated artifacts after dependency or security tasks

# GUIDANCE

- start with `man polyglot`
- prefer validated starter workflows over improvised ones
- keep changes aligned with the repository's security-first posture
- use the Knowledge layer when judgment is needed, not just mechanics

# SEE ALSO

- `polyglot(7)`
- `polyglot-task-contract(7)`
- `polyglot-knowledge(7)`
- `polyglot-troubleshooting(7)`
