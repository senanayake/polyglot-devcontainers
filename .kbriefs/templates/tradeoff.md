---
id: KB-YYYY-NNN
type: tradeoff
status: draft
created: YYYY-MM-DD
updated: YYYY-MM-DD
tags: []
related: []
---

# [Title: Trade-Off Being Analyzed]

## Context

Why this trade-off matters for the project.

## Variables

The competing factors in this trade-off:
- Variable 1 (e.g., latency)
- Variable 2 (e.g., cost)
- Variable 3 (e.g., complexity)

## Options Considered

List of approaches evaluated:

### Option A: [Name]
- Description
- Characteristics

### Option B: [Name]
- Description
- Characteristics

### Option C: [Name]
- Description
- Characteristics

## Trade-Off Analysis

### Quantitative Comparison

| Option | Variable 1 | Variable 2 | Variable 3 | Overall |
|--------|-----------|-----------|-----------|---------|
| A      | High      | Low       | Medium    | Score   |
| B      | Medium    | Medium    | Low       | Score   |
| C      | Low       | High      | High      | Score   |

### Qualitative Insights

Key relationships discovered:
- Improving X degrades Y by Z%
- Variable A dominates when [condition]
- Sweet spot exists at [point]

## Trade-Off Curves

If quantified, describe the relationship:
- Linear, exponential, logarithmic?
- Inflection points
- Diminishing returns regions

```
[Optional: ASCII graph or reference to data visualization]
```

## Evidence

Data supporting the trade-off analysis:
- Benchmarks
- Experiments
- Case studies
- Prior art

## Decision Guidance

### When to Choose Option A
Conditions favoring this approach.

### When to Choose Option B
Conditions favoring this approach.

### When to Choose Option C
Conditions favoring this approach.

## Constraints That Change the Trade-Off

External factors that shift the balance:
- Scale (e.g., "at >10k users, Option B dominates")
- Budget (e.g., "under $500/month, Option A only")
- Team expertise
- Time constraints

## Implications

What this trade-off means for:
- Architecture
- Roadmap
- Resource allocation
- Risk management

## Recommendations

Default recommendation with rationale.

## Applicability

Where this trade-off applies:
- ✅ Applies to: [systems, scenarios, contexts]
- ❌ Does not apply to: [exceptions, special cases]

## Related Knowledge

- Related K-Briefs
- ADRs
- Documentation
- Issues
