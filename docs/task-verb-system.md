# Task Verb System

**Version:** 1.0  
**Status:** Implemented (Phase 1)  
**Last Updated:** 2026-04-06

---

## Overview

The Task Verb System provides a **unified, polyglot-consistent interface** for common development workflows across all scenarios in polyglot-devcontainers.

**Core Principles:**
1. **Check/Fix Pairs** - Every check verb has a corresponding fix verb
2. **Polyglot Consistency** - Same verbs work across all languages
3. **Progressive Disclosure** - Check first, fix if needed
4. **Discoverable** - `task --list` shows clear patterns
5. **Safe by Default** - Checks are read-only, fixes require explicit action

---

## Task Verb Reference

### Core Workflow

| Verb | Description | Type | Safe to Auto-Run |
|------|-------------|------|------------------|
| `task init` | Initialize development environment | Setup | Yes |
| `task ci` | Run all checks (init + lint + test + scan) | Check | Yes |

---

### Check Verbs (Read-Only)

Check verbs **never modify code**. They fail if issues are found.

| Verb | Description | What It Checks | Exit Code |
|------|-------------|----------------|-----------|
| `task lint` | Check code quality | Format, style, types | 0 = pass, 1 = issues found |
| `task test` | Run test suite | Unit tests, coverage | 0 = pass, 1 = tests failed |
| `task scan` | Check security | Dependencies, secrets | 0 = pass, 1 = vulnerabilities |

**Usage:**
```bash
# Check code quality
task lint

# If it fails, you have two options:
# 1. Fix manually
# 2. Use the fix verb (see below)
```

---

### Fix Verbs (Write)

Fix verbs **modify code** to resolve issues automatically.

| Verb | Description | What It Fixes | Corresponding Check |
|------|-------------|---------------|---------------------|
| `task format` | Auto-fix code formatting and style | Formatting, auto-fixable style issues | `task lint` |

**Usage:**
```bash
# Fix code formatting issues
task format

# Then verify
task lint
```

**What `task format` does (Python):**
1. Runs `ruff check --fix` (auto-fix style issues)
2. Runs `ruff format` (format code)

---

### Development Tasks

| Verb | Description | Scenario Type |
|------|-------------|---------------|
| `task dev` | Run development server with hot reload | API scenarios only |

**Usage:**
```bash
# Start development server (API scenarios)
task dev

# Access at http://localhost:8000/api/docs
```

---

### Dependency Management

| Verb | Description | Type |
|------|-------------|------|
| `task deps:inventory` | List all dependencies with current versions | Read-only |
| `task deps:plan` | Plan dependency updates (show available upgrades) | Read-only |
| `task deps:report` | Generate comprehensive dependency report | Read-only |
| `task upgrade` | Upgrade dependencies (interactive) and verify with CI | Write |

**Usage:**
```bash
# See what dependencies can be upgraded
task deps:plan

# Upgrade dependencies interactively
task upgrade
```

---

## Workflow Examples

### Daily Development Workflow

```bash
# 1. Start fresh
task init

# 2. Make code changes
# ... edit files ...

# 3. Fix formatting
task format

# 4. Run all checks
task ci
```

---

### Fixing Lint Failures

```bash
# Run checks
task lint
# ❌ Fails with formatting issues

# Auto-fix
task format

# Verify
task lint
# ✅ Passes
```

---

### Complete CI Workflow

```bash
# Run everything
task ci

# Equivalent to:
task init    # Install dependencies
task lint    # Check code quality
task test    # Run tests
task scan    # Check security
```

---

## Language-Specific Implementations

### Python

**Check verbs:**
- `task lint` → `ruff format --check` + `ruff check` + `mypy`
- `task test` → `pytest --cov`
- `task scan` → `pip-audit` + `gitleaks`

**Fix verbs:**
- `task format` → `ruff check --fix` + `ruff format`

---

### Node/TypeScript (Future)

**Check verbs:**
- `task lint` → `prettier --check` + `eslint`
- `task test` → `jest` or `vitest`
- `task scan` → `npm audit` + `gitleaks`

**Fix verbs:**
- `task format` → `prettier --write` + `eslint --fix`

---

### Java (Future)

**Check verbs:**
- `task lint` → `mvn fmt:check` + `checkstyle`
- `task test` → `mvn test`
- `task scan` → `mvn dependency-check` + `gitleaks`

**Fix verbs:**
- `task format` → `mvn fmt:format`

---

## Future Enhancements (Phase 2+)

### Phase 2: Interactive Security Fixes

```bash
# Interactive vulnerability remediation
task scan:fix

# Shows:
# Found 5 vulnerabilities with fixes available:
# 1. python-jose 3.3.0 → 3.4.0 (fixes PYSEC-2024-232, PYSEC-2024-233)
# Apply fixes? [1-5/all/none/quit]:
```

**Features:**
- Interactive prompts for each fix
- Automatic rollback on test failures
- Batch processing with safety
- Clear feedback at each step

---

### Phase 3: Unified Fix Command

```bash
# Fix all fixable issues
task fix

# Equivalent to:
task format      # Fix formatting
task scan:fix    # Fix security (interactive)
```

---

## Design Decisions

### Why Check/Fix Pairs?

**Problem:** Users had to know language-specific commands
- Python: `ruff format`, `uv add`
- Node: `prettier --write`, `npm update`
- Java: `mvn fmt:format`, `mvn versions:use-latest-versions`

**Solution:** Unified verbs across all languages
- `task format` works everywhere
- Same UX, different implementations
- Polyglot consistency

---

### Why Separate Check and Fix?

**Safety:** Checks are read-only by default
- CI pipelines run checks only
- Developers explicitly choose to fix
- No accidental modifications

**Clarity:** Clear intent
- `task lint` → "Show me issues"
- `task format` → "Fix issues for me"

---

### Why Not `task lint --fix`?

**Discoverability:** Separate verbs are more discoverable
- `task --list` shows both check and fix
- Clear separation in documentation
- Easier to remember

**Consistency:** Matches existing patterns
- `task scan` (check) vs `task scan:fix` (fix)
- Uniform across all verbs

---

## Migration Guide

### For Existing Scenarios

**Before:**
```bash
# Manual formatting
.venv/bin/python -m ruff format src tests tasks.py

# Manual dependency updates
uv add "package>=version"
```

**After:**
```bash
# Unified formatting
task format

# Interactive dependency updates (Phase 2)
task scan:fix
```

---

### For New Scenarios

**Required tasks:**
- `task init` - Initialize environment
- `task lint` - Check code quality
- `task test` - Run tests
- `task scan` - Check security
- `task format` - Auto-fix formatting
- `task ci` - Run all checks

**Optional tasks:**
- `task dev` - Development server (API scenarios)
- `task deps:*` - Dependency management
- `task upgrade` - Upgrade dependencies

---

## Related Documentation

- **KB-2026-009:** Scenario adoption barriers (task verb design rationale)
- **AGENTS.md:** Task contract specification
- **docs/scenarios/reference/scenario-structure.md:** Task system architecture

---

## Status

**Phase 1 (Implemented):**
- ✅ Check verbs (lint, test, scan, ci)
- ✅ Fix verb (format)
- ✅ Development tasks (init, dev)
- ✅ Dependency management (deps:*, upgrade)

**Phase 2 (Planned):**
- ⏳ Interactive security fixes (scan:fix)
- ⏳ Batch fix workflow
- ⏳ Rollback on test failures

**Phase 3 (Future):**
- ⏳ Unified fix command (task fix)
- ⏳ Smart detection (only run what's needed)
- ⏳ Cross-language consistency validation
