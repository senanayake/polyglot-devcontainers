# Reference: Scenario Structure

**Information-oriented** | **Comprehensive** | **Technical**

Complete reference documentation for polyglot-devcontainers scenario structure, files, and conventions.

---

## Directory Structure

```
scenario-name/
├── .devcontainer/
│   ├── devcontainer.json      # Devcontainer configuration
│   └── Containerfile          # Container image definition
├── .git/                      # Git repository (initialized by init.sh)
├── .gitignore                 # Excludes artifacts (.venv, __pycache__, etc.)
├── src/                       # Application source code
│   └── scenario_package/      # Python package
│       ├── __init__.py
│       ├── main.py            # Application entry point
│       ├── config.py          # Settings management
│       └── routers/           # API routes (for API scenarios)
├── tests/                     # Test suite
│   └── test_*.py              # Test files
├── scripts/                   # Utility scripts
│   ├── install_runtime_docs.sh
│   └── evaluate_python_audit_policy.py
├── man/                       # Man pages for runtime guidance
│   └── man7/
│       └── polyglot-*.7
├── init.sh                    # Initialization automation script
├── tasks.py                   # Task runner implementation
├── Taskfile.yml               # Task definitions
├── pyproject.toml             # Python project metadata and dependencies
├── uv.lock                    # Locked dependencies
├── security-scan-policy.toml  # Security scanning configuration
├── .pre-commit-config.yaml    # Pre-commit hooks
├── .dockerignore              # Docker build exclusions
├── .env.example               # Environment variable template
└── README.md                  # Scenario documentation
```

---

## Core Files

### .devcontainer/devcontainer.json

Defines the development container configuration.

**Key properties:**
- `name` - Container display name
- `build.dockerfile` - Path to Containerfile
- `postCreateCommand` - Commands to run after container creation
- `customizations.vscode` - VSCode settings and extensions
- `remoteUser` - User to run as in container (typically "vscode")

**Example:**
```json
{
  "name": "Python API Secure",
  "build": {
    "dockerfile": "Containerfile"
  },
  "postCreateCommand": "bash scripts/install_runtime_docs.sh man/man7 && task init && pre-commit install",
  "customizations": {
    "vscode": {
      "settings": {
        "python.defaultInterpreterPath": "/workspaces/${localWorkspaceFolderBasename}/.venv/bin/python"
      },
      "extensions": [
        "ms-python.python",
        "charliermarsh.ruff"
      ]
    }
  },
  "remoteUser": "vscode"
}
```

### .devcontainer/Containerfile

Defines the container image.

**Structure:**
1. Base image (official devcontainer image)
2. System dependencies installation
3. Binary tool installation (task, gitleaks)
4. Checksum verification
5. Python tooling (pre-commit, uv)
6. User switch to vscode

**Example:**
```dockerfile
FROM mcr.microsoft.com/devcontainers/python:1-3.12-bookworm

USER root

ARG TASK_VERSION=3.49.1
ARG GITLEAKS_VERSION=8.30.0

RUN apt-get update && \
    apt-get install -y ca-certificates curl git && \
    # Install task and gitleaks with checksum verification
    # ... (see actual Containerfile for complete implementation)

USER vscode
```

### init.sh

Automation script for standalone scenario setup.

**Responsibilities:**
1. Verify script is in scenario directory
2. Clean host artifacts (.venv, __pycache__, etc.)
3. Verify bundled dependencies exist
4. Initialize git repository if needed
5. Start DevPod with VSCode
6. Provide next-step instructions

**Usage:**
```bash
./init.sh
```

**Exit codes:**
- `0` - Success
- `1` - Error (missing files, devpod not found, etc.)

### tasks.py

Python-based task runner implementation.

**Key components:**
- `ROOT` - Scenario directory path
- `REPO_ROOT` - Repository root (with fallback to ROOT)
- `PYTHON` - Path to Python interpreter in venv
- `UV` - Path to uv binary
- Task functions (init, lint, test, scan, ci, dev)

**Task contract:**
```bash
task init   # Initialize development environment
task lint   # Run code quality checks
task test   # Run test suite
task scan   # Run security scans
task ci     # Run lint + test + scan
task dev    # Start development server (API scenarios)
```

### Taskfile.yml

Declarative task definitions that delegate to tasks.py.

**Structure:**
```yaml
version: '3'

tasks:
  init:
    desc: Initialize development environment
    cmds:
      - python tasks.py init

  lint:
    desc: Run code quality checks
    cmds:
      - python tasks.py lint

  # ... other tasks
```

### pyproject.toml

Python project metadata and dependencies.

**Key sections:**
- `[project]` - Package metadata
- `[project.dependencies]` - Runtime dependencies
- `[project.optional-dependencies]` - Dev dependencies
- `[tool.ruff]` - Ruff configuration
- `[tool.mypy]` - MyPy configuration
- `[tool.pytest]` - Pytest configuration

### security-scan-policy.toml

Security scanning policy configuration.

**Structure:**
```toml
[policy]
fail_on_severity = ["CRITICAL"]
allow_no_fix = true

[[policy.accepted_advisories]]
id = "GHSA-xxxx-xxxx-xxxx"
reason = "False positive - not applicable to our usage"
expires = "2026-12-31"
```

### .gitignore

Excludes architecture-specific and generated files.

**Key exclusions:**
```gitignore
# Virtual environments
.venv/
venv/

# Python artifacts
__pycache__/
*.pyc

# Testing
.pytest_cache/
.coverage

# Project artifacts
.artifacts/
.tmp/

# Environment
.env
```

---

## File Conventions

### Naming

- **Scenario directories:** `language-purpose-secure` (e.g., `python-api-secure`)
- **Package names:** `scenario_name_template` (e.g., `python_api_secure_template`)
- **Test files:** `test_*.py` (pytest convention)
- **Script files:** `lowercase_with_underscores.sh`

### Paths

- **Absolute paths in container:** `/workspaces/<scenario-name>/`
- **Relative paths in code:** Use `ROOT` or `REPO_ROOT` constants
- **Virtual environment:** `.venv/` (always in scenario root)

### Permissions

- **Scripts:** Executable (`chmod +x init.sh`)
- **Source code:** Read/write for vscode user
- **Configuration files:** Read-only in container

---

## Environment Variables

### Container Environment

Set in `.devcontainer/devcontainer.json`:

```json
{
  "containerEnv": {
    "PROJECT_NAME": "My Project",
    "ENVIRONMENT": "development"
  }
}
```

### Application Environment

Set in `.env` file (gitignored):

```env
PROJECT_NAME="My API"
DATABASE_URL="postgresql://user:pass@localhost/db"
SECRET_KEY="your-secret-key"
```

Loaded via `pydantic-settings`:

```python
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "Default Name"
    DATABASE_URL: str = "sqlite:///./app.db"
    
    class Config:
        env_file = ".env"
```

---

## Dependencies

### System Dependencies

Installed in Containerfile:
- `ca-certificates` - SSL/TLS certificates
- `curl` - HTTP client
- `git` - Version control
- `jq` - JSON processor
- `less` - Pager
- `man-db` - Man page system
- `ripgrep` - Fast grep alternative
- `shellcheck` - Shell script linter
- `tar` - Archive utility
- `unzip` - ZIP extraction

### Binary Tools

Installed with checksum verification:
- **task** - Task runner (v3.49.1)
- **gitleaks** - Secret scanner (v8.30.0)

### Python Tools

Installed via pip:
- **pre-commit** - Git hook manager (v4.2.0)
- **uv** - Fast Python package installer (v0.8.13)

### Python Dependencies

Managed via uv and locked in `uv.lock`:
- **Runtime:** Listed in `[project.dependencies]`
- **Development:** Listed in `[project.optional-dependencies.dev]`

---

## Lifecycle Hooks

### Container Lifecycle

1. **Build time** - Containerfile execution
2. **Create time** - `postCreateCommand` execution
3. **Start time** - Container starts
4. **Attach time** - VSCode connects

### postCreateCommand Sequence

```bash
bash scripts/install_runtime_docs.sh man/man7 && \
task init && \
pre-commit install
```

**Steps:**
1. Install man pages
2. Initialize development environment (uv sync)
3. Install pre-commit hooks

### Pre-commit Hooks

Run automatically on `git commit`:
1. `ruff format` - Auto-format code
2. `ruff check` - Lint code
3. `mypy` - Type check
4. `trailing-whitespace` - Remove trailing whitespace
5. `end-of-file-fixer` - Ensure newline at EOF

---

## Task Contract

All scenarios must implement these tasks:

### task init

**Purpose:** Initialize development environment

**Actions:**
- Create virtual environment (.venv)
- Install dependencies (uv sync)
- Set up database (if applicable)

**Exit code:** 0 on success, non-zero on failure

### task lint

**Purpose:** Run code quality checks

**Checks:**
- Code formatting (ruff format --check)
- Linting (ruff check)
- Type checking (mypy)

**Exit code:** 0 if all checks pass, non-zero if any fail

### task test

**Purpose:** Run test suite

**Actions:**
- Run pytest with coverage
- Generate coverage report

**Exit code:** 0 if all tests pass, non-zero if any fail

### task scan

**Purpose:** Run security scans

**Scans:**
- Dependency vulnerabilities (pip-audit)
- Secret detection (gitleaks)
- Container scanning (if applicable)

**Exit code:** 0 if no issues, non-zero if issues found

### task ci

**Purpose:** Run complete CI pipeline

**Sequence:** lint → test → scan

**Exit code:** 0 if all pass, non-zero if any fail

### task dev (optional)

**Purpose:** Start development server

**Actions:**
- Start application with hot reload
- Bind to 0.0.0.0:8000 (or configured port)

**Exit:** Ctrl+C to stop

---

## Ports

### Standard Ports

- **8000** - API server (FastAPI/Uvicorn)
- **5432** - PostgreSQL (if using database)
- **6379** - Redis (if using cache)

### Port Forwarding

Configured in `devcontainer.json`:

```json
{
  "forwardPorts": [8000],
  "portsAttributes": {
    "8000": {
      "label": "API Server",
      "onAutoForward": "notify"
    }
  }
}
```

---

## VSCode Integration

### Settings

Applied automatically in container:
- Python interpreter path
- Formatting on save
- Test discovery
- Type checking mode

### Extensions

Installed automatically:
- `ms-python.python` - Python language support
- `charliermarsh.ruff` - Ruff linter
- `ms-python.mypy-type-checker` - MyPy integration

### Workspace Folder

Must be opened manually after container starts:
1. `File` → `Open Folder`
2. Navigate to `/workspaces/<scenario-name>`

---

## Security

### Scanning Policy

Defined in `security-scan-policy.toml`:
- Fail on CRITICAL severity
- Allow advisories with no fix available
- Accepted advisories with expiration dates

### Secret Detection

Gitleaks scans for:
- API keys
- Passwords
- Private keys
- Tokens

### Dependency Scanning

pip-audit checks for:
- Known vulnerabilities (CVEs)
- Security advisories (GHSAs)

---

## Customization Points

### Extend Dependencies

Edit `pyproject.toml`:

```toml
[project.dependencies]
fastapi = ">=0.115.0"
my-new-dependency = ">=1.0.0"
```

Then: `uv sync`

### Add System Packages

Edit `.devcontainer/Containerfile`:

```dockerfile
RUN apt-get update && \
    apt-get install -y my-system-package
```

Then: Rebuild container

### Modify Tasks

Edit `tasks.py`:

```python
def my_custom_task():
    """My custom task."""
    print("Running custom task...")
    # Implementation
```

Add to `Taskfile.yml`:

```yaml
tasks:
  custom:
    desc: My custom task
    cmds:
      - python tasks.py custom
```

---

## Related Documentation

- [Getting Started Tutorial](../tutorials/getting-started.md)
- [Standalone Usage How-To](../how-to/use-scenarios-standalone.md)
- [Scenario Architecture](../explanation/scenario-architecture.md)
- [Troubleshooting Guide](../how-to/troubleshooting.md)
