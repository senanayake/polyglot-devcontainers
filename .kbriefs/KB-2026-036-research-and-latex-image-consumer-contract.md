---
id: KB-2026-036
type: standard
status: active
created: 2026-05-16
updated: 2026-05-16
tags: [devcontainer, research-runner, latex, reproducibility, ghcr, image-metadata, kbpd]
related: [KB-2026-025, KB-2026-037]
---

# Research and LaTeX Devcontainer Image Consumer Contract

## Context

The repository needed two new published-image shapes for a paper artifact:
a Python/Node research runner and a standalone LaTeX builder. The images must
work when consumed directly through an `"image"` reference, not only when the
template source is opened from this repository.

## Problem/Need

Downstream artifact repositories need a small, reproducible contract:
- the image supplies execution tooling
- the downstream repository supplies code, lockfiles, data, and paper source
- task commands provide the reproducibility interface
- generated dependency folders and PDFs remain out of source control

## Standard/Pattern

### Description

Published devcontainer images that are intended for direct reuse must embed the
runtime defaults and bootstrap behavior in image metadata and image filesystem
content. Downstream repositories should be able to declare only:

```json
{
  "image": "ghcr.io/senanayake/polyglot-devcontainers-<name>:main"
}
```

and still get the correct `remoteUser`, lifecycle command, editor defaults,
runtime docs, and task runner behavior.

### Key Principles

- Keep execution dependencies in the image, not copied from the research
  workspace.
- Keep project dependencies in downstream lockfiles and install them with
  `task init`.
- Keep generated outputs reproducible but uncommitted unless intentionally
  released.
- Validate the final built image label with
  `scripts/validate_devcontainer_metadata.py`; source JSON alone is not proof.

### Implementation

For research artifacts:

```text
image: ghcr.io/senanayake/polyglot-devcontainers-research-runner:main
task init -> verify /opt/research-venv, Python packages, Node, npm, task
task test -> deterministic no-key validation
task experiment -> API-consuming experiment, requires OPENAI_API_KEY
```

For paper artifacts:

```text
image: ghcr.io/senanayake/polyglot-devcontainers-latex:main
task init -> verify TeX Live, BibTeX, latexmk, IEEEtran, TikZ, chktex, texcount
task build -> latexmk -pdf
task test -> build and validate main.pdf with pdfinfo
```

## Rationale

- A direct image reference is the lowest-friction path for paper artifacts and
  AI agents.
- Embedded metadata prevents downstream projects from repeating repository
  defaults like `remoteUser` and lifecycle commands.
- Separate research and paper images keep TeX Live size out of code execution
  containers and keep API tooling out of LaTeX containers.
- Task commands give a stable acceptance interface across local use, CI, and
  artifact review.

## Evidence

- `task maintainer:task -- image:build` succeeded after adding the two images
  and validating `devcontainer.metadata`.
- Research starter bootstrap smoke passed with
  `polyglot-devcontainers-research-runner:verify`.
- Downstream artifact validation passed in the research image with `task ci`.
- Downstream paper validation passed in the LaTeX image with `task ci` and
  produced an 8 page `main.pdf` in the temporary validation copy.
- `task maintainer:task -- image:verify` passed for the full image build,
  starter smoke, metadata, and template validation path.
- `task maintainer:task -- image:scan` passed and generated residual-risk
  summaries for the new `research-runner` and `latex` images.

## Constraints

- Repository maintenance and image validation must run inside the maintainer
  container.
- `OPENAI_API_KEY` must be passed as an environment variable for API-consuming
  experiment runs; no key is required for deterministic validation.
- Generated dependency folders, Python caches, and PDFs should be excluded from
  copied artifact source.

## Alternatives Considered

### Single Combined Image

Rejected because combining Python/Node research tooling with full TeX Live
would increase image size and vulnerability surface for both workflows.

### Downstream Dockerfiles

Rejected for the acceptance path because the project goal is published,
reusable devcontainer images with repo-owned metadata.

## Verification

Use the maintainer container to run:

```bash
task image:build
bash scripts/smoke_test_published_starter.sh --image polyglot-devcontainers-research-runner:verify
bash scripts/smoke_test_published_starter.sh --image polyglot-devcontainers-latex:verify
```

Then validate a downstream artifact by mounting it into each image and running:

```bash
task ci
```

## Applicability

Use this pattern for research or publication artifacts that need reproducible
execution and paper builds without copying local dependency installations.
