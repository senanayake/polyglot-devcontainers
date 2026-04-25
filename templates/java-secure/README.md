# java-secure

`java-secure` is a minimal Gradle-first Java starter repository for the
standard task contract.

Included:

- `.devcontainer/devcontainer.json`
- `Taskfile.yml`
- a small Java sample library and tests
- unit, property, integration, and acceptance test suites
- Spotless formatting checks
- SpotBugs with FindSecBugs
- Trivy-based dependency vulnerability auditing
- local runtime docs available through `man polyglot` in the published image

Focused test commands are also available:

```bash
task test
task test:fast
task test:unit
task test:integration
task test:acceptance
task test:property
```

After opening the template in a devcontainer, run:

```bash
man polyglot
task init
task ci
```

When consuming the published image directly in an empty workspace, `task init`
will scaffold the starter files, create a starter `AGENTS.md`, create a
`.kbriefs/` workspace with templates, create a Diataxis-shaped `docs/` tree,
and then prepare the project-local Gradle state inside that workspace.
