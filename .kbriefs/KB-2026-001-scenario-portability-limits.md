---
id: KB-2026-001
type: limit
status: validated
created: 2026-04-02
updated: 2026-04-02
tags: [scenarios, portability, phase-10, python, build-systems]
related: [KB-2026-002, KB-2026-003]
---

# Scenario Portability Limits: Task Contract Dependency

## Context

Phase 10 aimed to create an executable knowledge system where scenarios could run on arbitrary repositories to demonstrate dependency maintenance patterns. Understanding where scenarios work and where they fail is critical for Phase 10 direction and future scenario development.

## Question

Can scenarios designed for polyglot-devcontainers workspaces execute successfully on external Python repositories with different build systems and project structures?

## Experiment

### Methodology
Tested Python dependency maintenance scenarios against 3 real-world repositories:
- **httpx** (13k+ stars, Hatchling build system)
- **rich** (49k+ stars, Poetry build system)
- **fastapi** (76k+ stars, PDM build system)

### Test Scenarios
- `deps:inventory` - Dependency detection
- `deps:plan` - Update planning
- `deps:report` - Report generation

### Execution Environment
Maintainer container (`ghcr.io/senanayake/polyglot-devcontainers-maintainer:main`)

## Findings

### The Limit

**Scenarios fail on external repositories that don't use the polyglot-devcontainers task contract.**

Success rate: **0/3 repositories (0%)**

### Behavior Before Limit (Within Polyglot-Devcontainers)

Scenarios work perfectly on:
- `examples/python-maintenance-example`
- `templates/python-secure`
- `templates/python-api-secure`

All scenarios execute, produce artifacts, and verify successfully.

### Behavior At/Beyond Limit (External Repositories)

**Failure Mode:**
```
usage: tasks.py [format|init|inventory|lint|plan|scan|test|upgrade]
Error: No such command
```

**Root Causes:**
1. **Task Runner Dependency**: Scenarios hardcoded to `task deps:inventory`, but external repos use:
   - Poetry: `poetry show`
   - PDM: `pdm list`
   - Hatchling: `pip list`

2. **Workspace Coupling**: Scenario JSON specifies:
   ```json
   "workspace": "examples/python-maintenance-example"
   ```
   This path doesn't exist in external repos.

3. **Artifact Path Assumptions**: Scenarios expect:
   ```
   .artifacts/scans/dependency-inventory.json
   ```
   External repos don't create this structure.

4. **Build System Abstraction Missing**: No adapter layer to translate:
   - Scenario intent → Repository-specific commands
   - Repository output → Normalized artifacts

## Evidence

### Test Artifacts
- `.phase10-testing/results/` - Execution logs showing failures
- `.phase10-testing/FINDINGS.md` - Detailed failure analysis
- `.phase10-testing/GAP-ANALYSIS.md` - Architectural gap identification

### Specific Failures

**httpx (Hatchling):**
```
Error: task deps:inventory not found
Repository uses: hatchling build backend
No task contract present
```

**rich (Poetry):**
```
Error: task deps:inventory not found
Repository uses: poetry for dependency management
Different command structure
```

**fastapi (PDM):**
```
Error: task deps:inventory not found
Repository uses: pdm for dependency management
Different artifact locations
```

## Implications

### For Phase 10
- Original vision of "universal scenarios" is not viable without significant architectural changes
- Estimated 8-12 weeks to build adapter layer for portable execution
- Opportunity cost too high for uncertain value

### For Scenario Strategy
- Scenarios should target **polyglot-devcontainers workspaces** (templates, examples)
- Position scenarios as **internal patterns**, not universal tools
- Focus on demonstrating best practices within the opinionated substrate

### For Template Development
- Templates are the right place to showcase scenarios
- Each template can include template-specific scenarios
- Scenarios reinforce the value of the standardized task contract

### For Future Portability Work
If portable scenarios become necessary:
- Requires build system adapter layer
- Requires artifact normalization
- Requires standalone scenario runner
- Should be driven by demand evidence, not speculation

## Recommendations

### Within Limit (Polyglot-Devcontainers Workspaces)

**Continue developing scenarios for:**
- ✅ Templates (`templates/python-api-secure`, etc.)
- ✅ Examples (`examples/python-maintenance-example`)
- ✅ Internal workspace patterns

**Scenario value:**
- Demonstrate best practices
- Validate template quality
- Provide executable documentation
- Support agent-driven workflows

### Approaching Limit (Migration Scenarios)

For repositories migrating to polyglot-devcontainers:
- Create migration guides (Poetry → uv, etc.)
- Provide migration scripts
- Document adoption path
- Don't try to run scenarios on pre-migration repos

### Beyond Limit (External Repositories)

**Don't attempt** unless:
- Strong demand evidence emerges
- Willing to invest 8-12 weeks in adapter architecture
- Clear ROI on portable execution

**Alternative approaches:**
- Documentation and guides instead of executable scenarios
- Focus on template quality to attract adoption
- Let templates demonstrate the value proposition

## Applicability

### ✅ Applies To

- Scenarios for polyglot-devcontainers templates
- Scenarios for polyglot-devcontainers examples
- Internal workspace automation
- Template validation and testing
- Agent-driven workflows within the substrate

### ❌ Does Not Apply To

- External repositories with different build systems
- Repositories without task contract
- Arbitrary Python projects
- Pre-migration codebases
- Universal scenario execution

## Related Knowledge

- **KB-2026-002**: uv-based Python dependency management standard
- **KB-2026-003**: Template-focused vs universal scenario trade-off
- **ROADMAP.md**: Phase 10 outcome documentation
- **AGENTS.md**: Agent operating rules (to be updated with K-Brief workflow)

## Lessons Learned

1. **Test portability assumptions early** - Don't assume internal tools work externally
2. **Follow Gall's Law** - Prove simple portable version before building complex one
3. **Evidence-based decisions** - Testing revealed issues quickly, enabling pivot
4. **Honest assessment** - Better to acknowledge limits than force broken systems
5. **Opportunity cost matters** - 8-12 weeks for uncertain value vs proven template work

## Decision Impact

This K-Brief directly informed:
- Phase 10 pivot decision (partial success, focus on templates)
- Template development strategy (python-api-secure creation)
- Future roadmap prioritization (templates over portable scenarios)
- ROADMAP.md update documenting Phase 10 outcome

## Status

**Validated** - Findings confirmed through real-world testing on 3 diverse repositories.

This limit is now a **known constraint** that should guide future scenario development.
