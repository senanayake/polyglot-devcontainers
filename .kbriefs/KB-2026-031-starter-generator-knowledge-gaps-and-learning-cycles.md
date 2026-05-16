---
id: KB-2026-031
type: design-space
status: draft
created: 2026-04-26
updated: 2026-04-26
tags: [kbpd, starters, generator, learning-plan, scenarios, features, images, docs]
related: [KB-2026-009, KB-2026-012, KB-2026-028, KB-2026-029, KB-2026-030]
---

# Starter Generator Knowledge Gaps and Learning Cycles

## Context

`KB-2026-030` establishes that a first-class starter generator service is a
plausible direction for this repository. That decision is still not
implementation-ready because several high-value unknowns remain.

The purpose of this brief is to make those unknowns explicit and convert them
into bounded learning cycles rather than allowing the project to converge
prematurely on a service or UI shape.

## Problem Statement

Before building a local-and-hosted starter generator for
`polyglot-devcontainers`, what knowledge gaps must be closed so the resulting
system is:

- container-authoritative
- usable by humans and agents
- consistent with the task contract
- compatible with starter images, features, scenarios, and runtime docs

## What Is Already Known

The repository already has meaningful evidence:

- starter workflows are already documented in `docs/core/polyglot-starters.md`
- published starter images already support an empty-workspace bootstrap path via
  `task init`, as proven by `scripts/smoke_test_published_starter.sh`
- the current scenario runner in `scripts/run_scenario.py` is workspace-bound
  and assumes repo-owned paths
- `KB-2026-009` shows that DevPod and IDE friction make GUI-first proving too
  brittle
- `KB-2026-012` shows that downstream consumers need complete starters, not
  bare image references
- `KB-2026-028` and `KB-2026-029` show the project should preserve a robust
  local baseline while allowing stronger remote layers later

What remains unknown is not whether starter generation is valuable, but what
exact contract should be generated and proven.

## Prioritized Knowledge Gaps

### Tier 1: Contract Gaps

These gaps should be closed before building a serious generator core.

### Gap 1: Starter Metadata Schema

**Unknown**

What is the minimum metadata needed to drive starter generation, proofs, and
docs from one source of truth?

**Why it matters**

Without a stable schema, the generator will hard-code template-specific rules
and recreate the same drift that currently exists across templates, examples,
and docs.

**Current evidence**

- starter selection is described in `templates/README.md` and
  `docs/core/polyglot-starters.md`
- no repo-level starter catalog currently acts as the canonical source of truth
- starter bootstrap identity is implicit in image-level environment such as
  `POLYGLOT_BOOTSTRAP_TEMPLATE`, not in an explicit starter catalog

**Learning cycle**

Create a small starter catalog for two starters only:

- `python-secure`
- `python-node-secure`

The catalog should attempt to describe:

- starter id and description
- source template path
- published image reference
- supported task contract
- compatible features
- proof scenario hooks
- tutorial entry points

**Success signal**

One metadata entry can drive generation, smoke proof, and a minimal starter
README without starter-specific branching outside the catalog.

### Gap 2: Generated Output Contract

**Unknown**

Should the generator emit:

- a source-complete starter
- a thin image-backed starter
- both, as different generation modes

**Why it matters**

This decision determines portability, download size, offline behavior, and the
relationship between templates and published images.

**Current evidence**

- `KB-2026-012` shows a usable consumer must be source-complete enough for the
  first documented command to work
- published images already support empty-workspace scaffolding through `task init`
- `templates/java-secure/.devcontainer/bootstrap-workspace.sh` proves a thin
  image can materialize files into an empty workspace

**Learning cycle**

For one starter, build and compare two outputs:

- full-source starter archive
- thin image-backed starter archive

Evaluate:

- first-run friction
- offline usability
- clarity of docs
- CI proving complexity

**Success signal**

A clear recommendation emerges for the default starter mode, with any secondary
mode justified by a distinct use case rather than by ambiguity.

### Gap 3: Bootstrap and `task init` Semantics

**Unknown**

What exact behavior should users and agents be able to rely on from `task init`
across:

- templates
- published starter images
- reruns in partially initialized workspaces
- non-empty workspaces

**Why it matters**

The generator cannot be trustworthy unless the bootstrap contract is precise and
consistent.

**Current evidence**

- the published image bootstrap script refuses non-empty workspaces except for a
  small allowlist
- `scripts/smoke_test_published_starter.sh` assumes an empty workspace and then
  runs `task init`
- standalone `init.sh` exists for some Python templates but not consistently
  across templates
- starter-local proving scenarios currently exist primarily in
  `templates/python-node-secure`

**Learning cycle**

Define and execute a bootstrap acceptance matrix covering:

- empty workspace
- workspace containing only `.devcontainer`
- rerun after successful bootstrap
- rerun after partial bootstrap
- workspace with conflicting files

Run it for `python-secure`, `python-node-secure`, and `java-secure`.

**Success signal**

The repository can state one starter bootstrap contract in documentation and
prove it the same way across supported starter paths.

### Gap 4: Feature Compatibility Model

**Unknown**

How far can starter and feature composition be made generic before the system
needs explicit compatibility constraints?

**Why it matters**

A generator that over-promises composition will produce broken starters faster.

**Current evidence**

- `docs/how-to/compose-features.md` shows simple manual composition patterns
- `KB-2026-030` already identified over-generalized composition as a primary
  risk
- the repository strategy is still curated rather than fully open-ended

**Learning cycle**

Construct and prove a small compatibility matrix:

- `python-secure` + `security-baseline` + `python-engineering` + `agent-runtime`
- `python-node-secure` + `security-baseline` + `agent-runtime`
- `java-secure` + `security-baseline` + `java-engineering` + `agent-runtime`
- at least one intentionally invalid combination

**Success signal**

Compatibility rules can be expressed declaratively enough for the generator to
prevent or warn on unsupported combinations.

### Gap 5: Headless Proving Contract

**Unknown**

What is the minimum automated proof required for a generated starter to count as
valid?

**Why it matters**

If proof depends on DevPod or IDE opening, the system will remain fragile and
hard for agents to use.

**Current evidence**

- `KB-2026-009` shows GUI-first validation is too brittle
- `scripts/smoke_test_published_starter.sh` proves a useful headless slice
- `scripts/run_scenario.py` proves commands and artifacts in an existing
  workspace but does not yet provision one

**Learning cycle**

Define a headless starter proof that generates a workspace and then runs:

- bootstrap
- `task init`
- `task ci`
- starter-specific scenario checks where available

Apply it to one generated starter first.

**Success signal**

The project can validate starter correctness without requiring a GUI or manual
workspace navigation.

## Tier 2: Product Surface Gaps

These gaps should be explored after the core contract is proven.

### Gap 6: Service and Client API Shape

**Unknown**

What API boundary best serves CLI, local website, and future hosted use:

- metadata-only plus generation endpoint
- direct local-folder generation
- zip download only
- some combination

**Current evidence**

- Spring Initializr exposes metadata and generation endpoints
- the repository currently has no equivalent stable starter API

**Learning cycle**

Mock a minimal local API for one starter:

- metadata endpoint
- generation endpoint

Drive it from a CLI first.

**Success signal**

The API proves useful before a polished website exists.

### Gap 7: Scenario Boundary

**Unknown**

Are scenarios:

- attached proofs of starters
- generated starter variants
- separate executable knowledge packages layered on top of starters

**Why it matters**

The current scenario runner assumes repo-owned workspaces. A starter generator
needs a clearer product boundary.

**Current evidence**

- `scripts/run_scenario.py` resolves workspaces relative to the repo root
- `templates/python-node-secure/scenarios/starter-health.json` proves a
  starter-local scenario model exists
- the roadmap treats scenarios as executable knowledge, not just smoke tests

**Learning cycle**

Take one starter and attach one scenario manifest that can run against a
generated workspace rather than a repo-owned workspace.

**Success signal**

Scenarios can be described as reusable starter-adjacent proofs rather than as
repo-only fixtures.

### Gap 8: Release and Versioning Contract

**Unknown**

How should starter metadata, published image tags, docs, and generator releases
stay in sync?

**Why it matters**

A generator that emits stale image references or mismatched docs will fail at
the exact point where it is supposed to reduce friction.

**Current evidence**

- `KB-2026-012` already establishes that real published tags matter
- the repository does not yet expose one obvious canonical starter release
  manifest in the main source tree

**Learning cycle**

Define a single release artifact for one starter family containing:

- starter id
- generator version
- image tag
- proof status
- docs version or digest

**Success signal**

CI can verify that generated starter references point at real published
artifacts.

### Gap 9: Documentation Derivation

**Unknown**

How much starter documentation can be generated from metadata without becoming
too generic or low-signal?

**Current evidence**

- Phase 9d in `ROADMAP.md` already treats runtime docs as a first-class surface
- runtime guidance exists, but starter docs still require manual coordination

**Learning cycle**

Generate one starter README and one how-to page from metadata, then compare them
with the existing handwritten versions for clarity and correctness.

**Success signal**

Generated docs reduce drift while still reading like intentional guidance.

## Tier 3: Scaling Gaps

These gaps are real but should not block the first thin slice.

### Gap 10: Local vs Hosted Operating Model

**Unknown**

What parts of the starter service must work locally first, and what parts are
worth publishing to a hosted control plane later?

**Current evidence**

- `KB-2026-028` and `KB-2026-029` support a layered local-plus-remote model
- the repository still values the free local baseline as non-negotiable

**Learning cycle**

Prove the entire flow locally first in the maintainer container. Only then test
whether a hosted instance adds real value beyond discoverability.

**Success signal**

The hosted path becomes an acceleration layer, not a prerequisite for the
starter product to function.

## Suggested Learning Order

Recommended narrowing sequence:

1. close metadata schema gap
2. close generated output contract gap
3. close bootstrap semantics gap
4. close feature compatibility gap
5. close headless proving gap
6. then design the service and website around the proven contract

## Evidence

Files and artifacts that informed this brief:

- `docs/core/polyglot-starters.md`
- `templates/README.md`
- `docs/how-to/compose-features.md`
- `templates/java-secure/.devcontainer/bootstrap-workspace.sh`
- `templates/python-node-secure/scenarios/starter-health.json`
- `scripts/smoke_test_published_starter.sh`
- `scripts/run_scenario.py`
- `ROADMAP.md`
- `KB-2026-009`
- `KB-2026-012`
- `KB-2026-028`
- `KB-2026-029`
- `KB-2026-030`

## Implications

- The generator service is feasible, but the first work should target contract
  learning, not UI construction.
- The highest-risk failure mode is building a polished surface on top of an
  unstable or implicit starter contract.
- The fastest route to useful agentic development is a metadata-driven CLI plus
  headless proving, not a browser-first experience.

## Recommendations

- Treat the Tier 1 gaps as the immediate KBPD backlog.
- Avoid building a website until at least one starter family can be generated
  and proven from metadata alone.
- Use thin experimental slices with one or two starters rather than aiming for
  all templates and features at once.
- Keep all experiments container-authoritative and compatible with the standard
  task contract.

## Applicability

Where this brief applies:

- Applies to: starter generation, starter proving, feature composition, scenario
  packaging, runtime documentation derivation, and agent workflows
- Does not apply to: ad hoc examples, one-off local experiments, or remote
  platform decisions that are independent of starter generation
