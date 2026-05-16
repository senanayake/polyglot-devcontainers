---
id: KB-2026-070
type: failure-mode
status: active
created: 2026-05-16
updated: 2026-05-16
tags: [latex, published-images, starter-smoke, bootstrap]
related: [KB-2026-056]
---

# LaTeX Bootstrap Must Scaffold Project Conventions

## Context

Published image smoke tests exercise the empty-workspace bootstrap path before
running `task ci`. The smoke contract expects every starter-backed image to
produce a workspace with the shared project conventions, including `AGENTS.md`,
`.kbriefs/`, and the docs skeleton.

## System/Component

`templates/latex/.devcontainer/bootstrap-workspace.sh` and the LaTeX published
image build.

## Failure Description

### Symptoms

- `task image:build -- --image latex --smoke` fails after `task init`.
- Smoke diagnostics show a bootstrapped LaTeX workspace with only the LaTeX
  payload files.
- The generated workspace lacks `AGENTS.md`, `.kbriefs/`, and `docs/`.

### Failure Scenario

- A new image defines its own bootstrap script instead of inheriting an existing
  convention-aware script.
- The image copies its template payload but does not copy or invoke
  `polyglot-scaffold-project-conventions`.
- The shared `smoke_test_published_starter.sh` checks for starter conventions.

### Impact

The image can build successfully while still failing the downstream starter
contract. That blocks release validation and would publish an image whose
empty-workspace bootstrap path is weaker than the other published starter
images.

## Root Cause

The LaTeX image copied only the template payload and did not include the
repository-owned starter scaffold assets or invoke the project-conventions
scaffold helper after payload copy.

## Evidence

Targeted validation failed with:

```bash
task maintainer:task -- image:build -- --profile fast --image research-runner --image latex --smoke --inner-ci
```

The `research-runner` target passed. The `latex` target built and passed
devcontainer metadata validation, then failed the starter smoke test. Smoke
diagnostics listed the generated workspace contents and showed no `AGENTS.md`,
`.kbriefs/`, or `docs/`.

## Prevention

- Published starter images with custom bootstrap scripts must copy
  `scripts/scaffold_project_conventions.sh` into the image.
- They must copy `assets/starter-scaffold` into the image.
- Bootstrap scripts must run `polyglot-scaffold-project-conventions
  "${template}"` after copying the template payload.
- The bootstrap marker should record `project_conventions_scaffolded: true`.

## Detection

Run the published image smoke path for any new image:

```bash
task maintainer:task -- image:build -- --profile fast --image <target> --smoke
```

## Status

- [x] Documented
- [x] Prevention implemented for the LaTeX image
- [x] Detection implemented through existing starter smoke tests
- [x] Mitigation tested after the fix
