# Testing Taxonomy

This page defines the recommended Polyglot testing hierarchy and maps it to
concrete frameworks.

## Semantic Test Layers

| Layer | Purpose | Typical Scope | Default Verb |
| --- | --- | --- | --- |
| Unit | Verify small, local behavior | Single function, class, module | `task test:unit` |
| Property | Verify invariants across many generated inputs | Pure logic, contracts, transformations | `task test:property` |
| Integration | Verify collaboration across real boundaries | Process, storage, network, adapters, subsystems | `task test:integration` |
| Acceptance | Verify externally visible behavior from specs or examples | User-visible capability, business behavior, contract examples | `task test:acceptance` |
| Full regression | Verify the environment's full automated claim | All automated suites above | `task test` |

## Cross-Cutting Execution Aids

These do not define new semantic layers.

| Concern | Python | Java |
| --- | --- | --- |
| Parallel execution | `pytest-xdist` | Gradle parallelism / test distribution |
| Coverage evidence | `pytest-cov` | JaCoCo |
| Order sensitivity | `pytest-randomly` | JUnit ordering controls, custom Gradle invocations |
| Mutation analysis | optional future plugin | PIT |

## Framework Mapping

### Python

| Layer | Primary Tooling | Notes |
| --- | --- | --- |
| Unit | `pytest` | Fast inner-loop feedback |
| Property | `hypothesis` + `pytest` | Generated inputs plus shrinking |
| Integration | `pytest` markers and suite paths | Real resource boundaries stay explicit |
| Acceptance | `pytest-bdd` + Gherkin | Executable specification surface |
| Full regression | `pytest` over all test roots | Bound to `task test` |

### Java

| Layer | Primary Tooling | Notes |
| --- | --- | --- |
| Unit | JUnit 5 | Core xUnit layer |
| Property | jqwik | Property methods on the JUnit platform |
| Integration | Gradle JVM Test Suites + JUnit 5 | Separate source set and task surface |
| Acceptance | Cucumber-JVM + JUnit platform suite engine | BDD and executable specification layer |
| Full regression | Gradle invoking all suites | Bound to `task test` |

## Traceability Guidance

Prefer the following mapping whenever the repository or starter is substantial
enough to justify it:

| Artifact | Role |
| --- | --- |
| Requirement id | Stable statement of expected behavior or constraint |
| Executable specification | Human-readable example of the behavior |
| Automated test | Machine check that proves the behavior |
| Task verb | Stable execution entry point |

## Naming Guidance

Recommended optional zoom-in verbs:

- `task test:fast`
- `task test:unit`
- `task test:property`
- `task test:integration`
- `task test:acceptance`

Optional advanced verbs when justified:

- `task test:mutation`
- `task test:smoke`
- `task test:contract`

Not every environment must expose every optional verb, but `task test` should
remain the full automated bar for the verbs it does expose.
