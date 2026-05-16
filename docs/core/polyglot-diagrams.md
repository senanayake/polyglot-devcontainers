---
title: polyglot-diagrams
section: 7
header: Polyglot Devcontainers
footer: Runtime Documentation
---

# NAME

polyglot-diagrams - render presentation-quality diagrams from a deterministic
container workflow

# PURPOSE

This page explains the diagram rendering surface in the Polyglot diagrams image
and the repo-owned starter/example for CVE presentation work.

# WHEN TO USE

Read this page when you need to:

- generate slide-quality SVG diagrams from code
- validate D2 diagram sources in a task-based workflow
- render the initial CVE portfolio dependency diagrams

# PRIMARY COMMANDS

```bash
task init
task lint
task render
task test
task scan
task ci
diagram render --tool d2 --input docs/diagrams/example.d2 --output .artifacts/diagrams/example.svg --manifest .artifacts/diagrams/example.json
diagram validate --tool d2 --input docs/diagrams/example.d2
man polyglot
```

# WORKFLOW

1. Start in `templates/diagram-secure` or `examples/diagram-image-example`.
2. Run `task init` to create the artifacts directories.
3. Use `task lint` to format-check and validate the D2 sources.
4. Use `task render` to build SVG outputs and machine-readable manifests.
5. Use `task ci` to prove the full starter contract.

# OUTPUTS / ARTIFACTS

Diagram workspaces write:

- `.artifacts/diagrams/*.svg`
- `.artifacts/diagrams/*.json`
- `.artifacts/scans/gitleaks.sarif`

# GUIDANCE

- Prefer SVG as the primary presentation output.
- Keep the source diagrams explicit and reviewable.
- Treat legends and visual distinctions as part of the contract, not optional
  polish.
- Use `diagram render` when an agent needs a stable non-interactive interface.

# SEE ALSO

- `polyglot(7)`
- `polyglot-starters(7)`
- `polyglot-task-contract(7)`
