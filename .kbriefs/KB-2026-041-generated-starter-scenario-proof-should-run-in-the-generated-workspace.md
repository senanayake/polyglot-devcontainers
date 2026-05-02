---
id: KB-2026-041
type: standard
status: published
created: 2026-04-28
updated: 2026-04-28
tags: [starters, scenarios, portability, kbpd, generator]
related:
  - KB-2026-009-scenario-adoption-barriers.md
  - KB-2026-031-starter-generator-knowledge-gaps-and-learning-cycles.md
  - KB-2026-037-curated-composition-profiles-minimize-starter-compatibility-risk.md
---

# Generated Starter Scenario Proof Should Run In The Generated Workspace

## Context

The next starter-generator knowledge gap was scenario portability. Generated
starters were already proven through task commands and required artifact paths,
but that did not yet prove that starter-local scenarios still worked once the
template had been emitted as a standalone workspace.

## Decision

Treat generated-starter scenario proof as an explicit part of the starter
contract.

Use the generated workspace itself as the scenario root, and allow composition
profiles to declare a smaller `proof_scenarios` subset of their supported
scenario set.

## Why This Is The Right Standard Now

- it proves a real downstream starter path instead of only the template-authoring path
- it keeps the first portability step small by proving one explicit scenario
- it avoids forcing every supported scenario into the default proof lane before
  their runtime cost and value are understood

## Evidence

- `templates/python-node-secure/scripts/run_scenario.py` now accepts a
  `--workspace-root` override so the same scenario manifest can execute against
  a generated workspace
- `scripts/starter_catalog.py` now records `proof_scenarios` and executes them
  during starter proofing
- maintainer-container validation passed for:
  - `task starters:validate`
  - `task starters:prove -- --starter python-node-secure --profile polyglot-default`
  - `task starters:verify`
- the generated `python-node-secure` proof artifact now records a passed
  `starter-health` scenario under
  `.artifacts/starters/python-node-secure/polyglot-default/proof.json`

## Tradeoff

This keeps scenario proof curated and selective rather than exhaustive. That is
the correct trade while the repository is still learning which generated
starter scenarios provide durable value in CI.

## Applicability

### This Standard Applies To

- generated starter verification in CI
- starter composition profiles that need portable scenario evidence
- future local service and web clients that promise starter behavior

### This Standard Does Not Yet Apply To

- all scenario manifests by default
- repo-owned scenario families that still assume a repository-root workspace
- thin image-backed starters that have not yet proven the same scenario path
