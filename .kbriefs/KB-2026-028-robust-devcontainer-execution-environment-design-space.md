---
id: KB-2026-028
type: design-space
status: draft
created: 2026-04-25
updated: 2026-04-25
tags: [devcontainers, runtime, podman, coder, codespaces, devpod, gitpod, che, k8s, agents, kbpd]
related: [KB-2026-009, KB-2026-011, KB-2026-027]
---

# Robust Devcontainer Execution Environment Design Space

## Context

Polyglot has grown beyond a small local-only maintainer workflow. The project
now needs an execution strategy that works for:

- individual developers
- maintainers
- AI coding agents
- parallel background tasks
- security-conscious organizations

The repository philosophy still requires a free local path, but recent runtime
fragility shows that "free local" cannot be the only supported execution tier.

## Problem Statement

What environments should Polyglot support for robust devcontainer execution,
both for human developers and for agent-driven self-development, without giving
up the free local baseline?

## Design Space Dimensions

Key variables that define the solution space:

- Free local viability
- Devcontainer fidelity
- Agent isolation and parallelism
- Operational robustness
- Security and infrastructure control
- Cost and maintenance burden

## Options in the Space

### Option A: Local Podman or Docker with Dev Containers

**Position in space:**
- Free local viability: high
- Devcontainer fidelity: high
- Operational robustness: low to medium
- Security and control: high
- Agent scale: low
- Cost: low

**Characteristics:**
- Best baseline for the repository philosophy
- Works with the standard Dev Containers toolchain
- Keeps the source of truth close to the user
- On Windows, local robustness depends on WSL or equivalent VM machinery
- Podman's `kube play` is useful for local Kubernetes-shaped workflows, but it
  is not a substitute for a full remote workspace control plane
- Good for individuals, weak as the only control plane for many agents

### Option B: DevPod as a Multi-Backend Launcher

**Position in space:**
- Free local viability: high
- Devcontainer fidelity: high
- Operational robustness: medium
- Security and control: medium to high
- Agent scale: medium
- Cost: low to medium

**Characteristics:**
- DevPod is client-only and can target a local machine, Kubernetes cluster,
  remote machine, or cloud VM
- Strong portability layer for Polyglot consumers
- Useful as a bridge between local and remote execution tiers
- Not a full multi-user control plane by itself

### Option C: GitHub Codespaces

**Position in space:**
- Free local viability: low
- Devcontainer fidelity: high
- Operational robustness: high
- Security and control: medium
- Agent scale: medium
- Cost: medium to high

**Characteristics:**
- Best managed devcontainer experience for GitHub-centered developers
- GitHub documents prebuilds, VM sizes, and fast startup paths
- Strong for developer convenience and onboarding
- Not self-hosted
- Not aligned with the requirement that Polyglot always have a free local path
- Control is bounded by GitHub's platform model and codespaces-specific limits

### Option D: Coder on Kubernetes or VMs

**Position in space:**
- Free local viability: low
- Devcontainer fidelity: high
- Operational robustness: high
- Security and control: high
- Agent scale: high
- Cost: medium to high

**Characteristics:**
- Strongest current fit for Polyglot self-development at scale
- Coder is self-hosted and can run workspaces as VMs or Kubernetes pods
- Coder supports standard devcontainers and also offers Envbuilder for
  devcontainer-driven image construction without a Docker daemon
- Coder now explicitly positions itself as infrastructure for developers and AI
  coding agents working side by side
- Higher operational burden than local tooling or Codespaces

### Option E: Gitpod or Ona

**Position in space:**
- Free local viability: medium
- Devcontainer fidelity: high
- Operational robustness: high
- Security and control: medium to high
- Agent scale: medium to high
- Cost: medium to high

**Characteristics:**
- Strong remote developer experience with devcontainer support
- Current Gitpod/Ona positioning is increasingly environment-plus-automation and
  agent oriented
- Better fit than local-only tooling when startup speed, image caching, and
  managed remote workflows matter
- Less obviously aligned than Coder with a self-hosted, repo-owner-controlled
  substrate for Polyglot itself

### Option F: Eclipse Che or OpenShift Dev Spaces

**Position in space:**
- Free local viability: low
- Devcontainer fidelity: low to medium
- Operational robustness: high
- Security and control: high
- Agent scale: high
- Cost: high

**Characteristics:**
- Kubernetes-native developer platform with strong enterprise controls
- Better thought of as a DevWorkspace/devfile platform than a pure
  devcontainer-first system
- Persistent storage, operator model, and backup workflows are strengths
- Higher operational and conceptual distance from Polyglot's current
  devcontainer-centric substrate

### Option G: CrewAI AMP

**Position in space:**
- Free local viability: low
- Devcontainer fidelity: low
- Operational robustness: high for agent workflows
- Security and control: medium
- Agent scale: high
- Cost: medium to high

**Characteristics:**
- Valuable agent management platform
- Not a devcontainer workspace substrate
- Better treated as a higher-layer orchestration plane for agent workflows than
  as the environment where Polyglot workspaces run

## Design Space Map

| Option | Free local | Devcontainer fidelity | Robustness | Agent scale | Control | Viable as primary substrate? |
|--------|------------|-----------------------|------------|-------------|---------|------------------------------|
| Local Podman/Docker | High | High | Low-Med | Low | High | Only as baseline |
| DevPod | High | High | Med | Med | Med-High | As bridge, not sole control plane |
| GitHub Codespaces | Low | High | High | Med | Med | Good managed developer option |
| Coder | Low | High | High | High | High | Yes |
| Gitpod/Ona | Med | High | High | Med-High | Med-High | Plausible |
| Eclipse Che / Dev Spaces | Low | Low-Med | High | High | High | Only if devfile-first is acceptable |
| CrewAI AMP | Low | Low | Med-High | High | Med | No, wrong layer |

## Dominated Solutions

Options that are strictly worse than others:
- CrewAI AMP is dominated as a **workspace substrate** because it solves agent
  deployment and observability, not devcontainer execution itself.
- "Local runtime only" is dominated as the **only** strategy once parallel
  agents, platform reliability, and team-scale robustness become requirements.

## Pareto Frontier

Non-dominated solutions:
- Local Podman or Docker remains on the frontier because it uniquely satisfies
  the free local baseline.
- Coder is on the frontier because it combines self-hosting, strong control,
  devcontainer fidelity, and agent scale.
- GitHub Codespaces is on the frontier for managed developer experience and low
  platform-ops burden.
- DevPod is on the frontier as a portability layer across multiple backends.

## Constraints That Narrow the Space

Hard constraints that eliminate options:
- Polyglot must keep a free local version
- the repo is devcontainer-first, not devfile-first
- maintainers need an environment that can run many parallel agent tasks
- organizations using Polyglot may require self-hosted or VPC-contained
  execution
- the chosen design should not force Docker-in-Docker everywhere

## Unexplored Regions

Areas of the design space not yet investigated:
- Coder pilot using Envbuilder versus standard devcontainers inside workspaces
- DevPod provider strategy for a repo-owned remote cluster path
- hybrid model where local developers use DevPod while maintainers and agents
  use Coder-backed remote workspaces
- whether Gitpod/Ona is strategically better than Codespaces for
  devcontainer-plus-agent workflows

## Evidence

Data supporting the design space mapping:
- Podman documents that Windows uses a WSL-backed machine model:
  [podman-machine](https://docs.podman.io/en/latest/markdown/podman-machine.1.html)
- Podman's Kubernetes support is intentionally partial and some functionality is
  unavailable with remote clients, so it should be treated as a local
  compatibility tool, not as a scaled multi-user platform:
  [podman kube play](https://docs.podman.io/en/latest/markdown/podman-kube-play.1.html)
- DevPod documents that it deploys workspaces from a devcontainer to providers
  such as Kubernetes, remote machines, or other backends:
  [DevPod deployment model](https://devpod.sh/docs/how-it-works/deploying-workspaces)
- GitHub documents Codespaces prebuilds and notes that codespaces use hosted VM
  sizes:
  [Codespaces prebuilds](https://docs.github.com/en/codespaces/prebuilding-your-codespaces/about-github-codespaces-prebuilds)
- the devcontainer specification site lists supported services and notes
  Codespaces, DevPod, CodeSandbox, and Ona:
  [containers.dev supporting tools](https://containers.dev/supporting.html)
- Coder documents self-hosted control planes, VM or Kubernetes workspaces, and
  two devcontainer execution approaches:
  [Coder infrastructure](https://coder.com/docs/admin/infrastructure)
  [Coder devcontainers](https://coder.com/docs/admin/integrations/devcontainers)
- CrewAI AMP documents deployment, monitoring, and scaling for agent workflows:
  [CrewAI AMP](https://docs.crewai.com/en/enterprise/introduction)
- Eclipse Che documents a Kubernetes-native workspace platform:
  [Eclipse Che introduction](https://eclipse.dev/che/docs/stable/overview/introduction-to-eclipse-che/)

## Insights

Key learnings from mapping the space:
- there is no single environment that simultaneously gives free local use,
  maximum robustness, high agent scale, and zero operational burden
- the strongest answer is a layered platform strategy
- Coder is the strongest current self-hosted candidate for Polyglot
  self-development with agents
- GitHub Codespaces is the strongest current managed developer environment if
  GitHub-native convenience matters more than self-hosting
- DevPod is strategically useful as a portability bridge, not as the whole
  platform story
- CrewAI belongs above the workspace layer, not instead of it

## Decision Guidance

### Narrowing the Space

How to progressively eliminate options:
1. keep a free local baseline no matter what
2. reject solutions that do not execute devcontainers well enough
3. separate workspace substrate choices from agent orchestration choices
4. favor remote platforms that can isolate many agent jobs cleanly

### Convergence Strategy

When and how to commit to a solution:
- short term: harden the free local Podman path and document failure recovery
- medium term: pilot Coder as the remote substrate for maintainer and agent work
- optional path: support Codespaces or Gitpod/Ona for developer convenience
- longer term: revisit agent orchestration layers only after the workspace
  substrate is stable

## Implications

What this design space means for:
- Architecture: Polyglot should target a layered execution model
- Roadmap: runtime substrate work becomes first-order platform work
- Risk: local-runtime outages must not block all learning loops
- Innovation: agent scale is unlocked more by workspace control planes than by
  adding more local runtime tricks

## Recommendations

Suggested path forward:
- preserve local Podman or Docker as the free baseline
- treat DevPod as a useful developer-facing bridge across backends
- study Coder as the leading remote substrate for Polyglot self-development
  with agents
- study Codespaces or Gitpod/Ona as optional convenience tiers for developers
- do not treat CrewAI as the replacement for a workspace platform

## Applicability

Where this design space applies:
- Applies to: Polyglot maintainer workflows, downstream developer environments,
  remote agent execution, self-hosted platform planning
- Does not apply to: purely CI-only container execution or non-devcontainer
  developer platforms

## Related Knowledge

- [KB-2026-009](./KB-2026-009-scenario-adoption-barriers.md)
- [KB-2026-011](./KB-2026-011-vscode-podman-host-binding.md)
- [KB-2026-027](./KB-2026-027-windows-podman-machine-control-path-failure.md)
