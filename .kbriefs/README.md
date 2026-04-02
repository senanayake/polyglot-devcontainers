# Knowledge Briefs (K-Briefs)

This directory contains structured knowledge artifacts generated during product development.

## What is a K-Brief?

A K-Brief is a **reusable record of learning** that captures:
- What we learned
- Why it matters
- Where it applies
- What evidence supports it

K-Briefs are **first-class artifacts**, not optional documentation.

## When to Create a K-Brief

Create a K-Brief when:
- ✅ A decision is made
- ✅ An experiment is run
- ✅ A failure occurs
- ✅ A performance boundary is discovered
- ✅ A trade-off is analyzed
- ✅ A design space is explored

## K-Brief Types

### 1. Trade-Off K-Brief
Captures relationships between competing variables.

**Template:** `templates/tradeoff.md`

**Example:** Caching strategy (latency vs consistency vs cost)

### 2. Limit/Boundary K-Brief
Defines where something breaks or stops working.

**Template:** `templates/limit.md`

**Example:** Scenario portability limits (works on templates, fails on external repos)

### 3. Standard/Best Practice K-Brief
Captures proven solutions and patterns.

**Template:** `templates/standard.md`

**Example:** uv-based Python dependency management

### 4. Design Space K-Brief
Maps the range of possible solutions.

**Template:** `templates/design-space.md`

**Example:** Python dependency tools landscape

### 5. Failure Mode K-Brief
Documents how systems fail and how to prevent it.

**Template:** `templates/failure-mode.md`

**Example:** Scenarios failing on repos without task contract

## K-Brief Lifecycle

```
Knowledge Gap → Experiment → Findings → K-Brief → Reusable Knowledge
```

1. **Identify Gap** - What don't we know?
2. **Design Experiment** - How will we learn?
3. **Run Experiment** - Execute and observe
4. **Capture Findings** - Document what happened
5. **Create K-Brief** - Structure the knowledge
6. **Apply Knowledge** - Use in future decisions

## K-Brief Structure

All K-Briefs follow this structure:

```yaml
---
id: KB-YYYY-NNN
type: [tradeoff|limit|standard|design-space|failure-mode]
status: [draft|validated|deprecated]
created: YYYY-MM-DD
updated: YYYY-MM-DD
tags: [tag1, tag2, tag3]
related: [KB-YYYY-NNN, KB-YYYY-NNN]
---

# Title

## Context
Why this knowledge matters

## Question/Problem
What we needed to learn

## Experiment/Investigation
How we learned it

## Findings
What we discovered

## Evidence
Data, tests, artifacts supporting findings

## Implications
What this means for the project

## Recommendations
How to apply this knowledge

## Applicability
Where this knowledge applies (and doesn't)
```

## Querying K-Briefs

K-Briefs are stored as structured markdown with YAML frontmatter, making them:
- Human-readable
- Machine-queryable
- Version-controlled
- Linkable

**Search by type:**
```bash
grep -l "type: tradeoff" .kbriefs/*.md
```

**Search by tag:**
```bash
grep -l "tags:.*python" .kbriefs/*.md
```

**Find related:**
```bash
grep -l "related:.*KB-2026-001" .kbriefs/*.md
```

## Integration with Development

K-Briefs integrate with the task contract:

- `task kbrief:new` - Create new K-Brief from template
- `task kbrief:list` - List all K-Briefs
- `task kbrief:search` - Search K-Briefs by tag/type
- `task kbrief:validate` - Validate K-Brief structure

## Agent Guidance

When working on this repository, agents should:

1. **Before making decisions** - Search for relevant K-Briefs
2. **During experiments** - Document findings for K-Brief creation
3. **After learning** - Create K-Brief to capture knowledge
4. **When stuck** - Check if a K-Brief exists for similar situations

## K-Brief vs Other Artifacts

| Artifact | Purpose | Scope | Lifespan |
|----------|---------|-------|----------|
| K-Brief | Capture reusable knowledge | Specific learning | Long-term |
| ADR | Record architectural decision | Single decision | Permanent |
| Issue | Track work item | Task execution | Short-term |
| Documentation | Explain how things work | System behavior | Evolving |
| ROADMAP | Plan future work | Strategic direction | Living |

K-Briefs are **knowledge assets** that compound over time.

## Examples

See:
- `KB-2026-001-scenario-portability-limits.md` - Phase 10 learnings
- `KB-2026-002-uv-python-standard.md` - Python dependency management
- `KB-2026-003-template-vs-universal-tradeoff.md` - Template strategy

## Philosophy

> "The highest-performing teams don't just build products faster — they learn faster and encode that learning into the system."
> — Allen C. Ward, Knowledge-Based Product Development

K-Briefs are how we encode learning into the system.
