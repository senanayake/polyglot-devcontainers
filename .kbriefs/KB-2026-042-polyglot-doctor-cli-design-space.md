---
id: KB-2026-042
type: design-space
status: draft
created: 2026-05-09
updated: 2026-05-09
tags: [cli, doctor, polyglot-doctor, local-first, compliance, agent-ready, fleet]
related: [KB-2026-041, KB-2026-040, KB-2026-029]
---

# polyglot doctor CLI Design Space

## Context

The project's task contract gives every maintained repository a stable entry
point (`task init / lint / test / scan / ci`). What it does not yet provide is
a way to answer the question: "Is this repository actually compliant with the
Polyglot contract?" without running the full CI pipeline.

A `polyglot doctor` command fills this gap: a local-first diagnostic that reads
a project and reports its contract compliance, scan status, image signing state,
and agent-readiness in a single human-readable (and machine-readable) report.

## Problem Statement

How should `polyglot doctor` be designed so that:

- it runs locally without a container dependency (host CLI)
- it reads existing artifacts and the contract file rather than executing tools
- CI can invoke it and fail on policy violations
- AI agents can parse its output to understand repository readiness
- the implementation remains minimal until real usage proves its value

## Design Space Dimensions

Key variables:
- Execution model (host CLI vs. container-only vs. both)
- Input model (reads artifacts vs. executes scanners vs. both)
- Output model (human prose vs. structured JSON vs. both)
- Distribution model (Python package vs. shell script vs. container task vs. task verb)
- Scope (single-repo vs. fleet)

## Options in the Space

### Option A: Task Verb Only (Zero New Tooling)

**Position in space:**
- Execution model: container-only (runs inside maintainer image)
- Input model: reads existing artifacts
- Output model: console output only
- Distribution model: task verb
- Scope: single-repo

**Characteristics:**
Implement `polyglot doctor` as a new `task` verb that runs inside the
maintainer container. No new CLI distribution required.

```yaml
doctor:
  desc: Check repository contract compliance and report health
  cmds:
    - python scripts/doctor.py
```

- Strengths: no packaging, no distribution, works immediately, consistent with
  project's container-authoritative execution model.
- Weaknesses: requires the maintainer container to run; not a host-native CLI;
  weak product identity for enterprise demos.
- Constraints: sufficient for internal use; insufficient for standalone adoption.

### Option B: Python CLI Package (Recommended)

**Position in space:**
- Execution model: host-native (pip install polyglot-doctor) + task verb
- Input model: reads existing artifacts and contract file
- Output model: console table + optional JSON
- Distribution model: Python + Typer, published to PyPI
- Scope: single-repo, with fleet extension path

**Characteristics:**
A `polyglot-doctor` Python package built with Typer that reads the
`.polyglot-contract.yaml` and `.artifacts/` directory, then reports:

```
$ polyglot doctor

Polyglot Contract    PASS  (.polyglot-contract.yaml found, v0.1)
Devcontainer         PASS  (.devcontainer/devcontainer.json found)
Taskfile             PASS  (init, lint, test, scan, ci verified)
SBOM                 PASS  (.artifacts/sbom.spdx.json found)
Secret Scan          PASS  (.artifacts/scans/gitleaks.sarif found, 0 findings)
Vulnerability Scan   WARN  (.artifacts/scans/trivy.json, 2 medium, 0 critical)
Image Signature      SKIP  (no image artifact declared)
Provenance           SKIP  (not configured)
Agent Ready          PASS  (contract tasks and artifacts resolvable)

Overall: WARN (1 warning, 0 failures)
```

- Strengths:
  - Standalone product identity.
  - Host-native for enterprise demos.
  - Typer gives --help, --json, --output automatically.
  - Can be published to PyPI and installed with `pipx install polyglot-doctor`.
  - Fleet extension: `polyglot fleet scan ./repos --output report.html`.
- Weaknesses:
  - Requires packaging and PyPI publishing infrastructure.
  - Python version compatibility on host machines must be managed.
- Constraints:
  - Should read artifacts, not re-execute scanners — to stay fast and dry-run safe.

### Option C: Container-Native Only (polyglot/cli image)

**Position in space:**
- Execution model: Docker/Podman pull-and-run
- Input model: mounts project directory, reads artifacts
- Output model: console + JSON
- Distribution model: GHCR image
- Scope: single-repo

**Characteristics:**
Distribute `polyglot doctor` as a container image that users run with:
```
docker run --rm -v $(pwd):/project ghcr.io/senanayake/polyglot-cli doctor
```

- Strengths: no host dependencies; consistent execution environment.
- Weaknesses:
  - Requires container runtime on the host.
  - Slow for quick compliance checks.
  - Weak developer UX compared to a native CLI.
- Constraints: viable as a CI step but poor as an enterprise demo entry point.

## Design Space Map

| Option | Execution | Input | Output | Distribution | Fleet path |
|--------|-----------|-------|--------|-------------|------------|
| A: Task verb | Container | Artifacts | Console | Task | No |
| B: Python CLI | Host + container | Artifacts | Console + JSON | PyPI + task | Yes |
| C: Container CLI | Container | Artifacts | Console + JSON | GHCR | Partial |

## Dominated Solutions

Option C is dominated by Option B for adoption: a Python CLI is faster to
install and easier to demo than pulling a container image.

## Recommended Implementation

Option B with Option A as the implementation path:

1. Implement doctor logic in `scripts/doctor.py` (runs in container).
2. Wire as `task doctor` verb (Option A, immediate).
3. Package as Python CLI with Typer when demo value justifies distribution.
4. Add `polyglot fleet scan` as a subcommand once single-repo is proven.

## CLI Command Design

Recommended minimal commands for v0.1:

```
polyglot init --profile python-api-secure    # generate starter
polyglot check-contract                       # validate .polyglot-contract.yaml
polyglot doctor                               # full health report
polyglot scan-summary                         # summarize scan artifacts
polyglot repo-report                          # full report as markdown
polyglot fleet scan ./repos --output report.html  # fleet-level report
```

Minimum viable: `polyglot doctor` only for v0.1.

## Check Catalog for doctor v0.1

| Check | Source | Pass condition |
|-------|--------|---------------|
| Contract file present | .polyglot-contract.yaml | file exists + valid schema |
| Contract version | .polyglot-contract.yaml | contractVersion field present |
| Devcontainer | .devcontainer/devcontainer.json | file exists |
| Taskfile | Taskfile.yml | init/lint/test/scan/ci verbs present |
| SBOM | artifacts.sbom path from contract | file exists |
| Secret scan | artifacts.sarif path from contract | file exists, 0 critical |
| Vulnerability scan | artifacts.scan path from contract | file exists, policy.criticalVulnerabilities |
| Image signature | artifacts.signature from contract | file exists or SKIP |
| Agent ready | all tasks resolvable, artifacts resolvable | composite |

## Constraints That Change the Trade-Off

- If `.polyglot-contract.yaml` is not yet adopted, doctor can fall back to
  heuristic detection (find Taskfile.yml, find .devcontainer/).
- If fleet use cases emerge, Option B's fleet subcommand path must be built
  before the report UI is needed.

## Implications

- Architecture: `polyglot doctor` is a read-only compliance reporter, not an
  executor. It reads artifacts produced by `task scan / task ci`.
- Roadmap: implement as task verb first, promote to standalone CLI when demo
  value is proven.
- Agent readiness: `--json` output makes doctor consumable by AI agents
  without screen-scraping.

## Recommendations

1. Implement `task doctor` as `scripts/doctor.py` (container-based, immediate).
2. Generate JSON output for agent consumption from day one.
3. Promote to a standalone Python/Typer CLI before the killer demo.
4. Do not build the SaaS fleet dashboard until the CLI fleet report is proven.

## Applicability

Applies to: Phase 4 implementation, enterprise demo preparation, agent
integration, fleet reporting foundation.
Does not apply to: image build, scan execution, template generation.
