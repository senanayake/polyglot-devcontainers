# Runtime Documentation Architecture

This page describes the in-container runtime documentation system for
`polyglot-devcontainers`.

The goal is practical:

- a human or agent should be able to enter the container
- start from a top-level page such as `man polyglot`
- discover the correct starter and task workflow
- recover enough context to operate correctly
- follow strong software engineering and security practice without depending on
  external browsing or prior chat context

## Design goals

The runtime documentation system is:

- local to the container
- readable by both humans and agents
- authored in concise Markdown
- compiled into terminal-native output during the build pipeline
- aligned with the validated task contract and artifact conventions
- capable of carrying both repository-specific guidance and a curated baseline
  of strong engineering judgment

## Source of truth

Markdown remains the canonical authoring format.

The repository avoids writing roff by hand.

The authoring model is:

- repository Markdown pages are the source of truth
- build-time tooling converts selected pages into man pages
- runtime users consume those pages through `man`

Pandoc is used for the conversion step, but only as build-time tooling.
Humans and agents inside the container should never need to invoke it
directly. The repository provides a builder script at
`scripts/build_runtime_docs.py`, which uses local `pandoc` when available and
can fall back to a containerized `pandoc` invocation through `podman`.

## Runtime delivery model

The documentation system compiles selected Markdown files into:

- `man/man7/polyglot.7`
- `man/man7/polyglot-starters.7`
- `man/man7/polyglot-task-contract.7`
- `man/man7/polyglot-python.7`
- `man/man7/polyglot-java.7`
- `man/man7/polyglot-security.7`
- `man/man7/polyglot-deps.7`
- `man/man7/polyglot-agents.7`
- `man/man7/polyglot-knowledge.7`
- `man/man7/polyglot-troubleshooting.7`

Most of these belong in section `7` because they describe conventions,
workflows, and environment guidance rather than standalone executable commands.

## Top-down navigation model

The runtime help system is navigable from the top down.

The minimum intended flow is:

1. `man polyglot`
2. choose a starter path
3. read the relevant workflow page such as `polyglot-python` or
   `polyglot-java`
4. read `polyglot-task-contract`
5. consult `polyglot-security`, `polyglot-deps`, `polyglot-agents`, or
   `polyglot-troubleshooting` as needed

The important design rule is that users and agents should not need to know the
repository structure in advance to find the correct operating guidance.

## Recommended source layout

The documentation source tree is explicit and separate from the existing
Diataxis pages that target the repository website or Markdown readers.

Current source layout:

- `docs/core/polyglot.md`
- `docs/core/polyglot-starters.md`
- `docs/core/polyglot-task-contract.md`
- `docs/core/polyglot-python.md`
- `docs/core/polyglot-java.md`
- `docs/core/polyglot-security.md`
- `docs/core/polyglot-deps.md`
- `docs/core/polyglot-agents.md`
- `docs/core/polyglot-knowledge.md`
- `docs/core/polyglot-troubleshooting.md`

These files are optimized for runtime use, not for preserving the exact
shape of the existing Diataxis tree.

## Page schema

Each runtime-doc source page uses a stable structure so it is predictable
for both humans and agents.

Recommended section pattern:

- `NAME`
- `PURPOSE`
- `WHEN TO USE`
- `PRIMARY COMMANDS`
- `WORKFLOW`
- `OUTPUTS / ARTIFACTS`
- `COMMON FAILURES`
- `GUIDANCE`
- `SEE ALSO`

Not every page needs every section, but the schema should remain mostly stable.

## The "Knowledge" layer

The runtime documentation includes a curated "Knowledge" layer.

This is not meant to be a generic encyclopedia. It is meant to provide
high-signal, durable guidance that improves behavior inside the container.

Likely source inspiration includes:

- software engineering bodies of knowledge such as SWEBOK
- security guidance such as OWASP and NIST
- leading books, conference talks, standards, and publications on system
  design, architecture, testing, programming, and secure engineering

The "Knowledge" layer should:

- adapt strong ideas into concise operating guidance
- explain why they matter in this repository
- make the preferred behavior explicit for humans and agents
- avoid copying external sources verbatim

It should not:

- attempt to reproduce full standards or books
- become a dumping ground for generic advice
- drift away from the actual workflows supported in the container

## Knowledge entry format

Knowledge entries should use a tighter schema than general prose.

Recommended structure:

- `Principle`
- `Why It Matters`
- `How It Applies Here`
- `Failure Mode`
- `Recommended Behavior`
- `See Also`

This keeps the guidance compact, operational, and easy to translate into agent
behavior.

## Relationship to Diataxis

Diataxis remains useful as the primary writing discipline for the repository.

The runtime documentation system draws from that material, but it should
not mirror it mechanically.

A practical mapping is:

- tutorials inform starter and walkthrough man pages
- how-to guides inform operational man pages
- reference pages inform contract and artifact man pages
- explanation pages inform rationale and policy sections within runtime pages

The runtime docs are therefore a delivery layer, not a replacement for the
existing documentation structure.

## Build and installation flow

The build and installation flow is:

1. author or update Markdown under `docs/core/`
2. run `python scripts/build_runtime_docs.py` to convert the runtime pages into
   `man/man7/*.7`
3. copy the generated output into the starter template man directories
4. install the resulting pages into the image so they are available through
   `man`
5. call `bash scripts/install_runtime_docs.sh man/man7` in the relevant
   devcontainer `postCreateCommand`
6. validate that key pages render correctly in the root, Python, and Java
   starter environments

The installation path makes the pages available without requiring custom
shell aliases or manual environment setup by the user.

## Current implementation status

The current MVP is implemented in the repository:

- runtime-doc source lives under `docs/core/`
- generated man pages live under `man/man7/`
- the Python and Java starter templates ship the generated pages under their
  local `man/man7/` directories
- the root, Python, and Java devcontainer definitions install the runtime docs
  during `postCreateCommand`
- the root, Python, and Java container images install `man-db` and `less`

The validated user experience is:

1. open the root, Python, or Java devcontainer in VS Code
2. wait for the `postCreateCommand` to complete
3. run `man polyglot`, `man polyglot-python`, or `man polyglot-java`
4. use the task contract and linked man pages to operate the workspace

## Initial implementation phases

Phase 1: minimal runtime-doc pipeline

- define the `docs/core/` source tree
- generate a small set of man pages during the build pipeline
- install them into the root container
- validate `man polyglot` and `man polyglot-task-contract`

Phase 2: starter coverage

- add `polyglot-python`
- add `polyglot-java`
- add `polyglot-starters`
- validate that users and agents can select the correct starter workflow from
  inside the container

Phase 3: agent and security guidance

- add `polyglot-agents`
- add `polyglot-security`
- add `polyglot-deps`
- align with the existing artifact and task-reporting workflows

Phase 4: curated Knowledge layer

- add `polyglot-knowledge`
- start with a small set of durable, high-signal guidance entries
- validate that the content remains concise and operational

Phase 5: troubleshooting and refinement

- add `polyglot-troubleshooting`
- refine navigation, naming, and page cross-linking
- decide whether the runtime-doc contract is stable enough to treat as a
  first-class starter feature

Phases 1 to 5 are now represented in the repository as an MVP. The remaining
work is refinement:

- broaden starter coverage if more starter types are added
- keep the generated pages aligned with the source Markdown
- grow the Knowledge layer carefully without turning it into a generic manual
- decide whether runtime-doc generation should become part of a stricter CI
  verification path

## Validation criteria

The runtime documentation should be considered useful only if it satisfies
practical tests such as:

- a new human can find the correct starter workflow from `man polyglot`
- an agent can recover the task contract, artifact locations, and operating
  guidance from inside the container
- the pages remain aligned with actual container behavior and CI validation
- the guidance measurably reduces confusion or misuse of the environment

## Open design questions

- should generated man pages be committed, or only produced in CI/image builds?
- should the runtime-doc source live entirely in `docs/core/`, or be partially
  derived from the existing Diataxis pages?
- how much of the Knowledge layer should be global versus ecosystem-specific?
- what is the smallest useful initial page set that proves the model without
  overbuilding it?

## Current recommendation

The next implementation steps should focus on refinement rather than basic
plumbing:

- teach users how to rely on the runtime docs in the starter tutorials
- keep the generated man pages synchronized with `docs/core/`
- expand the Knowledge layer only when it sharpens real engineering behavior
- decide how much of the runtime-doc build should be enforced in CI
