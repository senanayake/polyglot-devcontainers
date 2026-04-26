---
id: KB-2026-037
type: standard
status: draft
created: 2026-04-26
updated: 2026-04-26
tags: [starters, compatibility, composition, kbpd, generator]
related: [KB-2026-031, KB-2026-033]
---

# Curated Composition Profiles Minimize Starter Compatibility Risk

## Context

The next starter-generator knowledge gap was how to represent valid starter
composition without claiming more compatibility than the repository has proven.

At this stage the generator can stamp and prove source-complete starter
workspaces, but it cannot yet synthesize or mutate devcontainer feature mixes.
That makes free-form `starter + feature + scenario` requests too optimistic.

## Decision

Use curated composition profiles as the compatibility contract.

Each starter declares:

- supported feature identifiers
- supported scenario identifiers
- one or more named composition profiles
- one default profile

Each profile pins the exact feature and scenario set that the repository is
willing to generate and prove for that starter.

## Why This Is The Right Standard Now

- it rejects unsupported composition requests before generation
- it avoids pretending that compatibility can be inferred from template shape
- it preserves room to add more profiles later as new combinations are proven
- it keeps the catalog reviewable and language-agnostic

## Evidence

- `scripts/starter_catalog.py` now validates starter profile membership against
  the starter-level supported feature and scenario lists
- generated starter stamps now record the selected profile, features, and
  scenarios
- a generated `python-node-secure` starter can now be proven through an
  explicit named profile rather than an implicit template default

## Tradeoff

Curated profiles are more manual than inferred compatibility, but that is the
correct trade for the current knowledge state. They bias toward safety and
evidence instead of convenience and guesswork.

## Applicability

### This Standard Applies To

- starter generation requests
- starter proving in CI
- future local service and web clients that need a stable starter contract

### This Standard Does Not Yet Apply To

- arbitrary user-chosen feature subsets
- automated compatibility inference from template or feature metadata alone
