---
id: KB-2026-021
type: design-space
status: active
created: 2026-04-12
updated: 2026-04-12
tags: [automation, dependency-updates, openrewrite, dependabot, renovate, framework-migration]
related: [KB-2026-020]
---

# Automatic Upgrade Technologies and the Role of OpenRewrite

## Context

Dependency update automation is not a single tool category.

There are at least two materially different automation layers:

1. **version update bots** that open update PRs when newer versions exist
2. **semantic migration tools** that change code, configuration, and build
   files to make larger upgrades feasible

Many organizations use the first and underinvest in the second, then wonder why
framework upgrades still become expensive and delayed.

## Core Conclusion

Tools such as Dependabot and Renovate are best for **continuous version
hygiene**. Tools such as OpenRewrite are best for **code-aware migration and
breaking-change remediation**.

OpenRewrite should not be treated as a replacement for dependency bots. It is a
complement that becomes especially valuable when:

- framework majors or minors require source changes
- configuration keys move
- deprecated APIs must be replaced
- build files must be rewritten in sync with code changes

## What Basic Update Bots Do Well

Dependabot and Renovate are strong at:

- detecting new releases
- opening small update PRs
- handling recurring dependency hygiene
- keeping version drift from becoming severe

GitHub's Dependabot documentation is explicit that version updates keep
dependencies current even when there are no known vulnerabilities. Renovate's
own best-practices guidance emphasizes running it on all repositories, updating
often, and taking major updates in sequence rather than letting them pile up.

This is the right base layer.

## Where Basic Update Bots Stop

Version update bots generally do **not** solve the hard part of major platform
upgrades when the update requires semantic code or config changes.

Examples:

- Jakarta namespace migrations
- framework API replacements
- annotation behavior changes
- config key renames
- coordinated dependency alignment during framework upgrades

Bots can propose the version bump, but they cannot always make the code compile
or preserve behavior.

## What OpenRewrite Adds

OpenRewrite's core model is recipe-driven semantic refactoring.

Its documentation states that:

- a recipe can represent a stand-alone refactoring or a larger framework
  migration
- recipes can be linked together into composite migrations
- framework migration recipes are developed with framework authors and the OSS
  community
- supported migrations include build file updates, API changes, and config
  changes

The Spring Boot migration recipes are a concrete example: OpenRewrite documents
that these recipes modify build files, change deprecated or preferred APIs, and
chain additional framework migrations needed for a given Boot target.

## Strategic Role of OpenRewrite

OpenRewrite is most valuable as:

- a **major/minor framework migration accelerator**
- a **technical debt reducer** for delayed upgrades
- a **portfolio-scale codemod engine** for consistent changes across many repos

It is especially strong when one upgrade has many repeatable edits.

## Limits of OpenRewrite

OpenRewrite is not magic.

Important limitations:

- it does not eliminate the need for tests
- it does not prove runtime behavior correctness on its own
- it does not replace architecture decisions
- it does not help equally in every ecosystem
- its value is highest where recipes are mature and the stack is well covered

Today, OpenRewrite's official documentation highlights strongest first-class
coverage around JVM ecosystems plus some JS/TS support. That means it is highly
strategic for Java/Spring-heavy estates, less universal as a one-tool answer
for all languages.

## Recommended Operating Model

Use a layered model:

### Layer 1: Continuous Hygiene

- Dependabot or Renovate on every repo
- small patch/minor PRs continuously
- automated test and scan gates

### Layer 2: Directed Migration Campaigns

- OpenRewrite or equivalent semantic codemod tooling
- recipe-based framework and platform upgrades
- coordinated migration waves across portfolios

### Layer 3: Human Review and Runtime Validation

- targeted manual review of behavior-sensitive areas
- performance, integration, and regression testing
- staged rollout for high-impact upgrades

## Economic Impact

Without semantic migration tooling:

- major upgrades are deferred
- EOL risk accumulates
- emergency upgrade projects become expensive
- teams over-index on short-term pinning and exceptions

With semantic migration tooling:

- upgrade lead time drops
- major-version changes become more schedulable
- portfolio-wide consistency improves
- CVE remediation that depends on framework movement becomes more feasible

## Practical Guidance

1. Run dependency bots continuously for small updates.
2. Use OpenRewrite when an update requires code/config/build changes.
3. Treat recipes as reusable migration assets, not one-off scripts.
4. Apply framework upgrades in smaller steps where possible.
5. Never merge large automated migrations without test coverage and review.

## References

- [GitHub Docs: About Dependabot version updates](https://docs.github.com/en/code-security/concepts/supply-chain-security/about-dependabot-version-updates?learn=dependency_version_updates)
- [Renovate Upgrade Best Practices](https://docs.renovatebot.com/upgrade-best-practices/)
- [OpenRewrite Recipes](https://docs.openrewrite.org/concepts-and-explanations/recipes)
- [OpenRewrite Supported Languages and Frameworks](https://docs.openrewrite.org/reference/supported-languages)
- [OpenRewrite Dependency Version Selectors](https://docs.openrewrite.org/reference/dependency-version-selectors)
- [OpenRewrite: Migrate to Java 17](https://docs.openrewrite.org/running-recipes/popular-recipe-guides/migrate-to-java-17)
- [OpenRewrite: Migrate to Spring Boot 2.6](https://docs.openrewrite.org/recipes/java/spring/boot2/upgradespringboot_2_6)
- [OpenRewrite: Upgrade Spring dependencies](https://docs.openrewrite.org/recipes/maven/spring/upgradeexplicitspringbootdependencies)
