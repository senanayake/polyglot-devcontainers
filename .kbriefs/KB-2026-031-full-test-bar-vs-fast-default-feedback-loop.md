---
id: KB-2026-031
type: tradeoff
status: validated
created: 2026-04-24
updated: 2026-04-24
tags: [testing, task-contract, tdd, ci, tradeoff]
related: [KB-2026-028, KB-2026-030, KB-2026-032]
---

# Full Test Bar Vs Fast-Default Feedback Loop

## Context

The repo had drifted into a state where the published contract described
`task test` as the full automated test bar while newer Python starters used
`task test` as a fast subset.

## Variables

- completion clarity
- inner-loop speed
- CI consistency
- agent predictability

## Options Considered

### Option A: Keep `task test` fast-by-default

- preserves fast local feedback
- weakens the meaning of the published contract

### Option B: Make `task test` the full bar and add `test:fast`

- restores contract clarity
- preserves fast TDD feedback through an explicit helper verb

### Option C: Keep `task test` ambiguous and rely on documentation

- avoids edits in the short term
- leaves humans and agents to guess

## Trade-Off Analysis

| Option | Completion clarity | Inner-loop speed | CI consistency | Overall |
| --- | --- | --- | --- | --- |
| A | Low | High | Low | Weak |
| B | High | High | High | Strong |
| C | Low | Medium | Low | Weak |

## Qualitative Insights

- the cost of adding `test:fast` is small compared with the confusion caused by
  redefining `task test`
- TDD benefits from a fast loop, but the completion bar benefits from a single
  unambiguous meaning
- agentic workflows are more reliable when the strongest bar is stable and the
  weaker bars are explicitly named

## Evidence

- root docs, AGENTS guidance, and task-contract docs already assumed `task
  test` was the full bar
- starter implementation showed that adding focused verbs is operationally easy
- internal remediation verification can still use fast subsets without changing
  the public contract

## Decision Guidance

### When to Choose Option B

Use the full-bar `task test` model whenever the repository publishes a stable
task contract or expects agents to treat `task ci` and `task test` as durable
interfaces.

## Implications

- `task test` regains its meaning as the full automated regression bar
- `test:fast` becomes the explicit inner-loop acceleration path
- future starter work should add semantic zoom-ins rather than silently
  weakening the default contract

## Recommendations

Default recommendation: choose Option B.

## Applicability

- Applies to: starter templates, repo docs, agent guidance
- Does not apply to: throwaway local scripts with no stable public contract
