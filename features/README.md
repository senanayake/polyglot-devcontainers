# Feature Library

The repository provides a small, composable feature library for secure
devcontainers.

- `security-baseline`: installs Task and Gitleaks
- `python-engineering`: installs Python workflow helpers such as `pre-commit`
  and `uv`
- `node-engineering`: enables `corepack` and pins `pnpm`
- `agent-runtime`: installs agent-friendly CLI utilities

Templates in this repository compose these features instead of relying on large
custom Dockerfiles.
