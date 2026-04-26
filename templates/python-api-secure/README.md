# python-api-secure

`python-api-secure` is a FastAPI starter with a small but structured testing
surface and the standard Polyglot task contract.

## Included

- `.devcontainer/devcontainer.json`
- `Taskfile.yml`
- a small FastAPI application under `src/python_api_secure_template/`
- unit, integration, acceptance, and property test examples under `tests/`
- FastAPI, Uvicorn, Pydantic, SQLAlchemy, and Alembic dependencies
- pinned Python developer tooling (`uv`, `ruff`, `mypy`, `pytest`,
  `pytest-bdd`, `hypothesis`)
- security scanning with `pip-audit`

## Primary Commands

```bash
task init
task dev
task ci
```

## Test Commands

```bash
task test              # Full automated suite
task test:fast         # Unit + property
task test:unit
task test:integration
task test:acceptance
task test:property
```

## Security Remediation

The Python task runner also exposes a policy-aware remediation loop:

```bash
task scan:plan
task scan:fix
task scan:auto
task scan:pr
```

## Published Image Bootstrap

When consuming the published starter image directly in an empty workspace,
`task init` scaffolds the project files, creates a starter `AGENTS.md`, creates
`.kbriefs/`, creates a Diataxis-shaped `docs/` tree, and prepares the local
Python environment in that workspace.
