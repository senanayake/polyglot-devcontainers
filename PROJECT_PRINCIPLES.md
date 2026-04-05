# Project Principles

These principles define how Polyglot Devcontainers should evolve and how change
should be judged.

## 1. Determinism First

The same repository inputs should produce the same working environment and the
same task entry points across machines and CI.

If a workflow only works on one host setup or through unstated local state, it
is not good enough.

## 2. Container-Authoritative Execution

The container is the source of truth for maintained workflows.

Host setup should stay minimal. Validation should happen inside the environment
the repository defines and publishes.

## 3. Explicit Contracts Over Hidden Behavior

Polyglot should prefer visible task entry points, declared files, and
reviewable configuration over magical automation or implicit side effects.

The system should be easy to inspect, debug, and explain.

## 4. Security In The Default Path

Security is not an optional add-on. Scanning, reviewable policy, and secure
defaults should live in the standard workflow.

## 5. Composition Over Reinvention

Use the existing devcontainer and ecosystem toolchain where it is strong.
Polyglot should add value through integration, structure, and clarity rather
than unnecessary replacement.

## 6. Scope Before Sprawl

The project should stay honest about what is currently supported.

It is better to be clear and credible about a smaller working system than to
market a larger system that has not yet been proven.

## 7. Scenarios Support The System; They Do Not Replace It

Scenarios are useful when they package runnable, documented flows around a
specific environment and verification path.

They should reinforce the task contract, not create a second hidden workflow
surface.

## 8. Community Requires Clarity

Open source contributors need a clear identity, visible scope, obvious
contribution paths, and understandable review criteria.

Presentation quality is part of system quality.

## Review Lens

Changes should be evaluated against these questions:

- Does this increase or reduce determinism?
- Is the behavior clear from the repository itself?
- Does it align with the task contract?
- Does it preserve explicit, reviewable execution?
- Does it keep scope honest?

If the answer is no, the change should be reworked or rejected.
