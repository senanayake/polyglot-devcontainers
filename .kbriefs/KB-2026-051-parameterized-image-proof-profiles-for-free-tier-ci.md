---
id: KB-2026-051
type: design-space
status: draft
created: 2026-05-01
updated: 2026-05-01
tags: [github-actions, ci, starters, images, parameterization, free-tier]
related:
  - KB-2026-031
  - KB-2026-037
  - KB-2026-042
  - KB-2026-049
  - KB-2026-050
---

# Parameterized Image-Proof Profiles for Free-Tier CI

## Context

The current PR lane hard-codes one heavy image-backed starter-proof path:

- `starters:verify:image-backed` always calls `task image:build`
- `task image:build` always builds four verify images
- the actual image-backed starter proofs currently use only two starter paths

The free-tier problem may not require smaller images. It may require a more
explicit way to choose which proof images a given lane needs to build and
exercise.

## Problem Statement

How should the repository parameterize image-backed proofing so that:

- free-tier PR workflows build only the images they actually need
- release and publish workflows can still build the full image set
- the task contract remains explicit and predictable
- CI behavior does not become a hidden function of undocumented environment
  variables

## Design Space Dimensions

Key variables that define the solution space:

- Contract clarity
- Free-tier efficiency
- Metadata duplication
- Workflow readability
- Risk of false green builds

## Options in the Space

### Option A: Parameterize by raw image names

**Position in space:**
- Contract clarity: medium
- Free-tier efficiency: high
- Metadata duplication: medium
- Workflow readability: medium

**Characteristics:**
- Example shape:
  - `task image:build -- --image java --image python-node`
  - `task image:build -- --save`
- Straightforward for image infrastructure work
- Makes starter-proof workflows reason in image vocabulary instead of starter vocabulary
- Risks drift between starter selection and image selection

### Option B: Parameterize by starter IDs

**Position in space:**
- Contract clarity: high
- Free-tier efficiency: high
- Metadata duplication: low-medium
- Workflow readability: high

**Characteristics:**
- Example shape:
  - `task starters:verify:image-backed -- --starter java-secure --starter python-node-secure`
- Closer to the user-facing proof intent
- Lets starter metadata determine the image set transitively
- Requires the catalog to encode or derive starter-to-image mapping explicitly

### Option C: Parameterize by named proof profiles

**Position in space:**
- Contract clarity: high
- Free-tier efficiency: high
- Metadata duplication: low
- Workflow readability: high

**Characteristics:**
- Example shape:
  - `task starters:verify:image-backed -- --profile pr`
  - `task starters:verify:image-backed -- --profile full`
- Best matches the repo's existing use of curated composition profiles
- Gives workflows stable names instead of hand-assembled subsets
- Requires a new profile contract and careful documentation

### Option D: Parameterize root `task ci` directly

**Position in space:**
- Contract clarity: low
- Free-tier efficiency: high
- Metadata duplication: low
- Workflow readability: low-medium

**Characteristics:**
- Example shape:
  - `task ci -- --image-profile pr`
  - `POLYGLOT_CI_PROFILE=pr task ci`
- Convenient at the call site
- Dangerous because two successful `task ci` executions may represent different bars
- Conflicts with prior repo knowledge favoring explicit stronger lanes and stable task semantics

## Design Space Map

| Option | Clarity | Efficiency | Drift risk | Viable? |
|--------|---------|------------|------------|---------|
| A | Medium | High | Medium | Yes |
| B | High | High | Low-Med | Yes |
| C | High | High | Low | Strong candidate |
| D | Low | High | High | Weak |

## Dominated Solutions

Options that are strictly worse than others:

- Parameterize root `task ci` through hidden environment without creating an
  explicit stronger or weaker lane name.
  This is dominated by named proof-profile approaches because it saves little
  code while greatly increasing ambiguity.

## Constraints That Narrow the Space

Hard constraints that eliminate options:

- The repo should not silently weaken `task ci` semantics.
- The proof selection contract should remain reviewable in source control.
- Starter proofing should stay aligned with starter metadata where practical.
- Release and publish workflows still need a full-image build path.

## Evidence

Data supporting this design space mapping:

- `Taskfile.yml` currently hard-codes both the image build set and the
  image-backed proof starter set.
- `starters/catalog.toml` already contains starter-level metadata and curated
  composition profiles.
- `.github/workflows/release-images.yml` already uses a matrix to model the full
  published image set explicitly.
- `KB-2026-031` favors explicit stronger lanes over ambiguous default verbs.
- `KB-2026-037` favors curated profiles over inferred compatibility.

## Insights

Key learnings from mapping the space:

- The repo already has a precedent for curated profiles at the starter layer and
  explicit matrices at the release-image layer.
- The main free-tier lever is likely not image-content reduction first; it is
  separating "build every publishable image" from "build only the images needed
  for this proof profile."
- Starter IDs or named proof profiles are a better abstraction than raw image
  names for most PR-proof decisions.

## Decision Guidance

### Narrowing the Space

How to progressively eliminate options:

1. Reject hidden parameterization of root `task ci`.
2. Determine whether the image-backed proof lane should be expressed in starter
   terms or in named proof-profile terms.
3. If the same subsets recur across workflows, prefer named proof profiles over
   ad hoc image lists.

### Convergence Strategy

When and how to commit to a solution:

- If only one or two stable subsets exist, introduce named proof profiles.
- If workflows need highly flexible ad hoc subsets, use raw image selectors at
  the infrastructure layer but keep starter-facing tasks profile-based.
- Keep the full-image release workflow separate from PR proof profiles.

## Implications

What this design space means for:

- Task design: image building may need separate verbs for build-only, build+save,
  and proof-profile execution
- Starter metadata: starter-to-proof-image mapping may become explicit catalog data
- CI policy: PR lanes can target a curated subset without pretending that subset
  equals the full release-image bar

## Recommendations

Suggested path forward:

- Prefer parameterizing `starters:verify:image-backed`, not root `task ci`.
- Prefer named proof profiles such as `pr` and `full` over hidden env-based
  `task ci` behavior.
- Let lower-level image build helpers accept explicit image selectors, but keep
  workflow-facing calls on curated starter/profile concepts.
- Reuse the release workflow's explicit image matrix as the authoritative full
  image set, not the PR lane.

## Applicability

Where this design space applies:

- Applies to: PR CI design, starter-proof tasks, image-build subset selection,
  free-tier workflow design
- Does not apply to: published image release completeness, where the full image
  set remains required

## Related Knowledge

- `KB-2026-031-full-test-bar-vs-fast-default-feedback-loop.md`
- `KB-2026-037-curated-composition-profiles-minimize-starter-compatibility-risk.md`
- `KB-2026-042-image-backed-starter-proof-should-use-branch-local-verify-images.md`
- `KB-2026-049-github-standard-runner-disk-exhaustion-during-image-backed-starter-proofs.md`
- `KB-2026-050-free-tier-ci-knowledge-gaps-for-image-backed-starter-proofing.md`
