---
id: KB-2026-040
type: design-space
status: draft
created: 2026-05-09
updated: 2026-05-09
tags: [commercial, open-core, enterprise, roadmap, positioning, business-model]
related: [KB-2026-029, KB-2026-028, KB-2026-022]
---

# Commercial Architecture and Open-Core Boundary Design Space

## Context

The project has a working open-source substrate: published OCI images, secure
starters for Python/Java/Node/polyglot, a task contract, K-Brief knowledge
capture, and scenario infrastructure. The question now is how to evolve this
into a commercially viable project with enterprise penetration while remaining
genuinely open.

The central tension is: what must stay free to drive adoption, and what can be
made commercially valuable without undermining the open value proposition?

## Problem Statement

How should Polyglot Devcontainers define its open-core boundary so that:

- open-source adoption is not impeded by commercial lock-in
- the commercial tier creates real value beyond the free tier
- the architecture supports both community use and enterprise requirements
- no SaaS investment is required before demand is proven

## Design Space Dimensions

Key variables:
- Open-core boundary depth (how much is free vs. paid)
- Time-to-commercial-value (when does revenue become possible)
- Enterprise fit (what enterprises will actually pay for)
- Operational cost (infrastructure required before revenue)
- Competitive moat (what is hard to replicate)

## Options in the Space

### Option A: Everything Open, Revenue from Services Only

**Position in space:**
- Open-core boundary depth: no boundary (fully open)
- Time-to-commercial-value: long (services only, consultancy model)
- Enterprise fit: medium (credible but hard to scale)
- Operational cost: very low
- Competitive moat: weak (anyone can fork and replicate)

**Characteristics:**
- All code, templates, features, and tooling remain open.
- Revenue comes from consulting, onboarding, and support contracts only.
- Strengths: maximum adoption, clear credibility, no license friction.
- Weaknesses: labor-intensive revenue, hard to scale, no product moat.
- Constraints: requires founder time per engagement at every stage.

### Option B: Open Core with Paid Enterprise Governance Layer

**Position in space:**
- Open-core boundary depth: medium (core open, governance closed)
- Time-to-commercial-value: medium (12-18 months to pilot revenue)
- Enterprise fit: high (regulated enterprises need governance, not templates)
- Operational cost: low initially (file-based, CLI-first)
- Competitive moat: medium-high (governed execution contracts are differentiated)

**Characteristics:**
- Core: templates, features, task contract, basic scanning, GHCR images — fully open.
- Commercial tier: enterprise policy packs, certified image channels, fleet
  inventory, upgrade wave planner, air-gapped bundles, advisory packages.
- Strengths:
  - Mirrors successful open-core patterns (HashiCorp, Grafana, Keycloak).
  - Enterprise governance is high-value and hard to self-assemble.
  - Pilot revenue possible as packaged professional services before SaaS exists.
- Weaknesses:
  - Requires clear communication of the open/commercial boundary.
  - Risk of community perception that core is being held back.
- Constraints:
  - Commercial tier needs 1-2 design partner enterprises to validate.

### Option C: Hosted SaaS Platform (Fleet Dashboard + Control Plane)

**Position in space:**
- Open-core boundary depth: shallow (most value in SaaS)
- Time-to-commercial-value: very long (SaaS requires infra, auth, billing)
- Enterprise fit: high if built, but high risk before adoption proven
- Operational cost: high
- Competitive moat: medium (similar to GitHub Advanced Security, Snyk)

**Characteristics:**
- Build a hosted control plane: fleet inventory, compliance dashboard, policy
  enforcement, upgrade planner.
- Strengths: recurring revenue, high enterprise fit if adopted.
- Weaknesses:
  - Requires significant upfront investment before revenue.
  - Competitors (Snyk, Chainguard, JFrog, GitHub GHAS) are well-funded.
  - No SaaS before proven demand is the explicit project constraint.
- Constraints: violates the project's explicit cost constraint.

## Design Space Map

| Option | Open boundary | Time to revenue | Enterprise fit | Op cost | Moat |
|--------|--------------|-----------------|---------------|---------|------|
| A: Services only | Full open | Long | Med | Very low | Weak |
| B: Open core + governance | Medium | Medium | High | Low-med | Med-high |
| C: SaaS platform | Shallow | Very long | Very high | High | Med |

## Dominated Solutions

Option C is dominated by Option B until adoption is proven. The SaaS control
plane can be layered on top of Option B later but must not be built first.

## Pareto Frontier

Option B occupies the Pareto frontier for this project at current scale:
- Best enterprise fit per unit of operational investment
- Strongest moat relative to consulting-only
- Compatible with the explicit low-budget constraint

## Recommended Boundary

### Open (always)
- Core devcontainer templates (python, java, node, polyglot)
- Base language features and security-baseline feature
- Task contract specification
- Basic scanner integrations (Grype, Trivy, Gitleaks, pip-audit)
- Example scenarios
- Documentation and man pages
- Published GHCR images
- Local-first CLI utilities (polyglot doctor, polyglot init)
- Basic reports

### Commercial (packaged product / paid packs)
- Enterprise policy packs (regulated-baseline, finserv, healthcare, FedRAMP-adjacent)
- Certified image channels with SLA and CVE SLA
- Private registry mirroring tooling
- Fleet inventory dashboard
- Upgrade wave planner with executive report
- Air-gapped bundle export
- Enterprise support subscriptions
- Agent governance modules (fine-grained policy enforcement for AI coders)
- Advisory / onboarding packages (the Phase 7 "Bootstrap" offer)

## Constraints That Change the Trade-Off

- If a design partner enterprise emerges, move toward Option B commercial tier faster.
- If the project gains significant open-source adoption (>100 GitHub stars, >10
  downstream repos), the SaaS path in Option C becomes more viable.
- If a well-funded competitor replicates the open core exactly, the commercial
  tier needs to deepen.

## Implications

- Architecture: the task contract and `polyglot-contract.yaml` spec are the
  stable interface — both open and commercial tiers build on top of them.
- Roadmap: the first commercial pilot offer should be a packaged professional
  service, not a SaaS subscription.
- Resource allocation: no SaaS infrastructure spend before first paid pilot.
- Risk management: maintain genuine open-core credibility to avoid
  community backlash.

## Recommendations

Adopt Option B immediately with a consulting-first revenue entry point.

Sequence:
1. Publish the open core clearly (ENTERPRISE.md, positioning).
2. Build the task contract spec (credibility for enterprise conversations).
3. Package the first commercial offer as a deliverable service (not SaaS).
4. Add fleet reporting as a file-first local tool (pre-SaaS foundation).
5. Only build a hosted control plane after the first paid pilot proves demand.

## Applicability

Applies to: roadmap sequencing, investor/partnership conversations, README
positioning, ENTERPRISE.md content, first commercial pilot design.
Does not apply to: individual starter or feature development decisions.
