# Use the Published Diagrams Image

Use this flow when you want a deterministic diagram-rendering workspace in VS
Code based on `ghcr.io/senanayake/polyglot-devcontainers-diagrams:main`.

If you want a ready-made proving path, start from
`examples/diagram-image-example`.

## 1. Create a project folder

Create or open a folder that will hold your diagram sources.

For the initial Polyglot shape, include:

- `Taskfile.yml`
- `docs/diagrams/`

## 2. Add a devcontainer definition

Create `.devcontainer/devcontainer.json` with:

```json
{
  "name": "diagram-secure",
  "image": "ghcr.io/senanayake/polyglot-devcontainers-diagrams:main",
  "remoteUser": "vscode",
  "customizations": {
    "vscode": {
      "settings": {
        "editor.formatOnSave": true,
        "files.associations": {
          "*.d2": "plaintext"
        }
      }
    }
  }
}
```

## 3. Open in VS Code

Then:

1. open the project folder in VS Code
2. run `Dev Containers: Reopen in Container`

## 4. Add the task contract

Use `templates/diagram-secure` if you want the full starter.

For a smaller manual setup, expose at least:

```yaml
version: "3"

tasks:
  init:
    cmds:
      - mkdir -p .artifacts/diagrams .artifacts/scans

  lint:
    cmds:
      - bash -lc 'find docs/diagrams -type f -name "*.d2" | while read -r file; do d2 fmt --check "$file"; diagram validate --tool d2 --input "$file"; done'

  render:
    cmds:
      - bash -lc 'find docs/diagrams -type f -name "*.d2" | while read -r file; do output=".artifacts/diagrams/${file#docs/diagrams/}"; output="${output%.d2}.svg"; mkdir -p "$(dirname "$output")"; diagram render --tool d2 --input "$file" --output "$output" --format svg; done'

  test:
    cmds:
      - task render

  scan:
    cmds:
      - mkdir -p .artifacts/scans
      - gitleaks dir . --no-banner --redact --report-format sarif --report-path .artifacts/scans/gitleaks.sarif

  ci:
    cmds:
      - task init
      - task lint
      - task test
      - task scan
```

## 5. Render and validate

Inside the container, run:

```bash
man polyglot
man polyglot-diagrams
task ci
```

For a single explicit render:

```bash
diagram render \
  --tool d2 \
  --input docs/diagrams/cve-portfolio/direct-vs-transitive.d2 \
  --output .artifacts/diagrams/direct-vs-transitive.svg \
  --manifest .artifacts/diagrams/direct-vs-transitive.json
```
