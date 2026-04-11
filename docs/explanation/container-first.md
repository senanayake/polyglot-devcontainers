# Container-First Workflow

The Linux container is the source of truth for this repository.

That choice reduces drift across Windows, macOS, and Linux because:

- tool installation happens in a known environment
- CI can mirror local setup more closely
- host package state does not become part of the contract

The host only needs enough capability to control the container workflow.

For maintainer and agent workflows, this repository now treats the checked-in
maintainer devcontainer definition as the host-side control plane:

- `.devcontainer/devcontainer.json` defines the maintainer environment
- the official Dev Containers CLI provides the supported `up` and `exec` path
- the published GHCR maintainer image remains the default runtime payload
- HTTPS Git remotes can be used from inside that container through the
  repository wrapper's one-command credential bridge, so the Git operation
  still runs in the maintainer container without writing credentials into the
  container filesystem
- GitHub CLI commands should use `task maintainer:gh -- ...`, which injects
  host-supplied or host-derived credentials into a single container-side `gh`
  command without persisting `gh` login state in the container or workspace

That keeps DevPod available for downstream IDE experiences without making it
the automation path for repository maintenance.

On Windows, container-authoritative Git is most reliable from WSL-backed
checkouts or normal clones. Git worktrees can also work when they are created
with `git worktree add --relative-paths`, which lets the Dev Containers CLI
mount the worktree common dir for Git operations inside the container.
