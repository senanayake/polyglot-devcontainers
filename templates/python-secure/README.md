# python-secure

`python-secure` is a minimal starter repository for a secure Python
devcontainer workflow.

## What's Included

- `.devcontainer/devcontainer.json` - Devcontainer configuration
- `Taskfile.yml` - Task automation
- `src/` - Python package structure
- `tests/` - Test suite
- Pinned Python developer tooling (uv, ruff, mypy, pytest)
- `uv.lock` - Reproducible dependency locking
- `pre-commit` configuration
- Security scanning with pip-audit

## Quick Start

### Option A: Automated Setup (Recommended for Standalone Use)

If you copied this template to use as a standalone scenario:

```bash
./init.sh
```

This script will:
- Clean any host artifacts (architecture-specific files)
- Verify bundled dependencies
- Initialize git repository (required for pre-commit)
- Start DevPod with VSCode
- Set up the complete development environment

**After VSCode opens:**
1. Open workspace folder: `/workspaces/python-secure`
2. In terminal: `cd /workspaces/python-secure`
3. Verify: `task ci`

### Option B: Manual Setup

If you prefer manual control or are using this within the polyglot-devcontainers repo:

```bash
# Open in devcontainer
devpod up .

# After container starts, run:
task ci
```
