# Testing Strategy

Polyglot treats testing as a structured system of evidence, not a single
undifferentiated runner invocation.

## Why This Matters

The repository has three overlapping needs:

1. a stable task contract that works across ecosystems
2. fast inner-loop feedback for humans and agents
3. traceable evidence that requirements and architectural decisions are still
   true

Those needs are not served by a single flat `task test` implementation.

## Verification And Validation

The testing model follows the standard distinction reflected in sources such as
SWEBOK, ISO/IEC/IEEE 29148, IEEE 1012, and NIST software verification guidance:

- verification asks whether the implementation conforms to its specified design
  and requirements
- validation asks whether the delivered behavior satisfies intended user or
  system needs

In practice:

- unit, integration, and property tests are primarily verification-heavy
- acceptance and BDD-style executable specifications sit closer to validation
- scenarios and operational proving flows bridge product behavior and execution
  environment concerns

## TDD And BDD In Polyglot

Polyglot treats TDD and BDD as workflow lenses layered on top of the same test
hierarchy.

- TDD is the inner-loop discipline: write or refine a focused failing test,
  implement, then refactor with fast feedback
- ATDD / specification by example / BDD are the collaborative outer-loop
  discipline: capture externally visible behavior as executable examples before
  or during implementation

That leads to a deliberate contract:

- `task test` is the full automated regression bar
- `task test:fast` exists for inner-loop TDD feedback where supported
- `task test:acceptance` carries BDD and executable specification suites where
  supported

## Test Taxonomy

Polyglot's recommended semantic hierarchy is:

1. `test:unit`
2. `test:property`
3. `test:integration`
4. `test:acceptance`
5. `test`

Interpretation:

- `test:unit` verifies small, local behavior with minimal setup
- `test:property` verifies invariants across generated input spaces
- `test:integration` verifies behavior across real boundaries or subsystems
- `test:acceptance` verifies externally visible behavior from requirements or
  executable specifications
- `test` runs the full automated suite that the environment claims to support

`test:all` is permitted as a compatibility alias but should resolve to the same
full bar as `test`, not a stronger one.

## Execution Amplifiers

Some tools improve the execution model without defining a new semantic test
layer.

Examples:

- `pytest-xdist` and Gradle parallelism accelerate execution
- `pytest-randomly` stresses order-dependence and hidden state coupling
- `pytest-cov` and JaCoCo provide structural coverage evidence
- PIT and similar mutation tools probe test effectiveness

These are important, but Polyglot treats them as amplifiers of semantic suites,
not replacements for the semantic hierarchy.

## Requirements And Traceability

Best-in-class scaffolding means the repo does not force future contributors to
reconstruct the relationship between requirements, examples, and tests.

The intended chain is:

```text
requirement -> executable specification -> automated test -> task verb
```

That is why feature scaffolds now generate:

- `specs/requirements.md`
- `specs/acceptance.feature`
- `specs/traceability.md`
- executable test placeholders

And why ADR scaffolds explicitly ask for:

- related requirements
- related K-Briefs
- verification and validation impact

## Language Mapping

### Python

- `pytest` provides the core test surface
- `pytest-bdd` provides executable specifications
- `hypothesis` provides property-based testing
- `pytest-xdist` is the main parallel execution amplifier

### Java

- JUnit 5 remains the unit and integration spine
- Gradle JVM Test Suites provide semantic suite separation
- jqwik provides property-based testing
- Cucumber-JVM provides acceptance and BDD coverage

## Design Consequence

The repo previously drifted toward a fast-default Python `task test` while the
published contract and documentation still described `task test` as the full
bar. This work resolves that inconsistency by restoring `task test` as the full
semantic bar and moving fast feedback into explicit zoom-in verbs.
