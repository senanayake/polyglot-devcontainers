---
title: polyglot-research
section: 7
header: Polyglot Devcontainers
footer: Runtime Documentation
---

# NAME

polyglot-research - LLM-assisted research experiment runner workflow

# PURPOSE

This page explains the supported workflow for the research runner image.

# WHEN TO USE

Use this image for Python plus Node.js research artifacts that run TypeScript
test harnesses, invoke LLM APIs, and produce structured result artifacts.

# PRIMARY COMMANDS

```bash
task init
task test
task experiment
task report
task ci
```

# WORKFLOW

The image provides Python, Node.js, npm, pnpm, `task`, `gitleaks`, and a
pre-built Python virtual environment at `/opt/research-venv`.

The image venv is automatically first on `PATH` and includes:

- `pyyaml`
- `openai`

Project-local lockfiles remain authoritative for experiment-specific code.
Use `npm ci` for Node projects with a `package-lock.json`. If a project needs
different Python packages, create and activate a project-local `.venv`; it will
shadow the image venv.

LLM experiments must receive credentials at runtime. Do not bake API keys into
the image or repository. Devcontainers should pass the host value through:

```json
{
  "remoteEnv": {
    "OPENAI_API_KEY": "${localEnv:OPENAI_API_KEY}"
  }
}
```

# OUTPUTS / ARTIFACTS

Research projects commonly write:

- `results/`
- `archive/`
- `scenario/runs/`
- generated reports under project-owned paths

Do not commit dependency directories such as `node_modules`, `.venv`,
`.pytest_cache`, or `__pycache__`.

# COMMON FAILURES

- Running the full LLM experiment without `OPENAI_API_KEY`.
- Treating `task ci` as an API-consuming task. CI should validate deterministic
  no-key paths.
- Committing local dependency directories instead of lockfiles and outputs.

# GUIDANCE

- Keep deterministic validation separate from API-consuming experiment runs.
- Use `task ci` for no-key validation.
- Use `task experiment` only when the API key and budget are intentionally
  available.
- Capture experiment outputs as reviewable artifacts.

# SEE ALSO

- `polyglot(7)`
- `polyglot-python(7)`
- `polyglot-task-contract(7)`
- `polyglot-security(7)`
