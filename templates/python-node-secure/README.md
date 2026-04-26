# python-node-secure

`python-node-secure` is a focused polyglot starter repository for projects that
need Python and Node / TypeScript in one development container.

Included:

- `.devcontainer/devcontainer.json`
- `Taskfile.yml`
- a small Python package under `backend/`
- a small TypeScript module under `frontend/`
- pinned Python and Node developer tooling
- a checked-in `uv.lock` file for the Python side of the workspace
- pre-commit configuration
- local runtime docs available through `man polyglot` in the published image
- a layered test surface:
  - `task test` - full Python + Node suite
  - `task test:fast` - Python unit + property plus Node unit tests
  - `task test:unit`
  - `task test:integration`
  - `task test:acceptance`
  - `task test:property`

After opening the template in a devcontainer, run:

```bash
man polyglot
task init
task ci
task scenarios:verify
```

When consuming the published image directly in an empty workspace, `task init`
will scaffold the starter files, create a starter `AGENTS.md`, create a
`.kbriefs/` workspace with templates, create a Diataxis-shaped `docs/` tree,
and then install the project-local Python and Node dependencies into that
workspace.

Starter-local scenarios are also available after bootstrap:

- `task scenarios:starter-health`
- `task scenarios:security-evidence`
- `task scenarios:non-git-scan-fallback`
- `task scenarios:verify`
