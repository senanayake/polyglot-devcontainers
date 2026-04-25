# python-secure

`python-secure` is a minimal starter repository for a secure Python
devcontainer workflow.

## What's Included

- `.devcontainer/devcontainer.json` - Devcontainer configuration
- `Taskfile.yml` - Task automation
- `src/` - Python package structure
- `tests/` - Test suite
- Pinned Python developer tooling (uv, ruff, mypy, pytest, pytest-bdd, hypothesis)
- `uv.lock` - Reproducible dependency locking
- `pre-commit` configuration
- Security scanning with pip-audit
- A layered test surface:
  - `task test` - full automated suite
  - `task test:fast` - unit + property
  - `task test:unit`
  - `task test:integration`
  - `task test:acceptance`
  - `task test:property`

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

## Security Remediation

The Python task runner also exposes a policy-aware remediation loop:

```bash
task scan:plan   # Inspect the automated remediation candidates
task scan:fix    # Review fixes interactively
task scan:auto   # Apply policy-allowed fixes with rollback and reporting
task scan:pr     # Create a remediation branch and commit accepted fixes
```

The behavior is controlled by `security-scan-policy.toml`.
