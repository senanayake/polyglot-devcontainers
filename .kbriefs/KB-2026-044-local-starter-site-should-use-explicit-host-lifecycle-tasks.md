---
id: KB-2026-044
type: standard
status: published
created: 2026-04-29
updated: 2026-04-29
tags: [starters, ui, host-workflow, kbpd]
related:
  - KB-2026-043-minimal-local-starter-ui-should-stay-thin-over-the-catalog.md
  - KB-2026-041-generated-starter-scenario-proof-should-run-in-the-generated-workspace.md
---

# Local Starter Site Should Use Explicit Host Lifecycle Tasks

## Context

Once the local starter website existed, the next friction point was basic host
operation. Running `python scripts/starter_site.py` manually was workable for
development, but it was not a stable consumption path for repeated localhost
testing.

## Decision

Expose explicit host lifecycle commands for the local starter website:

- `task starters:site:start`
- `task starters:site:status`
- `task starters:site:stop`

Keep these commands host-side, and keep starter proof inside the maintainer
container task surface.

## Why This Is The Right Standard Now

- it gives humans and agents a repeatable localhost workflow
- it avoids turning the website into the proof orchestrator prematurely
- it preserves the maintainer container as the authoritative validation path

## Evidence

- `scripts/manage_starter_site.py` manages a background site process, pid
  record, health checks, and log files under `.tmp/`
- `Taskfile.yml` exposes explicit host lifecycle tasks for the site
- `starters/README.md` documents those tasks as the default local website path

## Applicability

### This Standard Applies To

- local testing of the starter website on a host workstation
- agent workflows that need to bring the website up and down predictably

### This Standard Does Not Replace

- `task starters:serve` for foreground debugging
- maintainer-container proof commands such as `task starters:verify`
