# KB-2026-010: Interactive Fix Workflow Design

**Type:** Design Space K-Brief  
**Status:** Design Phase  
**Created:** 2026-04-06  
**Tags:** `interactive-fixes`, `agent-automation`, `human-agent-collaboration`, `security-workflow`, `kbpd`

---

## Context

**Problem:** Users must manually fix security vulnerabilities discovered by `task scan`.

**Current workflow:**
```bash
task scan
# ❌ Found 5 vulnerabilities
# User must:
# 1. Read pip-audit output
# 2. Identify fix versions
# 3. Run: uv add "package>=version"
# 4. Run: task ci
# 5. Debug if tests fail
# 6. Repeat for each vulnerability
```

**Desired workflow:**
```bash
task scan:fix
# Agent handles fix loop automatically
# Human provides guidance only when needed
```

---

## Knowledge Gaps

### Critical Unknowns

#### 1. Interaction Modality Trade-Offs

**Gap:** What's the optimal balance between human and agent autonomy?

**Why critical:**
- Too much automation → risk of breaking changes
- Too little automation → slow, tedious workflow
- Wrong balance → user frustration

**Evidence needed:**
- User testing of different interaction patterns
- Analysis of fix success rates by risk level
- Time-to-fix measurements

**Hypothesis:**
- LOW risk (patch updates) → 95%+ auto-fix success
- MEDIUM risk (minor updates) → 70% auto-fix success
- HIGH risk (major updates) → 30% auto-fix success

**Validation approach:**
- Analyze historical vulnerability data
- Test on real codebases
- Measure test failure rates

---

#### 2. Fix Success Rate Boundaries

**Gap:** What percentage of vulnerabilities can be auto-fixed safely?

**Why critical:**
- Sets user expectations
- Determines workflow design
- Influences agent strategy selection

**Evidence needed:**
- Analysis of PyPI vulnerability database
- Test suite robustness measurements
- Breaking change frequency by update type

**Hypothesis:**
```
Patch updates (3.3.0 → 3.3.1):  90-95% success
Minor updates (3.3.0 → 3.4.0):  60-70% success
Major updates (3.3.0 → 4.0.0):  20-30% success
```

**Validation approach:**
- Run automated fixes on 100+ real vulnerabilities
- Measure test pass rates
- Classify failure modes

---

#### 3. Rollback Complexity Limits

**Gap:** When does rollback become more complex than manual fix?

**Why critical:**
- Determines when to offer rollback vs restart
- Affects user trust in automation
- Influences error recovery strategy

**Evidence needed:**
- Git state complexity analysis
- Dependency graph depth measurements
- User preference for rollback vs restart

**Hypothesis:**
- Single dependency update → rollback simple
- Multiple cascading updates → rollback complex
- Lockfile regeneration → rollback unreliable

**Validation approach:**
- Test rollback on various scenarios
- Measure rollback success rates
- Identify failure modes

---

#### 4. Agent Refinement Loop Convergence

**Gap:** How many fix attempts before agent gives up?

**Why critical:**
- Prevents infinite loops
- Manages user time
- Balances automation vs human escalation

**Evidence needed:**
- Success rate by attempt number
- Diminishing returns analysis
- User patience thresholds

**Hypothesis:**
```
Attempt 1 (direct upgrade):      70% success
Attempt 2 (conservative):        20% success
Attempt 3 (minimal):            5% success
Attempt 4+:                     <1% success
```

**Validation approach:**
- Run multi-attempt fixes on failures
- Measure marginal success rates
- Identify optimal cutoff point

---

#### 5. Human-Agent Handoff Points

**Gap:** When should agent ask for help vs try again vs abort?

**Why critical:**
- Defines collaboration boundaries
- Affects user experience
- Determines agent capabilities

**Evidence needed:**
- User preference studies
- Task complexity classifications
- Agent capability limits

**Hypothesis:**
- Breaking changes → always ask human
- Dependency conflicts → try 3 times, then ask
- Test failures → analyze, then ask
- Unknown errors → ask immediately

**Validation approach:**
- User testing with various scenarios
- Measure user satisfaction
- Identify frustration points

---

## Design Space

### Interaction Pattern Options

#### Option A: Human-Interactive (Conservative)

**Description:** Human approves every fix

**Workflow:**
```
Agent: Found 5 vulnerabilities with fixes available
Agent: 1. python-jose 3.3.0 → 3.4.0 (fixes PYSEC-2024-232)
Human: [y/n/skip/quit]
Agent: Applying fix...
Agent: Running tests...
Agent: ✅ Tests passed
Agent: 2. sqlalchemy 2.0.36 → 2.0.37 (fixes GHSA-xxxx)
Human: [y/n/skip/quit]
...
```

**Pros:**
- ✅ Human in control at every step
- ✅ Clear decision points
- ✅ Safe, predictable
- ✅ Easy to understand

**Cons:**
- ❌ Requires constant human attention
- ❌ Slow for batch fixes (5+ vulnerabilities)
- ❌ Interrupts flow
- ❌ Tedious for low-risk fixes

**Best for:**
- Critical production systems
- Users who want full control
- High-risk updates

---

#### Option B: Agent-Autonomous (Aggressive)

**Description:** Agent fixes everything automatically

**Workflow:**
```
Agent: Found 5 vulnerabilities, attempting auto-fix...
Agent: Fixing python-jose 3.3.0 → 3.4.0...
Agent: Running tests...
Agent: ✅ Tests passed (1/5)
Agent: Fixing sqlalchemy 2.0.36 → 2.0.37...
Agent: Running tests...
Agent: ❌ Tests failed, rolling back...
Agent: Retrying with conservative approach...
Agent: ✅ Tests passed (2/5)
...
Agent: Summary: 4 fixed, 1 failed (manual intervention required)
```

**Pros:**
- ✅ Fast, autonomous
- ✅ Handles batch operations well
- ✅ Agent learns from failures
- ✅ Minimal human interruption

**Cons:**
- ❌ Less human control
- ❌ Risk of cascading failures
- ❌ Harder to debug when things go wrong
- ❌ May make unwanted changes

**Best for:**
- Development environments
- Trusted automation
- Low-risk scenarios

---

#### Option C: Hybrid-Adaptive (Recommended)

**Description:** Risk-based automation with human oversight

**Workflow:**
```
Agent: Found 5 vulnerabilities
Agent: Analyzing fix complexity...
Agent: 
Agent: Auto-fixable (low risk):
Agent:   1. python-jose 3.3.0 → 3.3.1 (patch update)
Agent:   2. pydantic 2.10.6 → 2.10.7 (patch update)
Agent: 
Agent: Requires review (higher risk):
Agent:   3. sqlalchemy 2.0.36 → 2.1.0 (minor update, breaking changes)
Agent:   4. fastapi 0.115.6 → 0.116.0 (minor update)
Agent: 
Agent: Cannot auto-fix:
Agent:   5. custom-package (no fix available)
Agent:
Agent: Auto-fix 2 low-risk items? [yes/no/review]: yes
Agent: 
Agent: Applying fixes...
Agent: [1/2] python-jose 3.3.0 → 3.3.1... ✅
Agent: [2/2] pydantic 2.10.6 → 2.10.7... ✅
Agent: Running tests... ✅ All passed
Agent:
Agent: Review higher-risk items? [yes/no/skip]: yes
Agent: 
Agent: 3. sqlalchemy 2.0.36 → 2.1.0
Agent:    CVEs fixed: GHSA-xxxx-xxxx-xxxx
Agent:    Breaking changes: New query API, deprecated methods removed
Agent:    Migration guide: https://docs.sqlalchemy.org/...
Agent:    Apply? [yes/no/diff]: diff
Agent: 
Agent: [shows migration guide and code changes]
Agent: 
Agent: Apply? [yes/no/defer]: no
Agent: Skipped (marked for manual review)
Agent:
Agent: Summary:
Agent:   ✅ Fixed: 2 vulnerabilities
Agent:   ⏭️  Skipped: 2 (manual review required)
Agent:   ❌ Cannot fix: 1 (no fix available)
```

**Pros:**
- ✅ Risk-based automation (safe by default)
- ✅ Human oversight where needed
- ✅ Batch processing with safety
- ✅ Agent learns complexity
- ✅ Clear categorization
- ✅ Efficient for common cases

**Cons:**
- ❌ More complex implementation
- ❌ Requires risk classification heuristics
- ❌ Needs good breaking change detection
- ❌ May misclassify risk levels

**Best for:**
- Most scenarios
- Balance of safety and efficiency
- Production and development

---

## Agent Refinement Loop Design

### Core Strategy

**Principle:** Try multiple strategies with increasing conservatism

```python
class FixRefinementLoop:
    """Agent refinement loop for automated fixes."""
    
    def __init__(self):
        self.max_attempts = 3
        self.strategies = [
            "direct_upgrade",       # Try exact recommended version
            "conservative_upgrade",  # Try latest patch only
            "minimal_upgrade",       # Try minimum version that fixes CVE
        ]
    
    def attempt_fix(self, vulnerability, attempt=1):
        """Attempt to fix vulnerability with refinement."""
        
        # Prevent infinite loops
        if attempt > self.max_attempts:
            return self.escalate_to_human(vulnerability)
        
        strategy = self.strategies[attempt - 1]
        
        # 1. Apply fix with current strategy
        result = self.apply_fix(vulnerability, strategy)
        
        # 2. Verify with tests
        test_result = self.run_tests()
        
        if test_result.passed:
            return FixSuccess(strategy=strategy, attempt=attempt)
        
        # 3. Analyze failure
        failure_type = self.classify_failure(test_result)
        
        if failure_type == "dependency_conflict":
            # Try next strategy (more conservative)
            return self.attempt_fix(vulnerability, attempt + 1)
        
        elif failure_type == "breaking_change":
            # Rollback and ask human
            self.rollback()
            return self.ask_human_for_guidance(vulnerability, test_result)
        
        elif failure_type == "unrelated_failure":
            # Tests were already broken
            self.rollback()
            return FixSkipped(reason="pre_existing_test_failure")
        
        else:
            # Unknown failure, escalate
            self.rollback()
            return self.escalate_to_human(vulnerability)
```

---

### Refinement Strategies

#### Strategy 1: Direct Upgrade

**Approach:** Use exact version recommended by pip-audit

```python
# Example: python-jose 3.3.0 has CVE
# pip-audit recommends: python-jose>=3.4.0
# Strategy: Install python-jose==3.4.0 (latest at time)

uv add "python-jose==3.4.0"
```

**Success rate:** ~70% (hypothesis)

**Failure modes:**
- Dependency conflicts
- Breaking API changes
- Test failures

---

#### Strategy 2: Conservative Upgrade

**Approach:** Use latest patch version only

```python
# Example: python-jose 3.3.0 has CVE
# Current: 3.3.0
# Latest patch: 3.3.1 (if exists)
# Strategy: Try patch first, then minor

if patch_version_exists:
    uv add "python-jose==3.3.1"
else:
    uv add "python-jose>=3.4.0,<3.5.0"
```

**Success rate:** ~20% additional (hypothesis)

**Rationale:**
- Patch updates rarely break APIs
- Safer than minor/major updates
- Good fallback for dependency conflicts

---

#### Strategy 3: Minimal Upgrade

**Approach:** Find minimum version that fixes CVE

```python
# Example: python-jose 3.3.0 has CVE
# CVE fixed in: 3.4.0
# Strategy: Use exact minimum

uv add "python-jose==3.4.0"
```

**Success rate:** ~5% additional (hypothesis)

**Rationale:**
- Last resort before human escalation
- Minimizes change surface
- May resolve edge case conflicts

---

### Failure Classification

```python
def classify_failure(test_result):
    """Classify test failure to determine next action."""
    
    # Check for dependency conflicts
    if "conflict" in test_result.stderr.lower():
        return "dependency_conflict"
    
    # Check for import errors (breaking changes)
    if "ImportError" in test_result.stderr or "AttributeError" in test_result.stderr:
        return "breaking_change"
    
    # Check if tests were already failing
    baseline = run_tests_on_current_version()
    if baseline.failed:
        return "unrelated_failure"
    
    # Unknown failure
    return "unknown"
```

---

## Human-Agent Collaboration Patterns

### Pattern 1: Agent-First with Human Fallback

**When:** Low-risk fixes (patch updates)

**Flow:**
```
Agent: Attempting auto-fix...
Agent: ✅ Success
```

**Human involvement:** None (unless failure)

---

### Pattern 2: Human-Approval with Agent Execution

**When:** Medium-risk fixes (minor updates)

**Flow:**
```
Agent: Found update: sqlalchemy 2.0.36 → 2.1.0
Agent: Risk: MEDIUM (minor update, potential breaking changes)
Human: [approve/reject/defer]
Agent: Applying fix...
Agent: ✅ Success
```

**Human involvement:** Decision only

---

### Pattern 3: Human-Guided with Agent Assistance

**When:** High-risk fixes (major updates)

**Flow:**
```
Agent: Found update: fastapi 0.115.6 → 1.0.0
Agent: Risk: HIGH (major update, breaking changes expected)
Agent: Migration guide: [link]
Agent: Breaking changes:
Agent:   - Removed: deprecated_function()
Agent:   - Changed: new_api_signature()
Human: [show diff/show guide/apply/reject]
Agent: [provides requested information]
Human: [apply]
Agent: Applying fix...
Agent: ❌ Tests failed
Agent: Failure: AttributeError: 'FastAPI' object has no attribute 'deprecated_function'
Human: [rollback/debug/manual]
```

**Human involvement:** Decision + guidance

---

### Pattern 4: Agent-Assisted Manual Fix

**When:** Cannot auto-fix (no fix available, complex migration)

**Flow:**
```
Agent: Cannot auto-fix: custom-package
Agent: Reason: No fix version available
Agent: Recommendation: Contact package maintainer or find alternative
Agent: Alternatives found:
Agent:   1. alternative-package (similar functionality)
Agent:   2. Fork and patch (advanced)
Human: [chooses approach]
```

**Human involvement:** Full manual fix with agent suggestions

---

## Implementation Phases

### Phase 1: Basic Interactive Fix (Current Priority)

**Scope:**
- Implement `task scan:fix` command
- Human-interactive mode (Option A)
- Single-strategy fixes (direct upgrade)
- Basic rollback on failure

**Deliverables:**
- `scan:fix` task in Taskfile.yml
- Interactive prompt system
- Test verification
- Rollback mechanism

**Success criteria:**
- User can fix vulnerabilities interactively
- Tests run after each fix
- Rollback works on failure
- Clear user feedback

---

### Phase 2: Agent Refinement Loop

**Scope:**
- Multi-strategy refinement
- Failure classification
- Automatic retry with fallback
- Smart escalation to human

**Deliverables:**
- Refinement loop implementation
- Strategy selection logic
- Failure analysis
- Escalation heuristics

**Success criteria:**
- 70%+ auto-fix success rate
- <3 attempts per fix
- Clear failure reasons
- Appropriate human escalation

---

### Phase 3: Hybrid-Adaptive Mode

**Scope:**
- Risk classification
- Batch auto-fix for low-risk
- Human review for high-risk
- Migration guide integration

**Deliverables:**
- Risk classification algorithm
- Batch processing
- Breaking change detection
- Migration guide fetching

**Success criteria:**
- 90%+ low-risk auto-fix
- Clear risk categorization
- Efficient batch processing
- Helpful migration guidance

---

## Validation Approach

### Experiment 1: Fix Success Rates

**Hypothesis:** Patch updates succeed 90%+ of the time

**Method:**
1. Collect 100 real vulnerabilities from PyPI
2. Categorize by update type (patch/minor/major)
3. Run automated fixes
4. Measure test pass rates

**Metrics:**
- Success rate by update type
- Test failure modes
- Time to fix

**Decision criteria:**
- If patch success <80%: Revise strategy
- If minor success <50%: Require human approval
- If major success <20%: Manual only

---

### Experiment 2: Refinement Loop Effectiveness

**Hypothesis:** 3 attempts sufficient for 95% of fixable issues

**Method:**
1. Run fixes with multi-strategy refinement
2. Track success by attempt number
3. Measure marginal gains

**Metrics:**
- Success rate by attempt
- Diminishing returns curve
- Time per attempt

**Decision criteria:**
- If attempt 4+ adds <2%: Stop at 3
- If attempt 2 adds <10%: Stop at 1
- If attempt 3 adds >5%: Continue to 4

---

### Experiment 3: User Preference Study

**Hypothesis:** Users prefer hybrid-adaptive mode

**Method:**
1. Test with 10+ users
2. Try all three interaction patterns
3. Collect feedback and preferences

**Metrics:**
- User satisfaction scores
- Time to complete fixes
- Error rates
- Preference rankings

**Decision criteria:**
- If hybrid preferred by <60%: Reconsider default
- If autonomous preferred: Add safety guardrails
- If interactive preferred: Improve batch UX

---

## Trade-Offs

### Automation vs Safety

**Tension:** More automation = less safety

**Options:**
1. **Conservative:** Human approval for everything
   - Pros: Very safe
   - Cons: Slow, tedious

2. **Aggressive:** Auto-fix everything
   - Pros: Fast, efficient
   - Cons: Risk of breaking changes

3. **Balanced:** Risk-based automation
   - Pros: Safe + efficient
   - Cons: Complex implementation

**Decision:** Start conservative (Phase 1), evolve to balanced (Phase 3)

---

### Speed vs Correctness

**Tension:** Fast fixes may be incorrect

**Options:**
1. **Fast:** Skip tests, fix quickly
   - Pros: Immediate results
   - Cons: May break code

2. **Thorough:** Run full test suite after each fix
   - Pros: High confidence
   - Cons: Slow for batch fixes

3. **Adaptive:** Quick tests first, full suite on failure
   - Pros: Fast + safe
   - Cons: Requires test categorization

**Decision:** Thorough for Phase 1, adaptive for Phase 2+

---

### Simplicity vs Capability

**Tension:** Simple systems are limited

**Options:**
1. **Simple:** Single-strategy, no refinement
   - Pros: Easy to understand
   - Cons: Low success rate

2. **Complex:** Multi-strategy with ML
   - Pros: High success rate
   - Cons: Hard to debug

3. **Pragmatic:** 3-strategy refinement
   - Pros: Good success rate, understandable
   - Cons: Some complexity

**Decision:** Pragmatic (3 strategies, clear rules)

---

## Related Knowledge

**Builds on:**
- KB-2026-009: Scenario adoption barriers (task verb system)
- KB-2026-007: Template portability (standalone scenarios)
- KB-2026-003: Checksum verification (security workflows)

**Informs:**
- Future: Cross-language fix workflows
- Future: AI-assisted code migration
- Future: Automated dependency management

**Blocks:**
- Phase 3 task verb system (unified `task fix`)
- Automated security compliance
- CI/CD integration

---

## Next Steps

### Immediate (This Session)

1. **Prototype Phase 1**
   - Implement basic `scan:fix` command
   - Human-interactive prompts
   - Single-strategy fixes
   - Test verification

2. **Validate assumptions**
   - Test on real vulnerabilities
   - Measure success rates
   - Identify failure modes

3. **Document learnings**
   - Update this K-Brief with findings
   - Create implementation guide
   - Share with users for feedback

---

### Short-term (Next Session)

1. **Implement Phase 2**
   - Multi-strategy refinement
   - Failure classification
   - Automatic retry

2. **Run experiments**
   - Fix success rate study
   - Refinement loop effectiveness
   - User preference testing

3. **Refine design**
   - Adjust strategies based on data
   - Optimize attempt limits
   - Improve escalation heuristics

---

### Long-term (Future)

1. **Implement Phase 3**
   - Risk classification
   - Hybrid-adaptive mode
   - Migration guide integration

2. **Extend to other languages**
   - Node.js (npm audit)
   - Java (dependency-check)
   - Rust (cargo audit)

3. **Advanced features**
   - ML-based risk prediction
   - Automated code migration
   - Dependency graph analysis

---

## Knowledge Compounding

This K-Brief captures:
- **Knowledge gaps** identified through KBPD analysis
- **Design space** exploration with trade-offs
- **Validation approach** with clear experiments
- **Refinement strategy** for agent automation
- **Human-agent collaboration** patterns

**Future value:**
- Prevents premature implementation
- Guides experimentation
- Documents decision rationale
- Enables informed iteration
- Builds institutional knowledge

**This is KBPD in action:** Identify gaps → explore design space → validate with experiments → make evidence-based decisions → iterate based on learnings
