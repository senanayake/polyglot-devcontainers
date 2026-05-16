# Compose Features

Use local features when you need a new secure devcontainer without writing a
large Dockerfile.

## Python example

```json
{
  "image": "mcr.microsoft.com/devcontainers/python:1-3.12-bookworm",
  "features": {
    "../../features/security-baseline": {},
    "../../features/python-engineering": {},
    "../../features/agent-runtime": {}
  }
}
```

## Node example

```json
{
  "image": "mcr.microsoft.com/devcontainers/typescript-node:1-22-bookworm",
  "features": {
    "../../features/security-baseline": {},
    "../../features/node-engineering": {},
    "../../features/agent-runtime": {}
  }
}
```

## Selection guidance

- Use `security-baseline` in every secure workspace.
- Add `pandoc` when the workspace needs deterministic Markdown-to-HTML or PDF
  rendering.
- Add `python-engineering` for Python repositories.
- Add `node-engineering` for Node/TypeScript repositories.
- Add `agent-runtime` when the environment should be optimized for terminal and
  AI-agent workflows.
