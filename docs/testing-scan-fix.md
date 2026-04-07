# Testing Interactive Fix Workflow (scan:fix)

**Status:** Phase 1 Implemented  
**Last Updated:** 2026-04-07

---

## Overview

The `task scan:fix` command provides an interactive workflow for fixing security vulnerabilities discovered by `pip-audit`. This guide explains how to test and validate the implementation.

---

## Prerequisites

**Environment:**
- Running inside maintainer devcontainer or scenario container
- Python 3.12+
- `uv` package manager installed
- `task` runner available

**Template:**
- `python-api-secure` or `python-secure`
- Initialized with `task init`

---

## Testing Approach

### Option 1: Test with Real Vulnerabilities (Recommended)

**When to use:** When templates have actual vulnerabilities

**Steps:**

1. **Check for vulnerabilities**
   ```bash
   cd templates/python-api-secure
   task scan
   ```

2. **Review findings**
   ```bash
   cat .artifacts/scans/pip-audit.json
   ```

3. **Run interactive fix**
   ```bash
   task scan:fix
   ```

4. **Verify fixes**
   ```bash
   task ci
   ```

---

### Option 2: Test with Simulated Vulnerabilities

**When to use:** When templates are clean (no vulnerabilities)

**Steps:**

1. **Create test scenario**
   ```bash
   # Copy template to test directory
   cp -r templates/python-api-secure /tmp/test-scan-fix
   cd /tmp/test-scan-fix
   ```

2. **Introduce vulnerability**
   ```bash
   # Downgrade python-jose to vulnerable version
   sed -i.bak 's/"python-jose\[cryptography\]>=3.4.0"/"python-jose[cryptography]==3.3.0"/' pyproject.toml
   ```

3. **Initialize environment**
   ```bash
   task init
   ```

4. **Verify vulnerability exists**
   ```bash
   task scan
   # Should show python-jose 3.3.0 with CVEs
   ```

5. **Run interactive fix**
   ```bash
   task scan:fix
   ```

6. **Test the workflow**
   - When prompted: `Apply fix? [y/n/skip/quit]:`
   - Enter `y` to apply fix
   - Watch as it:
     - Applies fix with `uv add`
     - Runs tests
     - Shows success or rollback

7. **Verify fix worked**
   ```bash
   task scan
   # Should show no vulnerabilities
   ```

8. **Clean up**
   ```bash
   cd -
   rm -rf /tmp/test-scan-fix
   ```

---

## Expected Workflow

### Successful Fix

```
$ task scan:fix

Running security scan...
🔍 Found 1 package(s) with vulnerabilities

[1/1] 📦 python-jose 3.3.0 → 3.4.0
  CVEs: PYSEC-2024-232, PYSEC-2024-233
  Apply fix? [y/n/skip/quit]: y
  🔧 Applying fix...
  🧪 Running tests...
  ✅ Tests passed

============================================================
Summary:
  ✅ Fixed: 1
  ⏭️  Skipped: 0
  ❌ Failed: 0
============================================================

💡 Tip: Run 'task ci' to verify all checks pass
```

---

### Failed Fix (with Rollback)

```
$ task scan:fix

Running security scan...
🔍 Found 1 package(s) with vulnerabilities

[1/1] 📦 some-package 1.0.0 → 2.0.0
  CVEs: CVE-2024-XXXX
  Apply fix? [y/n/skip/quit]: y
  🔧 Applying fix...
  🧪 Running tests...
  ❌ Tests failed
  🔄 Rolling back...
  ⚠️  Fix reverted due to test failures

============================================================
Summary:
  ✅ Fixed: 0
  ⏭️  Skipped: 0
  ❌ Failed: 1
============================================================
```

---

### User Skips Fix

```
$ task scan:fix

Running security scan...
🔍 Found 2 package(s) with vulnerabilities

[1/2] 📦 python-jose 3.3.0 → 3.4.0
  CVEs: PYSEC-2024-232, PYSEC-2024-233
  Apply fix? [y/n/skip/quit]: y
  🔧 Applying fix...
  🧪 Running tests...
  ✅ Tests passed

[2/2] 📦 sqlalchemy 2.0.36 → 2.1.0
  CVEs: GHSA-xxxx-xxxx-xxxx
  Apply fix? [y/n/skip/quit]: skip
  ⏭️  Skipped

============================================================
Summary:
  ✅ Fixed: 1
  ⏭️  Skipped: 1
  ❌ Failed: 0
============================================================
```

---

### User Quits Early

```
$ task scan:fix

Running security scan...
🔍 Found 3 package(s) with vulnerabilities

[1/3] 📦 python-jose 3.3.0 → 3.4.0
  CVEs: PYSEC-2024-232, PYSEC-2024-233
  Apply fix? [y/n/skip/quit]: quit

🛑 Aborted by user

Summary: 0 fixed, 0 skipped, 0 failed
```

---

## Validation Checklist

### Functional Tests

- [ ] **Parse vulnerabilities correctly**
  - Reads pip-audit JSON output
  - Extracts package name, version, CVEs
  - Identifies fix versions

- [ ] **Interactive prompts work**
  - Accepts y/yes to apply fix
  - Accepts n/no/skip to skip fix
  - Accepts q/quit to abort
  - Handles invalid input gracefully

- [ ] **Fix application works**
  - Runs `uv add package>=version`
  - Updates lockfile
  - Installs new version

- [ ] **Test verification works**
  - Runs pytest after fix
  - Detects test failures
  - Continues on success

- [ ] **Rollback works**
  - Creates lockfile backup
  - Restores backup on failure
  - Runs `uv sync --frozen` to reinstall
  - Cleans up backup on success

- [ ] **Summary statistics correct**
  - Counts fixed packages
  - Counts skipped packages
  - Counts failed packages
  - Displays at end

### Edge Cases

- [ ] **No vulnerabilities found**
  - Shows "✅ No vulnerabilities found!"
  - Exits gracefully

- [ ] **No fix available**
  - Shows "⚠️ No fix version available"
  - Counts as skipped
  - Continues to next vulnerability

- [ ] **Multiple vulnerabilities in one package**
  - Shows all CVE IDs
  - Uses first fix version
  - Applies single fix

- [ ] **Fix fails during uv add**
  - Catches exception
  - Rolls back
  - Counts as failed
  - Continues to next

- [ ] **Tests were already failing**
  - Detects pre-existing failures
  - Skips fix (doesn't blame new version)
  - Provides clear message

---

## Performance Metrics to Track

### Success Rates

- **Overall success rate:** Fixed / (Fixed + Failed)
- **By update type:**
  - Patch updates (x.y.z → x.y.z+1)
  - Minor updates (x.y.z → x.y+1.0)
  - Major updates (x.y.z → x+1.0.0)

### Time Measurements

- **Time per fix:** From prompt to result
- **Test duration:** How long tests take
- **Total workflow time:** Start to finish

### User Behavior

- **Skip rate:** Skipped / Total
- **Quit rate:** How often users quit early
- **Retry rate:** How often users retry failed fixes

---

## Known Limitations (Phase 1)

1. **Single-strategy only**
   - Only tries direct upgrade
   - No fallback to conservative/minimal
   - Phase 2 will add multi-strategy

2. **No risk classification**
   - Treats all fixes equally
   - No auto-fix for low-risk
   - Phase 3 will add risk-based automation

3. **Sequential processing**
   - One fix at a time
   - No batch mode
   - Future: parallel processing for independent fixes

4. **Basic rollback**
   - Lockfile-based only
   - May not handle all edge cases
   - Future: git-based rollback option

5. **No breaking change detection**
   - Doesn't analyze migration guides
   - Doesn't detect API changes
   - Phase 3 will add breaking change analysis

---

## Troubleshooting

### Issue: "No audit report found"

**Cause:** pip-audit failed to run

**Solution:**
```bash
# Run scan manually to see error
task scan

# Check if pip-audit is installed
.venv/bin/python -m pip list | grep pip-audit
```

---

### Issue: "Tests failed" but tests pass manually

**Cause:** Test environment issue

**Solution:**
```bash
# Run tests manually
task test

# Check test output
.venv/bin/python -m pytest -v
```

---

### Issue: Rollback fails

**Cause:** Lockfile backup missing or corrupted

**Solution:**
```bash
# Restore from git
git checkout uv.lock

# Reinstall
task init
```

---

### Issue: Fix applied but vulnerability still shows

**Cause:** pip-audit cache or version mismatch

**Solution:**
```bash
# Clear artifacts
rm -rf .artifacts/scans

# Run fresh scan
task scan
```

---

## Next Steps

### Phase 2: Agent Refinement Loop

- Multi-strategy refinement
- Failure classification
- Automatic retry with fallback
- Smart escalation to human

### Phase 3: Hybrid-Adaptive Mode

- Risk classification (low/medium/high)
- Batch auto-fix for low-risk
- Human review for high-risk
- Migration guide integration

---

## Related Documentation

- **KB-2026-010:** Interactive fix workflow design (KBPD analysis)
- **docs/task-verb-system.md:** Task verb reference
- **KB-2026-009:** Scenario adoption barriers

---

## Feedback

**What to track during testing:**

1. **User experience**
   - Is the workflow intuitive?
   - Are prompts clear?
   - Is feedback helpful?

2. **Success rates**
   - How many fixes succeed?
   - What causes failures?
   - Are rollbacks reliable?

3. **Performance**
   - How long does it take?
   - Are tests too slow?
   - Is the workflow efficient?

4. **Edge cases**
   - What breaks the workflow?
   - What's confusing?
   - What's missing?

**Please document findings in KB-2026-010 for future iterations.**
