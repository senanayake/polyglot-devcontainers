# Task: Add OpenRewrite to Java Image/Workflow

## Status
COMPLETE

## Orientation

**God nodes** — read these before changing anything:

- `AGENTS.md` — operating constraints, K-Brief requirements, maintainer-container discipline; must be followed in full
- `templates/java-secure/build.gradle.kts` + `Taskfile.yml` — canonical template; changes here propagate intent to examples
- `examples/java-maintenance-example/Taskfile.yml` + `build.gradle.kts` — primary proving path (has `_require_maintainer` guards)
- `examples/java-image-example/Taskfile.yml` + `build.gradle.kts` — secondary proving path
- `features/java-engineering/install.sh` — image toolchain definition; touch only if a binary install is justified

**Key relationships:**
- All new Gradle tasks flow from template → examples; template is the authority, examples prove them in a realistic context
- `_require_maintainer` in examples enforces container execution; the template does not have this guard (it is a starter, not a proof)
- `deps:inventory` / `deps:plan` / `upgrade` already exist — OpenRewrite tasks must be additive and orthogonal to them
- The repo uses Gradle Kotlin DSL; OpenRewrite Gradle plugin is the integration point

**Non-obvious constraints:**
- `AGENTS.md` requires a K-Brief before implementing a new capability; write it first
- Third-party tools must use latest upstream-supported releases — check the OpenRewrite Gradle plugin version at time of implementation
- OpenRewrite tasks must be explicitly separated from `ci` and `upgrade`; do not add them to either

## Knowledge Briefs Required

Write a K-Brief capturing:
- Which OpenRewrite Gradle plugin version was chosen and why
- Which recipe(s) form the first slice and why (prefer a single narrow, reviewable recipe over a bundle)
- Decision on dry-run vs mutating mode defaults
- Rationale for Gradle-first over CLI binary (or justification if CLI is added)

Reference existing briefs:
- `KB-2026-021` — role of OpenRewrite vs dependency bots (integration point: this task delivers the first slice described there)
- `KB-2026-022` — framework lifecycle governance
- `KB-2026-020` — dependency locking discipline (lockfile must be re-verified after any mutating run)

## Deliverables

1. **Gradle plugin integration** — `org.openrewrite.rewrite` plugin added to `templates/java-secure/build.gradle.kts` and both example `build.gradle.kts` files
2. **Taskfile tasks** in template and both examples:
   - `rewrite:dry-run` — non-destructive; reports what would change; always safe to run
   - `rewrite:run` — mutating; applies recipes; must be followed by `task ci` to verify
3. **K-Brief** — records recipe selection rationale and plugin version decision
4. **Docs update** — add a section to `man/man7/polyglot-java.7` (or equivalent) explaining when to use `rewrite:dry-run` vs `task upgrade`

## Task Contract (do not break)

These must continue to pass after changes:

```
python scripts/run_in_maintainer_container.py exec -- task -t templates/java-secure/Taskfile.yml init
python scripts/run_in_maintainer_container.py exec -- task -t templates/java-secure/Taskfile.yml lint
python scripts/run_in_maintainer_container.py exec -- task -t templates/java-secure/Taskfile.yml test
python scripts/run_in_maintainer_container.py exec -- task -t templates/java-secure/Taskfile.yml scan
python scripts/run_in_maintainer_container.py exec -- task -t templates/java-secure/Taskfile.yml ci
```

## Proof Paths

Run in this order. Each must pass before proceeding.

### 1. Template — dry-run (non-destructive)

```
python scripts/run_in_maintainer_container.py exec -- task -t templates/java-secure/Taskfile.yml init
python scripts/run_in_maintainer_container.py exec -- task -t templates/java-secure/Taskfile.yml rewrite:dry-run
python scripts/run_in_maintainer_container.py exec -- task -t templates/java-secure/Taskfile.yml ci
```

Expected: `rewrite:dry-run` prints a report (or "no changes") without modifying any source files.

### 2. Example — dry-run

```
python scripts/run_in_maintainer_container.py exec -- task -t examples/java-maintenance-example/Taskfile.yml init
python scripts/run_in_maintainer_container.py exec -- task -t examples/java-maintenance-example/Taskfile.yml rewrite:dry-run
python scripts/run_in_maintainer_container.py exec -- task -t examples/java-maintenance-example/Taskfile.yml ci
```

### 3. Example — mutating run (if `rewrite:run` is implemented)

```
python scripts/run_in_maintainer_container.py exec -- task -t examples/java-maintenance-example/Taskfile.yml rewrite:run
python scripts/run_in_maintainer_container.py exec -- task -t examples/java-maintenance-example/Taskfile.yml ci
```

Expected: `ci` passes after mutation — recipes must not break the build. If `ci` fails after `rewrite:run`, revert and narrow the recipe selection.

### 4. Image-example proving path

```
python scripts/run_in_maintainer_container.py exec -- task -t examples/java-image-example/Taskfile.yml init
python scripts/run_in_maintainer_container.py exec -- task -t examples/java-image-example/Taskfile.yml rewrite:dry-run
python scripts/run_in_maintainer_container.py exec -- task -t examples/java-image-example/Taskfile.yml ci
```

## Acceptance Criteria

- [x] `rewrite:dry-run` runs inside the maintainer container without modifying source files
- [x] `rewrite:run` (if added) is clearly labelled as mutating in the Taskfile description
- [x] `task ci` passes on template and both examples after all changes
- [x] `task upgrade` behaviour is unchanged
- [x] A K-Brief records recipe selection and plugin version rationale
- [x] Docs explain when to use `rewrite:dry-run` vs `task upgrade`
- [x] Lockfile re-verification discipline is preserved after any mutating run

## Non-Goals

- Do not add Node remediation
- Do not add OpenRewrite to `task ci` or `task upgrade`
- Do not install an OpenRewrite CLI binary unless explicitly justified in the K-Brief
- Do not choose a broad recipe bundle (e.g. `Java21Migration`) without scoping it to the specific sub-recipes in use

## Agent Log <!-- [AGENT-MAINTAINED] -->

<!-- Append entries here as work progresses. Format: YYYY-MM-DD: what was done -->

2026-05-02: Wrote K-Brief KB-2026-059 capturing plugin version (7.32.0), recipe
selection (org.openrewrite.java.RemoveUnusedImports), dry-run-first default,
and Gradle-first rationale. Added org.openrewrite.rewrite plugin and rewrite {}
block to templates/java-secure/build.gradle.kts,
examples/java-maintenance-example/build.gradle.kts, and
examples/java-image-example/build.gradle.kts. Added rewrite:dry-run and
rewrite:run tasks to all three Taskfile.yml files; examples carry
_require_maintainer guard; rewrite:run desc is labelled MUTATING. Added
SEMANTIC REFACTORING WITH OPENREWRITE section to docs/core/polyglot-java.md
explaining rewrite:dry-run vs task upgrade and when rewrite:run requires task
init + task ci; manually translated the new section into man/man7/polyglot-java.7
(pandoc unavailable in current execution environment). Ran all four proof paths
(template init+rewrite:dry-run+ci; maintenance-example init+rewrite:dry-run+ci;
maintenance-example rewrite:run+ci; image-example init+rewrite:dry-run+ci) —
all BUILD SUCCESSFUL. Discovered that the rewrite Gradle configuration is empty
by design (built-in recipes ship in the plugin classpath); updated all three
gradle.lockfile files so that rewrite appears in the empty= line. K-Brief
updated with lockfile behaviour clarification.

2026-05-02 (session 2): Re-ran all four proof paths; all BUILD SUCCESSFUL. All
seven acceptance criteria verified. git-log inaccessible from container (worktree
.git file references Windows path C:/dev/polyglot-devcontainers/.git/worktrees/
polyglot-openrewrite which is not reachable from the Linux container). All file
changes are on disk in the worktree and ready for commit from the host. Status
updated to COMPLETE.
