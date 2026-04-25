# Base Image Contract

**Status:** Stable  
**Last Updated:** 2026-04-15

---

## Overview

This document defines the **stable API** that polyglot-devcontainers guarantees for downstream projects. These guarantees allow you to build private images with confidence that your dependencies won't break unexpectedly.

---

## Versioning and Stability

### Semantic Versioning

Polyglot follows semantic versioning for breaking changes:
- **Major version** - Breaking changes to stable API
- **Minor version** - New features, backward compatible
- **Patch version** - Bug fixes, backward compatible

### Stability Levels

| Level | Guarantee | Example |
|-------|-----------|---------|
| **Stable** | Won't change without major version bump | User `vscode`, tool paths |
| **Experimental** | May change in minor versions | New features, beta tools |
| **Internal** | No guarantees, may change anytime | Build scripts, temp files |

---

## Universal Guarantees

These guarantees apply to **all** polyglot base images.

### User and Permissions

**User:** `vscode`
- **UID:** 1000
- **GID:** 1000
- **Home:** `/home/vscode`
- **Shell:** `/bin/bash`
- **Groups:** `vscode`, `sudo` (passwordless)

**Stability:** ✅ **Stable** - Will not change

**Example:**
```dockerfile
FROM ghcr.io/senanayake/polyglot-devcontainers-python-node:latest
# You can rely on:
USER vscode  # Always exists
WORKDIR /home/vscode  # Always writable
```

---

### Core Tools

All images include these tools at stable paths:

| Tool | Path | Version | Stability |
|------|------|---------|-----------|
| `task` | `/usr/local/bin/task` | 3.x | ✅ Stable |
| `gitleaks` | `/usr/local/bin/gitleaks` | 8.x | ✅ Stable |
| `pre-commit` | `/usr/local/bin/pre-commit` | Latest | ✅ Stable |
| `git` | `/usr/bin/git` | 2.x | ✅ Stable |
| `bash` | `/bin/bash` | 5.x | ✅ Stable |
| `curl` | `/usr/bin/curl` | 7.x+ | ✅ Stable |
| `jq` | `/usr/bin/jq` | 1.x | ✅ Stable |

**Stability:** ✅ **Stable** - Paths and major versions guaranteed

**Example:**
```dockerfile
FROM ghcr.io/senanayake/polyglot-devcontainers-java:latest
# You can rely on:
RUN /usr/local/bin/task --version  # Always works
RUN /usr/local/bin/gitleaks version  # Always works
```

---

### Environment Variables

| Variable | Value | Purpose | Stability |
|----------|-------|---------|-----------|
| `HOME` | `/home/vscode` | User home directory | ✅ Stable |
| `USER` | `vscode` | Current user | ✅ Stable |
| `SHELL` | `/bin/bash` | Default shell | ✅ Stable |
| `PATH` | Includes `/usr/local/bin` | Tool discovery | ✅ Stable |

**Stability:** ✅ **Stable** - Will not change

---

### Directory Structure

| Path | Purpose | Writable by vscode | Stability |
|------|---------|-------------------|-----------|
| `/home/vscode` | User home | ✅ Yes | ✅ Stable |
| `/workspace` | Default workspace | ✅ Yes | ✅ Stable |
| `/usr/local/bin` | User-installed binaries | ❌ No (root only) | ✅ Stable |
| `/opt` | Optional software | ❌ No (root only) | ✅ Stable |
| `/tmp` | Temporary files | ✅ Yes | ✅ Stable |

**Stability:** ✅ **Stable** - Paths and permissions guaranteed

---

## Python-Node Image Contract

**Image:** `ghcr.io/senanayake/polyglot-devcontainers-python-node:latest`

### Python Guarantees

| Component | Path | Version | Stability |
|-----------|------|---------|-----------|
| Python | `/usr/bin/python3` | 3.12.x | ✅ Stable (3.12+) |
| pip | `/usr/bin/pip3` | Latest | ✅ Stable |
| uv | `/usr/local/bin/uv` | 0.11.x+ | ✅ Stable |
| venv | Built-in | - | ✅ Stable |

**Python version policy:**
- **Guaranteed:** Python 3.12 or newer
- **Upgrade path:** Minor version bumps (3.12 → 3.13) are backward compatible
- **Breaking change:** Major version bumps (3.x → 4.x) would require polyglot major version bump

**Example:**
```dockerfile
FROM ghcr.io/senanayake/polyglot-devcontainers-python-node:latest
# You can rely on:
RUN python3 --version  # Always 3.12+
RUN uv --version  # Always available
RUN python3 -m venv .venv  # Always works
```

---

### Node.js Guarantees

| Component | Path | Version | Stability |
|-----------|------|---------|-----------|
| Node.js | `/usr/bin/node` | 22.x | ✅ Stable (22+) |
| npm | `/usr/bin/npm` | 10.x+ | ✅ Stable |
| pnpm | Via corepack | 9.x+ | ✅ Stable |
| corepack | `/usr/bin/corepack` | Latest | ✅ Stable |

**Node.js version policy:**
- **Guaranteed:** Node.js 22 or newer (LTS)
- **Upgrade path:** LTS upgrades (22 → 24) are backward compatible
- **Breaking change:** Non-LTS or major breaking changes would require polyglot major version bump

**Example:**
```dockerfile
FROM ghcr.io/senanayake/polyglot-devcontainers-python-node:latest
# You can rely on:
RUN node --version  # Always 22+
RUN pnpm --version  # Always available via corepack
RUN npm --version  # Always available
```

---

### Package Manager Guarantees

| Tool | Availability | Stability |
|------|--------------|-----------|
| `uv` | ✅ Guaranteed | ✅ Stable |
| `pnpm` | ✅ Guaranteed (via corepack) | ✅ Stable |
| `npm` | ✅ Guaranteed | ✅ Stable |
| `pip` | ✅ Guaranteed | ✅ Stable |

**Example:**
```dockerfile
FROM ghcr.io/senanayake/polyglot-devcontainers-python-node:latest
# You can rely on:
RUN uv pip install package  # Always works
RUN pnpm install  # Always works
RUN npm install  # Always works
```

---

## Java Image Contract

**Image:** `ghcr.io/senanayake/polyglot-devcontainers-java:latest`

### Java Guarantees

| Component | Path | Version | Stability |
|-----------|------|---------|-----------|
| Java (Temurin) | `/usr/bin/java` | 21.x | ✅ Stable (21+) |
| javac | `/usr/bin/javac` | 21.x | ✅ Stable |
| JAVA_HOME | `/usr/lib/jvm/temurin-21-jdk-amd64` | 21.x | ✅ Stable |

**Java version policy:**
- **Guaranteed:** Java 21 (LTS) or newer
- **Upgrade path:** LTS upgrades (21 → 25) are backward compatible
- **Breaking change:** Major breaking changes would require polyglot major version bump

**Example:**
```dockerfile
FROM ghcr.io/senanayake/polyglot-devcontainers-java:latest
# You can rely on:
RUN java --version  # Always 21+
RUN javac --version  # Always 21+
ENV JAVA_HOME=/usr/lib/jvm/temurin-21-jdk-amd64  # Always set
```

---

### Build Tool Guarantees

| Tool | Availability | Version | Stability |
|------|--------------|---------|-----------|
| Gradle | ✅ Guaranteed | 8.x+ | ✅ Stable |
| Maven | ⚠️ Not guaranteed | - | ❌ Not stable |

**Example:**
```dockerfile
FROM ghcr.io/senanayake/polyglot-devcontainers-java:latest
# You can rely on:
RUN gradle --version  # Always available
```

---

## Diagrams Image Contract

**Image:** `ghcr.io/senanayake/polyglot-devcontainers-diagrams:latest`

### Diagram Tool Guarantees

| Tool | Availability | Stability |
|------|--------------|-----------|
| Mermaid CLI | ✅ Guaranteed | ✅ Stable |
| PlantUML | ✅ Guaranteed | ✅ Stable |
| Graphviz | ✅ Guaranteed | ✅ Stable |

**Example:**
```dockerfile
FROM ghcr.io/senanayake/polyglot-devcontainers-diagrams:latest
# You can rely on:
RUN mmdc --version  # Mermaid CLI
RUN plantuml -version  # PlantUML
RUN dot -V  # Graphviz
```

---

## What's NOT Guaranteed

### Experimental Features

These may change in minor versions:
- New tools added in recent releases
- Beta features marked as experimental
- Tools not listed in this contract

### Internal Implementation

These may change at any time:
- Build scripts and Containerfiles
- Internal directory structure (outside documented paths)
- Temporary files and caches
- Image layer structure

### System Packages

These may be upgraded in patch versions:
- System libraries (libc, openssl, etc.)
- Debian base packages
- Security updates

**Recommendation:** If you depend on specific system package versions, pin them explicitly in your Dockerfile.

---

## Deprecation Policy

### How Deprecations Work

1. **Announcement** - Feature marked as deprecated in release notes
2. **Grace period** - Minimum 6 months before removal
3. **Removal** - Only in major version bump

### Example Deprecation

```
v1.5.0 - Feature X deprecated, use Feature Y instead
v1.6.0 - Feature X still works, deprecation warning
v1.7.0 - Feature X still works, deprecation warning
v2.0.0 - Feature X removed
```

---

## Breaking Change Examples

### What Requires Major Version Bump

❌ **Breaking changes:**
- Removing `vscode` user
- Changing UID/GID of `vscode` user
- Removing guaranteed tools (`task`, `gitleaks`, etc.)
- Changing tool paths (`/usr/local/bin/task` → `/usr/bin/task`)
- Downgrading language versions (Python 3.12 → 3.11)
- Removing guaranteed environment variables

### What Doesn't Require Major Version Bump

✅ **Non-breaking changes:**
- Adding new tools
- Upgrading language versions (Python 3.12 → 3.13)
- Adding new environment variables
- Improving performance
- Security updates
- Bug fixes

---

## Testing Your Dependencies

### Verify Stable API

Create a test Dockerfile:

```dockerfile
FROM ghcr.io/senanayake/polyglot-devcontainers-python-node:latest

# Test user
RUN [ "$(whoami)" = "vscode" ] || exit 1
RUN [ "$(id -u)" = "1000" ] || exit 1

# Test tools
RUN task --version
RUN gitleaks version
RUN pre-commit --version

# Test languages
RUN python3 --version | grep -E "3\.(12|13|14|15|16)"
RUN node --version | grep -E "v(22|24|26)"

# Test package managers
RUN uv --version
RUN pnpm --version

# Test paths
RUN [ -x /usr/local/bin/task ]
RUN [ -x /usr/local/bin/gitleaks ]
RUN [ -d /home/vscode ]
RUN [ -w /home/vscode ]

# Test environment
RUN [ "$HOME" = "/home/vscode" ]
RUN [ "$USER" = "vscode" ]
RUN [ "$SHELL" = "/bin/bash" ]

RUN echo "All stable API tests passed!"
```

Run:
```bash
podman build -f test.Dockerfile -t api-test .
```

---

## Version Compatibility Matrix

### Python-Node Image

| Polyglot Version | Python | Node | uv | pnpm |
|------------------|--------|------|-----|------|
| 1.x (current) | 3.12+ | 22+ | 0.11+ | 9+ |
| 2.x (future) | 3.13+ | 24+ | 0.12+ | 10+ |

### Java Image

| Polyglot Version | Java | Gradle |
|------------------|------|--------|
| 1.x (current) | 21+ | 8+ |
| 2.x (future) | 25+ | 9+ |

---

## Reporting Issues

### If Something Breaks

If a guaranteed feature breaks:

1. **Check your base image tag** - Are you using `:latest` or `:main`?
2. **Review release notes** - Was there a major version bump?
3. **File an issue** - [GitHub Issues](https://github.com/senanayake/polyglot-devcontainers/issues)

Include:
- Base image and tag used
- Expected behavior (per this contract)
- Actual behavior
- Minimal reproduction Dockerfile

---

## Future Guarantees

### Planned Additions (v2.x)

These features are planned for future major versions:

- **Rust toolchain** - rustc, cargo
- **Go toolchain** - go compiler
- **Container tools** - buildah, skopeo
- **Cloud CLIs** - aws, gcloud, az

These will be added with stability guarantees in future releases.

---

## Summary

### What You Can Rely On

✅ **User and permissions** - `vscode` user (UID 1000)  
✅ **Core tools** - task, gitleaks, pre-commit, git, bash  
✅ **Tool paths** - `/usr/local/bin/task`, etc.  
✅ **Environment** - HOME, USER, SHELL, PATH  
✅ **Directory structure** - `/home/vscode`, `/workspace`, etc.  
✅ **Language versions** - Python 3.12+, Node 22+, Java 21+  
✅ **Package managers** - uv, pnpm, npm, pip  

### What May Change

⚠️ **Experimental features** - New tools, beta features  
⚠️ **Internal implementation** - Build scripts, layer structure  
⚠️ **System packages** - Security updates, library versions  

---

## Next Steps

1. **Review your dependencies** - Check if they're in the stable API
2. **Pin your base image** - Use specific tags (`:latest` or `:v1.0.0`)
3. **Test your build** - Verify stable API with test Dockerfile
4. **Monitor releases** - Watch for deprecation announcements

---

## Related Documentation

- [Downstream README](README.md) - Overview and quick start
- [Building Private Images](building-private-images.md) - Dockerfile patterns
- [Private Scenarios](private-scenarios.md) - Scenario patterns

---

**Build with confidence knowing what's stable and what's not.**
