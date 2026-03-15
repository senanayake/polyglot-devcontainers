# java-image-example

`java-image-example` is a minimal Gradle-first Java workspace that consumes the
published image `ghcr.io/senanayake/polyglot-devcontainers-java:main`
directly.

Use it when you want to validate the stable image-consumption path in VS Code
without building a local devcontainer definition first.

After opening the example in a devcontainer, run:

```bash
task ci
```
