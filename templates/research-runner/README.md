# Research Runner Template

This template consumes the `polyglot-devcontainers-research-runner` image.

The image provides Python, Node.js, npm, pnpm, `task`, `gitleaks`, and a
pre-built `/opt/research-venv` containing `pyyaml` and `openai`.

Use project-local lockfiles for experiment-specific dependencies. If a project
needs different Python versions, create a local `.venv`; it will shadow the
image venv after activation.

```bash
task ci
```
