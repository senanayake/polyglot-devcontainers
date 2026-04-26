# diagram-image-example

`diagram-image-example` consumes the published image
`ghcr.io/senanayake/polyglot-devcontainers-diagrams:main` directly.

It is the first proving workspace for the presentation use case around CVE
management in a large software portfolio.

The included diagrams show:

- direct versus transitive dependencies
- a direct dependency becoming vulnerable through the community CVE process
- a transitive dependency becoming vulnerable through the same process

## Workflow

After opening the example in the published image, run:

```bash
man polyglot
man polyglot-diagrams
task ci
```

If you want just the rendered artifacts:

```bash
task render
```

Outputs land under:

- `.artifacts/diagrams/*.svg`
- `.artifacts/diagrams/*.json`

The JSON files are machine-readable render manifests designed for agent use.
