---
id: KB-2026-019
type: standard
status: validated
created: 2026-04-11
updated: 2026-04-11
tags: [maintainer, github, gh, credentials, security, kbpd, container-first]
related: [KB-2026-008, KB-2026-018]
---

# Maintainer GitHub Authentication Standard

## Context

The maintainer container is the source of truth for repository maintenance, but
some maintainer workflows need GitHub API access for Actions, releases, PRs,
and package investigation.

That created a gap: the container needed `gh`, but the repository also needed a
safe answer to how credentials should reach that tool without creating another
stateful credential store inside the maintainer environment.

## Problem/Need

We needed a standard that:

- keeps GitHub operations container-first
- works for both humans and agents
- does not rely on `gh auth login` inside the container
- does not write credentials into the repository or container home
- remains compatible with existing host credential-manager setups

## Standard/Pattern

### Description

For maintainer workflows, GitHub CLI access should happen only through:

```bash
task maintainer:gh -- <gh arguments>
```

That wrapper must:

- run `gh` inside the maintainer container
- inject credentials per command through environment variables
- create a temporary `GH_CONFIG_DIR`
- delete that config directory on exit
- block interactive or persistent `gh auth` flows inside the container

### Key Principles

- Container execution remains authoritative.
- Authentication is ephemeral, not stateful.
- The supported path must not encourage repository-local secret files.

### Implementation

Supported credential sources, in order:

1. `GH_TOKEN` / `GITHUB_TOKEN` on the host for `github.com`
2. `GH_ENTERPRISE_TOKEN` / `GITHUB_ENTERPRISE_TOKEN` plus `GH_HOST` on the
   host for GHES
3. the host Git credential store through `git credential fill` for the
   repository remote

The maintainer image should install `gh` from the official GitHub CLI Debian
repository and verify the published signing-key fingerprints during image
build.

## Rationale

This approach is preferred because:

- GitHub CLI officially supports `GH_TOKEN` / `GITHUB_TOKEN` for
  non-interactive authentication
- it preserves the container-first boundary without storing long-lived login
  state in the container
- it reuses existing host credential-manager setups when explicit environment
  variables are not present

## Benefits

- Agents can inspect Actions and releases from inside the maintainer container.
- Authentication state is reduced to one command invocation at a time.
- The safe path is explicit and easy to document.

## Constraints

- Repository operators still need valid GitHub credentials on the host.
- The host credential-store fallback depends on an HTTPS remote with usable
  credentials.
- Persistent `gh auth` features inside the container are intentionally not part
  of the supported contract.

## Alternatives Considered

### `gh auth login` Inside The Container

- Simple, familiar CLI flow.
- Rejected because it persists GitHub auth state in the container and makes
  secret sprawl harder to control.

### Mount The Host `gh` Configuration Directory

- Reuses an existing login.
- Rejected because it couples the container to host-specific secret state and
  widens the accidental-exfiltration surface.

### Repository-Local Token Files

- Easy to script.
- Rejected because the repository should never need a credential file for the
  maintainer path, and such files are too easy to commit by mistake.

## Evidence

- GitHub CLI manual: `GH_TOKEN` / `GITHUB_TOKEN` take precedence over stored
  credentials for `github.com` and avoid interactive auth prompts:
  <https://cli.github.com/manual/gh_help_environment>
- GitHub CLI manual: Linux installation via the official GitHub CLI Debian
  repository is the maintainer-supported path:
  <https://raw.githubusercontent.com/cli/cli/trunk/docs/install_linux.md>
- Repository investigation showed the previous maintainer image did not install
  `gh`, and the maintainer wrapper only bridged `git`.

## Anti-Patterns

- Running `gh auth login` inside the maintainer container.
- Copying tokens into repository files.
- Falling back to host-side `gh` execution as proof of a maintainer workflow.

## Verification

Run through the maintainer control path:

```bash
task maintainer:up
task maintainer:gh -- --version
task maintainer:gh -- auth status
```

Expected behavior:

- `gh` is available in the maintainer container
- `auth status` works when the host supplies a token or the host credential
  store can satisfy the repository remote
- no credential files are written into the repository

## Exceptions

- Public read-only `gh` commands may work without authentication.
- Direct host `gh` usage may still be acceptable for unrelated host tasks, but
  not as proof that the repository maintainer path works.

## Applicability

### Use This Standard When

- the work is on `polyglot-devcontainers`
- the operation needs GitHub API access from the maintainer lane
- credentials must stay out of the workspace

### Don't Use This Standard When

- a task only needs `git` transport and `task maintainer:git -- ...` is enough
- a downstream repository is defining its own credential model

## Maintenance

- Keep the GitHub CLI install path on the current maintainer-supported
  repository.
- Revisit the wrapper if GitHub CLI changes its supported environment-variable
  authentication model.

## Related Knowledge

- `KB-2026-008-container-architecture-mismatch.md`
- `KB-2026-018-automated-python-cve-remediation-standard.md`
- `docs/how-to/use-github-cli-in-maintainer.md`

## Success Metrics

- `gh`-based maintainer investigations run inside the maintainer container.
- Supported workflows do not require `gh auth login` inside the container.
- The repo no longer needs ad hoc container package installs to investigate
  GitHub Actions.
