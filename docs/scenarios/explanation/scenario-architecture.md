# Explanation: Scenario Architecture

**Understanding-oriented** | **Conceptual** | **Background**

This document explains the design principles, architecture, and rationale behind polyglot-devcontainers scenarios.

---

## What Are Scenarios?

Scenarios are **self-contained, ready-to-use development environments** that combine:
- A specific technology stack (e.g., Python + FastAPI)
- Security best practices
- Development tooling
- Testing infrastructure
- Documentation

**Purpose:** Enable rapid learning and development without setup friction.

---

## Design Principles

### 1. Self-Contained by Default

**Principle:** Scenarios should work standalone without external dependencies.

**Why:** Users should be able to copy a scenario and have it work immediately, without hunting for missing files or configuration.

**Implementation:**
- All required files bundled in scenario directory
- No hard dependencies on repository structure
- Fallback patterns for optional integrations

**Example:**
```python
# REPO_ROOT with fallback
try:
    REPO_ROOT = next(
        parent for parent in Path(__file__).resolve().parents 
        if (parent / "AGENTS.md").exists()
    )
except StopIteration:
    REPO_ROOT = ROOT  # Fallback to scenario directory
```

### 2. Container-First Workflow

**Principle:** Development happens inside containers, not on host machines.

**Why:**
- Consistent environment across platforms (macOS, Windows, Linux)
- No "works on my machine" problems
- Reproducible builds
- Isolation from host system

**Implementation:**
- Devcontainer specification
- Official base images
- Pinned tool versions
- Locked dependencies

### 3. Security by Default

**Principle:** Security is integrated, not optional.

**Why:**
- Security should be easy to do right
- Developers shouldn't need to be security experts
- Vulnerabilities should be caught early

**Implementation:**
- Dependency scanning (pip-audit)
- Secret detection (gitleaks)
- Security policy enforcement
- Pre-commit hooks

### 4. Task Contract

**Principle:** All scenarios expose the same task interface.

**Why:**
- Consistent user experience across scenarios
- Predictable workflow
- Easy to switch between scenarios
- CI/CD integration

**Contract:**
```bash
task init   # Initialize environment
task lint   # Check code quality
task test   # Run tests
task scan   # Security scans
task ci     # Complete pipeline
```

### 5. Progressive Disclosure

**Principle:** Simple things should be simple, complex things should be possible.

**Why:**
- Beginners can get started quickly
- Experts can customize deeply
- Learning curve is gradual

**Implementation:**
- `init.sh` for simple usage
- Manual steps for control
- Extensible task system
- Clear documentation layers

---

## Architecture Layers

### Layer 1: Container Image

**Base:** Official devcontainer images (e.g., `mcr.microsoft.com/devcontainers/python`)

**Additions:**
- System dependencies (git, curl, etc.)
- Binary tools (task, gitleaks)
- Python tooling (uv, pre-commit)

**Characteristics:**
- Immutable
- Versioned
- Cached for performance
- Checksum-verified binaries

### Layer 2: Development Environment

**Created at runtime:**
- Virtual environment (.venv)
- Installed dependencies
- Pre-commit hooks
- Git repository

**Characteristics:**
- Mutable
- User-specific
- Reproducible via uv.lock
- Isolated from host

### Layer 3: Application Code

**User's work:**
- Source code (src/)
- Tests (tests/)
- Configuration
- Documentation

**Characteristics:**
- Version controlled
- Portable
- Testable
- Deployable

---

## Dependency Management

### Philosophy

**Principle:** Dependencies should be explicit, locked, and verified.

**Why:**
- Reproducibility across machines and time
- Security (know exactly what you're running)
- Debugging (consistent versions)

### Levels of Dependencies

#### 1. System Dependencies

**Managed by:** Containerfile (apt-get)

**Examples:** git, curl, ca-certificates

**Pinning:** OS package versions

#### 2. Binary Tools

**Managed by:** Containerfile (direct download)

**Examples:** task, gitleaks

**Pinning:** Explicit version + checksum verification

#### 3. Python Tools

**Managed by:** Containerfile (pip install)

**Examples:** pre-commit, uv

**Pinning:** Explicit version

#### 4. Python Dependencies

**Managed by:** uv + uv.lock

**Examples:** fastapi, pytest, ruff

**Pinning:** uv.lock (complete dependency graph)

---

## Portability Strategy

### Problem

Scenarios need to work in two modes:
1. **Repo-integrated:** Inside polyglot-devcontainers repository
2. **Standalone:** Copied outside repository

### Solution: Hybrid Architecture

**Components:**

1. **Bundled Dependencies**
   - security-scan-policy.toml
   - scripts/evaluate_python_audit_policy.py
   - Bundled in each scenario

2. **Fallback Patterns**
   ```python
   try:
       REPO_ROOT = find_repo_root()
   except StopIteration:
       REPO_ROOT = ROOT  # Use scenario directory
   ```

3. **Automation Script**
   - init.sh handles setup
   - Works without script (self-contained)
   - Better UX with script

**Trade-offs:**
- ✅ Works in both modes
- ✅ No breaking changes
- ❌ Some duplication (bundled files)
- ❌ Manual sync needed for shared files

---

## Security Architecture

### Defense in Depth

Multiple layers of security checks:

1. **Build Time**
   - Checksum verification of binaries
   - Official base images
   - Minimal attack surface

2. **Development Time**
   - Pre-commit hooks (prevent bad commits)
   - Linting (catch bugs early)
   - Type checking (prevent type errors)

3. **Test Time**
   - Dependency scanning (pip-audit)
   - Secret detection (gitleaks)
   - Test coverage

4. **Deploy Time**
   - CI pipeline (task ci)
   - Security policy enforcement
   - Container scanning (future)

### Security Policy

**Configurable via security-scan-policy.toml:**

```toml
[policy]
fail_on_severity = ["CRITICAL"]  # Block critical vulnerabilities
allow_no_fix = true              # Allow if no fix available

[[policy.accepted_advisories]]
id = "GHSA-xxxx"                 # Explicitly accept specific advisories
reason = "False positive"
expires = "2026-12-31"           # Time-bound acceptance
```

**Philosophy:**
- Fail fast on critical issues
- Pragmatic about unfixable issues
- Explicit risk acceptance
- Time-bound exceptions

---

## Initialization Flow

### Automated (init.sh)

```
User runs ./init.sh
    ↓
Clean host artifacts (.venv, __pycache__)
    ↓
Verify bundled dependencies exist
    ↓
Initialize git repository (if needed)
    ↓
Start DevPod container
    ↓
Container builds (or uses cache)
    ↓
postCreateCommand runs:
  - Install man pages
  - task init (uv sync)
  - pre-commit install
    ↓
VSCode opens
    ↓
User opens workspace folder
    ↓
Ready to develop
```

### Manual

```
User copies scenario
    ↓
User cleans artifacts manually
    ↓
User initializes git manually
    ↓
User runs: devpod up .
    ↓
[Same as automated from here]
```

---

## Task System Architecture

### Design

**Two-layer architecture:**

1. **Taskfile.yml** - Declarative task definitions
2. **tasks.py** - Python implementation

**Why two layers?**
- Taskfile.yml: Simple, readable, IDE-friendly
- tasks.py: Complex logic, error handling, flexibility

### Task Implementation

```python
# tasks.py structure
ROOT = Path(__file__).parent
REPO_ROOT = find_repo_root_with_fallback()
PYTHON = ROOT / ".venv" / "bin" / "python"

def init():
    """Initialize development environment."""
    run([UV, "sync", "--frozen", "--extra", "dev"])

def lint():
    """Run code quality checks."""
    run([PYTHON, "-m", "ruff", "format", "--check", "src", "tests"])
    run([PYTHON, "-m", "ruff", "check", "src", "tests"])
    run([PYTHON, "-m", "mypy", "src"])

def ci():
    """Run complete CI pipeline."""
    lint()
    test()
    scan()
```

**Benefits:**
- Consistent interface across scenarios
- Easy to extend
- Testable
- Portable

---

## VSCode Integration

### Why VSCode?

- Industry standard for devcontainers
- Rich extension ecosystem
- Good remote development support
- Free and open source

### Integration Points

1. **devcontainer.json** - Configuration
2. **Extensions** - Auto-installed
3. **Settings** - Pre-configured
4. **Tasks** - Integrated with task runner

### Limitations

**Current:**
- Workspace folder not auto-opened (manual step required)
- Terminal starts in home directory (must cd to workspace)

**Future improvements:**
- Auto-open workspace folder
- Terminal in correct directory
- Better progress feedback

---

## Performance Considerations

### Container Build

**Optimization strategies:**
- Layer caching (Docker/Podman)
- Minimal base images
- Parallel downloads
- Checksum verification (security + cache validation)

**Typical times:**
- First build: 2-3 minutes
- Cached build: 10-30 seconds

### Dependency Installation

**Optimization strategies:**
- uv (fast Python package installer)
- Locked dependencies (uv.lock)
- Binary wheels (no compilation)
- Parallel downloads

**Typical times:**
- First install: 30-60 seconds
- Cached install: 5-10 seconds

### Development Loop

**Hot reload:**
- Code changes: Instant
- Dependency changes: 5-10 seconds (uv sync)
- Container changes: 10-30 seconds (rebuild)

---

## Extensibility Points

### Add New Scenario

1. Copy existing scenario as template
2. Modify dependencies (pyproject.toml)
3. Update application code (src/)
4. Update tests (tests/)
5. Update README
6. Test standalone usage

### Customize Existing Scenario

1. Fork or copy scenario
2. Modify as needed
3. Keep init.sh and task contract
4. Update documentation

### Add New Task

1. Add function to tasks.py
2. Add entry to Taskfile.yml
3. Document in README
4. Test in container

### Extend Container

1. Modify Containerfile
2. Add system dependencies
3. Add binary tools
4. Rebuild container

---

## Trade-offs and Decisions

### Container vs Native

**Decision:** Container-first

**Trade-offs:**
- ✅ Consistency, reproducibility
- ✅ Isolation, security
- ❌ Startup time
- ❌ Resource usage

**Rationale:** Consistency and reproducibility outweigh performance costs.

### uv vs pip

**Decision:** uv for package management

**Trade-offs:**
- ✅ 10-100x faster
- ✅ Better dependency resolution
- ❌ Newer tool (less mature)
- ❌ Different CLI

**Rationale:** Speed and better resolution worth the learning curve.

### Bundled vs Shared Dependencies

**Decision:** Bundled (Hybrid Option 5)

**Trade-offs:**
- ✅ Standalone scenarios work
- ✅ No external dependencies
- ❌ File duplication
- ❌ Manual sync needed

**Rationale:** Portability and user experience over DRY principle.

### Task vs Make vs Just

**Decision:** Task (go-task)

**Trade-offs:**
- ✅ Cross-platform
- ✅ YAML syntax
- ✅ Good documentation
- ❌ Binary dependency
- ❌ Less familiar than Make

**Rationale:** Cross-platform support and modern syntax.

---

## Future Evolution

### Near-term (Next 3 months)

- Code formatting in templates (ship lint-clean)
- CI validation of standalone usage
- More scenarios (Node.js, Java, Rust)
- Improved VSCode integration

### Medium-term (3-6 months)

- Scenario registry (central catalog)
- Automated scenario testing
- Performance optimizations
- Better error messages

### Long-term (6-12 months)

- DevPod scenario provider
- VSCode extension
- Scenario templates
- Multi-language scenarios

---

## Related Documentation

- [Getting Started Tutorial](../tutorials/getting-started.md) - First-time usage
- [Standalone Usage How-To](../how-to/use-scenarios-standalone.md) - Standalone setup
- [Scenario Structure Reference](../reference/scenario-structure.md) - Complete reference
- [KB-2026-009](../../../.kbriefs/KB-2026-009-scenario-adoption-barriers.md) - Design space analysis
