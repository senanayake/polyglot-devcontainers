---
id: KB-2026-009
type: design-space
status: active
created: 2026-04-03
updated: 2026-04-03
tags: [scenario, adoption, user-experience, devpod, vscode, portability, one-step-experience]
related: [KB-2026-007, KB-2026-008, KB-2026-001]
---

# Scenario Adoption Barriers: One-Step Experience Design Space

## Context

The vision for polyglot-devcontainers is to enable users to **open different scenarios in one step** and immediately jump into a working development experience. This would facilitate learning across different scenarios (Python API, Node.js, Java, etc.) with minimal friction.

**Current reality:** Opening a standalone template scenario requires multiple manual steps, deep technical knowledge, and iterative debugging. This session revealed a cascade of failures that block the one-step experience.

**Background:**
- Templates are designed to be portable (repo-integrated or standalone)
- DevPod + VSCode should provide seamless container-based development
- Scenarios should be learning vehicles, not debugging exercises
- End-user adoption depends on frictionless experience

## System/Component

**Affected:** Scenario distribution and consumption workflow

**Components involved:**
- Template portability (REPO_ROOT, file dependencies)
- Container architecture compatibility (.venv, node_modules)
- Git context requirements (pre-commit, hooks)
- DevPod + VSCode integration
- Workspace folder navigation
- Code formatting expectations

## Knowledge Gaps Identified

This session exposed critical knowledge gaps between **what works in development** and **what end users experience**.

### Gap 1: Hidden File Dependencies

**What we assumed:**
- Templates are self-contained
- Copy template → run devpod → works

**What we learned:**
- Templates depend on repo-level files (security-scan-policy.toml, evaluate_python_audit_policy.py)
- REPO_ROOT discovery fails outside repo
- No clear documentation of required files
- No validation that dependencies exist

**Evidence:**
```python
# tasks.py assumes these exist:
PYTHON_AUDIT_POLICY = REPO_ROOT / "security-scan-policy.toml"
PYTHON_AUDIT_EVALUATOR = REPO_ROOT / "scripts" / "evaluate_python_audit_policy.py"

# Fails with StopIteration when REPO_ROOT not found
```

**Impact on one-step experience:**
- User copies template
- Runs devpod up
- **Fails immediately** with cryptic error
- Must debug Python import-time failure
- Must identify missing files
- Must manually copy dependencies

**Knowledge gap:** Templates don't declare their external dependencies explicitly.

---

### Gap 2: Architecture-Specific Artifacts

**What we assumed:**
- Copy project directory → container handles environment

**What we learned:**
- Host artifacts (macOS .venv) copied into container
- Binary format mismatch (Mach-O vs ELF) causes exec format error
- Error message doesn't mention architecture
- No .gitignore to prevent artifact pollution
- Failure occurs at runtime, not copy time

**Evidence:**
```
error: Failed to query Python interpreter at `.venv/bin/python3`
Caused by: Exec format error (os error 8)
```

**Impact on one-step experience:**
- User copies template (includes .venv from host)
- Container builds successfully ✓
- Initialization **fails mysteriously**
- Error message misleading (doesn't say "wrong architecture")
- Must understand binary formats to diagnose
- Must manually clean artifacts

**Knowledge gap:** Users don't know which artifacts are architecture-specific and must be excluded.

---

### Gap 3: Git Context Dependency

**What we assumed:**
- Templates work standalone
- Tools adapt to environment

**What we learned:**
- pre-commit requires git repository
- Fails with "not a Git repository" error
- No graceful degradation
- Not documented as requirement
- Blocks entire initialization

**Evidence:**
```
An error has occurred: FatalError: git failed. Is it installed, and are you in a Git repository directory?
```

**Impact on one-step experience:**
- User copies template
- Runs devpod up
- Container builds ✓
- Dependencies install ✓
- **pre-commit fails**
- Must initialize git manually
- Must commit before continuing

**Knowledge gap:** Git context is a hidden prerequisite for development tools.

---

### Gap 4: VSCode Workspace Navigation

**What we assumed:**
- devpod up → VSCode opens in workspace folder
- File explorer shows project structure
- Terminal in correct directory

**What we learned:**
- VSCode opens but not in workspace folder
- File explorer shows home directory (~)
- Terminal starts in /home/vscode
- User must manually navigate
- No automatic workspace folder opening

**Evidence:**
```bash
whoami  # vscode ✓
pwd     # /home/vscode ✗ (should be /workspaces/python-api-secure)
```

**Impact on one-step experience:**
- VSCode opens ✓
- But user sees empty file explorer
- Terminal in wrong directory
- Must manually: File → Open Folder → /workspaces/...
- Must manually: cd /workspaces/...

**Knowledge gap:** DevPod + VSCode integration doesn't automatically open workspace folder.

---

### Gap 5: Code Formatting Expectations

**What we assumed:**
- Templates ship with passing lint
- Users can immediately run task ci

**What we learned:**
- Template code has formatting issues
- task lint fails on fresh checkout
- Blocks CI workflow
- Not clear if this is expected or bug

**Evidence:**
```
Would reformat: src/python_api_secure_template/config.py
Would reformat: tests/test_api.py
task: Failed to run task "lint": exit status 1
```

**Impact on one-step experience:**
- User runs task lint (as documented)
- **Fails immediately**
- Unclear if this is their fault or template issue
- Must run ruff format manually
- Breaks "works out of box" expectation

**Knowledge gap:** Templates don't ship in lint-passing state.

---

### Gap 6: Multi-Step Manual Process

**Current reality - what it actually takes:**

```bash
# Step 1: Copy template
cp -r templates/python-api-secure /path/to/standalone/

# Step 2: Clean host artifacts (not obvious which ones)
rm -rf .venv .artifacts .tmp __pycache__ .pytest_cache .coverage

# Step 3: Copy dependencies (must know which files)
cp security-scan-policy.toml /path/to/standalone/
mkdir -p scripts
cp scripts/evaluate_python_audit_policy.py /path/to/standalone/scripts/

# Step 4: Initialize git (not documented as requirement)
cd /path/to/standalone
git init
git add .
git commit -m "Initial commit"

# Step 5: Start container
devpod up .

# Step 6: Wait for VSCode to open

# Step 7: Manually open workspace folder
# File → Open Folder → /workspaces/python-api-secure

# Step 8: Navigate terminal
cd /workspaces/python-api-secure

# Step 9: Fix formatting
ruff format src tests tasks.py

# Step 10: Verify
task lint
task test
```

**What users expect (one-step experience):**
```bash
# Download scenario
curl -O https://example.com/scenarios/python-api-secure.tar.gz
tar -xzf python-api-secure.tar.gz
cd python-api-secure

# Open in VSCode
devpod up . --ide vscode

# Result: Working environment, ready to learn
```

**Gap:** 10 manual steps vs 1 expected step = **10x complexity barrier**

---

## Failure Chain Analysis

### Complete Failure Sequence (This Session)

1. **Attempt 1:** Copy template → devpod up
   - **Failure:** StopIteration (REPO_ROOT not found)
   - **Root cause:** Template depends on repo structure
   - **Fix required:** Implement REPO_ROOT fallback

2. **Attempt 2:** With REPO_ROOT fallback → devpod up
   - **Failure:** Exec format error (os error 8)
   - **Root cause:** macOS .venv copied to Linux container
   - **Fix required:** Add .gitignore, clean artifacts

3. **Attempt 3:** Clean artifacts → devpod up
   - **Failure:** pre-commit "not a Git repository"
   - **Root cause:** Git context required but not documented
   - **Fix required:** Initialize git repository

4. **Attempt 4:** Initialize git → devpod up
   - **Success:** Container initialized ✓
   - **Problem:** VSCode opened in wrong folder
   - **Workaround required:** Manually open workspace folder

5. **Attempt 5:** Open workspace folder → task lint
   - **Failure:** Formatting issues in template code
   - **Root cause:** Template doesn't ship lint-clean
   - **Fix required:** Run ruff format manually

**Pattern:** Each fix revealed the next hidden requirement. No single failure was obvious from error messages. Required deep technical knowledge at each step.

---

## Barriers to One-Step Experience

### Technical Barriers

1. **Template portability not validated**
   - No CI testing of standalone usage
   - Only tested within repo context
   - Hidden dependencies not documented

2. **Architecture-specific artifacts not excluded**
   - Missing .gitignore files
   - No validation of clean copy
   - Error messages don't mention architecture

3. **Git context not optional**
   - pre-commit hard dependency on git
   - No graceful degradation
   - Not documented as requirement

4. **DevPod + VSCode integration incomplete**
   - Workspace folder not opened automatically
   - Terminal not in workspace directory
   - Requires manual navigation

5. **Template quality not enforced**
   - Code ships with formatting issues
   - Lint fails on fresh checkout
   - Breaks "works out of box" promise

### Knowledge Barriers

1. **Users must understand:**
   - Repository structure dependencies
   - Binary architecture compatibility
   - Git context requirements
   - DevPod workspace mechanics
   - VSCode remote development
   - Container vs host filesystem

2. **Users must know how to:**
   - Identify missing dependencies
   - Clean architecture-specific artifacts
   - Initialize git repositories
   - Navigate VSCode remote workspaces
   - Debug container initialization
   - Fix code formatting issues

3. **Users must have:**
   - Deep technical expertise
   - Patience for iterative debugging
   - Understanding of error messages
   - Knowledge of workarounds

**Reality:** This is expert-level complexity, not beginner-friendly learning experience.

---

## Design Space: Solutions for One-Step Experience

### Option 1: Self-Contained Scenario Packages

**Approach:** Bundle everything needed into single artifact

**Implementation:**
```bash
# Scenario package structure
python-api-secure-scenario/
├── .devcontainer/
│   ├── devcontainer.json
│   └── Containerfile
├── .gitignore              # Excludes architecture artifacts
├── .git/                   # Pre-initialized git repo
├── src/                    # Application code (lint-clean)
├── tests/                  # Tests (lint-clean)
├── tasks.py                # No REPO_ROOT dependency
├── security-scan-policy.toml  # Bundled, not referenced
├── scripts/
│   └── evaluate_python_audit_policy.py  # Bundled
└── README.md               # Clear usage instructions
```

**Advantages:**
- ✅ No external dependencies
- ✅ No manual file copying
- ✅ Git pre-initialized
- ✅ Architecture artifacts excluded
- ✅ Lint-clean code

**Disadvantages:**
- ❌ Duplication of shared files
- ❌ Updates require re-bundling
- ❌ Larger package size

**Trade-off:** Simplicity vs maintainability

---

### Option 2: Scenario Initialization Script

**Approach:** Automated setup script handles all steps

**Implementation:**
```bash
#!/bin/bash
# init-scenario.sh

SCENARIO=$1
DEST=${2:-.}

# Download scenario template
curl -fsSL "https://scenarios.example.com/${SCENARIO}.tar.gz" | tar -xz -C "$DEST"
cd "$DEST/${SCENARIO}"

# Clean any artifacts
find . -name '.venv' -o -name 'node_modules' -o -name '__pycache__' | xargs rm -rf

# Copy shared dependencies
curl -fsSL "https://scenarios.example.com/shared/security-scan-policy.toml" -o security-scan-policy.toml
mkdir -p scripts
curl -fsSL "https://scenarios.example.com/shared/evaluate_python_audit_policy.py" -o scripts/evaluate_python_audit_policy.py

# Initialize git
git init
git add .
git commit -m "Initialize ${SCENARIO} scenario"

# Format code
ruff format src tests tasks.py 2>/dev/null || true

# Open in VSCode
devpod up . --ide vscode --open-ide

echo "✓ ${SCENARIO} scenario ready!"
```

**Usage:**
```bash
./init-scenario.sh python-api-secure
```

**Advantages:**
- ✅ One command to run
- ✅ Handles all setup steps
- ✅ Can fetch latest dependencies
- ✅ Validates environment

**Disadvantages:**
- ❌ Requires network access
- ❌ Script must be maintained
- ❌ Platform-specific (bash)
- ❌ Still multi-step internally

**Trade-off:** Automation vs complexity

---

### Option 3: DevPod Scenario Provider

**Approach:** Extend DevPod with scenario-aware provider

**Implementation:**
```bash
# Register scenario provider
devpod provider add scenarios https://scenarios.example.com/provider.json

# Open scenario (one command)
devpod up scenarios/python-api-secure --ide vscode
```

**Provider handles:**
- Fetching scenario template
- Bundling dependencies
- Cleaning artifacts
- Initializing git
- Opening workspace folder
- Running post-setup tasks

**Advantages:**
- ✅ True one-step experience
- ✅ Integrated with DevPod
- ✅ Consistent across scenarios
- ✅ Handles all complexity

**Disadvantages:**
- ❌ Requires DevPod provider development
- ❌ Custom infrastructure needed
- ❌ Tightly coupled to DevPod
- ❌ Learning curve for provider API

**Trade-off:** Best UX vs implementation effort

---

### Option 4: VSCode Extension

**Approach:** VSCode extension manages scenario lifecycle

**Implementation:**
```javascript
// VSCode command palette
> Polyglot: Open Scenario
  → Select: Python API Secure
  → Extension handles:
     - Download template
     - Clean artifacts
     - Initialize git
     - Start DevPod
     - Open workspace
     - Run post-setup
```

**Advantages:**
- ✅ Native VSCode integration
- ✅ GUI-driven experience
- ✅ Progress feedback
- ✅ Error handling

**Disadvantages:**
- ❌ VSCode-specific (not portable)
- ❌ Extension development effort
- ❌ Maintenance burden
- ❌ Doesn't help CLI users

**Trade-off:** VSCode UX vs portability

---

### Option 5: Hybrid Approach (Recommended)

**Combine multiple strategies:**

1. **Self-contained packages** (Option 1)
   - Bundle all dependencies
   - Pre-initialize git
   - Ship lint-clean code
   - Include .gitignore

2. **Initialization script** (Option 2)
   - Automate setup steps
   - Validate environment
   - Handle edge cases

3. **Clear documentation**
   - One-page quickstart
   - Troubleshooting guide
   - Video walkthrough

**Implementation:**
```bash
# Scenario package (self-contained)
scenarios/
└── python-api-secure/
    ├── .devcontainer/
    ├── .git/              # Pre-initialized
    ├── .gitignore         # Complete
    ├── src/               # Lint-clean
    ├── security-scan-policy.toml  # Bundled
    ├── scripts/           # Bundled
    └── init.sh            # Optional automation

# Usage (simple)
cd scenarios/python-api-secure
devpod up . --ide vscode

# Usage (automated)
./scenarios/python-api-secure/init.sh
```

**Advantages:**
- ✅ Works without script (self-contained)
- ✅ Script provides better UX
- ✅ No custom infrastructure
- ✅ Incremental improvement path

**Disadvantages:**
- ❌ Still requires some user action
- ❌ Not true "one-click"

**Trade-off:** Pragmatic balance of simplicity and UX

---

## Critical Questions to Answer

### 1. What is the acceptable complexity budget for end users?

**Current state:** 10 manual steps, expert knowledge required

**Options:**
- **Zero complexity:** One command, everything automated
- **Minimal complexity:** 2-3 commands, clear instructions
- **Moderate complexity:** 5-6 steps, documented workflow
- **Current complexity:** 10+ steps, debugging required

**Decision needed:** Where on this spectrum is acceptable for "learning scenarios"?

---

### 2. Who is the target user?

**Persona A: Expert Developer**
- Comfortable with containers, git, command line
- Can debug issues independently
- Willing to read documentation
- **Current experience:** Acceptable with documentation

**Persona B: Learning Developer**
- New to containers, devcontainers, DevPod
- Wants to focus on learning scenario content
- Frustrated by setup complexity
- **Current experience:** Blocked, gives up

**Decision needed:** Optimize for which persona?

---

### 3. What is the maintenance trade-off?

**Self-contained packages:**
- ✅ Simple for users
- ❌ Duplication, update burden

**Shared dependencies:**
- ✅ DRY, easier to update
- ❌ Complex for users

**Decision needed:** Optimize for user experience or maintainability?

---

### 4. What is the distribution model?

**Current:** Copy from repo templates/

**Options:**
- **GitHub releases:** Packaged scenarios
- **Scenario registry:** Central catalog
- **Direct download:** curl/wget
- **VSCode marketplace:** Extension-based
- **DevPod provider:** Integrated

**Decision needed:** How do users discover and obtain scenarios?

---

### 5. What is the validation strategy?

**Current:** No validation of standalone usage

**Options:**
- **CI testing:** Test each scenario standalone
- **Automated validation:** Script checks dependencies
- **User testing:** Beta users validate experience
- **Dogfooding:** Team uses scenarios regularly

**Decision needed:** How to ensure scenarios work standalone?

---

## Recommendations

### Immediate Actions (Low-Hanging Fruit)

1. **Ship lint-clean templates**
   ```bash
   # Before committing templates
   ruff format src tests tasks.py
   task lint  # Must pass
   ```

2. **Add .gitignore to all templates**
   ```gitignore
   .venv/
   node_modules/
   __pycache__/
   .artifacts/
   .tmp/
   ```

3. **Bundle dependencies in templates**
   ```bash
   # Each template includes:
   templates/python-api-secure/
   ├── security-scan-policy.toml  # Bundled
   └── scripts/
       └── evaluate_python_audit_policy.py  # Bundled
   ```

4. **Document standalone usage**
   ```markdown
   # README.md in each template
   ## Standalone Usage
   1. Copy this directory
   2. `git init && git add . && git commit -m "init"`
   3. `devpod up . --ide vscode`
   ```

5. **Test standalone in CI**
   ```yaml
   # .github/workflows/test-templates.yml
   - name: Test standalone template
     run: |
       cp -r templates/python-api-secure /tmp/test
       cd /tmp/test
       git init && git add . && git commit -m "test"
       devpod up . --test
   ```

---

### Medium-Term Improvements

1. **Create scenario packages**
   - Pre-bundled, self-contained
   - Published as GitHub releases
   - Versioned and tested

2. **Develop init script**
   - Automates all setup steps
   - Validates environment
   - Provides clear feedback

3. **Improve DevPod integration**
   - Investigate workspace folder opening
   - Document VSCode remote quirks
   - Provide troubleshooting guide

---

### Long-Term Vision

1. **Scenario registry**
   - Central catalog of scenarios
   - One-command download and setup
   - Version management

2. **VSCode extension**
   - GUI for scenario selection
   - Automated setup
   - Progress feedback

3. **DevPod provider**
   - Native scenario support
   - True one-step experience
   - Integrated validation

---

## Success Metrics

**One-step experience achieved when:**

- ✅ User can go from "nothing" to "working environment" in < 5 minutes
- ✅ No manual file copying required
- ✅ No debugging required for happy path
- ✅ Error messages are actionable
- ✅ 90% of users succeed on first try
- ✅ Documentation is < 1 page
- ✅ No expert knowledge required

**Current state:**
- ❌ 30+ minutes for first-time users
- ❌ 10+ manual steps
- ❌ Debugging required
- ❌ Error messages cryptic
- ❌ <50% success rate (estimated)
- ❌ Documentation scattered
- ❌ Expert knowledge required

**Gap:** Significant work needed to achieve one-step vision

---

## Lessons Learned

### 1. Hidden Complexity Compounds

Each hidden requirement adds multiplicative complexity:
- REPO_ROOT dependency × architecture mismatch × git context × VSCode navigation × code formatting
- **Result:** 5 independent failures = 5! possible failure paths

### 2. Error Messages Are Critical

Poor error messages block users:
- "Exec format error" doesn't mention architecture
- "StopIteration" doesn't mention missing REPO_ROOT
- "git failed" doesn't say "initialize git first"

**Learning:** Error messages must be actionable for target user persona

### 3. Testing Must Match Usage

Testing within repo doesn't validate standalone usage:
- All tests passed in repo context
- All failed in standalone context
- **Gap:** Test environment ≠ user environment

**Learning:** CI must test actual user workflows

### 4. Defaults Matter

Every manual step is a drop-off point:
- 10 steps = 10 opportunities to fail
- Each failure requires debugging knowledge
- **Result:** Exponential complexity

**Learning:** Optimize for zero-config defaults

### 5. Documentation Is Not Enough

Even with perfect documentation:
- Users don't read it
- Users don't understand it
- Users expect things to "just work"

**Learning:** UX must work without documentation

---

## Applicability

### ✅ This Analysis Applies To

- Any scenario-based learning system
- Template distribution workflows
- Container-based development environments
- DevPod + VSCode integrations
- Cross-platform portability
- End-user adoption challenges

### ❌ This Analysis Does Not Apply To

- Expert-only tools (complexity acceptable)
- Single-use templates (setup cost amortized)
- Repo-integrated workflows (different constraints)

---

## Status

- [x] Failures documented
- [x] Knowledge gaps identified
- [x] Design space explored
- [ ] Solution selected
- [ ] Implementation planned
- [ ] Validation strategy defined

---

## Related Knowledge

- **KB-2026-001**: Scenario portability limits
- **KB-2026-007**: Template portability failure (REPO_ROOT)
- **KB-2026-008**: Container architecture mismatch (venv)
- **AGENTS.md Section 0**: KBPD principles (failure → learning → knowledge)

---

## Next Steps

1. **Decision:** Select solution approach (recommend Hybrid Option 5)
2. **Design:** Specify scenario package format
3. **Implement:** Create first self-contained scenario package
4. **Test:** Validate with target users
5. **Iterate:** Refine based on feedback
6. **Scale:** Apply to all scenarios

---

## Knowledge Compounding

This K-Brief synthesizes learnings from:
- KB-2026-007: REPO_ROOT portability
- KB-2026-008: Architecture mismatch
- This session: Complete failure chain analysis

**Future value:**
- Prevents building scenarios that don't work standalone
- Guides scenario package design
- Informs testing strategy
- Shapes user experience decisions
- Documents complexity trade-offs

**This is KBPD in action:** Multiple failures → pattern recognition → design space exploration → informed decisions
