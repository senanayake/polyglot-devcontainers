# java-secure

`java-secure` is a minimal Gradle-first Java starter repository for the
standard task contract.

Included:

- `.devcontainer/devcontainer.json`
- `Taskfile.yml`
- a small Java sample library and tests
- Spotless formatting checks
- SpotBugs with FindSecBugs
- Trivy-based dependency vulnerability auditing
- local runtime docs available through `man polyglot` in the published image

After opening the template in a devcontainer, run:

```bash
man polyglot
task init
task ci
```

When consuming the published image directly in an empty workspace, `task init`
will scaffold the starter files and then prepare the project-local Gradle state
inside that workspace.
