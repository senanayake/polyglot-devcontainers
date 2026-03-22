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
task maintainer:pull
task maintainer:task -- ci
task image:discover
task image:pin -- --write
task image:verify
task ci
```

# WORKFLOW

Agent defaults:

1. gather context from local runtime docs and the workspace
2. pull and use the published maintainer container as the only valid agent execution environment
3. follow the task contract
4. inspect artifacts when doing security or dependency work
5. use `task image:discover` before changing published image base references
6. use an explicit write step such as `task image:pin -- --write`
7. verify the published images with `task image:verify`
8. classify critical published-image findings as either `repo-fixable` or
   `upstream residual`
9. prefer the latest upstream-supported binary release for third-party tools
   and do not self-build vendor tools only to suppress scanner output
10. use the smallest change that solves the real problem

# OUTPUTS / ARTIFACTS

Agents should treat `.artifacts/scans/` as a first-class source of evidence.

Published image maintenance also writes evidence under:

- `base-image-report.json`
- `base-image-report.md`
- `image-security/`
- `image-security/residual-risk.json`
- `image-security/residual-risk.md`

# COMMON FAILURES

- relying on memory instead of reading the local contract
- using host tooling as proof of success
- rebuilding the maintainer container on the host when the published GHCR image is sufficient
- running repository workflows on the host instead of the maintainer container
- skipping `task ci`
- ignoring generated artifacts after dependency or security tasks
- editing published image base references without an explicit discovery report
- changing pins without a deliberate write step
- treating the latest upstream-supported vendor binary as repository-owned code
  that should be privately rebuilt to hide a scanner finding

# GUIDANCE

- start with `man polyglot`
- prefer validated starter workflows over improvised ones
- keep changes aligned with the repository's security-first posture
- use the Knowledge layer when judgment is needed, not just mechanics
- treat the published images as a separate maintenance lane: discover, pin, verify, then scan
- use `task maintainer:pull` and `task maintainer:task -- ...` when you need to enter the maintainer lane from the host
- if the maintainer container cannot execute the workflow, fix the maintainer container rather than falling back to the host
- for published-image CVEs, fix repo-owned causes first: stale base images,
  stale distro packages, stale pinned versions, and missing verification
- if a critical remains in the latest upstream-supported release of a managed
  binary such as `trivy`, `gitleaks`, or `task`, record it as upstream residual
  risk and keep the upstream artifact

# SEE ALSO

- `polyglot(7)`
- `polyglot-task-contract(7)`
- `polyglot-knowledge(7)`
- `polyglot-troubleshooting(7)`
