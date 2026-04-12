# diagram-secure

`diagram-secure` is the initial Polyglot starter for presentation-quality
diagrams as code.

It is built around:

- `d2` for authored diagram sources
- `graphviz` for secondary layout compatibility
- `diagram`, a stable wrapper CLI for render and validate operations
- an SVG-first task contract for slide-ready outputs

Use this starter when you want a focused container for architecture, dependency,
and security storytelling rather than a language-specific application stack.

## Task contract

```bash
task init
task lint
task render
task test
task scan
task ci
```

`task test` renders the diagram set into `.artifacts/diagrams/` and emits a
JSON manifest for each output.

## Included proving slice

The starter ships with the first CVE presentation use cases:

- direct versus transitive dependencies
- vulnerability emergence on a direct dependency
- vulnerability emergence on a transitive dependency

## Primary files

- `docs/diagrams/cve-portfolio/direct-vs-transitive.d2`
- `docs/diagrams/cve-portfolio/vulnerability-emergence-direct.d2`
- `docs/diagrams/cve-portfolio/vulnerability-emergence-transitive.d2`

## Agent interface

Use the wrapper CLI when you need a deterministic container command:

```bash
diagram render \
  --tool d2 \
  --input docs/diagrams/cve-portfolio/direct-vs-transitive.d2 \
  --output .artifacts/diagrams/direct-vs-transitive.svg \
  --manifest .artifacts/diagrams/direct-vs-transitive.json
```

For local runtime guidance in the container, run:

```bash
man polyglot
man polyglot-diagrams
```
