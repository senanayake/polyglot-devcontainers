---
id: KB-2026-030
type: design-space
status: draft
created: 2026-04-26
updated: 2026-04-26
tags: [starters, generator, metadata, devcontainers, devpod, features, scenarios, agent-workflows]
related: [KB-2026-009, KB-2026-012, KB-2026-028, KB-2026-029]
---

# Starter Generator Service Design Space

## Context

This repository already has starter templates, published starter-image proving,
scenario evidence capture, and runtime documentation. What it does not yet have
is a first-class product surface for generating downstream starter projects.
That gap keeps the starter path manual and makes agentic development of new
images, features, and scenarios harder than it needs to be.

The design question is whether `polyglot-devcontainers` should evolve toward a
`start.spring.io`-style model where starter generation is a product in its own
right rather than an indirect effect of templates, examples, and docs.

## Problem Statement

How should this repository expose starter generation so that:

- humans can create a project quickly through a local or hosted UI
- agents can generate starters headlessly and prove them automatically
- images, features, scenarios, and tutorials stay aligned with what is actually
  generated
- the solution remains container-authoritative and maintainable

## Design Space Dimensions

Key variables that define the solution space:
- Automation leverage: how easily agents and CI can generate and prove starters
- Product coherence: whether starters, docs, and proofs come from one source
- Operational complexity: local setup, hosting, and maintenance burden

## Options in the Space

### Option A: Template-First Manual Workflow

**Position in space:**
- Automation leverage: low
- Product coherence: low to medium
- Operational complexity: low

**Characteristics:**
- Keep templates, examples, `init.sh`, and docs as the primary entry points.
- Humans copy a template or mount a published image and then open it in DevPod.
- Agents prove starters indirectly via repo-local scripts and examples.
- Strengths:
  - Minimal new implementation
  - Preserves current workflows
- Weaknesses:
  - Starter generation remains implicit
  - DevPod and IDE flows remain too manual for reliable agentic proving
  - Docs, generated state, and proving logic can drift
- Constraints:
  - Does not create a reusable public-facing starter product

### Option B: Local CLI Generator Only

**Position in space:**
- Automation leverage: medium to high
- Product coherence: medium
- Operational complexity: low to medium

**Characteristics:**
- Add a repo-owned generator CLI that creates a complete downstream starter in a
  workspace from catalog metadata.
- Make the CLI the basis for CI and agent workflows.
- Strengths:
  - Strong headless path for agents and CI
  - Simpler than running a hosted service
  - Good first step toward a productized starter path
- Weaknesses:
  - No first-class web experience
  - Limited discovery for users who expect a browser entry point
  - Third-party IDE integrations are harder without an HTTP metadata surface
- Constraints:
  - Still needs a formal catalog and compatibility model

### Option C: Metadata-Driven Generator Core Plus Service and Thin Clients

**Position in space:**
- Automation leverage: high
- Product coherence: high
- Operational complexity: medium

**Characteristics:**
- Build a reusable generator core, expose it through a local/publishable HTTP
  service, and layer CLI and Web UI clients on top.
- Treat metadata as the product: starter catalog, image refs, feature options,
  compatibility rules, scenarios, and tutorial hooks.
- Strengths:
  - Local service can run in the maintainer container
  - Same generation engine serves agents, CI, CLI users, and a website
  - Starter path becomes first class and testable
  - Tutorials and how-tos can derive from the same metadata
- Weaknesses:
  - More moving parts than a CLI-only approach
  - Requires careful scope control to avoid over-generalized composition
- Constraints:
  - Needs a stable starter metadata model
  - Needs verification tests that prove generated outputs, not just source

### Option D: Full Remote Workspace Provisioning Platform

**Position in space:**
- Automation leverage: high
- Product coherence: medium to high
- Operational complexity: high

**Characteristics:**
- Treat remote workspace orchestration as the primary interface and provision
  starters directly into managed environments.
- Strengths:
  - Strongest end-to-end onboarding experience
  - Can reduce host/runtime friction for teams
- Weaknesses:
  - Expensive and operationally heavy
  - Over-solves the immediate problem
  - Makes product progress depend on infrastructure maturity
- Constraints:
  - Better as a later control-plane layer than as the first implementation

## Design Space Map

| Option | Automation leverage | Product coherence | Operational complexity | Viable? |
|--------|---------------------|-------------------|------------------------|---------|
| A | Low | Low-Med | Low | Yes, but weak |
| B | Med-High | Med | Low-Med | Yes |
| C | High | High | Med | Yes |
| D | High | Med-High | High | Later |

## Dominated Solutions

Options that are strictly worse than others:
- A UI-only generator without a stable CLI or API is dominated by Option C
  because it increases surface area without improving agentic proving.
- Treating DevPod or VS Code opening as the primary automation contract is
  dominated by Options B and C because GUI opening is not a reliable proof path.

## Pareto Frontier

Non-dominated solutions:
- Option B is attractive when minimizing implementation cost while improving
  automation quickly.
- Option C is the best balance when the starter path is intended to become a
  first-class product.
- Option D is only justified once the generator model is stable and remote
  control-plane value clearly outweighs operational cost.

## Constraints That Narrow the Space

Hard constraints that eliminate options:
- Repository maintenance and proof must remain container-authoritative.
- Starter outputs must preserve the standard task contract.
- New generation paths must prove real generated workspaces, not only source
  templates.
- The repository is still in a curated phase; arbitrary cross-language feature
  composition should not be assumed safe.

## Unexplored Regions

Areas of the design space not yet investigated:
- Whether the starter service should emit zip archives only or also support
  direct local-folder generation through the same API contract
- How far feature composition can be made generic before compatibility metadata
  becomes too costly to maintain
- Whether a static web client plus API is sufficient or whether a server-rendered
  site would simplify local operation

## Evidence

Data supporting the design space mapping:
- Repo evidence:
  - `Taskfile.yml` already exposes image build/verify lanes and maintainer entry
    points
  - `scripts/smoke_test_published_starter.sh` already proves a generated empty
    workspace path for published images
  - `scripts/run_scenario.py` already captures scenario evidence after scripted
    execution
  - `docs/core/polyglot-starters.md` already describes starter-centric workflows
- Prior knowledge:
  - `KB-2026-009` shows current scenario adoption is limited by manual multi-step
    bootstrap and IDE friction
  - `KB-2026-012` shows downstream consumers need complete starters rather than
    image references alone
  - `KB-2026-028` and `KB-2026-029` show remote control planes are useful but
    should not replace a robust local-first baseline prematurely
- External inspiration:
  - Spring Initializr exposes an extensible generation library plus web endpoints
    for third-party clients and local instances
  - `start.spring.io` keeps the website as a separate thin layer with its own
    client, site configuration, and verification project

## Insights

Key learnings from mapping the space:
- The right product boundary is not "open DevPod automatically"; it is "generate
  and prove a starter deterministically."
- Metadata is the missing first-class artifact in this repository. Today the
  starter catalog is implicit across templates, examples, docs, and scripts.
- A thin UI should sit on top of a stable generator core, not replace it.
- Feature and scenario development become more agentic only when they can be
  attached to a generated starter contract and proven headlessly.

## Decision Guidance

### Narrowing the Space

How to progressively eliminate options:
1. Reject GUI-first automation as the primary proof mechanism.
2. Introduce a starter metadata catalog and generation core.
3. Prove the core through CLI-driven local generation and container-authoritative
   acceptance tests.
4. Add the HTTP service and web UI once the metadata model is stable enough to
   support local and hosted clients.

### Convergence Strategy

When and how to commit to a solution:
- Converge on Option C as the target architecture.
- Implement it incrementally in Option B order:
  - core metadata
  - generator library
  - local CLI
  - proving suite
  - HTTP service
  - web UI
- Keep Option D explicitly out of scope until the local-first generator path is
  mature and routinely used.

## Implications

What this design space means for:
- Architecture:
  - the repository should separate generator core, service surface, and UI
- Roadmap:
  - starter generation should become a product lane alongside images, features,
    and scenarios
- Risk:
  - the main risk is over-generalizing starter composition before compatibility
    rules are explicit
- Innovation:
  - a first-class starter generator enables agentic TDD loops for new features,
    starter variants, and scenario packages

## Recommendations

Suggested path forward:
- Adopt Option C as the destination architecture.
- Start with a thin slice that adds:
  - starter metadata descriptors
  - a local generator CLI
  - a headless starter proving command
- Add a local web service and website only after the generator contract is
  already usable by agents and CI.
- Generate starter READMEs and tutorial pages from the same metadata that drives
  generation to reduce drift.
- Treat DevPod as an interactive client of the starter system, not the core
  proving mechanism.

## Applicability

Where this design space applies:
- Applies to: published starter images, repo templates, feature proving,
  scenario packaging, tutorial generation, and agent workflows
- Does not apply to: one-off example fixtures, ad hoc experiments, or remote
  control-plane productization before the starter contract is stable

## Related Knowledge

- `KB-2026-009-scenario-adoption-barriers.md`
- `KB-2026-012-diagram-consumer-starter-contract.md`
- `KB-2026-028-robust-devcontainer-execution-environment-design-space.md`
- `KB-2026-029-free-local-baseline-vs-robust-remote-control-plane.md`
- `docs/core/polyglot-starters.md`
- `scripts/smoke_test_published_starter.sh`
