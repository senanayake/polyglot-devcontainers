---
title: polyglot-starters
section: 7
header: Polyglot Devcontainers
footer: Runtime Documentation
---

# NAME

polyglot-starters - choose the right starter or proving path

# PURPOSE

This page explains which starter path to use and how the published starter
images behave when opened into an empty workspace.

# WHEN TO USE

Read this page when you want to start real work and need to choose the correct
starter.

# PRIMARY COMMANDS

```bash
man polyglot-python
man polyglot-java
man polyglot-troubleshooting
```

# WORKFLOW

Use these paths for practical starts:

- `templates/python-secure`
  Preferred Python starter template.
- `templates/python-node-secure`
  Preferred published-image starter for Python plus Node / TypeScript.
- `templates/java-secure`
  Preferred Java starter template.
- `examples/python-image-example`
  Use when you want to validate the published Python image consumption path.
- `examples/java-image-example`
  Use when you want to validate the published Java image consumption path.

Published starter image workflow:

1. mount an empty or nearly empty workspace
2. open the published image
3. run `task init`
4. let the starter scaffold the local project files
5. run `task ci`

Starter image behavior:

- the image already contains the runtime, package managers, scanners, and local
  man pages
- `task init` installs project-local dependencies into the mounted workspace
- `task init` may create `.venv`, `node_modules`, `.gradle`, lockfile-backed
  caches, and `.artifacts`
- the workspace does not need to be a Git repository before `task init`

Treat these differently:

- `examples/python-maintenance-example`
  A proving fixture for dependency maintenance experiments.
- `examples/java-maintenance-example`
  A proving fixture for Java dependency maintenance experiments.

# OUTPUTS / ARTIFACTS

Starters and examples write artifacts under their own `.artifacts/scans/`
directories.

# COMMON FAILURES

- Starting from a proving fixture when you only needed a clean starter.
- Expecting a published starter image to contain your project files before
  running `task init`.
- Expecting `task init` to be a no-op in a fresh mounted workspace.
- Treating image-consumption examples as the same thing as authoring templates.

# GUIDANCE

- For a new Python project, start from `python-secure`.
- For a new Python plus Node / TypeScript project, start from
  `python-node-secure`.
- For a new Java project, start from `java-secure`.
- Use image examples when you are validating the published container path.
- When consuming a published starter image directly, keep the mounted workspace
  effectively empty until bootstrap completes.

# SEE ALSO

- `polyglot(7)`
- `polyglot-python(7)`
- `polyglot-java(7)`
- `polyglot-troubleshooting(7)`
