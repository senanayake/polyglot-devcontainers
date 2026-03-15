# Use the Published Java Image

Use this flow when you want a Java workspace in VS Code based on the published
image `ghcr.io/senanayake/polyglot-devcontainers-java:main` instead of building
the template locally.

If you want a ready-made starting point, copy
`examples/java-image-example` and adjust it for your project.

## 1. Create a repository folder

Create or open your Java project folder.

The project should contain at least:

- `settings.gradle.kts`
- `build.gradle.kts`
- `src/main/java/`
- `src/test/java/`

## 2. Add a devcontainer definition

Create `.devcontainer/devcontainer.json` with:

```json
{
  "name": "java-secure",
  "image": "ghcr.io/senanayake/polyglot-devcontainers-java:main",
  "remoteUser": "vscode",
  "customizations": {
    "vscode": {
      "extensions": [
        "vscjava.vscode-java-pack"
      ],
      "settings": {
        "editor.formatOnSave": true,
        "java.configuration.updateBuildConfiguration": "automatic",
        "java.import.gradle.enabled": true
      }
    }
  }
}
```

## 3. Open in VS Code

On Windows, prefer a WSL path.

Then:

1. open the project folder in VS Code
2. run `Dev Containers: Reopen in Container`

VS Code will pull `ghcr.io/senanayake/polyglot-devcontainers-java:main` and
open your project inside that container.

## 4. Add the standard task contract

If your project does not already expose the repository task contract, add a
`Taskfile.yml` with:

```yaml
version: "3"

tasks:
  init:
    cmds:
      - mkdir -p .artifacts/scans
      - GRADLE_USER_HOME=.gradle gradle --no-daemon --write-locks testClasses

  lint:
    deps: [init]
    cmds:
      - GRADLE_USER_HOME=.gradle gradle --no-daemon spotlessCheck spotbugsMain spotbugsTest

  test:
    deps: [init]
    cmds:
      - GRADLE_USER_HOME=.gradle gradle --no-daemon test

  scan:
    deps: [init]
    cmds:
      - mkdir -p .artifacts/scans
      - trivy fs --scanners vuln --format json --output .artifacts/scans/trivy-java.json .
      - gitleaks dir . --no-banner --redact --report-format sarif --report-path .artifacts/scans/gitleaks.sarif

  ci:
    cmds:
      - task init
      - task lint
      - task test
      - task scan
```

## 5. Validate the workspace

Inside the container terminal, run:

```bash
task ci
```

That proves the project works against the same contract used throughout this
repository.
