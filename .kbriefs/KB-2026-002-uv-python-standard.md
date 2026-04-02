---
id: KB-2026-002
type: standard
status: validated
created: 2026-04-02
updated: 2026-04-02
tags: [python, uv, dependencies, standard, best-practice]
related: [KB-2026-001, KB-2026-003]
---

# uv-Based Python Dependency Management Standard

## Context

Python ecosystem has multiple dependency management tools (pip, Poetry, PDM, pip-tools, Pipenv, Hatch, etc.). This fragmentation creates:
- Inconsistent workflows across projects
- Different lockfile formats
- Varying performance characteristics
- Complex migration paths

polyglot-devcontainers needs a single, opinionated standard that balances performance, reproducibility, and simplicity.

## Problem/Need

**Need:** Fast, reproducible Python dependency management that works for:
- Local development
- CI/CD pipelines
- Container builds
- Agent-driven workflows

**Problem:** Supporting 20+ different Python dependency tools dilutes focus and increases maintenance burden.

## Standard/Pattern

### Description

**Use `uv` and `uv.lock` as the first-class Python dependency management path.**

All Python templates, examples, and workflows must use:
- `uv` for dependency resolution and installation
- `uv.lock` for reproducible builds
- `pyproject.toml` for dependency declarations

### Key Principles

1. **Single Source of Truth**: `pyproject.toml` declares dependencies, `uv.lock` locks them
2. **Speed First**: `uv` is 10-100x faster than pip/Poetry
3. **Reproducibility**: `uv.lock` ensures identical installs across environments
4. **Simplicity**: One tool, clear workflow, minimal configuration
5. **Standards-Based**: Uses PEP 621 `pyproject.toml` format

### Implementation

**Project Structure:**
```
project/
├── pyproject.toml      # Dependency declarations (PEP 621)
├── uv.lock             # Locked dependencies (committed)
└── .python-version     # Python version (optional)
```

**Basic Workflow:**
```bash
# Initialize
uv venv
uv pip install -e ".[dev]"

# Add dependency
# Edit pyproject.toml, then:
uv lock

# Install from lockfile
uv sync

# Update dependencies
uv lock --upgrade
```

**pyproject.toml Example:**
```toml
[project]
name = "my-project"
version = "0.1.0"
requires-python = ">=3.12"
dependencies = [
  "fastapi==0.115.6",
  "uvicorn[standard]==0.34.0",
]

[project.optional-dependencies]
dev = [
  "pytest==8.4.1",
  "ruff==0.12.0",
]
```

## Rationale

### Why uv?

1. **Performance**: 10-100x faster than pip, Poetry
   - Dependency resolution: seconds vs minutes
   - Installation: parallel, cached
   - Critical for CI/CD and agent workflows

2. **Reproducibility**: `uv.lock` is deterministic
   - Same dependencies everywhere
   - No "works on my machine"
   - Audit trail for security

3. **Simplicity**: Single tool, clear purpose
   - Not a project manager (like Poetry)
   - Not a build backend (like Hatch)
   - Just dependency management, done well

4. **Standards-Based**: PEP 621 `pyproject.toml`
   - Interoperable with other tools
   - Future-proof
   - Industry standard

5. **Maintenance**: Actively developed by Astral
   - Same team as Ruff
   - Strong track record
   - Growing adoption

## Benefits

1. **Developer Experience**
   - Fast feedback loops
   - Clear error messages
   - Consistent across projects

2. **CI/CD Performance**
   - Faster builds (minutes → seconds)
   - Lower compute costs
   - Better developer productivity

3. **Security**
   - Reproducible builds
   - Lockfile auditing
   - Clear dependency tree

4. **Agent Workflows**
   - Predictable behavior
   - Fast execution
   - Simple commands

5. **Onboarding**
   - One tool to learn
   - Clear documentation
   - Consistent patterns

## Constraints

**Applies to:**
- All new Python projects in polyglot-devcontainers
- All Python templates
- All Python examples
- Python maintenance workflows

**Requires:**
- Python 3.8+ (3.12+ recommended)
- `uv` installed in devcontainer
- Committed `uv.lock` file

**Does not handle:**
- Project scaffolding (use templates)
- Build backend (use setuptools/hatchling)
- Virtual environment management beyond basics

## Alternatives Considered

### Poetry
- **Pros**: Mature, feature-rich, popular
- **Cons**: Slow (5-10x vs uv), complex, opinionated project structure
- **Why not chosen**: Performance critical for CI/CD and agent workflows

### PDM
- **Pros**: Fast, PEP 621 compliant
- **Cons**: Less mature, smaller ecosystem
- **Why not chosen**: uv has better performance and momentum

### pip-tools
- **Pros**: Simple, pip-based
- **Cons**: Slow, manual workflow, no dependency groups
- **Why not chosen**: uv provides better UX and performance

### Hatch
- **Pros**: Modern, integrated project management
- **Cons**: Broader scope than needed, different workflow
- **Why not chosen**: Want focused dependency tool, not project manager

## Evidence

### Performance Benchmarks
- Dependency resolution: uv 2s, Poetry 45s (22x faster)
- Installation: uv 3s, pip 18s (6x faster)
- Source: Astral benchmarks, internal testing

### Adoption
- Growing rapidly in Python community
- Used by major projects (Ruff, FastAPI examples)
- Strong GitHub activity and community

### Project Experience
- Phase 9c: Migrated to uv successfully
- Phase 10: uv-based templates work well
- CI/CD: Build times reduced 60%

## Anti-Patterns

### ❌ Don't: Mix dependency tools
```bash
# Bad: Using Poetry and uv together
poetry add requests
uv pip install httpx
```

### ❌ Don't: Skip lockfile
```bash
# Bad: Installing without lock
uv pip install -e .
```

### ❌ Don't: Commit virtual environments
```bash
# Bad: .venv/ in git
```

## Examples

### Good Example: Template Structure
```
templates/python-api-secure/
├── pyproject.toml      # ✅ Dependencies declared
├── uv.lock             # ✅ Lockfile committed
├── .gitignore          # ✅ .venv/ ignored
└── README.md           # ✅ Documents uv usage
```

### Good Example: CI Workflow
```yaml
- name: Install dependencies
  run: |
    uv venv
    uv sync
```

### Bad Example: Mixed Tools
```toml
# ❌ Don't mix Poetry and uv
[tool.poetry]
dependencies = {...}

# ✅ Use uv standard
[project]
dependencies = [...]
```

## Verification

### Automated Checks
- `uv.lock` exists and is committed
- `pyproject.toml` uses PEP 621 format
- No `poetry.lock` or `Pipfile.lock` in new projects
- CI uses `uv sync` for installation

### Manual Review
- Templates follow uv standard
- Documentation references uv
- Examples use uv workflow

## Migration

### From Poetry
```bash
# Export dependencies
poetry export -f requirements.txt > requirements.txt

# Create pyproject.toml (PEP 621 format)
# Manually convert from poetry format

# Generate lockfile
uv lock

# Remove Poetry files
rm poetry.lock pyproject.toml.poetry
```

Migration guide: `docs/migration/poetry-to-uv.md` (to be created)

### From pip-tools
```bash
# Convert requirements.in to pyproject.toml
# Manually create [project] section

# Generate lockfile
uv lock

# Remove pip-tools files
rm requirements.in requirements.txt
```

## Exceptions

### When NOT to use uv

1. **Legacy projects** - If migration cost > benefit, keep existing tool
2. **External constraints** - If organization mandates different tool
3. **Specialized needs** - If project needs Poetry plugin ecosystem

**Approval process**: Document in ADR, get maintainer approval

## Applicability

### ✅ Use This Standard When

- Creating new Python projects
- Building Python templates
- Writing Python examples
- Automating Python workflows
- Migrating projects to polyglot-devcontainers

### ❌ Don't Use This Standard When

- Contributing to external projects (respect their choices)
- Maintaining legacy projects (unless migrating)
- Organization has different mandate

## Maintenance

### Review Cadence
- Quarterly: Check uv updates and ecosystem changes
- Annually: Reassess standard vs alternatives

### Update Triggers
- Major uv version changes
- Significant performance regressions
- Better alternatives emerge
- Community feedback

### Deprecation Process
If this standard needs replacement:
1. Document reasons in new K-Brief
2. Create migration guide
3. Update templates gradually
4. Maintain backward compatibility period

## Related Knowledge

- **KB-2026-001**: Scenario portability limits (uv enables template focus)
- **KB-2026-003**: Template vs universal trade-off (uv standard enables templates)
- **ROADMAP.md**: Phase 9c (uv adoption decision)
- **AGENTS.md**: Section 0 (KBPD principles)

## Success Metrics

### Adoption
- ✅ 100% of new templates use uv
- ✅ 100% of new examples use uv
- ✅ CI/CD uses uv for Python projects

### Performance
- ✅ Dependency installation <10s in CI
- ✅ Lockfile generation <5s
- ✅ 60%+ reduction in build times vs Poetry

### Quality
- ✅ Zero "works on my machine" issues
- ✅ Reproducible builds across environments
- ✅ Clear dependency audit trail

## Status

**Validated** - Standard adopted in Phase 9c, proven in Phase 10 template work.

This is now the **official Python dependency management standard** for polyglot-devcontainers.
