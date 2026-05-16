---
id: KB-2026-030
type: design-space
status: validated
created: 2026-04-24
updated: 2026-04-24
tags: [testing, taxonomy, python, java, bdd, tdd, traceability]
related: [KB-2026-029, KB-2026-031, KB-2026-032]
---

# Polyglot Testing Taxonomy And Framework Mapping

## Context

Polyglot needed a test model that would scale across ecosystems while staying
small enough to remain a usable task contract.

## Problem Statement

What semantic testing hierarchy should Polyglot expose, and how should that
hierarchy map to Python and Java frameworks?

## Design Space Dimensions

- semantic clarity
- cross-language consistency
- agent readability
- execution speed

## Options in the Space

### Option A: Single flat `task test`

**Position in space:**
- semantic clarity: low
- cross-language consistency: medium
- agent readability: low
- execution speed: medium

**Characteristics:**
- simplest on paper
- hides unit vs integration vs acceptance semantics
- makes traceability weak

### Option B: Semantic hierarchy with focused verbs

**Position in space:**
- semantic clarity: high
- cross-language consistency: high
- agent readability: high
- execution speed: high

**Characteristics:**
- keeps one full bar plus focused zoom-in verbs
- maps well to both Python and Java
- supports TDD and BDD without creating two competing contracts

### Option C: Framework-specific verbs

**Position in space:**
- semantic clarity: medium
- cross-language consistency: low
- agent readability: low
- execution speed: medium

**Characteristics:**
- easy to wire to local tooling
- leaks ecosystem details into the public contract
- weak for polyglot documentation and agent guidance

## Design Space Map

| Option | Semantic clarity | Cross-language consistency | Agent readability | Viable? |
| --- | --- | --- | --- | --- |
| A | Low | Medium | Low | No |
| B | High | High | High | Yes |
| C | Medium | Low | Low | No |

## Dominated Solutions

- Option A is dominated by Option B because it loses semantic precision
  without reducing meaningful implementation cost.
- Option C is dominated by Option B because it sacrifices consistency while
  still requiring the same underlying suite structure.

## Pareto Frontier

- Option B is the useful frontier for this repository.

## Constraints That Narrow the Space

- `task test` already exists as the stable contract surface
- Python and Java both need first-class support
- the model must remain understandable to humans and AI agents

## Evidence

- SWEBOK and IEEE/NIST sources support separating verification and validation
  concerns
- `pytest-bdd`, `hypothesis`, Gradle JVM Test Suites, jqwik, and Cucumber map
  cleanly onto semantic layers
- the implemented Python and Java starter changes proved the mapping is
  operational, not just theoretical

## Insights

- TDD and BDD are workflow lenses, not substitute task hierarchies
- property-based testing deserves its own semantic zoom-in verb
- execution amplifiers such as coverage and parallelism should not be confused
  with semantic test layers

## Decision Guidance

### Narrowing the Space

1. keep the top-level contract small
2. add only semantic zoom-in verbs
3. map framework-specific execution aids beneath those verbs

### Convergence Strategy

- standardize on `test:unit`, `test:property`, `test:integration`,
  `test:acceptance`, and `test`
- treat `test:all` as an alias, not a stronger bar

## Implications

- repo docs and starter templates can now describe a coherent test model
- requirements, executable specifications, and tests can be linked more easily
- agents gain a stable, language-agnostic way to choose the right feedback loop

## Recommendations

- keep semantic test verbs stable
- let framework-specific execution aids remain implementation details
- use feature scaffolds to generate requirement/spec/test traceability from the
  start

## Applicability

- Applies to: Python starters, Java starters, repo-level task guidance
- Does not apply to: environments that only expose the minimum contract and do
  not yet justify focused test layers
