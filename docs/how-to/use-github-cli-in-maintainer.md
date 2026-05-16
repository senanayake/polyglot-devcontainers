# Use GitHub CLI In The Maintainer Container

Use this path when you need GitHub API, Actions, release, or PR operations
from the maintainer container.

The supported entrypoint is:

```bash
task maintainer:gh -- <gh arguments>
```

Examples:

```bash
task maintainer:gh -- run view 24285030079
task maintainer:gh -- release view v0.0.23
task maintainer:gh -- pr status
```

## Credential Supply

The maintainer container does not have its own long-lived GitHub CLI login.

Supported credential sources, in order:

1. `GH_TOKEN` or `GITHUB_TOKEN` on the host for `github.com`
2. `GH_ENTERPRISE_TOKEN` or `GITHUB_ENTERPRISE_TOKEN` on the host for a GHES
   host
3. the host Git credential store, when the repository remote already has HTTPS
   credentials available through `git credential fill`

PowerShell example:

```powershell
$env:GH_TOKEN = "<token>"
task maintainer:gh -- auth status
task maintainer:gh -- run view 24285030079
Remove-Item Env:GH_TOKEN
```

Bash example:

```bash
export GH_TOKEN="<token>"
task maintainer:gh -- auth status
task maintainer:gh -- run view 24285030079
unset GH_TOKEN
```

If you target a GitHub Enterprise Server host, also set `GH_HOST` on the host
before running `task maintainer:gh -- ...`.

## Security Model

The wrapper is intentionally narrow:

- it injects credentials into one container-side `gh` command at a time
- it sets `GH_PROMPT_DISABLED=1` so the container does not fall back to an
  interactive login path
- it creates a temporary `GH_CONFIG_DIR` for each command and deletes it on
  exit
- it does not mount or reuse the host `gh` configuration directory
- it does not read credentials from repository files

This keeps GitHub authentication ephemeral and out of the workspace.

## Unsupported Patterns

Do not use:

- `task maintainer:gh -- auth login`
- `task maintainer:gh -- auth refresh`
- `task maintainer:gh -- auth setup-git`
- repository-local token files such as `.env`, `.token`, or ad hoc shell
  scripts
- manual copies of host `~/.config/gh` content into the container

Those flows either persist credentials or make it too easy to commit them by
mistake.

## Preventing Credential Commits

The supported path avoids writing credentials into the repository at all.

Repository backstops remain in place:

- `task scan` runs `gitleaks`
- `task ci` includes `task scan`

Treat any credential file created in the repository as a bug. Delete it and
move back to host environment variables or the host credential manager.
