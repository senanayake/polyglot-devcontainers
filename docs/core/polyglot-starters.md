---
title: polyglot-starters
section: 7
header: Polyglot Devcontainers
footer: Runtime Documentation
---

# NAME

polyglot-starters - choose the right starter or proving path

# PURPOSE

This page explains which Python or Java workspace to use as a starting point.

# WHEN TO USE

Read this page when you want to start real work and need to choose the correct
starter.

# PRIMARY COMMANDS

```bash
man polyglot-python
man polyglot-java
```

# WORKFLOW

Use these paths for practical starts:

- `templates/python-secure`
  Preferred Python starter template.
- `templates/java-secure`
  Preferred Java starter template.
- `examples/python-image-example`
  Use when you want to validate the published root image consumption path.
- `examples/java-image-example`
  Use when you want to validate the published Java image consumption path.

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
- Treating image-consumption examples as the same thing as authoring templates.

# GUIDANCE

- For a new Python project, start from `python-secure`.
- For a new Java project, start from `java-secure`.
- Use image examples when you are validating the published container path.

# SEE ALSO

- `polyglot(7)`
- `polyglot-python(7)`
- `polyglot-java(7)`
