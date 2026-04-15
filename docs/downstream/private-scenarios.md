# Private Scenarios

**Status:** Stable  
**Last Updated:** 2026-04-15

---

## Overview

This guide shows you how to create private scenarios that follow polyglot-devcontainers patterns. You'll learn how to structure scenarios, run them outside the polyglot repository, and integrate with private registries.

---

## Table of Contents

- [What Are Scenarios?](#what-are-scenarios)
- [Scenario Structure](#scenario-structure)
- [Creating Private Scenarios](#creating-private-scenarios)
- [Running Private Scenarios](#running-private-scenarios)
- [Integration Patterns](#integration-patterns)
- [Example Scenarios](#example-scenarios)
- [Best Practices](#best-practices)

---

## What Are Scenarios?

Scenarios are **pre-configured development environments** that combine:
- A devcontainer configuration
- Language-specific tooling
- Security scanning tools
- Task automation
- Testing frameworks

Polyglot provides public scenarios like `python-api-secure` and `python-secure`. You can create **private scenarios** for your organization following the same patterns.

---

## Scenario Structure

### Standard Scenario Layout

```
my-private-scenario/
├── .devcontainer/
│   ├── devcontainer.json       # DevContainer configuration
│   └── Containerfile           # Custom image (optional)
├── .gitignore                  # Ignore build artifacts
├── README.md                   # Scenario documentation
├── Taskfile.yml                # Task automation
├── tasks.py                    # Task implementation
├── pyproject.toml              # Python dependencies (if Python)
├── package.json                # Node dependencies (if Node)
├── src/                        # Application source
│   └── main.py
├── tests/                      # Test suite
│   └── test_main.py
└── security-scan-policy.toml   # Security policy (optional)
```

---

## Creating Private Scenarios

### Step 1: Choose Your Base

Start with a polyglot base image or public scenario:

**Option A: Use polyglot base image directly**
```json
{
  "name": "My Private Scenario",
  "image": "ghcr.io/senanayake/polyglot-devcontainers-python-node:latest"
}
```

**Option B: Copy and customize a public scenario**
```bash
# Copy public scenario as template
cp -r polyglot-devcontainers/templates/python-api-secure my-private-scenario
cd my-private-scenario

# Customize for your needs
# - Update .devcontainer/devcontainer.json
# - Modify pyproject.toml dependencies
# - Add your application code
```

**Option C: Build custom image from polyglot base**
```dockerfile
# .devcontainer/Containerfile
FROM ghcr.io/senanayake/polyglot-devcontainers-python-node:latest

USER root

# Add organization-specific tools
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        your-org-tool && \
    rm -rf /var/lib/apt/lists/*

USER vscode
```

---

### Step 2: Configure DevContainer

Create `.devcontainer/devcontainer.json`:

```json
{
  "name": "My Private Scenario",
  "image": "ghcr.io/senanayake/polyglot-devcontainers-python-node:latest",
  
  "customizations": {
    "vscode": {
      "extensions": [
        "ms-python.python",
        "ms-python.vscode-pylance",
        "dbaeumer.vscode-eslint"
      ],
      "settings": {
        "python.defaultInterpreterPath": ".venv/bin/python",
        "python.linting.enabled": true
      }
    }
  },
  
  "features": {
    "ghcr.io/devcontainers/features/docker-in-docker:2": {}
  },
  
  "forwardPorts": [8000, 3000],
  
  "postCreateCommand": "task init",
  
  "remoteUser": "vscode"
}
```

---

### Step 3: Define Task Contract

Create `Taskfile.yml` following polyglot's task verb system:

```yaml
version: '3'

tasks:
  # ============================================================================
  # Lifecycle Tasks
  # ============================================================================
  
  init:
    desc: Initialize development environment
    cmds:
      - python tasks.py init
  
  # ============================================================================
  # Check Verbs (read-only)
  # ============================================================================
  
  lint:
    desc: Check code quality (formatting, style, types)
    cmds:
      - python tasks.py lint
  
  test:
    desc: Run test suite
    cmds:
      - python tasks.py test
  
  scan:
    desc: Check security vulnerabilities
    cmds:
      - python tasks.py scan
  
  ci:
    desc: Run all checks (init + lint + test + scan)
    cmds:
      - task init
      - task lint
      - task test
      - task scan
  
  # ============================================================================
  # Fix Verbs (write, auto-fix issues)
  # ============================================================================
  
  format:
    desc: Auto-fix code formatting and style issues
    cmds:
      - python tasks.py format
  
  scan:fix:
    desc: Interactive security vulnerability fixes
    cmds:
      - python tasks.py scan_fix
```

---

### Step 4: Implement Tasks

Create `tasks.py` with your task implementations. You can copy from polyglot templates and customize:

```python
#!/usr/bin/env python3
"""Task automation for private scenario."""

import subprocess
import sys
from pathlib import Path

# Paths
ROOT = Path(__file__).parent
PYTHON = ROOT / ".venv" / "bin" / "python"
UV = "uv"  # Assumes uv is in PATH from base image

def run(cmd: list[str], **kwargs) -> subprocess.CompletedProcess:
    """Run command with consistent settings."""
    return subprocess.run(
        cmd,
        check=True,
        **kwargs
    )

def init() -> None:
    """Initialize development environment."""
    print("Initializing environment...")
    
    # Create virtual environment
    run([UV, "venv", ".venv"])
    
    # Install dependencies
    run([UV, "sync", "--frozen", "--extra", "dev"])
    
    print("✅ Environment initialized")

def lint() -> None:
    """Check code quality."""
    print("Running linters...")
    
    # Ruff check
    run([str(PYTHON), "-m", "ruff", "check", "src", "tests", "tasks.py"])
    
    # Ruff format check
    run([str(PYTHON), "-m", "ruff", "format", "--check", "src", "tests", "tasks.py"])
    
    print("✅ Linting passed")

def test() -> None:
    """Run test suite."""
    print("Running tests...")
    
    run([str(PYTHON), "-m", "pytest", "-v"])
    
    print("✅ Tests passed")

def scan() -> None:
    """Check security vulnerabilities."""
    print("Running security scans...")
    
    # Dependency scan
    run([str(PYTHON), "-m", "pip_audit", "--format", "json"])
    
    # Secret scan
    run(["gitleaks", "dir", ".", "--no-banner"])
    
    print("✅ Security scans passed")

# Command registry
COMMANDS = {
    "init": init,
    "lint": lint,
    "test": test,
    "scan": scan,
}

def main() -> int:
    """Main entry point."""
    if len(sys.argv) < 2 or sys.argv[1] not in COMMANDS:
        print(f"Usage: {sys.argv[0]} <command>")
        print(f"Commands: {', '.join(COMMANDS.keys())}")
        return 1
    
    COMMANDS[sys.argv[1]]()
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
```

---

### Step 5: Add Dependencies

Create `pyproject.toml` (for Python scenarios):

```toml
[project]
name = "my-private-scenario"
version = "0.1.0"
description = "Private scenario for my organization"
requires-python = ">=3.12"

dependencies = [
    "fastapi>=0.115.6",
    "uvicorn[standard]>=0.34.0",
    # Add your dependencies
]

[project.optional-dependencies]
dev = [
    "pytest>=8.3.4",
    "pytest-cov>=6.0.0",
    "ruff>=0.15.9",
    "pip-audit>=2.8.0",
]

[tool.ruff]
line-length = 100
target-version = "py312"

[tool.ruff.lint]
select = ["E", "F", "I", "N", "W", "UP"]

[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = ["test_*.py"]
```

---

## Running Private Scenarios

### Option 1: DevPod (Recommended)

```bash
# Navigate to scenario directory
cd my-private-scenario

# Start DevPod
devpod up . --ide vscode

# Inside container, run tasks
task init
task lint
task test
task scan
```

---

### Option 2: VS Code Dev Containers

1. Open scenario folder in VS Code
2. **Cmd+Shift+P** → "Dev Containers: Reopen in Container"
3. Wait for container to build
4. Open terminal and run tasks:
   ```bash
   task init
   task ci
   ```

---

### Option 3: Standalone Container

```bash
# Build container
podman build -f .devcontainer/Containerfile -t my-scenario:latest .

# Run container
podman run -it --rm \
    -v $(pwd):/workspace \
    -w /workspace \
    my-scenario:latest \
    bash

# Inside container
task init
task ci
```

---

## Integration Patterns

### Pattern 1: Private Registry

Push your scenario image to a private registry:

```bash
# Build image
podman build -f .devcontainer/Containerfile \
    -t registry.example.com/my-scenario:latest .

# Push to private registry
podman push registry.example.com/my-scenario:latest

# Use in devcontainer.json
{
  "image": "registry.example.com/my-scenario:latest"
}
```

---

### Pattern 2: Organization Template

Create a template repository for your organization:

```bash
# Create template repo
gh repo create my-org/scenario-template --template --public

# Clone and customize
git clone https://github.com/my-org/scenario-template my-new-project
cd my-new-project

# Initialize
task init
```

---

### Pattern 3: Multi-Scenario Monorepo

Organize multiple scenarios in one repository:

```
my-org-scenarios/
├── api-service/
│   ├── .devcontainer/
│   ├── Taskfile.yml
│   └── ...
├── batch-processor/
│   ├── .devcontainer/
│   ├── Taskfile.yml
│   └── ...
└── ml-pipeline/
    ├── .devcontainer/
    ├── Taskfile.yml
    └── ...
```

Each scenario is independent and can be opened separately in DevPod/VS Code.

---

## Example Scenarios

### Example 1: FastAPI Service

```
fastapi-service/
├── .devcontainer/
│   └── devcontainer.json
├── Taskfile.yml
├── tasks.py
├── pyproject.toml
├── src/
│   ├── main.py
│   ├── config.py
│   └── routers/
│       └── health.py
└── tests/
    └── test_api.py
```

**devcontainer.json:**
```json
{
  "name": "FastAPI Service",
  "image": "ghcr.io/senanayake/polyglot-devcontainers-python-node:latest",
  "forwardPorts": [8000],
  "postCreateCommand": "task init",
  "customizations": {
    "vscode": {
      "extensions": ["ms-python.python"]
    }
  }
}
```

---

### Example 2: Full-Stack App

```
fullstack-app/
├── .devcontainer/
│   └── devcontainer.json
├── Taskfile.yml
├── tasks.py
├── pyproject.toml          # Backend
├── package.json            # Frontend
├── backend/
│   └── src/
│       └── main.py
├── frontend/
│   └── src/
│       └── App.tsx
└── tests/
    ├── backend/
    └── frontend/
```

**devcontainer.json:**
```json
{
  "name": "Full-Stack App",
  "image": "ghcr.io/senanayake/polyglot-devcontainers-python-node:latest",
  "forwardPorts": [8000, 3000],
  "postCreateCommand": "task init"
}
```

---

### Example 3: Data Pipeline

```
data-pipeline/
├── .devcontainer/
│   └── devcontainer.json
├── Taskfile.yml
├── tasks.py
├── pyproject.toml
├── src/
│   ├── extract.py
│   ├── transform.py
│   └── load.py
├── tests/
│   └── test_pipeline.py
└── data/
    └── .gitkeep
```

**Additional dependencies:**
```toml
dependencies = [
    "pandas>=2.0.0",
    "sqlalchemy>=2.0.0",
    "apache-airflow>=2.8.0",
]
```

---

## Best Practices

### 1. Follow Task Verb System

Use polyglot's task verb system for consistency:
- **init** - Initialize environment
- **lint** - Check code quality
- **test** - Run tests
- **scan** - Security checks
- **ci** - Run all checks
- **format** - Auto-fix formatting

---

### 2. Document Your Scenario

Create a comprehensive README.md:

```markdown
# My Private Scenario

## Quick Start

\`\`\`bash
devpod up . --ide vscode
task init
task ci
\`\`\`

## What's Included

- FastAPI 0.115+
- PostgreSQL client
- Redis tools
- Custom authentication library

## Task Reference

- `task init` - Initialize environment
- `task dev` - Start development server
- `task test` - Run tests
- `task scan` - Security scans
```

---

### 3. Pin Dependencies

Use exact versions for reproducibility:

```toml
dependencies = [
    "fastapi==0.115.6",      # Exact version
    "uvicorn[standard]>=0.34.0,<0.35.0",  # Range
]
```

---

### 4. Include Security Policy

Create `security-scan-policy.toml`:

```toml
[policy]
fail_on = ["CRITICAL"]
allow_no_fix = true

[accepted_advisories]
# Temporary acceptance with expiration
# "PYSEC-2024-123" = { reason = "No fix available", expires = "2026-06-01" }
```

---

### 5. Add .gitignore

Exclude build artifacts:

```gitignore
# Virtual environments
.venv/
venv/
env/

# Build artifacts
__pycache__/
*.pyc
*.pyo
dist/
build/
*.egg-info/

# Test artifacts
.pytest_cache/
.coverage
htmlcov/

# Security scans
.artifacts/

# IDE
.vscode/
.idea/

# OS
.DS_Store
Thumbs.db
```

---

### 6. Test Portability

Ensure your scenario works outside the polyglot repo:

```bash
# Test in clean directory
mkdir /tmp/test-scenario
cp -r my-private-scenario /tmp/test-scenario/
cd /tmp/test-scenario/my-private-scenario

# Initialize git (required for some tools)
git init

# Test with DevPod
devpod up . --ide vscode

# Inside container
task init
task ci
```

---

## Troubleshooting

### Issue: "REPO_ROOT not found"

**Symptom:** `StopIteration` error when running tasks

**Cause:** tasks.py tries to find `AGENTS.md` in parent directories

**Solution:** Use standalone-friendly path resolution:

```python
# Instead of:
REPO_ROOT = next(
    parent for parent in Path(__file__).resolve().parents 
    if (parent / "AGENTS.md").exists()
)

# Use:
try:
    REPO_ROOT = next(
        parent for parent in Path(__file__).resolve().parents 
        if (parent / "AGENTS.md").exists()
    )
except StopIteration:
    # Fallback for standalone usage
    REPO_ROOT = Path(__file__).parent
```

---

### Issue: "Git context required"

**Symptom:** Gitleaks or pre-commit fails

**Cause:** Scenario not in a git repository

**Solution:** Initialize git:

```bash
git init
git add .
git commit -m "Initial commit"
```

---

### Issue: "Architecture mismatch"

**Symptom:** `Exec format error` when running binaries

**Cause:** Virtual environment created on different architecture

**Solution:** Add `.venv/` to `.gitignore` and rebuild:

```bash
# Clean up
rm -rf .venv

# Rebuild in container
task init
```

---

## Migration from Public Scenarios

### Migrating from polyglot templates

If you started with a polyglot template and want to make it private:

1. **Copy the template:**
   ```bash
   cp -r polyglot-devcontainers/templates/python-api-secure my-private-scenario
   cd my-private-scenario
   ```

2. **Remove polyglot-specific references:**
   ```python
   # In tasks.py, update REPO_ROOT logic
   # Add fallback for standalone usage
   ```

3. **Update dependencies:**
   ```toml
   # In pyproject.toml, add your private packages
   dependencies = [
       "fastapi>=0.115.6",
       "my-org-auth-lib>=1.0.0",  # Private package
   ]
   ```

4. **Test standalone:**
   ```bash
   git init
   devpod up . --ide vscode
   task init
   task ci
   ```

---

## Next Steps

1. **Choose a base image** - See [README](README.md#choosing-a-base-image)
2. **Review the contract** - See [base-image-contract.md](base-image-contract.md)
3. **Create your scenario** - Follow patterns in this guide
4. **Test thoroughly** - Validate with DevPod/VS Code
5. **Document** - Add comprehensive README
6. **Share** - Create template repo for your organization

---

## Related Documentation

- [Downstream README](README.md) - Overview and quick start
- [Building Private Images](building-private-images.md) - Dockerfile patterns
- [Base Image Contract](base-image-contract.md) - Stable API reference
- [Polyglot Scenarios](../scenarios/README.md) - Public scenario reference

---

**Ready to create your private scenario? Start with a polyglot template and customize!**
