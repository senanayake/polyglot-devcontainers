---
id: KB-2026-059
type: standard
status: active
created: 2026-05-02
updated: 2026-05-02
tags: [java, openrewrite, gradle, recipes, code-migration, dependency-locking]
related: [KB-2026-020, KB-2026-021, KB-2026-022]
---

# OpenRewrite First Slice: Gradle Plugin and Recipe Selection

## Context

KB-2026-021 established OpenRewrite as the semantic migration layer complementing
dependency bots. This brief records the first concrete implementation slice:
which plugin version was chosen, which recipe forms the initial scope, how
dry-run vs mutating modes are defaulted, and why Gradle-first was chosen over a
CLI binary.

This brief captures the decisions made when wiring `rewrite:dry-run` and
`rewrite:run` into the `templates/java-secure`, `examples/java-maintenance-example`,
and `examples/java-image-example` proving paths.

## Plugin Version Decision

### Chosen Version

`org.openrewrite.rewrite` version **7.30.0**

### Rationale

7.30.0 is the latest stable release on the Gradle Plugin Portal as of 2026-05-02
(published 2026-04-08). The OpenRewrite docs "latest versions" reference also
lists `org.openrewrite:rewrite-gradle-plugin` 7.30.0. The repository policy
(AGENTS.md §7) requires latest upstream-supported releases for third-party
tools, so the repository should track 7.30.0 rather than an unpublished or
unverified newer value.

The plugin brings `rewrite-java` transitively, which supplies all core Java
recipes including `org.openrewrite.java.RemoveUnusedImports`. No separate
recipe library dependency is required for the first slice.

## Recipe Selection Decision

### Chosen Recipe

`org.openrewrite.java.RemoveUnusedImports`

### Rationale

The task specification explicitly requires a single narrow, reviewable recipe
rather than a bundle. The considerations:

**Why not a broad bundle (e.g., `UpgradeToJava21` composite)?**

- Composite migration recipes bundle dozens of sub-recipes; changes become hard
  to review atomically
- The codebase already targets Java 21; many sub-recipes in migration bundles
  would be no-ops and add noise
- Any single recipe in the composite that breaks the build would block the
  entire bundle, making the root cause harder to diagnose
- AGENTS.md explicitly requires scoping to specific sub-recipes

**Why `RemoveUnusedImports` specifically?**

- Strictly non-destructive: removing unused imports cannot change runtime behaviour
- Produces zero false-positive behavioural changes — safe to apply without deep
  review
- Works on any Java source regardless of dependencies or framework
- Universally applicable across all three proving paths (template, maintenance
  example, image example) without assumptions about the specific libraries in use
- If the code is already clean (no unused imports), the dry-run output is
  "no changes" — which is the correct proof that the task runs end-to-end
  without needing contrived test code
- Supplied by `rewrite-java` which is bundled with the plugin; no additional
  `rewrite` configuration dependencies required

**Future recipe expansion**

Subsequent slices can narrow into one specific sub-recipe from broader groups
(e.g., a single annotation modernization recipe from the Java 17/21 migration
family). Each expansion follows the same pattern: one recipe per slice, verified
against the proving paths before merging.

## Dry-Run vs Mutating Mode Decision

### Default: dry-run is the safe, always-available command

`rewrite:dry-run` maps to Gradle's `rewriteDryRun` task.

- Calls `rewriteDryRun`, which produces a unified diff report under
  `build/rewrite/rewrite.patch` and prints a human-readable summary to stdout
- Source files are never modified
- Safe to run at any point in the development workflow; does not require
  lockfile regeneration after the run
- Named and described to make its non-destructive nature obvious

`rewrite:run` maps to Gradle's `rewriteRun` task.

- Described explicitly as **MUTATING** in the Taskfile `desc` field
- Modifies source files in place
- Must be followed by `task ci` to verify the build is still green
- If `task ci` fails after `rewrite:run`, the developer should revert and narrow
  the recipe selection before re-applying
- After any `rewrite:run`, if recipes modified `build.gradle.kts`, run
  `task init` to re-write dependency locks before `task ci` (see KB-2026-020)

### Why dry-run as the default

The OpenRewrite docs describe `rewriteDryRun` as a "print what would change"
task that makes no source modifications. The repository's inspection-first
philosophy (run `deps:plan` before `upgrade`; see the Taskfile pattern) extends
naturally to code refactoring: inspect the proposed change first, then apply.

Making `rewrite:dry-run` the easy, always-safe entry point reduces the risk of
accidental source mutation. The mutating variant is an explicit, labelled action.

## Gradle-First Decision (No CLI Binary)

### Decision: Gradle plugin only; no OpenRewrite CLI binary

The task specification lists CLI installation as a non-goal unless justified in
this K-Brief. The justification for Gradle-first is:

1. **Already in the build lifecycle**: the Gradle plugin integrates with
   `dependencyLocking`, `spotlessCheck`, and `spotbugsMain`. The `rewrite`
   Gradle configuration is empty by default (no user-supplied recipe libraries)
   and is recorded in the `empty=` line of `gradle.lockfile`. The plugin's own
   core libraries are pinned through the plugin version in the `plugins {}` block.

2. **No extra binary to install or maintain**: the `features/java-engineering/install.sh`
   feature already installs Gradle. A CLI binary would add a second download path
   with its own versioning and checksum discipline.

3. **Consistent invocation model**: `GRADLE_USER_HOME` and `--no-daemon` flags
   already used by every other Gradle-backed task apply equally to rewrite tasks.

4. **Lockfile integration**: Gradle manages the `rewrite` configuration's
   transitive closure as a resolvable configuration subject to `lockAllConfigurations()`.
   A CLI binary bypasses Gradle's dependency resolution and would require a
   separate version pin mechanism.

The CLI binary path remains open for a future slice if specific requirements
arise (e.g., running recipes against a non-Gradle project within this
repository), but it is not justified for the initial slice.

## Dependency Locking Behaviour

### The `rewrite` configuration is empty and tracked

The `rewrite` Gradle configuration is created by the plugin. It is intended for
user-supplied recipe library JARs (e.g., custom or third-party recipe modules).
When using only built-in recipes (such as `org.openrewrite.java.RemoveUnusedImports`
from `rewrite-java`), the `rewrite` configuration has **no entries** — the recipe
library ships as part of the plugin's own classpath, not as a project-level
dependency.

The OpenRewrite plugin's core libraries are therefore pinned through the plugin
version declaration in the `plugins {}` block (`"7.30.0"`), not through the
`gradle.lockfile`. This is the standard and correct behaviour for Gradle plugins.

With `lockAllConfigurations()` in effect, the `rewrite` configuration IS
tracked in `gradle.lockfile` — it appears in the `empty=` line:

```
empty=...,rewrite,...
```

This line records all lock-enabled configurations that resolved with no
dependencies. Gradle 9 preserves `empty=` entries across subsequent
`--write-locks` runs; once a configuration appears in the lockfile it is
retained even if it isn't resolved during that particular build invocation.

**Important**: if future work adds a user-supplied recipe library (e.g.,
`rewrite("org.openrewrite.recipe:rewrite-spring:...")` in `build.gradle.kts`),
that dependency will be resolved into the `rewrite` configuration and WILL
appear in `gradle.lockfile` with its version pinned. The locking mechanism will
then validate it on every subsequent build.

After a `rewrite:run` that modifies `build.gradle.kts` (e.g., from a future
dependency-version recipe), re-run `task init` to regenerate the lockfile before
`task ci`, as required by KB-2026-020.

## Anti-Patterns Avoided

- **Broad composite bundle without scoping** — `UpgradeToJava21` or
  `CommonStaticAnalysis` would apply dozens of sub-recipes in a single opaque
  step; each sub-recipe should be introduced separately
- **Adding OpenRewrite to `task ci`** — rewrite tasks are opt-in developer and
  migration tooling; automatic runs in `ci` would cause unexpected source
  mutations
- **Adding OpenRewrite to `task upgrade`** — `upgrade` manages dependency
  version hygiene; OpenRewrite manages semantic code changes; conflating them
  obscures which change originated from which tool
- **Installing a CLI binary without justification** — the Gradle plugin covers
  all current needs; adding a binary creates an extra maintenance surface

## References

- [OpenRewrite Gradle Plugin on Gradle Plugin Portal](https://plugins.gradle.org/plugin/org.openrewrite.rewrite)
- [OpenRewrite Gradle Plugin Configuration Docs](https://docs.openrewrite.org/reference/gradle-plugin-configuration)
- [OpenRewrite: RemoveUnusedImports recipe](https://docs.openrewrite.org/recipes/java/removeunusedimports)
- KB-2026-020 — Dependency locking discipline
- KB-2026-021 — Role of OpenRewrite vs dependency bots
- KB-2026-022 — Framework lifecycle governance
