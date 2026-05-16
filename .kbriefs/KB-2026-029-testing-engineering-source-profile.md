---
id: KB-2026-029
type: source-profile
status: validated
created: 2026-04-24
updated: 2026-04-24
tags: [testing, standards, research, python, java, task-contract]
related: [KB-2026-030, KB-2026-031, KB-2026-032]
---

# Testing Engineering Source Profile

## Source

- Name: Standards, framework documentation, and canonical testing references
- Kind: Standards and primary-source documentation bundle
- Owner or maintainer: IEEE Computer Society, ISO/IEC/IEEE, NIST, pytest, Cucumber, jqwik, JUnit, Gradle, PIT, Agile Alliance, Manning, Pearson, xUnitPatterns.com
- Locator:
  - https://www.computer.org/education/bodies-of-knowledge/software-engineering/v4/
  - https://standards.ieee.org/ieee/1012/7324/
  - https://www.iso.org/standard/72089.html
  - https://www.nist.gov/itl/executive-order-14028-improving-nations-cybersecurity/software-supply-chain-security-guidance-0
  - https://pytest-bdd.readthedocs.io/
  - https://hypothesis.works/
  - https://docs.gradle.org/current/userguide/jvm_test_suite_plugin.html
  - https://cucumber.io/docs
  - https://jqwik.net/docs/current/user-guide
  - https://docs.junit.org/5.11.0/user-guide/
  - https://pitest.org/
  - https://agilealliance.org/glossary/atdd/
  - https://agilealliance.org/glossary/bdd/
  - https://www.oreilly.com/library/view/specification-by-example/9781617290084/
  - https://www.pearson.com/en-us/subject-catalog/p/growing-object-oriented-software-guided-by-tests/P200000009298
  - https://xunitpatterns.com/

## Why This Source Matters

The repository needed a testing model that was both theoretically grounded and
implementable across Python and Java without inventing a private taxonomy.

## Summary

The source bundle converges on a stable split:

- standards define verification, validation, requirements, and test taxonomy
- framework docs define the current executable surface in Python and Java
- canonical books explain the workflow layer: TDD, ATDD, BDD, specification by
  example, and test design quality

## Quality Signals

- Maintenance activity: active framework docs and recently updated standards pages
- Release cadence: current framework versions and recent guide updates were available
- Documentation quality: primary-source docs were sufficient to map tools to semantics
- Security or trust signals: official docs, standards bodies, and primary maintainers
- Ecosystem adoption: pytest, JUnit, Cucumber, Gradle, and jqwik are mainstream

## Risks and Caveats

- standards give taxonomy, not repo-specific task design
- BDD literature is frequently tool-agnostic, so framework mapping still
  requires concrete implementation judgment
- mutation tooling is useful but was not necessary to make the first-class
  contract coherent

## Recommended Use

- use standards to define semantic layers and traceability expectations
- use framework docs to define the executable mapping in each language
- use the books and Agile Alliance material to justify TDD and BDD as workflow
  lenses rather than as competing task contracts

## Not Appropriate For

- selecting exact framework versions without compatibility testing
- proving repository-specific UX without experiments in the templates

## Evidence

- Python templates now use `pytest`, `pytest-bdd`, and `hypothesis`
- Java template now uses Gradle JVM Test Suites, jqwik, and Cucumber-JVM
- the repo docs now define `task test` as the full bar with explicit zoom-in
  verbs for semantic layers
