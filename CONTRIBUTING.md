# Contributing

Thank you for contributing to Polyglot Devcontainers.

This project values contributions that improve reproducibility, clarity,
security, and usability for both humans and AI agents.

## Ways To Contribute

You can contribute through:

- templates
- examples
- scenarios
- workflows and release automation
- documentation
- image and feature hardening

## Contribution Expectations

Contributions should:

- preserve the task contract
- improve determinism or clarity
- keep behavior explicit and reviewable
- work inside the defined container-first workflow
- avoid hidden host-specific assumptions

## Design Constraints

All accepted changes should respect these constraints:

- reproducibility is required
- the task contract is the primary working interface
- no hidden logic should be required to understand how the repo works
- container-authoritative validation is the source of truth

## Boundary Rule

Polyglot core executes; it does not hide reasoning or semantic interpretation.

That means:

- the core should expose deterministic entry points
- automation should stay inspectable
- evidence and execution surfaces should be explicit
- reasoning layers should not be smuggled into the core workflow

## Recommended Workflow

1. Read [README.md](./README.md) and [PROJECT_PRINCIPLES.md](./PROJECT_PRINCIPLES.md).
2. Open the repository in the maintainer devcontainer.
3. Make the smallest clear change that improves the system.
4. Run the relevant task workflow.
5. Update docs when the public surface changes.

For repository-wide changes, the standard bar is:

```bash
task ci
```

inside the maintainer container.

## Change Types

### Templates

Good template changes:

- improve starter clarity
- reduce setup friction
- harden security defaults
- keep the task contract simple and visible

### Examples

Good example changes:

- make the system easier to learn
- show published-image and runtime-doc behavior clearly
- provide honest, runnable proving paths

### Scenarios

Good scenario changes:

- explain a real situation the repository already supports
- remain executable and observable
- end in verification rather than narrative only

### Workflows

Good workflow changes:

- improve parity between local and CI execution
- preserve or strengthen reproducibility
- make release and validation logic easier to trust

## Review Criteria

Review will prioritize:

- determinism
- clarity
- alignment with the task contract
- explicit behavior over implicit behavior
- maintainability over cleverness

## Community And Governance

See:

- [COMMUNITY.md](./COMMUNITY.md)
- [GOVERNANCE.md](./GOVERNANCE.md)
