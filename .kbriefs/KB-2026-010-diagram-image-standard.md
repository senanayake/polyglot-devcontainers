---
id: KB-2026-010
type: standard
status: draft
created: 2026-04-11
updated: 2026-04-11
tags: [diagrams, image, presentation, agent-interface, visualization, requirements]
related: []
---

# Diagram Image Standard: Agent-Callable Presentation Diagram Stack

## Context

Polyglot currently publishes maintainer and starter images for engineering
workflows, but it does not yet publish a focused image for high-quality
diagram generation.

There is now a concrete use case for one:

- an upcoming presentation about CVE management in a large software portfolio
- a need for slide-ready diagrams that explain dependency structure and
  vulnerability emergence clearly
- a desire to let agents generate and revise those diagrams by calling a
  container image rather than depending on local desktop tools

This K-Brief defines the proposed standard and requirements for that image.

## Problem/Need

The new image must solve two problems at once:

1. Produce presentation-quality diagrams that are good enough for a conference
   talk, not only engineering documentation.
2. Expose a deterministic, agent-friendly rendering surface that works inside a
   container and can be automated without hidden manual steps.

The immediate proving slice is a CVE narrative with two diagrams:

- Diagram 1: direct vs transitive dependencies in a software component
  hierarchy
- Diagram 2: any component, direct or transitive, can become vulnerable at any
  time through the community CVE process

## Standard/Pattern

### Description

The proposed standard is a new published image:

`ghcr.io/<owner>/polyglot-devcontainers-diagrams`

This image should be a batch renderer for diagrams-as-code, optimized for:

- SVG-first presentation output
- deterministic agent execution
- software architecture and dependency visualization
- reusable visual themes and branded styling
- small, proven scope rather than a kitchen-sink diagram platform

### Key Principles

- Vector-first: SVG is the primary output format for slide quality and
  post-processing.
- Container-first: rendering must work fully inside the image with no host GUI
  dependency.
- Agent-callable: the image must expose a simple CLI with stable inputs,
  outputs, and exit codes.
- Theme-driven: "TED talk quality" comes from curated themes, fonts, spacing,
  and composition rules, not from raw syntax support alone.
- Layered tooling: the image should start with the smallest tool stack that
  covers the target diagrams well.
- Offline by default: rendering should not require network access during normal
  execution.

### Implementation

The initial standard should require the following capabilities.

#### 1. Rendering Contract

The image should expose a stable command surface such as:

```bash
diagram render \
  --tool d2 \
  --input docs/diagrams/cve/dependency-hierarchy.d2 \
  --output .artifacts/diagrams/dependency-hierarchy.svg \
  --format svg
```

Minimum contract requirements:

- stable non-interactive CLI
- deterministic exit codes
- input from file, with stdin support where practical
- output to an explicit path
- machine-readable manifest output, for example:

```json
{
  "tool": "d2",
  "format": "svg",
  "input": "docs/diagrams/cve/dependency-hierarchy.d2",
  "output": ".artifacts/diagrams/dependency-hierarchy.svg",
  "warnings": []
}
```

- no hidden downloads during render
- no dependence on an interactive browser session

#### 2. Tool Stack

The initial image should be **D2-first**, with **Graphviz** included as a
secondary engine.

Required tools for the first release:

- `d2`
- `graphviz`
- curated open fonts for presentation use

Optional but deferred from the first release:

- Mermaid CLI
- PlantUML
- Structurizr CLI
- Kroki server mode

#### 3. Visual System

The image should include a small curated style system:

- 2-3 presentation themes, not dozens
- open fonts suitable for slides
- light background defaults first
- transparent background option
- slide-safe spacing and line weights
- standard legend and callout styles
- emphasis styles for:
  - direct dependency
  - transitive dependency
  - vulnerable node
  - external CVE signal / advisory feed

#### 4. Repository Shape

The first slice should assume diagram sources and outputs live in a predictable
layout such as:

```text
docs/diagrams/
  cve-portfolio/
    dependency-hierarchy.d2
    vulnerability-emergence.d2
    theme/
      conference-light.d2
      conference-contrast.d2
.artifacts/diagrams/
```

#### 5. Validation

The image should be considered valid only if it can:

- render reference diagrams deterministically in CI
- produce SVG outputs for the proving slice
- render at least one multi-board or stepped diagram
- run from the container with no network dependency during render
- emit a manifest and fail clearly on syntax or asset errors

#### 6. Presentation Use-Case Requirements

##### Diagram 1: Direct vs Transitive Dependencies

This diagram should show:

- an application at the top of the hierarchy
- a clear first layer of direct dependencies
- one or more deeper layers of transitive dependencies
- visual distinction between direct and transitive nodes
- arrows or containment that make dependency direction obvious
- a legend that defines the terms directly on the slide

Acceptance criteria:

- a non-technical audience can tell in under 10 seconds which components are
  direct vs transitive
- the application, direct layer, and transitive layers remain legible on a
  16:9 presentation slide
- the diagram works in both static form and build-up form

##### Diagram 2: Vulnerability Emergence

This diagram should show:

- the same dependency topology or a simplified derivative of Diagram 1
- a community vulnerability signal arriving after the dependency graph exists
- any node, whether direct or transitive, being capable of switching into a
  vulnerable state
- clear emphasis that the application did not need to change for the risk state
  to change

Acceptance criteria:

- at least one direct dependency and one transitive dependency can be marked as
  vulnerable in separate variants
- the vulnerability state is obvious without reading presenter notes
- the diagram can be exported as either:
  - separate step images, or
  - a multi-board document suitable for slide build-up

## Rationale

This standard is shaped by the immediate use case rather than by generic
diagram coverage.

For the first presentation slice, the image needs:

- strong hierarchical layout
- nested containers/clusters
- visual polish suitable for slides
- easy theming
- deterministic CLI rendering
- support for stepped narrative variants

That points to D2 plus Graphviz rather than a broader initial stack.

## Benefits

- small first release with honest scope
- high-quality SVG output for presentation decks
- deterministic agent interface for automated generation
- reusable visual language across future talks and docs
- lower maintenance burden than bundling every diagram tool immediately

## Constraints

- "TED talk quality" is not a single tool feature; it requires curated themes,
  fonts, spacing, and review.
- D2 PNG and PDF exports rely on Playwright/browser dependencies, so SVG should
  remain the primary artifact and PNG/PDF should be treated as secondary export
  paths.
- Mermaid C4 is currently documented as experimental, so it should not be the
  primary standard for this image.
- Structurizr CLI does not directly export PNG or SVG from the CLI, so it is
  not a good primary renderer for slide-image generation in phase 1.

## Alternatives Considered

### Alternative A: Mermaid-First Image

- Strong ubiquity
- Good for lightweight docs
- Better fit for Markdown ecosystems than for high-polish conference slides
- C4 support is still documented as experimental

Why not chosen as the initial standard:

- weaker match for the presentation-quality dependency story
- less attractive starting point for layered narrative diagrams

### Alternative B: PlantUML-First Image

- Very broad diagram coverage
- Official themes and SVG/PDF export
- Strong UML support

Why not chosen as the initial standard:

- adds Java runtime and extra maintenance cost
- defaults are less presentation-oriented unless heavily styled
- broader than needed for the proving slice

### Alternative C: Structurizr-First Image

- Strong software architecture model
- exports to PlantUML, Mermaid, DOT, and static sites
- perspective support is valuable for security views

Why not chosen as the initial standard:

- CLI does not directly export PNG/SVG
- better as a model-first architecture tool than as a first slide-image
  renderer
- adds more workflow complexity than the initial presentation slice needs

### Alternative D: Kitchen-Sink Image With All Major Diagram Tools

- maximum coverage
- fewer future installation decisions

Why not chosen as the initial standard:

- violates Gall's Law
- larger image and larger maintenance burden
- harder for agents to choose the correct renderer consistently

## Evidence

Primary-source evidence reviewed:

- D2 documents production-ready themes, sketch mode, container support,
  multiple layout engines, custom fonts, and CLI exports including SVG, PNG,
  PDF, PPTX, and GIF:
  - https://d2lang.com/
  - https://d2lang.com/tour/exports/
  - https://d2lang.com/tour/composition-formats/
- Graphviz documents hierarchical `dot` layouts, cluster handling, clustered
  graph layouts, and SVG/PDF outputs:
  - https://graphviz.org/
  - https://graphviz.org/docs/layouts/dot/
  - https://graphviz.org/docs/clusters/
  - https://graphviz.org/docs/layouts/osage/
  - https://graphviz.org/docs/outputs/
- Mermaid documents architecture diagrams, theme configuration, and currently
  marks C4 as experimental:
  - https://mermaid.js.org/syntax/architecture.html
  - https://mermaid.js.org/config/theming
  - https://mermaid.js.org/syntax/c4
- PlantUML documents official themes and SVG export:
  - https://plantuml.com/
  - https://plantuml.com/theme
  - https://plantuml.com/svg
- Structurizr documents CLI export behavior and the lack of direct CLI PNG/SVG
  export:
  - https://docs.structurizr.com/cli
  - https://docs.structurizr.com/cli/export
  - https://docs.structurizr.com/dsl/cookbook/perspectives-static/

## Anti-Patterns

- Making the first image a universal diagram platform
- Using raster-first output as the primary artifact
- Depending on a hosted rendering service for normal operation
- Letting agents choose tools without an explicit contract or selection rules
- Using experimental syntax as the default standard for production slide assets
- Treating prompt-generated layout as enough without checked-in source files

## Examples

### Good Example

- Diagram source checked into the repo
- D2 theme imported from a repo-owned theme file
- SVG output rendered inside the image
- manifest produced for the agent
- slide-ready output reviewed and versioned

### Bad Example

- ad hoc prompt in chat
- screenshot from a browser editor
- no checked-in source
- no deterministic renderer
- no reusable theme or layout conventions

## Verification

The standard should be verified by:

- rendering fixture diagrams in CI
- checking that expected SVG outputs are produced
- ensuring manifests are emitted with no hidden warnings
- manual review for:
  - legibility on a 16:9 slide
  - distinction between direct and transitive dependencies
  - clarity of vulnerability highlighting

## Migration

If this standard is adopted:

1. Start with a D2-first image and the two CVE presentation diagrams only.
2. Prove the rendering contract and visual theme system.
3. Add Mermaid or PlantUML only if a later use case clearly requires them.
4. Revisit Structurizr only if the repo wants model-first architecture views
   rather than slide-first rendered assets.

## Exceptions

It is acceptable to use another renderer when:

- the target diagram type is not supported well by D2 plus Graphviz
- the output needs a standards-based UML diagram best served by PlantUML
- the workflow is model-first architecture documentation rather than slide
  assets

Those exceptions should be explicit and checked into the repo as source, not
handled through opaque one-off prompts.

## Applicability

### Use This Standard When

- the goal is slide-quality software/system diagrams
- agents need a deterministic rendering interface
- diagrams must be versioned as source
- the visual story depends on hierarchy, grouping, and emphasis overlays

### Don't Use This Standard When

- the goal is a full architecture modeling platform on day one
- the primary need is casual Markdown documentation diagrams
- the only output needed is a quick one-off sketch

## Maintenance

This standard should evolve when:

- the proving slice shows that D2 plus Graphviz is insufficient
- another renderer is repeatedly needed for real diagrams
- the agent contract proves too weak or too verbose
- new published-image scope is approved in the roadmap

The review trigger should be the next real presentation or doc set that needs
more than the current proving slice.

## Related Knowledge

- [docs/reference/published-images.md](../docs/reference/published-images.md)
- [ROADMAP.md](../ROADMAP.md)
- Allen C. Ward's KBPD framing as captured in the repo's K-Brief workflow

## Success Metrics

- the two proving-slice diagrams can be generated from checked-in sources
- agents can render them through a stable container command without manual
  intervention
- the outputs are accepted for use in the presentation deck with minimal manual
  cleanup
- follow-on diagrams reuse the same theme and contract rather than starting
  over
