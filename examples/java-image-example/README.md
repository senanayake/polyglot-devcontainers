# java-image-example

`java-image-example` is a minimal Gradle-first Java workspace that consumes the
published image `ghcr.io/senanayake/polyglot-devcontainers-java:main`
directly.

Use it when you want to validate the stable image-consumption path in VS Code
without building a local devcontainer definition first.

What it teaches:

- consuming the published Java image directly in VS Code
- the Gradle-first Java task contract
- dependency and security scanning in the standard workflow
- runtime guidance through `man`

After opening the example in a devcontainer, start with:

```bash
man polyglot
man polyglot-java
```

Then run:

```bash
task ci
```

Key implemented features:

- `task init|lint|test|scan|ci`
- Gradle wrapper workflow
- Spotless
- SpotBugs with FindSecBugs
- Trivy and `gitleaks`
- in-container runtime docs
