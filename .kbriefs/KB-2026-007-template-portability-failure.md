---
id: KB-2026-007
type: failure-mode
status: validated
created: 2026-04-03
updated: 2026-04-03
tags: [templates, portability, tasks.py, repo-structure, standalone, initialization]
related: [KB-2026-001]
---

# Template Portability Failure: REPO_ROOT Dependency on Repository Structure

## Context

Templates in `polyglot-devcontainers` are designed to be reusable development environments. However, when templates are copied outside the repository structure for standalone use or testing, the `postCreateCommand` fails during container initialization with a `StopIteration` error in `tasks.py`.

This K-Brief documents the failure mode, analyzes the root cause, and provides solutions for template portability.

**Background:**
- Templates live in `templates/` directory of polyglot-devcontainers repo
- Each template has a `tasks.py` script for initialization and workflow automation
- Some templates depend on repository-level files (e.g., `security-scan-policy.toml`)
- Templates are intended to be both repo-integrated and potentially standalone

## System/Component

**Affected templates:**
- `templates/python-secure/` - Uses REPO_ROOT pattern
- `templates/python-api-secure/` - Uses REPO_ROOT pattern

**Not affected:**
- `templates/python-node-secure/` - Uses ROOT-relative pattern (standalone-compatible)

**Specific implementation:**

`@/Users/chrissenanayake/dev/polyglot-devcontainers/templates/python-api-secure/tasks.py:18-22`
```python
REPO_ROOT = next(
    parent for parent in Path(__file__).resolve().parents if (parent / "AGENTS.md").exists()
)
PYTHON_AUDIT_POLICY = REPO_ROOT / "security-scan-policy.toml"
PYTHON_AUDIT_EVALUATOR = REPO_ROOT / "scripts" / "evaluate_python_audit_policy.py"
```

**Dependency chain:**
```
tasks.py → REPO_ROOT → AGENTS.md (repo marker)
         → PYTHON_AUDIT_POLICY → security-scan-policy.toml
         → PYTHON_AUDIT_EVALUATOR → scripts/evaluate_python_audit_policy.py
```

## Failure Description

### Symptoms

Container builds successfully, but `postCreateCommand` fails during initialization:

```
00:45:56 warn task: [init] python tasks.py init
00:45:56 warn Traceback (most recent call last):
00:45:56 warn File "/workspaces/python-api-secure/tasks.py", line 18, in <module>
00:45:56 warn REPO_ROOT = next(
00:45:56 warn ^^^^^
00:45:56 warn StopIteration
00:45:56 warn task: Failed to run task "init": exit status 1
00:45:56 info lifecycle hooks: failed to run: bash scripts/install_runtime_docs.sh man/man7 && task init && pre-commit install, error: exit status 201
```

**User experience:**
- Container image builds successfully ✅
- Checksum verification passes ✅
- Binary installation succeeds ✅
- Container starts ✅
- `postCreateCommand` begins execution ✅
- `tasks.py` import fails ❌
- Development environment not initialized ❌

### Failure Scenario

**Trigger conditions:**
1. Copy template to standalone directory outside repo
2. Start devcontainer with `devpod up .`
3. Container builds successfully
4. `postCreateCommand` runs: `task init && pre-commit install`
5. Task runner executes `python tasks.py init`
6. Python imports `tasks.py` module
7. Module-level code executes `REPO_ROOT = next(...)`
8. No parent directory contains `AGENTS.md`
9. `next()` raises `StopIteration`
10. Import fails, task fails, initialization fails

**Timeline:**
- 00:44:55 - Workspace creation starts
- 00:44:58 - Container build begins
- 00:45:11 - Checksum verification succeeds
- 00:45:24 - Container build completes
- 00:45:54 - `postCreateCommand` starts
- 00:45:56 - **Failure:** `tasks.py` import raises `StopIteration`

### Impact

**Severity: Medium**

- **Container builds**: ✅ Succeeds
- **Binary verification**: ✅ Succeeds
- **Development environment**: ❌ Not initialized
- **User workflow**: ❌ Blocked

**Blast radius:**
- Templates copied outside repository structure
- Standalone template usage
- Testing in isolated directories
- User projects based on templates

**Does not affect:**
- Templates used within repository structure
- Templates with ROOT-relative paths (python-node-secure)
- Container builds (only runtime initialization)

## Root Cause

### Primary Cause

**Hard-coded dependency on repository structure**

The `REPO_ROOT` discovery pattern assumes the template is located within the `polyglot-devcontainers` repository:

```python
REPO_ROOT = next(
    parent for parent in Path(__file__).resolve().parents if (parent / "AGENTS.md").exists()
)
```

**This pattern:**
1. Walks up parent directories from `tasks.py`
2. Looks for `AGENTS.md` as repository marker
3. Assumes it will find the marker
4. Raises `StopIteration` if not found

**When template is standalone:**
```
/some/standalone/directory/python-api-secure/
├── tasks.py          ← starts here
├── pyproject.toml
├── src/
└── tests/

# Walks up:
/some/standalone/directory/python-api-secure/  ← no AGENTS.md
/some/standalone/directory/                    ← no AGENTS.md
/some/standalone/                              ← no AGENTS.md
/some/                                         ← no AGENTS.md
/                                              ← no AGENTS.md

# Result: StopIteration (no parent has AGENTS.md)
```

### Contributing Factors

1. **Implicit repository assumption** - Code assumes repo context
2. **No fallback mechanism** - `next()` without default raises exception
3. **Module-level execution** - Runs during import, not during function call
4. **Missing standalone support** - No detection of standalone mode
5. **Inconsistent patterns** - Some templates use ROOT, others use REPO_ROOT

### Failure Mechanism

```
Template copied outside repo →
Container starts →
postCreateCommand runs →
Python imports tasks.py →
Module-level REPO_ROOT assignment executes →
Parent directory walk finds no AGENTS.md →
next() raises StopIteration →
Import fails →
Task fails →
Initialization blocked
```

## Evidence

### Incident Report

**Date:** 2026-04-03 00:45:56  
**Reporter:** User testing template in standalone directory  
**Environment:** DevPod with Podman, macOS

**Error log:**
```
00:45:56 warn Traceback (most recent call last):
00:45:56 warn File "/workspaces/python-api-secure/tasks.py", line 18, in <module>
00:45:56 warn REPO_ROOT = next(
00:45:56 warn ^^^^^
00:45:56 warn StopIteration
```

### Pattern Analysis

**Templates using REPO_ROOT pattern (affected):**

`templates/python-secure/tasks.py`:
```python
REPO_ROOT = next(
    parent for parent in Path(__file__).resolve().parents if (parent / "AGENTS.md").exists()
)
PYTHON_AUDIT_POLICY = REPO_ROOT / "security-scan-policy.toml"
PYTHON_AUDIT_EVALUATOR = REPO_ROOT / "scripts" / "evaluate_python_audit_policy.py"
```

`templates/python-api-secure/tasks.py`:
```python
REPO_ROOT = next(
    parent for parent in Path(__file__).resolve().parents if (parent / "AGENTS.md").exists()
)
PYTHON_AUDIT_POLICY = REPO_ROOT / "security-scan-policy.toml"
PYTHON_AUDIT_EVALUATOR = REPO_ROOT / "scripts" / "evaluate_python_audit_policy.py"
```

**Templates using ROOT-relative pattern (not affected):**

`templates/python-node-secure/tasks.py`:
```python
ROOT = Path(__file__).resolve().parent
PYTHON_AUDIT_POLICY = ROOT / "security-scan-policy.toml"
PYTHON_AUDIT_EVALUATOR = ROOT / "scripts" / "evaluate_python_audit_policy.py"
```

**Key difference:**
- REPO_ROOT pattern: Searches for repository root, fails if not found
- ROOT pattern: Uses template directory, always succeeds

### File Dependency Analysis

**Files referenced via REPO_ROOT:**
- `security-scan-policy.toml` - Python package audit policy
- `scripts/evaluate_python_audit_policy.py` - Policy evaluation script

**Repository structure:**
```
polyglot-devcontainers/
├── AGENTS.md                           ← REPO_ROOT marker
├── security-scan-policy.toml           ← Shared policy
├── scripts/
│   └── evaluate_python_audit_policy.py ← Shared script
└── templates/
    ├── python-secure/
    │   └── tasks.py                    ← Uses REPO_ROOT
    ├── python-api-secure/
    │   └── tasks.py                    ← Uses REPO_ROOT
    └── python-node-secure/
        ├── tasks.py                    ← Uses ROOT
        ├── security-scan-policy.toml   ← Local copy
        └── scripts/
            └── evaluate_python_audit_policy.py  ← Local copy
```

**Observation:** `python-node-secure` bundles required files locally, making it standalone-compatible.

## Reproduction

### Minimal Reproduction Case

```bash
# Copy template to standalone directory
mkdir -p /tmp/test-template
cp -r templates/python-api-secure /tmp/test-template/

# Try to start devcontainer
cd /tmp/test-template/python-api-secure
devpod up .

# Expected: Container builds, postCreateCommand fails with StopIteration
```

**Result:**
- Container build: ✅ Succeeds
- Checksum verification: ✅ Succeeds
- `postCreateCommand`: ❌ Fails with `StopIteration`

### Conditions Required

- Template copied outside `polyglot-devcontainers` repository
- No `AGENTS.md` in any parent directory
- `tasks.py` uses REPO_ROOT pattern
- `postCreateCommand` executes `task init` or similar

## Prevention

### Design Changes

**Solution 1: Fallback to ROOT (Recommended)**

Make REPO_ROOT discovery resilient with fallback:

```python
# Before (fails):
REPO_ROOT = next(
    parent for parent in Path(__file__).resolve().parents if (parent / "AGENTS.md").exists()
)

# After (resilient):
try:
    REPO_ROOT = next(
        parent for parent in Path(__file__).resolve().parents if (parent / "AGENTS.md").exists()
    )
except StopIteration:
    # Fallback for standalone usage
    REPO_ROOT = ROOT
```

**Why this works:**
- Tries to find repository root first
- Falls back to template directory if not in repo
- Works in both repo-integrated and standalone contexts
- No breaking changes for existing usage

**Solution 2: Bundle Required Files**

Copy shared files into template (like `python-node-secure`):

```bash
# In template directory:
templates/python-api-secure/
├── tasks.py
├── security-scan-policy.toml           ← Local copy
└── scripts/
    └── evaluate_python_audit_policy.py ← Local copy
```

Update `tasks.py`:
```python
# Use ROOT instead of REPO_ROOT
PYTHON_AUDIT_POLICY = ROOT / "security-scan-policy.toml"
PYTHON_AUDIT_EVALUATOR = ROOT / "scripts" / "evaluate_python_audit_policy.py"
```

**Trade-offs:**
- ✅ Fully standalone
- ✅ No repo dependency
- ❌ File duplication
- ❌ Sync burden (must update all copies)

**Solution 3: Provide Default Value**

Use `next()` with default:

```python
REPO_ROOT = next(
    (parent for parent in Path(__file__).resolve().parents if (parent / "AGENTS.md").exists()),
    ROOT  # Default to template directory
)
```

**Why this works:**
- Single-line change
- No try/except needed
- Same behavior as Solution 1

### Operational Controls

**1. Document template usage modes**

Add to template README:
```markdown
## Usage Modes

### Within Repository (Recommended)
```bash
cd polyglot-devcontainers/templates/python-api-secure
devpod up .
```

### Standalone (Requires setup)
Copy required files:
- `security-scan-policy.toml`
- `scripts/evaluate_python_audit_policy.py`
```

**2. Provide template initialization script**

```bash
#!/bin/bash
# scripts/init_standalone_template.sh
template_dir="$1"
cp security-scan-policy.toml "$template_dir/"
mkdir -p "$template_dir/scripts"
cp scripts/evaluate_python_audit_policy.py "$template_dir/scripts/"
```

**3. Add validation to tasks.py**

```python
if not PYTHON_AUDIT_POLICY.exists():
    print(f"ERROR: Required file not found: {PYTHON_AUDIT_POLICY}")
    print("If using template standalone, copy security-scan-policy.toml to template directory")
    sys.exit(1)
```

### Code Review Checklist

When adding new templates or modifying `tasks.py`:
- ✅ Does REPO_ROOT discovery have a fallback?
- ✅ Are required files bundled or documented?
- ✅ Does template work outside repository?
- ✅ Are file dependencies validated at runtime?
- ✅ Is usage documented in README?

## Detection

### Early Warning Signs

- Template copied to new location
- `devpod up` succeeds but postCreateCommand fails
- `StopIteration` error in tasks.py
- Error occurs during module import, not function execution

### Detection Methods

**Automated:**
- CI test: Copy template to temp directory and run `devpod up`
- Integration test: Test templates in isolated environments
- Linting: Check for `next()` without default in module-level code

**Manual:**
- Test template in standalone directory before release
- Review tasks.py for REPO_ROOT dependencies
- Verify required files are bundled or documented

**Debugging:**
```python
# Add to tasks.py for debugging
import sys
print(f"DEBUG: __file__ = {__file__}", file=sys.stderr)
print(f"DEBUG: ROOT = {ROOT}", file=sys.stderr)
try:
    print(f"DEBUG: REPO_ROOT = {REPO_ROOT}", file=sys.stderr)
except NameError:
    print(f"DEBUG: REPO_ROOT not set (StopIteration)", file=sys.stderr)
```

## Mitigation

### Immediate Response

When this failure occurs:

**Option 1: Use template within repository**
```bash
cd /path/to/polyglot-devcontainers/templates/python-api-secure
devpod up .
```

**Option 2: Copy required files**
```bash
# In standalone template directory
cp /path/to/polyglot-devcontainers/security-scan-policy.toml .
mkdir -p scripts
cp /path/to/polyglot-devcontainers/scripts/evaluate_python_audit_policy.py scripts/
```

**Option 3: Patch tasks.py**
```python
# Add fallback to tasks.py
try:
    REPO_ROOT = next(
        parent for parent in Path(__file__).resolve().parents if (parent / "AGENTS.md").exists()
    )
except StopIteration:
    REPO_ROOT = ROOT
```

### Recovery Procedure

**For users experiencing failure:**

1. **Identify the issue**
```bash
# Check if AGENTS.md exists in parent directories
find /path/to/template/.. -name "AGENTS.md" -type f
# If empty, template is standalone
```

2. **Choose recovery path**
   - Move template into repository structure, OR
   - Copy required files to template directory, OR
   - Patch tasks.py with fallback

3. **Retry initialization**
```bash
devpod up .
```

**For maintainers:**

1. Update affected templates with fallback pattern
2. Test templates in standalone mode
3. Document standalone usage requirements
4. Consider bundling required files

## Testing

### Test Cases

**Test 1: Repo-integrated usage**
```bash
cd polyglot-devcontainers/templates/python-api-secure
devpod up .
# Expected: Container builds, initialization succeeds
```

**Test 2: Standalone usage (before fix)**
```bash
mkdir /tmp/test && cp -r templates/python-api-secure /tmp/test/
cd /tmp/test/python-api-secure
devpod up .
# Expected: Container builds, initialization fails with StopIteration
```

**Test 3: Standalone usage (after fix)**
```bash
# Apply fallback fix to tasks.py
mkdir /tmp/test && cp -r templates/python-api-secure /tmp/test/
cd /tmp/test/python-api-secure
devpod up .
# Expected: Container builds, initialization succeeds
```

**Test 4: Validate file dependencies**
```bash
# After initialization
ls -la security-scan-policy.toml
ls -la scripts/evaluate_python_audit_policy.py
# Expected: Files exist (either from REPO_ROOT or ROOT)
```

### Validation Criteria

**Fix is successful if:**
- ✅ Template works within repository structure
- ✅ Template works in standalone directory
- ✅ Required files are accessible
- ✅ No StopIteration errors
- ✅ Initialization completes successfully

## Related Failure Modes

**Similar failures:**
- Any code using `next()` without default
- Hard-coded path assumptions
- Module-level code with external dependencies
- Repository structure dependencies

**Git Context Requirement:**

**Failure:** pre-commit install fails with "not a Git repository"

**Cause:** pre-commit requires git context to install hooks

**Error:**
```
An error has occurred: FatalError: git failed. Is it installed, and are you in a Git repository directory?
```

**Solution:** Initialize git repository before running pre-commit:
```bash
git init
git add .
git commit -m "Initial commit"
```

**Applicability:** Any tool that relies on git hooks or git context (pre-commit, husky, etc.)

**Cascading effects:**
- If tasks.py fails, no initialization occurs
- If initialization fails, development environment incomplete
- If environment incomplete, user workflow blocked

**Prevention applies to:**
- All template tasks.py files
- Any repository-aware tooling
- Shared configuration discovery
- Path resolution logic

## Lessons Learned

### Key Insights

1. **next() requires defaults for resilience**
   - `next(iterator)` raises StopIteration if empty
   - `next(iterator, default)` returns default if empty
   - Module-level code should always have fallbacks

2. **Templates have dual usage modes**
   - Repo-integrated: Access shared files via REPO_ROOT
   - Standalone: Need local copies or fallbacks
   - Code must support both modes

3. **Module-level execution is fragile**
   - Runs during import, before any function calls
   - Failures block entire module
   - Should be resilient to environment variations

4. **Inconsistency indicates incomplete design**
   - `python-node-secure` uses ROOT (standalone-compatible)
   - `python-api-secure` uses REPO_ROOT (repo-dependent)
   - Inconsistency suggests pattern not fully thought through

5. **File bundling vs sharing trade-off**
   - Bundling: Standalone-compatible, but duplication
   - Sharing: DRY, but repo-dependent
   - Fallback pattern: Best of both worlds

### Best Practices

**When discovering paths:**

1. **Always provide fallback**
```python
# Good
REPO_ROOT = next(
    (parent for parent in Path(__file__).resolve().parents if (parent / "AGENTS.md").exists()),
    ROOT  # Fallback
)

# Better
try:
    REPO_ROOT = next(
        parent for parent in Path(__file__).resolve().parents if (parent / "AGENTS.md").exists()
    )
except StopIteration:
    REPO_ROOT = ROOT  # Explicit fallback with comment
```

2. **Validate file dependencies**
```python
if not PYTHON_AUDIT_POLICY.exists():
    print(f"WARNING: Policy file not found: {PYTHON_AUDIT_POLICY}")
    print("Using default policy...")
```

3. **Document usage modes**
```python
# tasks.py header comment:
"""
This script supports two usage modes:
1. Repo-integrated: Finds shared files via REPO_ROOT
2. Standalone: Falls back to ROOT-relative paths
"""
```

4. **Test both modes**
```bash
# CI should test:
# - Template within repo
# - Template copied to temp directory
```

## Applicability

### ✅ This Failure Mode Applies To

- Templates using REPO_ROOT discovery pattern
- Code using `next()` without default
- Module-level path resolution
- Repository structure dependencies
- Standalone template usage

### ❌ This Failure Mode Does Not Apply To

- Templates using ROOT-relative paths
- Function-level path resolution (can handle errors)
- Templates with bundled dependencies
- Repo-only usage (never standalone)

## Status

- [x] Documented
- [ ] Prevention implemented (pending fix)
- [x] Detection implemented (user report)
- [ ] Mitigation tested
- [ ] Monitoring in place (pending CI update)

## Related Knowledge

- **KB-2026-001**: Scenario portability limits (similar portability issue)
- **KB-2026-008**: Container architecture mismatch (venv exec format error)
- **AGENTS.md Section 0**: KBPD principles (failure → learning → knowledge)
- **AGENTS.md Section 9**: CI Strategy (should mirror local workflow)

## Fix Implementation

**Recommended fix for affected templates:**

```python
# templates/python-secure/tasks.py
# templates/python-api-secure/tasks.py

# Before:
REPO_ROOT = next(
    parent for parent in Path(__file__).resolve().parents if (parent / "AGENTS.md").exists()
)

# After:
try:
    REPO_ROOT = next(
        parent for parent in Path(__file__).resolve().parents if (parent / "AGENTS.md").exists()
    )
except StopIteration:
    # Fallback for standalone usage: use template directory as root
    REPO_ROOT = ROOT
    
# Ensure required files exist
PYTHON_AUDIT_POLICY = REPO_ROOT / "security-scan-policy.toml"
PYTHON_AUDIT_EVALUATOR = REPO_ROOT / "scripts" / "evaluate_python_audit_policy.py"

# Validate at runtime
if not PYTHON_AUDIT_POLICY.exists():
    print(f"ERROR: Required file not found: {PYTHON_AUDIT_POLICY}")
    print("For standalone usage, copy security-scan-policy.toml to template directory")
    sys.exit(1)
```

**Files to update:**
- `templates/python-secure/tasks.py`
- `templates/python-api-secure/tasks.py`

**Testing:**
```bash
# Test repo-integrated
cd templates/python-api-secure && devpod up .

# Test standalone
mkdir /tmp/test && cp -r templates/python-api-secure /tmp/test/
cd /tmp/test/python-api-secure && devpod up .
```

## Decision Impact

This K-Brief informs:
- Template portability requirements
- Path resolution patterns
- Standalone template support
- Error handling in module-level code
- Template testing procedures

## Validation

**Status: Validated**

Failure confirmed through:
- User report (2026-04-03 00:45:56)
- Reproduction in standalone directory
- Root cause analysis (REPO_ROOT discovery)
- Pattern comparison across templates

This is now a **documented failure mode** with solution patterns.

## Knowledge Compounding

This K-Brief extends the portability knowledge:

```
KB-2026-001: Scenario portability limits
    ↓
KB-2026-007: Template portability failure (this document)
```

**Future value:**
- Prevents repeating this failure
- Guides template design patterns
- Documents dual usage mode support
- Provides error handling patterns
- Informs testing requirements

**This is KBPD in action:** Failure → Investigation → Understanding → Documentation → Prevention
