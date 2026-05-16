# Downstream Consumption of Polyglot DevContainers

**Status:** Stable  
**Last Updated:** 2026-04-15

---

## Overview

The polyglot-devcontainers project publishes container images to GitHub Container Registry (GHCR) that can be used as base images for your own private containers and development environments.

This documentation helps downstream projects:
- **Extend polyglot base images** for private use cases
- **Understand the stable API** that polyglot guarantees
- **Build private scenarios** following polyglot patterns
- **Configure devcontainers** for downstream projects

---

## Published Images

All images are available at `ghcr.io/senanayake/polyglot-devcontainers-*`:

| Image | Base | Use Case |
|-------|------|----------|
| `python-node:latest` | Python 3.12 + Node 22 | Full-stack web applications, API services |
| `python-node:main` | Python 3.12 + Node 22 | Latest development version |
| `java:latest` | Java 21 (Temurin) | Java applications, JVM services |
| `java:main` | Java 21 (Temurin) | Latest development version |
| `diagrams:latest` | Diagram tools | Documentation, architecture diagrams |
| `diagrams:main` | Diagram tools | Latest development version |

**Tagging strategy:**
- `:latest` - Latest stable release
- `:main` - Latest commit on main branch
- `:v*` - Specific version tags (future)

---

## Quick Start

### Use as DevContainer Base

Create `.devcontainer/devcontainer.json`:

```json
{
  "name": "My Project",
  "image": "ghcr.io/senanayake/polyglot-devcontainers-python-node:latest",
  "customizations": {
    "vscode": {
      "extensions": ["ms-python.python"]
    }
  }
}
```

### Build Private Image

Create `Dockerfile`:

```dockerfile
FROM ghcr.io/senanayake/polyglot-devcontainers-python-node:latest

USER root

# Install additional tools
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        your-package-here && \
    rm -rf /var/lib/apt/lists/*

# Copy application
WORKDIR /app
COPY . .

# Install dependencies
RUN pnpm install

USER vscode

CMD ["pnpm", "start"]
```

Build:
```bash
podman build -f Dockerfile -t my-private-image:latest .
```

---

## Documentation Structure

### [Building Private Images](building-private-images.md)

Detailed guide for extending polyglot base images:
- Dockerfile patterns and best practices
- Choosing the right base image
- Adding private tooling
- Security considerations
- Example templates

### [Base Image Contract](base-image-contract.md)

What downstream projects can rely on:
- Stable tools and paths across all images
- Language-specific guarantees (Python, Node, Java)
- User and permission model
- Environment variables

### [Private Scenarios](private-scenarios.md)

Creating private scenarios following polyglot patterns:
- Scenario structure and conventions
- Running scenarios outside polyglot repo
- Integration with private registries
- Example private scenario

---

## Real-World Example: Sententia

The Sententia project successfully uses polyglot images as base for private services:

**API Service (Node.js/TypeScript):**
```dockerfile
FROM ghcr.io/senanayake/polyglot-devcontainers-python-node:latest
USER root
RUN apt-get update && \
    apt-get install -y --no-install-recommends docker.io && \
    rm -rf /var/lib/apt/lists/*
WORKDIR /app
COPY package.json pnpm-lock.yaml ./
RUN pnpm install --frozen-lockfile
COPY . .
RUN pnpm build
USER vscode
CMD ["pnpm", "tsx", "src/index.ts"]
```

**Formal Methods Service (Java):**
```dockerfile
FROM ghcr.io/senanayake/polyglot-devcontainers-java:latest
USER root
RUN mkdir -p /opt/alloy && \
    curl -fsSL "https://github.com/AlloyTools/org.alloytools.alloy/releases/download/v6.1.0/org.alloytools.alloy.dist.jar" \
    -o /opt/alloy/alloy.jar
COPY alloy-runner.sh /opt/alloy/
RUN chmod +x /opt/alloy/alloy-runner.sh
USER vscode
ENTRYPOINT ["/opt/alloy/alloy-runner.sh"]
```

Both images built and ran successfully with Podman.

---

## Common Patterns

### Pattern 1: Add System Dependencies

```dockerfile
FROM ghcr.io/senanayake/polyglot-devcontainers-python-node:latest
USER root
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        postgresql-client \
        redis-tools && \
    rm -rf /var/lib/apt/lists/*
USER vscode
```

### Pattern 2: Install Private Tools

```dockerfile
FROM ghcr.io/senanayake/polyglot-devcontainers-java:latest
USER root
RUN curl -fsSL https://your-private-registry/tool.tar.gz | \
    tar -xz -C /usr/local/bin
USER vscode
```

### Pattern 3: Application Container

```dockerfile
FROM ghcr.io/senanayake/polyglot-devcontainers-python-node:latest
USER root
WORKDIR /app
COPY requirements.txt package.json ./
RUN uv pip install -r requirements.txt && \
    pnpm install
COPY . .
USER vscode
CMD ["python", "src/main.py"]
```

---

## Security Considerations

### Non-Root User

All polyglot images run as the `vscode` user (UID 1000) by default:
- Switch to `USER root` only when necessary
- Always switch back to `USER vscode` before CMD/ENTRYPOINT
- Never run application code as root

### Minimal Layers

```dockerfile
# ❌ Bad: Multiple RUN commands
RUN apt-get update
RUN apt-get install -y package1
RUN apt-get install -y package2

# ✅ Good: Single RUN with cleanup
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        package1 \
        package2 && \
    rm -rf /var/lib/apt/lists/*
```

### Secrets Management

```dockerfile
# ❌ Bad: Secrets in image
ENV API_KEY=secret123

# ✅ Good: Secrets at runtime
# Pass via environment or mount
```

---

## Image Selection Guide

### Choose `python-node` when:
- Building full-stack web applications
- Need both Python and Node.js
- API services with frontend
- Data processing with web UI

### Choose `java` when:
- Building JVM applications
- Need Java 21 (Temurin)
- Spring Boot, Quarkus, etc.
- Formal methods tools (Alloy, TLA+)

### Choose `diagrams` when:
- Generating architecture diagrams
- Documentation workflows
- Mermaid, PlantUML, Graphviz

---

## Versioning and Stability

### Stable Guarantees

Polyglot guarantees backward compatibility for:
- User: `vscode` (UID 1000)
- Tools: `task`, `gitleaks`, `pre-commit`
- Paths: `/usr/local/bin/task`, `/usr/local/bin/gitleaks`
- Shell: `bash`

See [Base Image Contract](base-image-contract.md) for full details.

### Breaking Changes

Breaking changes will be:
- Documented in release notes
- Versioned with major version bump
- Announced in advance when possible

---

## Support and Feedback

### Getting Help

- **Issues:** [GitHub Issues](https://github.com/senanayake/polyglot-devcontainers/issues)
- **Discussions:** [GitHub Discussions](https://github.com/senanayake/polyglot-devcontainers/discussions)
- **Documentation:** [Main README](../../README.md)

### Contributing

If you've built something useful on polyglot:
- Share your patterns via GitHub Discussions
- Contribute documentation improvements
- Report issues or missing features

---

## Next Steps

1. **Read the base image contract** - Understand what's stable
2. **Choose your base image** - Pick the right image for your use case
3. **Build a private image** - Follow the detailed guide
4. **Test in DevPod/VS Code** - Validate your setup
5. **Deploy** - Use in CI/CD or production

---

## Related Documentation

- [Building Private Images](building-private-images.md) - Detailed Dockerfile guide
- [Base Image Contract](base-image-contract.md) - Stable API reference
- [Private Scenarios](private-scenarios.md) - Scenario patterns
- [Main README](../../README.md) - Polyglot overview
- [Scenario Documentation](../scenarios/README.md) - Public scenarios

---

**Ready to build? Start with the [Building Private Images](building-private-images.md) guide.**
