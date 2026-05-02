---
id: KB-2026-036
type: failure-mode
status: active
created: 2026-05-01
updated: 2026-05-01
tags: [github-actions, ci, maintainer-container, docker, devcontainers, starter-generator, failure-mode]
related: [KB-2026-027, KB-2026-035]
---

# Maintainer Control Path Drift Breaks Image-Backed Proofs

## Context

The `codex/starter-generator` branch extended the root repository workflow so
`task ci` now includes `task starters:verify`, which in turn runs
`task starters:verify:image-backed` for starters that prove published-image
bootstrap paths.

Those image-backed proofs require an OCI runtime from inside the maintainer
container.

## Failure Description

### Symptoms

- GitHub Actions `ci` job passed image build and metadata validation.
- The `Smoke test maintainer Dev Containers CLI control path` step passed.
- The later `Run root workflow` step failed inside `task ci`.
- Failure output showed `scripts/start_docker_daemon.sh` attempting to start
  `dockerd` and failing to create the Docker NAT chain with iptables permission
  errors.

### Concrete Failure

```text
task: Failed to run task "starters:verify:image-backed":
task: Failed to run task "_require_image_runtime": exit status 1
```

and:

```text
failed to start daemon: Error initializing network controller:
failed to create NAT chain DOCKER: iptables failed ... Permission denied
```

## Root Cause

### Primary Cause

The GitHub Actions root workflow bypassed the repository's official maintainer
control path and ran the maintainer image with a raw `docker run` command.

That direct invocation omitted the required devcontainer `runArgs` from
`.devcontainer/devcontainer.json`, specifically `--privileged`.

As a result, once `task ci` reached image-backed starter proofs, the maintainer
container had no reachable OCI daemon and tried to bootstrap its own nested
`dockerd`. On GitHub-hosted runners, that inner daemon could not configure the
required iptables/NAT rules without the missing privileged container runtime
configuration.

### Contributing Factors

- The workflow already had a passing step using `scripts/run_in_maintainer_container.py`,
  but the main `task ci` step did not reuse it.
- Earlier branch CI did not hit this path because root `task ci` did not yet
  include image-backed starter proofs.
- The repository's authoritative maintainer entrypoint is the Dev Containers CLI,
  but the workflow had drifted to a simpler raw Docker invocation.

## Evidence

- Failing run:
  `https://github.com/senanayake/polyglot-devcontainers/actions/runs/25202895318`
- The passing smoke-test step in that same run used
  `scripts/run_in_maintainer_container.py`.
- The failing root-workflow step used plain `docker run`.
- `.devcontainer/devcontainer.json` declares:
  `"runArgs": ["--privileged"]`

## Learning

- CI steps that execute maintainer workflows must use the same control path as
  maintainers and agents, not an approximation.
- Once repository tasks begin requiring nested OCI runtime access, bypassing the
  devcontainer launch contract becomes a correctness bug, not just an
  implementation detail.
- The right fix is to restore control-path fidelity by invoking
  `scripts/run_in_maintainer_container.py`, rather than adding ad hoc runtime
  flags to individual workflow steps.

## Decision

Update the GitHub Actions root `Run root workflow` step to execute through
`scripts/run_in_maintainer_container.py` with
`POLYGLOT_MAINTAINER_IMAGE=polyglot-devcontainers-maintainer:ci`.

## Consequences

- GitHub Actions now uses the same maintainer container contract as local agent
  workflows.
- Required devcontainer runtime settings such as `--privileged` stay centralized
  in repo-owned configuration.
- Future maintainer-runtime changes are less likely to drift between local and
  CI execution paths.
