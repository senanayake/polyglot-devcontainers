---
id: KB-2026-026
type: design-space
status: draft
created: 2026-04-23
updated: 2026-04-23
tags: [python, images, security, dependency-updates, remediation, codemods, testing, kbpd]
related: [KB-2026-002, KB-2026-013, KB-2026-014, KB-2026-020, KB-2026-021, KB-2026-022, KB-2026-023, KB-2026-024]
---

# Python Image Security and Remediation Tooling Design Space

## Context

The repository already has a clear Python proving path:

- `uv` and `uv.lock` are the first-class dependency workflow
- Python workspaces install developer tooling into project-local virtual
  environments with `uv sync --frozen --extra dev`
- `pip-audit` findings are evaluated through a repository-owned policy overlay
- repo-owned Python tasks expose `deps:inventory`, `deps:plan`, `deps:report`,
  and `upgrade`
- published images stay intentionally lean and do not pre-install every Python
  development or remediation tool

That working slice is valuable, but it creates a new design question:

Which additional Python-oriented libraries should be leveraged in the polyglot
Python images and task workflows to improve security and automated remediation
without bloating the images or duplicating existing capabilities?

## Problem Statement

The repository needs a practical way to evaluate a broad set of Python tooling
for:

- vulnerability detection
- secret detection
- code modernization
- semantic remediation
- test hardening
- notebook and template support

The decision cannot be based on generic ecosystem popularity alone. It has to
fit the repository's actual constraints:

- container-first validation
- task-contract-first workflows
- evidence before mutation
- minimal maintenance burden
- strong security value per added dependency
- no premature expansion into broad framework-specific automation

## Design Space Dimensions

Key variables that define the solution space:

- Default image footprint: should the tool live in the image, the workspace, or
  only in specialized maintenance flows?
- Security leverage: does the tool materially improve exploit detection,
  prevention, or safe remediation?
- Automation leverage: can the tool drive repeatable evidence, planning, or
  code changes with low human effort?
- False-positive and policy cost: how much policy tuning, exception handling, or
  developer education does the tool require?
- Scope specificity: is the tool broadly reusable across Python paths, or only
  for notebooks, Django, legacy typing, or specific migration campaigns?

## Current Repository Baseline

The active Python proving paths currently center on:

- `uv`, `uv.lock`, and `uv sync --frozen --extra dev`
- `pip-audit` plus `security-scan-policy.toml` and
  `scripts/evaluate_python_audit_policy.py`
- `ruff`, `mypy`, `pytest`, and `pytest-cov`
- `gitleaks` for repository secret scanning
- normalized dependency evidence via `dependency-inventory.json`,
  `dependency-plan.json`, `dependency-report.json`, and `pypi-upgrades.json`

Evidence in repo:

- [`templates/python-secure/pyproject.toml`](../templates/python-secure/pyproject.toml)
- [`examples/python-image-example/pyproject.toml`](../examples/python-image-example/pyproject.toml)
- [`examples/python-maintenance-example/tasks.py`](../examples/python-maintenance-example/tasks.py)
- [`templates/python-node-secure/tasks.py`](../templates/python-node-secure/tasks.py)
- [`scripts/evaluate_python_audit_policy.py`](../scripts/evaluate_python_audit_policy.py)
- [`man/man7/polyglot-python.7`](../man/man7/polyglot-python.7)
- [`man/man7/polyglot-security.7`](../man/man7/polyglot-security.7)

This means the real decision is not "what tools exist?" but "which additional
layers strengthen the current model without replacing it?"

## Options in the Space

### Option A: Keep the current lean baseline and strengthen evidence output

**Position in space:**

- Default image footprint: low
- Security leverage: medium to high
- Automation leverage: medium
- False-positive and policy cost: low

**Characteristics:**

- Keep `uv`, `pip-audit`, `ruff`, `mypy`, `pytest`, and `gitleaks` as the
  default Python lane
- Extend evidence using `uv export` for standardized lock exports or SBOM
  generation where useful
- Keep mutation grounded in existing `task deps:*` and `task upgrade` flows
- Add only tools that integrate cleanly into repo policy and artifacts

**Strengths:**

- Best preserves the proven repository architecture
- Lowest image and onboarding cost
- Strong fit with KB-2026-002 and KB-2026-020

**Weaknesses:**

- Leaves some security classes uncovered at the Python source level
- Relies heavily on dependency and secret scanning rather than source-security
  analysis

**Constraints:**

- Needs additional layers if the repo wants deeper Python security posture than
  package CVEs and secret scanning alone

### Option B: Add a Python source-security lane

**Position in space:**

- Default image footprint: low to medium if workspace-local, medium if baked in
- Security leverage: high
- Automation leverage: medium
- False-positive and policy cost: medium

**Characteristics:**

- Add `bandit` and `detect-secrets` as Python-specific source scanning tools
- Keep them task-wrapped and artifact-producing rather than ad hoc CLI tools
- Use them to complement, not replace, `pip-audit` and `gitleaks`

**Strengths:**

- `bandit` catches common insecure Python coding patterns and supports baseline,
  severity, confidence, and JSON output
- `detect-secrets` gives a baseline-centered workflow that is closer to the
  repo's explicit policy and exception model than naive full-history blocking
- Improves "new issue prevention" rather than only "dependency issue
  reporting"

**Weaknesses:**

- More false-positive management than current `pip-audit` policy overlay
- Potential overlap with `gitleaks` unless roles are defined carefully
- `bandit` findings are useful, but many do not auto-remediate by themselves

**Constraints:**

- Better as workspace-local dev dependencies and task/report layers than as
  unconditional base-image tools

### Option C: Add a test-hardening lane for upgrade confidence

**Position in space:**

- Default image footprint: low if optional, medium if always installed
- Security leverage: indirect but meaningful
- Automation leverage: high for safe upgrades
- False-positive and policy cost: low to medium

**Characteristics:**

- Add selective use of `pytest-xdist`, `pytest-randomly`, and `hypothesis`
- Treat these as confidence multipliers for automated dependency remediation
- Use them to make `task upgrade` safer, not just faster

**Strengths:**

- `pytest-xdist` reduces the feedback cost of broader verification
- `pytest-randomly` helps expose hidden order dependencies that make automated
  upgrades risky
- `hypothesis` finds edge cases that example-based tests often miss, which is
  especially valuable for dependency and framework refreshes

**Weaknesses:**

- Does not directly reduce vulnerability counts
- Can expose latent test flakiness and therefore increase short-term noise
- Property-based testing only pays off where there are good functional
  invariants to encode

**Constraints:**

- Strong fit for proving fixtures and richer starters
- Weak fit for minimal examples where the test surface is intentionally tiny

### Option D: Add a semantic remediation and modernization lane

**Position in space:**

- Default image footprint: low if on-demand, high if always installed
- Security leverage: high when tied to upgrade campaigns
- Automation leverage: high
- False-positive and policy cost: medium

**Characteristics:**

- Use `pyupgrade`, `flynt`, `LibCST`, and `Fixit` as code transformation tools
- Reserve `django-upgrade` and `django-codemod` for framework-specific paths,
  not as general image defaults
- Treat codemods as a campaign tool for migration and remediation, not a
  day-one default

**Strengths:**

- `pyupgrade` and `flynt` can cheaply modernize Python syntax and make future
  upgrades easier
- LibCST provides a lossless CST and codemod framework suitable for safe,
  reviewable automated rewrites
- Fixit adds custom lint rules with auto-fixes, which is a good fit for
  repository-specific guardrails once a rule is proven valuable

**Weaknesses:**

- These tools require rule design and testing, not just installation
- The value is highest when there is a repeated migration pattern to encode
- Framework-specific codemods create scope pressure beyond the current proving
  path

**Constraints:**

- Should be added as an opt-in maintenance layer, not bundled into the default
  Python image

### Option E: Add notebook and template workflow layers

**Position in space:**

- Default image footprint: low to medium depending on target audience
- Security leverage: low direct, medium indirect
- Automation leverage: medium
- False-positive and policy cost: low

**Characteristics:**

- Use `nbqa` and `papermill` only for notebook-bearing templates or scenarios
- Use `python-dotenv` only when a template truly benefits from local `.env`
  parity
- Use `copier` for template lifecycle and repo bootstrap governance, not for
  runtime security

**Strengths:**

- `nbqa` lets notebook workflows reuse the same lint rules and pre-commit model
- `papermill` provides parameterized, recorded notebook execution for CI or
  data pipelines
- `copier` is useful for regenerating or updating templated repositories over
  time

**Weaknesses:**

- These tools do not meaningfully strengthen the current core Python security
  posture on their own
- They add weight mainly for notebook-heavy or template-governance use cases,
  which are not the current center of the repo

**Constraints:**

- Better treated as scenario- or template-specific additions than as baseline
  image content

### Option F: Expand environment and matrix orchestration

**Position in space:**

- Default image footprint: medium
- Security leverage: indirect
- Automation leverage: medium
- False-positive and policy cost: low

**Characteristics:**

- Add `nox` or `tox` when the repository genuinely needs multi-interpreter or
  multi-environment orchestration beyond the task contract
- Keep `task` as the public interface even if these are added underneath

**Strengths:**

- Good for compatibility testing across Python versions
- Can help when templates evolve into multi-matrix proving systems

**Weaknesses:**

- The repository already has a task-contract-first orchestration layer
- Adding `tox` or `nox` too early risks duplicating `task` rather than
  extending it
- They do not directly improve remediation unless multi-version validation is a
  real blocker

**Constraints:**

- Useful later if Python support widens materially
- Not justified as a default today

## Library-Level Assessment

### High-leverage now

- `pip-audit`: already well aligned with the repository; strongest immediate
  Python security tool because it supports machine-readable output and automated
  fix mode while fitting the repo's policy overlay
- `uv`: already the right default; its newer export paths, including PEP 751
  `pylock.toml` and CycloneDX export, make it more useful as a security and
  artifact source than a resolver alone
- `detect-secrets`: best candidate to evaluate next if the repo wants a
  baseline-based Python-adjacent secret policy in addition to `gitleaks`
- `bandit`: best candidate to evaluate next for Python source-security checks
- `pytest-randomly`, `pytest-xdist`, `hypothesis`: best candidates for raising
  confidence in automated remediation workflows

### Useful, but only in targeted workflows

- `pip-tools`: useful as a compatibility-detection path, already reflected in
  the repo's task logic, but no longer the primary optimization target
- `pyupgrade`, `flynt`: useful for low-risk modernization sweeps
- `LibCST`, `Fixit`: valuable for reusable remediation codemods and policy
  enforcement once repeated patterns exist
- `python-dotenv`: useful for app templates that intentionally support `.env`
  development flows
- `nbqa`, `papermill`: useful if notebook support becomes first-class
- `copier`: useful for template lifecycle, not for runtime security
- `pyright`: reasonable as a faster complementary type checker, but it would be
  additive to `mypy`, not an obvious replacement in the current path
- `pytest-bdd`: only useful if requirements-style acceptance testing becomes a
  first-class proving path

### Low-priority or currently misaligned

- `tox`, `nox`: premature while `task` is the public contract and Python is
  still intentionally narrow
- `django-upgrade`, `django-codemod`: valuable only if the repository
  intentionally adopts Django-based starters
- `MonkeyType`, `pyannotate`, `com2ann`: niche for incremental typing
  migrations, but not core to the current Python image mission
- `rope`, `bowler`, `fissix`, `modernize`: older or more migration-specific
  refactoring tools with weaker fit than LibCST/Fixit for new repository-owned
  automation
- `tree-sitter`: useful for specialized analysis, but not a strong next default
  compared with LibCST for Python-safe transforms

## Design Space Map

| Option | Image Cost | Security Gain | Remediation Gain | Repo Fit | Viable? |
|--------|------------|---------------|------------------|----------|---------|
| A. Lean baseline + better evidence | Low | Medium | Medium | High | Yes |
| B. Source-security lane | Low-Med | High | Medium | High | Yes |
| C. Test-hardening lane | Low-Med | Indirect | High | High | Yes |
| D. Semantic remediation lane | Low if on-demand | High | High | Medium-High | Yes |
| E. Notebook/template layers | Low-Med | Low | Medium | Medium | Yes, selectively |
| F. tox/nox matrix expansion | Medium | Low | Medium | Low-Medium | Not now |

## Dominated Solutions

Options that are strictly worse than others:

- "Install everything in the base image" is dominated by layered,
  workspace-local tooling because it increases image weight and maintenance
  without improving proof quality
- "Use raw scanner CLIs with no repo policy wrapper" is dominated by the
  current evidence-and-policy model because it creates less reusable knowledge
  and weaker operator understanding
- "Replace `uv` with `pip-tools` as the default" is dominated by the current
  repo standard because it would move away from the already validated Python
  workflow
- "Adopt framework-specific codemods as default image content" is dominated by
  on-demand semantic remediation because the current repo does not yet have
  those framework commitments

## Pareto Frontier

The non-dominated choices for this repository are:

- Lean baseline plus stronger evidence
- Source-security lane as a targeted extension
- Test-hardening lane for safer automation
- Semantic remediation lane as an on-demand maintenance layer

These four choices each optimize a different dimension without clearly
dominating the others.

## Constraints That Narrow the Space

Hard constraints that eliminate options:

- The maintainer container and published images should remain intentionally
  curated, not kitchen-sink toolboxes
- The public contract is `task`, not direct invocation of every ecosystem tool
- The repository's first-class Python path is `uv` and `uv.lock`
- Security policy should stay declarative and reviewable
- The repo currently prioritizes Python and Java proving paths, with Node only
  now beginning to inherit the same structure

## Unexplored Regions

Areas not yet proven in this repository:

- using `uv export --format pylock.toml` or CycloneDX to extend Python security
  artifacts
- adding a Python source-security task/report layer with `bandit`
- comparing `detect-secrets` baseline workflows against current `gitleaks`
  behavior for starter repos and non-git workspaces
- using `pytest-randomly` and `hypothesis` specifically as upgrade-confidence
  tools rather than generic testing add-ons
- proving LibCST or Fixit for a concrete Python remediation campaign

## Evidence

### Repository evidence

- Maintained Python paths use `uv` lockfiles and task-wrapped dependency
  evidence and upgrade flows
- `pip-audit` is already policy-wrapped rather than used as a raw gate
- Python images deliberately install a small toolchain in the image and rely on
  project-local dependency install for workspace tools

### Upstream documentation reviewed

- `pip-audit` supports machine-readable output, CycloneDX SBOM output, and
  `--fix`: [PyPI](https://pypi.org/project/pip-audit/),
  [GitHub](https://github.com/pypa/pip-audit)
- `uv` supports lock export to `requirements.txt`, `pylock.toml`, and
  CycloneDX, and supports syncing exact environments:
  [Locking/compile](https://docs.astral.sh/uv/pip/compile/),
  [Export](https://docs.astral.sh/uv/concepts/projects/export/),
  [Layout](https://docs.astral.sh/uv/concepts/projects/layout/)
- `pip-tools` remains a deterministic compile/sync path:
  [docs](https://pip-tools.readthedocs.io/)
- `detect-secrets` is explicitly baseline-oriented:
  [GitHub](https://github.com/Yelp/detect-secrets)
- `bandit` supports severity, confidence, JSON output, and baselines:
  [Bandit CLI docs](https://bandit.readthedocs.io/en/latest/man/bandit.html)
- `nbqa` integrates with `pre-commit`:
  [docs](https://nbqa.readthedocs.io/en/latest/pre-commit.html)
- `papermill` supports parameterized notebook execution:
  [execute docs](https://papermill.readthedocs.io/en/latest/usage-execute.html),
  [workflow reference](https://papermill.readthedocs.io/en/latest/reference/papermill-workflow.html)
- LibCST provides codemod support:
  [Codemods](https://libcst.readthedocs.io/en/latest/codemods.html)
- Fixit provides lint rules with auto-fixes on top of LibCST:
  [overview](https://fixit.readthedocs.io/en/latest/),
  [API](https://fixit.readthedocs.io/en/latest/api.html)
- `python-dotenv` supports loading `.env` files without overriding existing
  environment variables by default:
  [PyPI](https://pypi.org/pypi/python-dotenv)
- `pytest-bdd`, `pytest-cov`, `pytest-xdist`, `pytest-randomly`, `hypothesis`,
  `mypy`, `nox`, and `tox` all remain current and maintained options for their
  niche roles:
  [pytest-bdd](https://pytest-bdd.readthedocs.io/),
  [pytest-cov](https://pytest-cov.readthedocs.io/en/latest/readme.html),
  [pytest-xdist](https://pytest-xdist.readthedocs.io/),
  [pytest-randomly](https://pypi.org/pypi/pytest-randomly),
  [Hypothesis](https://hypothesis.readthedocs.io/),
  [mypy](https://mypy.readthedocs.io/en/stable/existing_code.html),
  [pyright](https://github.com/microsoft/pyright),
  [nox](https://nox.thea.codes/en/latest/config.html),
  [copier](https://copier.readthedocs.io/en/stable/updating/)

## Insights

Key learnings from mapping the space:

- The highest-value next step is not another dependency manager. The repo
  already chose the right one for its current Python path.
- The strongest incremental security value now comes from adding either
  Python-source scanning (`bandit`, possibly `detect-secrets`) or stronger
  upgrade-confidence testing (`pytest-randomly`, `hypothesis`, `pytest-xdist`).
- Codemod tooling is promising, but only once tied to a concrete repeated
  migration or remediation need.
- Several libraries on the candidate list are good tools in general but weak
  defaults for these images because their scope is too specialized.

## Decision Guidance

### Narrowing the Space

Progressive elimination path:

1. Keep `uv` as the default and reject dependency-manager churn.
2. Prefer additions that strengthen either:
   - policy-aware security scanning, or
   - automated remediation safety.
3. Reject tools that only make sense for notebooks, Django, or large typing
   migrations unless those paths become first-class.
4. Add code-rewriting tools only after a repeated manual pattern has been
   observed.

### Convergence Strategy

Recommended convergence order:

1. Evaluate a Python source-security experiment with `bandit`.
2. Evaluate whether `detect-secrets` adds value beyond current `gitleaks`
   behavior for starter repos and non-git scans.
3. Add a test-hardening experiment using `pytest-randomly` and, where useful,
   `hypothesis`.
4. Only then consider a LibCST/Fixit codemod lane for repeated Python
   remediation patterns.

## Implications

What this design space means for the repository:

- The default Python image should remain lean.
- Security and remediation value should come from task-wrapped layers and
  structured artifacts, not from indiscriminately expanding the image.
- The repo should continue to separate:
  - baseline image responsibilities
  - workspace-local developer tool installation
  - specialized maintenance or migration tooling

## Recommendations

Suggested path forward:

- Keep `pip-audit`, `uv`, `ruff`, `mypy`, `pytest`, and `gitleaks` as the core
  Python baseline.
- Prioritize experiments around `bandit`, `detect-secrets`, `pytest-randomly`,
  `pytest-xdist`, and `hypothesis`.
- Treat `LibCST` and `Fixit` as opt-in remediation infrastructure once the repo
  has a concrete repeated migration or secure-coding rule worth encoding.
- Keep `pip-tools` as a compatibility-detection path only.
- Do not add `tox`, `nox`, Django codemods, legacy typing generators, or
  notebook tooling to the default images without a stronger proving need.

## Applicability

Where this design space applies:

- Applies to:
  - repo-owned Python images and starters
  - task-driven Python dependency maintenance flows
  - security and remediation decisions for future Python starter hardening
- Does not apply to:
  - Django-specific repositories unless a Django starter becomes first-class
  - notebook-heavy data-science images unless notebooks become a primary repo
    target
  - broad portfolio-scale semantic migrations outside the repository's current
    proving scope

## Related Knowledge

- KB-2026-002 on `uv` as the Python standard
- KB-2026-013 on risk-driven CVE management
- KB-2026-014 on reducing CVE inflow
- KB-2026-020 on lockfiles plus continuous refresh
- KB-2026-021 on upgrade bots versus semantic migration tooling
- KB-2026-022 on lifecycle governance
- KB-2026-023 on transitive overrides as exceptions
- KB-2026-024 on the analogous Node design space
