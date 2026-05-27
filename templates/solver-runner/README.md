# Solver Runner Template

This template consumes the `polyglot-devcontainers-solver-runner` image.

The image provides Python, Node.js, Java, Alloy/Kodkod, Z3, cvc5, MiniSat,
SQLite, Postgres client tooling, `task`, and `gitleaks` for deterministic
formal-methods and data-modeling correctness experiments.

Use this image when a project needs executable solver checks next to TypeScript,
Python, or data-modeling harnesses. Keep domain-specific translators and model
fixtures in the consuming project; this template only proves that the shared
solver toolchain is present and scriptable.

```bash
task ci
```

