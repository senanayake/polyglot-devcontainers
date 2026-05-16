# Building Private Images from Polyglot Base

**Status:** Stable  
**Last Updated:** 2026-04-15

---

## Overview

This guide shows you how to build private container images using polyglot-devcontainers as a base. You'll learn Dockerfile patterns, security best practices, and how to choose the right base image for your use case.

---

## Table of Contents

- [Choosing a Base Image](#choosing-a-base-image)
- [Dockerfile Patterns](#dockerfile-patterns)
- [Security Best Practices](#security-best-practices)
- [Common Use Cases](#common-use-cases)
- [Building and Testing](#building-and-testing)
- [Example Templates](#example-templates)
- [Troubleshooting](#troubleshooting)

---

## Choosing a Base Image

### Available Base Images

| Image | Languages | Tools | Best For |
|-------|-----------|-------|----------|
| `python-node:latest` | Python 3.12, Node 22 | uv, pnpm, task | Full-stack apps, APIs |
| `java:latest` | Java 21 (Temurin) | Gradle, task | JVM applications |
| `diagrams:latest` | - | Mermaid, PlantUML | Documentation |

### Decision Matrix

**Choose `python-node` if you need:**
- ✅ Python 3.12+ and Node 22+
- ✅ Modern package managers (uv, pnpm)
- ✅ Full-stack web development
- ✅ API services with frontend
- ✅ Data processing with web UI

**Choose `java` if you need:**
- ✅ Java 21 (Temurin JDK)
- ✅ Gradle build system
- ✅ JVM-based applications
- ✅ Formal methods tools (Alloy, TLA+)

**Choose `diagrams` if you need:**
- ✅ Diagram generation (Mermaid, PlantUML, Graphviz)
- ✅ Documentation workflows
- ✅ Architecture visualization

---

## Dockerfile Patterns

### Pattern 1: Basic Extension

Add system dependencies to an existing base image.

```dockerfile
FROM ghcr.io/senanayake/polyglot-devcontainers-python-node:latest

# Switch to root to install packages
USER root

# Install additional system packages
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        postgresql-client \
        redis-tools \
        curl \
        jq && \
    rm -rf /var/lib/apt/lists/*

# Switch back to non-root user
USER vscode

# Set working directory
WORKDIR /workspace
```

**Key points:**
- Always `USER root` before `apt-get`
- Always `USER vscode` after installation
- Clean up apt cache with `rm -rf /var/lib/apt/lists/*`
- Use `--no-install-recommends` to minimize image size

---

### Pattern 2: Application Container

Build a production-ready application container.

```dockerfile
FROM ghcr.io/senanayake/polyglot-devcontainers-python-node:latest

USER root

# Install runtime dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        libpq5 \
        ca-certificates && \
    rm -rf /var/lib/apt/lists/*

# Set up application directory
WORKDIR /app

# Copy dependency files first (for layer caching)
COPY package.json pnpm-lock.yaml requirements.txt ./

# Install dependencies
RUN pnpm install --frozen-lockfile && \
    uv pip install -r requirements.txt

# Copy application code
COPY . .

# Build application (if needed)
RUN pnpm build

# Switch to non-root user
USER vscode

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Start application
CMD ["pnpm", "start"]
```

**Key points:**
- Copy dependency files before application code (layer caching)
- Install dependencies as root if needed
- Build application before switching to vscode user
- Always run application as vscode user
- Include health check for production deployments

---

### Pattern 3: Private Tool Installation

Install private or third-party tools.

```dockerfile
FROM ghcr.io/senanayake/polyglot-devcontainers-java:latest

USER root

# Create tool directory
RUN mkdir -p /opt/alloy

# Download and install private tool
RUN curl -fsSL \
    "https://github.com/AlloyTools/org.alloytools.alloy/releases/download/v6.1.0/org.alloytools.alloy.dist.jar" \
    -o /opt/alloy/alloy.jar

# Copy runner script
COPY alloy-runner.sh /opt/alloy/
RUN chmod +x /opt/alloy/alloy-runner.sh

# Make tool accessible
RUN ln -s /opt/alloy/alloy-runner.sh /usr/local/bin/alloy

USER vscode

ENTRYPOINT ["/opt/alloy/alloy-runner.sh"]
```

**Key points:**
- Install tools to `/opt/` for organization
- Use versioned URLs for reproducibility
- Make tools executable with `chmod +x`
- Symlink to `/usr/local/bin/` for PATH access

---

### Pattern 4: Multi-Stage Build

Optimize image size with multi-stage builds.

```dockerfile
# Build stage
FROM ghcr.io/senanayake/polyglot-devcontainers-python-node:latest AS builder

USER root
WORKDIR /build

# Copy and build
COPY package.json pnpm-lock.yaml ./
RUN pnpm install --frozen-lockfile

COPY . .
RUN pnpm build

# Production stage
FROM ghcr.io/senanayake/polyglot-devcontainers-python-node:latest

USER root

# Install only runtime dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        ca-certificates && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy only production dependencies
COPY package.json pnpm-lock.yaml ./
RUN pnpm install --prod --frozen-lockfile

# Copy built artifacts from builder
COPY --from=builder /build/dist ./dist

USER vscode

CMD ["node", "dist/index.js"]
```

**Key points:**
- Use `AS builder` for build stage
- Install dev dependencies only in builder
- Copy only production artifacts to final stage
- Results in smaller final image

---

## Security Best Practices

### 1. Non-Root User

**Always run applications as the `vscode` user (UID 1000).**

```dockerfile
# ❌ Bad: Running as root
FROM ghcr.io/senanayake/polyglot-devcontainers-python-node:latest
CMD ["python", "app.py"]  # Runs as root!

# ✅ Good: Explicit non-root user
FROM ghcr.io/senanayake/polyglot-devcontainers-python-node:latest
USER vscode
CMD ["python", "app.py"]
```

### 2. Minimal Layers

**Combine RUN commands to reduce layers and image size.**

```dockerfile
# ❌ Bad: Multiple layers
RUN apt-get update
RUN apt-get install -y package1
RUN apt-get install -y package2
RUN rm -rf /var/lib/apt/lists/*

# ✅ Good: Single layer with cleanup
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        package1 \
        package2 && \
    rm -rf /var/lib/apt/lists/*
```

### 3. No Secrets in Images

**Never embed secrets in container images.**

```dockerfile
# ❌ Bad: Secrets in environment
ENV API_KEY=secret123
ENV DATABASE_PASSWORD=password

# ✅ Good: Secrets at runtime
# Pass via:
# - Environment variables at runtime
# - Secret management system
# - Mounted files
```

### 4. Verify Downloads

**Verify checksums for downloaded files.**

```dockerfile
# ✅ Good: Verify checksum
RUN curl -fsSL https://example.com/tool.tar.gz -o tool.tar.gz && \
    echo "expected-sha256-hash  tool.tar.gz" | sha256sum -c - && \
    tar -xzf tool.tar.gz -C /usr/local/bin && \
    rm tool.tar.gz
```

### 5. Use Specific Versions

**Pin versions for reproducibility.**

```dockerfile
# ❌ Bad: Unpinned versions
RUN apt-get install -y nodejs

# ✅ Good: Specific versions
RUN apt-get install -y nodejs=22.0.0-1nodesource1
```

---

## Common Use Cases

### Use Case 1: FastAPI Application

```dockerfile
FROM ghcr.io/senanayake/polyglot-devcontainers-python-node:latest

USER root

# Install runtime dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        libpq5 && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python dependencies
COPY requirements.txt ./
RUN uv pip install -r requirements.txt

# Copy application
COPY . .

USER vscode

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

---

### Use Case 2: Node.js API with Docker Access

```dockerfile
FROM ghcr.io/senanayake/polyglot-devcontainers-python-node:latest

USER root

# Install Docker CLI for container management
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        docker.io && \
    rm -rf /var/lib/apt/lists/*

# Add vscode user to docker group
RUN usermod -aG docker vscode

WORKDIR /app

# Install dependencies
COPY package.json pnpm-lock.yaml ./
RUN pnpm install --frozen-lockfile

# Copy application
COPY . .

# Build TypeScript
RUN pnpm build

USER vscode

EXPOSE 3000

CMD ["pnpm", "tsx", "src/index.ts"]
```

---

### Use Case 3: Java Service with Custom JAR

```dockerfile
FROM ghcr.io/senanayake/polyglot-devcontainers-java:latest

USER root

# Create application directory
RUN mkdir -p /opt/myapp

# Copy JAR file
COPY target/myapp.jar /opt/myapp/

# Create startup script
COPY docker-entrypoint.sh /opt/myapp/
RUN chmod +x /opt/myapp/docker-entrypoint.sh

USER vscode

WORKDIR /opt/myapp

EXPOSE 8080

ENTRYPOINT ["/opt/myapp/docker-entrypoint.sh"]
```

---

## Building and Testing

### Build with Podman

```bash
# Build image
podman build -f Dockerfile -t my-private-image:latest .

# Tag for registry
podman tag my-private-image:latest registry.example.com/my-private-image:latest

# Push to registry
podman push registry.example.com/my-private-image:latest
```

### Build with Docker

```bash
# Build image
docker build -f Dockerfile -t my-private-image:latest .

# Tag for registry
docker tag my-private-image:latest registry.example.com/my-private-image:latest

# Push to registry
docker push registry.example.com/my-private-image:latest
```

### Test Locally

```bash
# Run container
podman run -it --rm \
    -p 8000:8000 \
    -v $(pwd):/workspace \
    my-private-image:latest

# Run with environment variables
podman run -it --rm \
    -e DATABASE_URL=postgresql://localhost/db \
    -e API_KEY=test-key \
    my-private-image:latest

# Run with shell for debugging
podman run -it --rm \
    --entrypoint /bin/bash \
    my-private-image:latest
```

### Test with DevPod

Create `.devcontainer/devcontainer.json`:

```json
{
  "name": "My Private Image",
  "image": "my-private-image:latest",
  "customizations": {
    "vscode": {
      "extensions": ["ms-python.python"]
    }
  }
}
```

Start DevPod:
```bash
devpod up . --ide vscode
```

---

## Example Templates

### Template 1: Python API

```dockerfile
FROM ghcr.io/senanayake/polyglot-devcontainers-python-node:latest

USER root

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        libpq5 \
        ca-certificates && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt ./
RUN uv pip install -r requirements.txt

COPY . .

USER vscode

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=3s \
    CMD curl -f http://localhost:8000/health || exit 1

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

---

### Template 2: Full-Stack App

```dockerfile
FROM ghcr.io/senanayake/polyglot-devcontainers-python-node:latest

USER root

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        nginx && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Backend
COPY requirements.txt ./
RUN uv pip install -r requirements.txt

# Frontend
COPY package.json pnpm-lock.yaml ./
RUN pnpm install --frozen-lockfile

COPY . .

# Build frontend
RUN pnpm build

USER vscode

EXPOSE 8000 3000

CMD ["./start.sh"]
```

---

### Template 3: Batch Processing

```dockerfile
FROM ghcr.io/senanayake/polyglot-devcontainers-python-node:latest

USER root

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        cron \
        logrotate && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt ./
RUN uv pip install -r requirements.txt

COPY . .

# Set up cron job
COPY crontab /etc/cron.d/batch-job
RUN chmod 0644 /etc/cron.d/batch-job && \
    crontab /etc/cron.d/batch-job

USER vscode

CMD ["cron", "-f"]
```

---

## Troubleshooting

### Issue: Permission Denied

**Symptom:**
```
Error: permission denied while trying to connect to the Docker daemon socket
```

**Solution:**
```dockerfile
# Add vscode user to docker group
USER root
RUN usermod -aG docker vscode
USER vscode
```

---

### Issue: Package Not Found

**Symptom:**
```
E: Package 'package-name' has no installation candidate
```

**Solution:**
```dockerfile
# Update package lists first
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        package-name && \
    rm -rf /var/lib/apt/lists/*
```

---

### Issue: Layer Caching Not Working

**Symptom:** Rebuilds install dependencies every time

**Solution:**
```dockerfile
# Copy dependency files first
COPY package.json pnpm-lock.yaml ./
RUN pnpm install --frozen-lockfile

# Then copy application code
COPY . .
```

---

### Issue: Image Too Large

**Symptom:** Image size is several GB

**Solution:**
```dockerfile
# Use multi-stage build
FROM base AS builder
# ... build steps ...

FROM base
COPY --from=builder /build/dist ./dist

# Clean up apt cache
RUN rm -rf /var/lib/apt/lists/*

# Use --no-install-recommends
RUN apt-get install -y --no-install-recommends package
```

---

## Best Practices Summary

✅ **Do:**
- Use specific base image tags (`:latest` or `:main`)
- Switch to `USER vscode` before CMD/ENTRYPOINT
- Combine RUN commands to reduce layers
- Clean up apt cache after installation
- Pin versions for reproducibility
- Include health checks for production
- Use multi-stage builds for optimization

❌ **Don't:**
- Run applications as root
- Embed secrets in images
- Use unpinned versions
- Create unnecessary layers
- Install recommended packages (`--no-install-recommends`)
- Leave apt cache in image

---

## Next Steps

1. **Choose your base image** - See [README](README.md#choosing-a-base-image)
2. **Review the base image contract** - See [base-image-contract.md](base-image-contract.md)
3. **Build your Dockerfile** - Use patterns from this guide
4. **Test locally** - Validate with Podman/Docker
5. **Deploy** - Push to your private registry

---

## Related Documentation

- [Downstream README](README.md) - Overview and quick start
- [Base Image Contract](base-image-contract.md) - Stable API reference
- [Private Scenarios](private-scenarios.md) - Scenario patterns

---

**Ready to build? Start with a template and customize for your use case.**
