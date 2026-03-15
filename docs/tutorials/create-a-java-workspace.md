# Create a Java Workspace

This tutorial walks through the smallest Java workflow in the repository.

## 1. Copy the template

Copy `templates/java-secure` into a new repository or working folder.

## 2. Open it in a devcontainer

Use the Java template's `.devcontainer/devcontainer.json` and reopen the
workspace in the container.

The container provides:

- Java 21
- `task`
- `gitleaks`
- pinned `gradle`

## 3. Initialize the workspace

Run:

```bash
task init
```

This resolves the Gradle project and prepares the sample sources.

## 4. Run the quality checks

Run:

```bash
task lint
```

This executes:

- Spotless formatting checks
- SpotBugs with FindSecBugs

## 5. Run tests

Run:

```bash
task test
```

The sample JUnit test should pass.

## 6. Run the security workflow

Run:

```bash
task scan
```

This performs:

- dependency vulnerability auditing with Trivy
- secret scanning with `gitleaks`

## 7. Run the full contract

Run:

```bash
task ci
```

At this point you have a working Java workspace that matches the repository's
container-first contract.
