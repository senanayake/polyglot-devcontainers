---
id: KB-2026-020
type: tradeoff
status: active
created: 2026-04-12
updated: 2026-04-12
tags: [dependencies, lockfiles, pinning, floating-versions, reproducibility, maintenance-economics]
related: [KB-2026-013, KB-2026-014]
---

# Dependency Locking vs Floating Versions

## Context

Teams often oscillate between two bad extremes:

- completely locked dependency configurations that never move
- free-floating dependency versions that drift whenever builds run

Both create security and maintenance problems, but in different ways.

This brief summarizes current guidance from Google Cloud, OpenSSF, GitHub, and
ecosystem tooling documentation on how to balance reproducibility, upgrade
speed, and CVE response.

## Core Conclusion

For **applications**, the strongest pattern is:

- keep a declared compatibility policy in manifests
- pin the resolved dependency graph with lockfiles
- automate refresh of those locked versions continuously

For **libraries/frameworks**, the pattern is different:

- preserve a compatibility window in manifests
- avoid over-constraining downstream consumers
- still test against resolved versions regularly

This is an inference from the sources, especially Google Cloud and OpenSSF:
neither source states the full pattern in exactly these words, but together
they point clearly to this operating model.

## The Two Extremes

### 1. Fully Floating Dependencies

Examples:

- broad semver ranges with no lockfile
- implicit "latest compatible" installs on every build
- transitive graph changing without a reviewed commit

Advantages:

- less immediate manual version upkeep
- faster pickup of upstream fixes in theory

Disadvantages:

- non-reproducible builds
- harder incident forensics
- harder rollback and audit
- scan results can differ between builds with no source change
- production risk can change silently

Google Cloud's dependency management guidance is explicit that version pinning
supports reproducible builds, and that lockfiles capture the fully resolved
dependency tree. Free-floating application installs work directly against that
goal.

### 2. Fully Locked But Rarely Updated Dependencies

Examples:

- exact versions everywhere
- committed lockfiles
- no automated update flow
- giant manual upgrade projects every 6 to 18 months

Advantages:

- highly reproducible builds
- accurate vulnerability and inventory visibility
- easier debugging and release control

Disadvantages:

- security fixes do not arrive automatically
- CVE backlog accumulates
- major-version cliffs become harder over time
- emergency patching becomes expensive because the codebase is far behind

Google Cloud explicitly notes this tradeoff: pinning helps reproducibility, but
also means builds do not include security fixes or bug fixes automatically.

## Recommended Pattern

### Applications

Applications should generally:

- commit lockfiles where the ecosystem supports them
- prefer exact resolved trees over build-time drift
- use automated dependency updates to refresh those lockfiles
- run tests and scans on every proposed update

OpenSSF states this directly: applications, but not libraries, should use
lockfiles where available. It also recommends package managers, automated
updates, vulnerability alerts, and tests every time dependencies change.

### Libraries

Libraries should generally:

- declare supported compatibility ranges in manifests
- avoid over-pinning transitive consumers
- maintain CI against concrete resolved sets
- publish compatible releases that are easy for downstreams to adopt

This is a practical inference from OpenSSF's distinction between applications
and libraries and from the general need to avoid forcing downstream dependency
conflicts.

## Why the Middle Pattern Wins

The best economic/security balance is:

- **manifests** express intent and compatibility
- **lockfiles** express actual deployed resolution
- **automation** keeps the lockfile from going stale

That gives:

- reproducibility
- controlled review
- accurate SBOM/vulnerability analysis
- smaller update increments
- lower emergency-change cost

## Implications for CVE Management

Completely floating graphs make CVE governance weak because:

- you cannot easily prove what was deployed
- scanners and SBOMs become less stable
- exposure may change outside normal code review

Completely frozen graphs make CVE governance expensive because:

- easy fixes are delayed
- exploit windows stay open longer
- major upgrade debt grows until it becomes a separate project

The optimal path is not "lock" versus "float". It is **lock plus continuous
refresh**.

## Practical Guidance

1. For app repos, commit lockfiles.
2. For app repos, do not allow build-time dependency drift outside reviewed PRs.
3. Enable automated version updates, not only security-only updates.
4. Keep update PRs small and frequent.
5. Run tests and security checks on each update PR.
6. For libraries, publish broad-enough compatibility while continuously testing
   resolved versions.
7. Use SBOMs and lockfiles together for portfolio visibility.

## References

- [Google Cloud Dependency Management](https://cloud.google.com/software-supply-chain-security/docs/dependencies)
- [OpenSSF: Simplifying Software Component Updates](https://best.openssf.org/Simplifying-Software-Component-Updates)
- [GitHub Docs: About Dependabot version updates](https://docs.github.com/en/code-security/concepts/supply-chain-security/about-dependabot-version-updates?learn=dependency_version_updates)
- [GitHub Docs: Controlling which dependencies are updated by Dependabot](https://docs.github.com/en/code-security/how-tos/secure-your-supply-chain/manage-your-dependency-security/controlling-dependencies-updated)
- [Renovate Upgrade Best Practices](https://docs.renovatebot.com/upgrade-best-practices/)
