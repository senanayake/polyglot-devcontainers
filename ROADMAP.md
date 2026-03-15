# ROADMAP.md

This roadmap describes the evolution of `polyglot-devcontainers` and the
broader Polyglot ideas it may evaluate over time.

This repository hosts the substrate first:

- devcontainer environments
- reusable features and templates
- published OCI images
- the repository task contract

It may evaluate broader Polyglot interface ideas later, but the repository does
not currently commit to a separate CLI or parallel workflow contract.

The project follows Gall's Law:

> A complex system that works is invariably found to have evolved from a simple
> system that worked.

The project also borrows from moonshot-style planning:

- define bold but plausible axioms
- identify the real kill hypotheses early
- run cheap experiments before hardening architecture
- prefer proving the monkey over polishing the pedestal

The system evolves in layers:

Devcontainer environments
-> engineering capability layer
-> automation and modernization
-> agent-compatible evidence and planning

Early phases focus on practical developer environments that work locally in
IDEs and in CI.

Later phases introduce broader workflow standardization, security automation,
agent-compatible interfaces, and potentially a reusable dependency intelligence
engine if the early experiments justify it.

---

# Guiding Axioms

The project is guided by several assumptions about the future of software
engineering.

### Portable development environments

Development environments will increasingly be defined as portable
infrastructure artifacts rather than manually configured machines.

Devcontainers allow environments to be defined declaratively and reproduced
across machines and CI systems.

### Deterministic environments enable automation

Automation systems, CI pipelines, and development tooling require deterministic
environments.

Containerized development environments provide consistency across developers and
automation systems.

### Security remediation will become increasingly automated

Dependency vulnerabilities and insecure code patterns will increasingly be
addressed through automated detection, safe upgrades, targeted
modernization, and policy-aware planning.

### Software systems remain polyglot

Real-world systems combine multiple languages and ecosystems.

Development environments must support this reality.

### Developer tools must remain simple

Developer platforms succeed when their surface area remains simple and proven by
use:

- `task init`
- `task lint`
- `task test`
- `task scan`
- `task ci`

Additional task entry points may be added when they clearly remove friction, but
the task contract remains the primary working interface.

### Learn through small working systems

The repository should use a small number of working environments to test the
larger ideas before broadening the platform.

### Agent workflows should be proven in the same environments they depend on

If the project introduces agent-driven remediation or planning, it should first
be built and exercised inside the devcontainer substrate provided by this
repository.

The project should eat its own dogfood.

### Planning should be separated from execution

Security and upgrade automation should distinguish between:

- discovering current state
- reasoning about safe target state
- executing changes
- verifying repository health

This improves composability, auditability, and future agent use.

---

# Kill Hypotheses

These are the main assumptions that must prove true for the broader dependency
planning direction to deserve more investment.

### Hypothesis 1: Repositories will accept container-first dependency maintenance

The Python and Java paths must remain practical to run inside the devcontainer
and inside the published images.

If users bypass the container or cannot trust the image-based workflow, the
substrate is not strong enough.

### Hypothesis 2: Safe dependency upgrades can be automated without excessive breakage

The repository must show that `task upgrade` can apply useful updates and still
re-verify the project in a controlled way.

If updates routinely break the examples or templates, the automation remains too
fragile.

### Hypothesis 3: Structured evidence and planning add value beyond raw scanner output

If normalized evidence and plan artifacts do not materially improve triage or
automation, there is no reason to build a separate planning engine.

### Hypothesis 4: A reusable planning core can stay simpler than ad hoc wrappers

If a planning layer becomes more complex than the ecosystem-native tools it is
wrapping, it should not be promoted into a first-class subsystem.

### Hypothesis 5: Python and Java are enough to prove the next set of ideas

Node should not enter the remediation path until the Python and Java
maintenance workflows show real value.

---

# Core Architectural Concepts

Polyglot distinguishes between:

`intent -> capability -> tool adapter`

Example:

`dependency_vulnerability_audit`
-> Python: `pip-audit`
-> Node: `pnpm audit` or `npm audit`
-> Java: `OWASP Dependency-Check`

This prevents the architecture from being tightly coupled to specific tools.

A second important distinction is:

`evidence -> plan -> execution`

Example:

`dependency evidence`
-> current versions, advisories, fixed versions, severity, provenance
-> safe upgrade plan
-> ecosystem-native change execution

This prevents the architecture from collapsing into "just run the updater."

The current repository contract remains the source of truth for local and CI
validation:

- `task init`
- `task lint`
- `task test`
- `task scan`
- `task ci`

Additional task flows may be added for dependency planning and remediation, but
they should extend the existing task workflow rather than replace it.

Any future higher-level interface should only be introduced if it removes
concrete friction that the task contract does not already solve.

---

# Capability Model

The platform defines portable engineering capabilities.

Tools implement these capabilities within specific ecosystems.

| Capability | Description |
|---|---|
| build | compile or package the system |
| test | run automated tests |
| lint | enforce code quality |
| format | enforce code formatting |
| type_analysis | semantic correctness checks |
| dependency_inventory | identify direct and transitive dependencies |
| dependency_vulnerability_audit | detect vulnerable dependencies (CVEs and advisory aliases) |
| dependency_remediation_planning | determine safe target versions and upgrade paths |
| dependency_upgrade | update dependencies safely |
| static_security_analysis | detect insecure coding patterns (CWEs) |
| secret_scan | detect embedded secrets |
| code_modernization | refactor code for new APIs or safer patterns |
| sbom_generation | produce a software bill of materials |
| reachability_analysis | estimate whether vulnerable code paths are actually exercised |
| agent_execution_contract | expose deterministic machine-usable metadata and outputs |

---

# Target Capability Mappings

These are target capability mappings for the first three ecosystems the project
wants to exercise. They are not a claim that every adapter below is already
implemented in this repository.

| Capability | Python | Node / TypeScript | Java |
|---|---|---|---|
| build | packaging tools | `tsc` / bundlers | Maven / Gradle |
| test | `pytest` | Vitest / Jest | Maven Surefire / Gradle test |
| lint | Ruff | ESLint | Checkstyle |
| format | Ruff / Black | Prettier | Spotless |
| type_analysis | MyPy / Pyright | TypeScript compiler | compiler checks / Error Prone class tools later |
| dependency_inventory | lockfiles / SBOM / packaging metadata | lockfiles / SBOM | lockfiles / SBOM / dependency tree |
| dependency_vulnerability_audit | `pip-audit`, OSV-backed tooling | `pnpm audit`, `npm audit`, OSV-backed tooling | OWASP Dependency-Check, OSV-backed tooling |
| dependency_remediation_planning | planning policies over Python evidence | planning policies over Node evidence | planning policies over Java evidence |
| static_security_analysis | Bandit / Semgrep | Semgrep / eslint security rules | SpotBugs / Semgrep |
| secret_scan | `gitleaks` | `gitleaks` | `gitleaks` |
| dependency_upgrade | `pip` / `uv` / Poetry workflows | `npm` / `pnpm` update workflows | Maven Versions Plugin / Gradle versions tooling |
| code_modernization | codemods where available | codemods | OpenRewrite |
| sbom_generation | CycloneDX / Syft | CycloneDX / Syft | CycloneDX / Syft |
| reachability_analysis | limited / later | limited / later | strongest early candidate |
| agent_execution_contract | structured JSON outputs and task metadata | structured JSON outputs and task metadata | structured JSON outputs and task metadata |

---

# Implemented Phases

## Phase 0 - Seed System

Delivered:

- Python devcontainer
- standard `task` workflow
- dependency vulnerability auditing
- secret scanning
- example Python project
- CI workflow running `task ci`

Outcome:

Minimal secure Python development environment.

## Phase 1 - Harden Python Environment

Delivered:

- Ruff lint and format
- MyPy type checking
- pre-commit hooks
- pinned developer tooling
- improved IDE defaults

Outcome:

High-quality Python engineering baseline.

## Phase 2 - Devcontainer Templates

Delivered:

- `templates/python-secure`

Outcome:

Reusable secure Python project template.

## Phase 3 - Node / TypeScript Support

Delivered:

- `templates/node-secure`

Includes:

- pnpm
- ESLint
- Prettier
- Vitest
- standard task lifecycle

Outcome:

Validated TypeScript development environment.

## Phase 4 - Feature Library

Delivered:

- `features/security-baseline`
- `features/python-engineering`
- `features/node-engineering`
- `features/agent-runtime`

Features remain:

- modular
- composable
- minimal

Outcome:

Composable engineering capability modules.

## Phase 5 - Polyglot Devcontainers

Delivered:

- `templates/python-node-secure`

Outcome:

Validated polyglot development workflow.

## Phase 6 - CI/CD and Image Distribution

Delivered:

- image validation pipelines
- OCI image publication
- Trivy scanning
- Cosign signing
- provenance attestations

Published images:

- `ghcr.io/senanayake/polyglot-devcontainers-root`
- `ghcr.io/senanayake/polyglot-devcontainers-java`
- `ghcr.io/senanayake/polyglot-devcontainers-python-node`

Outcome:

Secure development environment artifacts.

## Phase 7 - Java Engineering Environment

Delivered:

- `templates/java-secure`
- `features/java-engineering`
- a Gradle-first Java path
- Java dependency vulnerability auditing and static security analysis inside the
  standard task contract

Outcome:

A practical Java environment now exercises the next set of polyglot ideas
inside this repository.

## Phase 8 - IDE-First Experience

Delivered:

- improved VS Code devcontainer customizations for Python, Node, Java, and the
  repository root workspace
- stronger test discovery and formatter defaults in active templates
- Java and IDE usage documentation additions in the existing Diataxis structure

Outcome:

The active templates are more usable as daily-driver environments in the IDE
without changing the task contract.

## Phase 9a - Initial Dependency Upgrade Slice

Delivered:

- Python dependency upgrade tasks for `templates/python-secure` and
  `examples/python-image-example`
- Java dependency upgrade tasks for `templates/java-secure` and
  `examples/java-image-example`
- normalized dependency inventory artifacts for the Python and Java template and
  published-image example paths
- normalized dependency planning artifacts for the Python and Java template and
  published-image example paths
- upgrade artifacts written into `.artifacts/scans/`

Outcome:

The repository now has a small working dependency-upgrade system for Python and
Java that runs inside the same images and devcontainers it depends on.

---

# Current De-Risking Stage

## Phase 9b - Prove Secure Dependency Maintenance on Real Repositories

Objective:

Move from simple ecosystem-specific upgrade tasks toward an agent-friendly,
security-first dependency maintenance flow that still honors the existing task
contract.

This phase is about proving or killing the next idea, not committing to a fixed
architecture.

The project should continue to eat its own dogfood by developing dependency
remediation capabilities inside the same secure environments that will later run
them.

Expanded objective for this stage:

Automate dependency-oriented detection, planning, and safe upgrade workflows
before taking on broader CWE remediation.

Capabilities to prove:

- dependency inventory
- dependency vulnerability auditing
- secret scanning
- safe dependency upgrade workflows
- machine-readable evidence artifacts
- machine-readable planning artifacts

Automation flow:

`inventory -> audit -> plan -> upgrade -> test -> propose changes`

Key design principles:

- security is a policy overlay, not a separate semver lane
- the system should prefer the lowest safe non-vulnerable version where policy
  allows
- patch, minor, and major changes should remain distinct execution paths
- execution should remain ecosystem-native where possible
- planning and evidence should be captured in structured artifacts

Scope:

- dependency inventory
- dependency vulnerability auditing
- dependency remediation planning
- dependency upgrade workflows
- repository verification after upgrades
- implementation should extend the existing task-based workflow rather than
  introduce a new required command layer
- Python and Java are the proving set for this stage

Non-scope for this stage:

- Node remediation flows
- broad automated source-code rewriting for CWE remediation
- deep reachability analysis
- graph-optimized minimal upgrade solving
- committing to a standalone planning engine

Success signals:

- Python and Java examples remain usable under repeated `task upgrade` runs
- structured evidence artifacts improve operator understanding
- structured plan artifacts help distinguish safe patch/minor/major paths
- the workflow still feels simpler than bespoke per-repo scripting

Current working slice:

- `task deps:inventory` writes normalized dependency inventory artifacts for the
  Python and Java proving paths
- `task deps:plan` writes normalized dependency planning artifacts for the
  Python and Java proving paths
- `task upgrade` continues to execute the ecosystem-native changes and
  re-verify the repository

Failure signals:

- upgrades routinely break verification
- evidence and planning artifacts do not help enough to justify themselves
- the implementation starts to feel more complex than the ecosystem-native tools

Outcome if successful:

The repository earns the right to try a reusable planning core.

Outcome if unsuccessful:

The project should narrow back to simpler ecosystem-native upgrade flows.

---

# Conditional Experiments

## Experiment 10 - Evaluate a Reusable Dependency Planning Core

Hypothesis:

A small reusable planning core could add enough value over raw scanner output
and direct updaters to justify its own existence.

Working name:

`UpgradePath`

Important status:

This is a hypothesis, not a committed architecture.

The repository should not assume from the start that `UpgradePath` must become:

- a standalone package
- a stable CLI
- a separate repository
- the center of the project

Questions to answer:

- can evidence be normalized across Python and Java without adding excessive
  complexity?
- can a planning layer preserve advisory provenance and still stay understandable?
- do users benefit from policy-aware plans enough to justify another layer?

Minimal acceptable shape for experimentation:

- a monorepo-local implementation if needed
- simple test fixtures
- JSON artifacts if they prove genuinely useful
- no hidden coupling that makes rollback difficult

Decision rule:

Either the project proves a planning core is worth keeping, or it learns that
lighter-weight task flows are enough.

## Experiment 11 - Integrate Planning into the Existing Task Workflow

Objective:

If the planning-core hypothesis survives, expose it through the existing task
workflow in the smallest practical way.

Principles:

- complement `task scan` and `task ci`; do not replace them
- prefer optional helper tasks over a new command layer
- keep outputs structured and inspectable

Possible task surface:

- `task deps:inventory`
- `task deps:assess`
- `task deps:plan`
- `task deps:report`

These are examples, not a commitment.

Exit criteria before this phase should be treated as real:

- the planning model has been useful on Python and Java repos
- the JSON outputs are stable enough to rely on
- the extra workflow clearly removes friction rather than adding it

Decision rule:

The repository either gains a practical planning workflow, or it decides not to
promote the experiment further.

## Experiment 12 - Reduce Input Friction for Proven Planning Workflows

Objective:

If planning has proven useful, reduce friction by generating more of the needed
evidence automatically.

Possible directions:

- detect Python and Java projects automatically
- generate SBOMs as needed
- ingest lockfiles and scanner outputs where appropriate
- distinguish direct and transitive dependencies when possible
- classify runtime, dev, test, and build scopes when possible

Node may enter the discussion only after Python and Java flows are clearly
useful.

Decision rule:

Only continue this work if earlier planning experiments are already useful on
real repositories.

## Experiment 13 - Policy-Aware Prioritization

Objective:

If planning survives earlier stages, make the output more operationally useful
by ranking findings with policy and context.

Possible inputs:

- severity
- direct versus transitive status
- runtime versus dev/test scope
- no-fix-yet classification
- suppression metadata with rationale and expiration

Key principle:

CVSS is an important input, not the whole decision engine.

Decision rule:

Only continue this work if policy-aware ranking clearly improves decisions over
plain scanner output.

## Experiment 14 - Static Security Analysis and CWE Remediation

Objective:

Add code-oriented security analysis and targeted remediation workflows after
dependency upgrade automation and planning are working well.

Capabilities:

- static security analysis
- targeted code modernization workflows

Examples:

- Semgrep-based detection
- Java modernization via OpenRewrite
- targeted codemods for safer APIs and framework migrations

Decision rule:

Only continue this work after dependency maintenance and planning are clearly
useful and stable enough to justify a larger problem space.

## Experiment 15 - Reachability Hooks

Objective:

Begin incorporating reachability-style evidence only after dependency planning
has already proven its usefulness.

Possible early directions:

- Java-first experimentation
- CodeQL or equivalent integration points
- test-execution evidence hooks
- classification such as reachable, potentially reachable, not observed,
  unknown

Decision rule:

Only continue this work if reachability evidence materially reduces false
positives or meaningfully changes remediation priority.

## Experiment 16 - Explore Stronger Upgrade Planning

Objective:

Only if earlier phases justify it, explore whether smaller or safer upgrade sets
can be computed across a dependency graph instead of treating each package
independently.

Possible techniques:

- SAT / SMT / optimization-based planning
- policy-defined cost functions
- phased upgrade campaign generation

This should be treated as an advanced experiment, not an expected destination.

Decision rule:

Only continue this work if simpler planning approaches have already proven
useful and the repository has enough fixtures and evidence to evaluate more
advanced methods honestly.

## Ongoing Work - Expand Diataxis Coverage

Objective:

Expand existing Diataxis documentation coverage for the broader Polyglot ideas
being incubated here.

Priority areas:

- capability model
- Java environment setup and operation
- dependency inventory and advisory evidence
- planning workflow experiments
- dependency detection and safe upgrade workflows
- agent-driven devcontainer workflows
- CWE remediation and modernization workflows

Documentation forms:

- tutorials
- how-to guides
- explanations
- reference material

This work should track the experiments that actually survive.

## Conditional Experiment - Agent-Compatible Environments and Contracts

Objective:

Add stronger structured metadata for automation tools and coding agents.

Examples:

- `.devcontainer/agent.json`
- contract-aware command discovery
- structured scan and planning outputs
- explicit machine-usable task metadata
- stable artifact conventions for evidence and plans

This phase should reflect lessons learned while dogfooding planning and
remediation inside the repository.

Decision rule:

Only continue this work if agent-driven planning or remediation inside the
repository proves useful enough to need stronger machine-readable contracts.

## Conditional Experiment - Environment Catalog and Release Channels

Objective:

Clarify consumption modes and release channels for stable reuse.

The project should support both:

- templates and features for authoring and experimentation
- published images for stable consumption

Potential catalog targets:

- `polyglot/python`
- `polyglot/node`
- `polyglot/java`
- `polyglot/python-node`
- later combinations justified by validated workflows

Near-term implementation should evolve from the existing GHCR-published images
and release workflow rather than introducing a wholly separate distribution
model.

Potential release channels:

- stable
- candidate
- nightly

If a planning core proves stable and valuable outside this repository, it may
later be extracted from the monorepo into its own repository and release
cadence.

That extraction should happen only after:

- real reuse value is proven
- command and artifact contracts are stable enough
- independent tests and fixtures justify the split

Decision rule:

Only continue this work when the published-image set and downstream consumption
patterns are broad enough to justify more formal release channels.

## Conditional Experiment - Upgrade Recipes

Objective:

Introduce reusable modernization recipes once the capability and contract layers
have proven useful.

Examples:

- Python runtime upgrades
- Node ecosystem migrations
- Java framework upgrades
- policy-aware upgrade campaigns generated from proven planning evidence

Inspired by:

- OpenRewrite
- codemod frameworks

Decision rule:

Only continue this work after the repository has proven evidence, planning, and
upgrade workflows that are worth turning into reusable recipes.

## Potential Future Idea - Polyglot Interface Layer

The repository may later evaluate a higher-level Polyglot interface such as a
CLI or machine-readable contract if real usage shows that the existing task
contract is not enough.

That idea should only move forward if it clearly removes concrete friction such
as:

- cross-repository environment startup
- cross-ecosystem capability resolution
- agent-oriented command discovery beyond task names alone
- external tooling that cannot cleanly integrate with the current task contract

Until that need is proven, `task` remains the primary contract and the simpler
working system.

---

# Non-goals

The repository intentionally avoids:

- enterprise-specific assumptions
- proprietary integrations
- large platform frameworks before the substrate is proven
- supporting every language at once
- universal containers containing every runtime
- complex orchestration systems
- platform lock-in
- release pipelines that bypass `task ci`
- broad abstractions that replace concrete working environments too early
- turning a planning hypothesis into a broad auto-editing system before its
  evidence model is proven

---

# Long-Term Vision

`polyglot-devcontainers` aims to provide portable, secure, and automated
development environments that work consistently across local machines, CI
systems, and automated tooling.

The near-term path remains substrate-first:

- secure devcontainers
- simple task-based workflows
- reproducible engineering environments
- polyglot capability mappings

Within that substrate, the project may now test a security-first,
agent-friendly dependency planning direction, but that direction remains a
hypothesis until the real de-risking work proves it.

If the broader Polyglot interface and contract ideas prove useful, they can be
evaluated here later, but they are not part of the committed near-term
execution plan.
