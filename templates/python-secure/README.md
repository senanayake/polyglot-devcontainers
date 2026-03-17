# python-secure

`python-secure` is a minimal starter repository for a secure Python
devcontainer workflow.

Included:

- `.devcontainer/devcontainer.json`
- `Taskfile.yml`
- a small `src/` package
- tests
- pinned Python developer tooling
- a checked-in `uv.lock` file for reproducible Python bootstrap
- pre-commit configuration

After opening the template in a devcontainer, run:

```bash
task ci
```
