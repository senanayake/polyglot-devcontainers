# Task Contract

Every supported repository in this project family must expose these commands:

```bash
task init
task lint
task test
task scan
task ci
```

## Meanings

- `init`: bootstrap the development environment
- `lint`: run code quality and type checks
- `test`: run automated tests
- `scan`: run security checks
- `ci`: run the full workflow

## Phase 1 Python behavior

In the root repository:

- `lint` runs Ruff and MyPy
- `test` runs Pytest with coverage
- `scan` runs `pip-audit` and Gitleaks with artifact output
