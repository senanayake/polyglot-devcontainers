# Task Contract

Every supported repository in this project family must expose these commands:

```bash
task init
task lint
task test
task scan
task ci
```

Some repositories may also expose optional helper tasks such as:

```bash
task format
task test:fast
task test:unit
task test:integration
task test:acceptance
task test:property
task deps:inventory
task deps:plan
task deps:report
task scenarios:python-maintenance
task scenarios:python-audit-policy
task scenarios:java-maintenance
task scenarios:verify
task upgrade
```

These helpers must extend the standard workflow rather than replace it.

## Meanings

- `init`: bootstrap the development environment
- `lint`: run code quality and type checks
- `test`: run automated tests
- `test:fast` (optional): run a fast inner-loop subset such as unit and
  property tests
- `test:unit` (optional): run unit tests only
- `test:integration` (optional): run integration tests only
- `test:acceptance` (optional): run executable specification / BDD tests only
- `test:property` (optional): run property-based tests only
- `scan`: run security checks
- `ci`: run the full workflow
- `deps:inventory` (optional): write normalized dependency inventory artifacts
- `deps:plan` (optional): write normalized dependency update planning artifacts
- `deps:report` (optional): summarize dependency inventory and plan artifacts
  into compact JSON and Markdown reports
- `scenarios:python-maintenance` (optional): run the current Python
  dependency-maintenance scenario and verify its artifacts
- `scenarios:python-audit-policy` (optional): run the current Python
  audit-policy scenario and verify its artifacts
- `scenarios:java-maintenance` (optional): run the current Java
  dependency-maintenance scenario and verify its artifacts
- `scenarios:verify` (optional): run the current repo-owned scenario proving set
- `upgrade` (optional): run a validated dependency-upgrade workflow and
  re-verify the repository

For Python, the dependency helpers now also emit strategy detection metadata so
the evidence path can distinguish between workflows such as:

- `uv-lock`
- `pip-tools`
- `pyproject-exact-pins`
- `plain-pyproject`

In `polyglot-devcontainers`, `uv-lock` is now the first-class Python workflow.
The maintained Python examples and templates therefore check in `uv.lock` and
bootstrap with `uv sync --frozen`. The other shapes remain important for
detection, compatibility, and honest artifact generation, but they are not the
primary path the repository is optimizing going forward.

## Testing Hierarchy

Polyglot now treats `task test` as the full automated regression bar.

When an environment needs faster or narrower feedback loops, it should expose
focused verbs such as:

- `task test:fast`
- `task test:unit`
- `task test:integration`
- `task test:acceptance`
- `task test:property`

Those helper verbs extend the contract. They do not redefine `task test` to
mean a smaller suite.
