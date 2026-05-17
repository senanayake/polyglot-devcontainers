---
id: KB-2026-037
type: failure-mode
status: active
created: 2026-05-16
updated: 2026-05-16
tags: [devcontainer, bash, path, python, venv, research-runner, smoke-test, kbpd]
related: [KB-2026-036]
---

# Login Shell PATH Reset Hid the Research Runner Virtualenv

## Context

The research-runner image installs its Python dependencies into
`/opt/research-venv` and expects `python3` to resolve from that virtual
environment.

## System/Component

- `templates/research-runner/.devcontainer/Containerfile`
- `templates/research-runner/Taskfile.yml`
- `scripts/smoke_test_published_starter.sh`
- base image shell profile behavior inherited from the Python/Node image

## Failure Description

### Symptoms

The image built successfully, and a direct `docker run image which python3`
resolved to `/opt/research-venv/bin/python3`. The starter smoke test still
failed:

```text
task: [init] test "$(which python3)" = "/opt/research-venv/bin/python3"
task: Failed to run task "init": exit status 1
```

### Failure Scenario

The smoke test runs commands through `bash -lc`. The login shell profile from
the base image reset `PATH`, so the Dockerfile `ENV PATH=...` value was not
preserved for the actual devcontainer-style command path.

### Impact

- The image appeared correct under direct non-login commands.
- The devcontainer-consumer path was broken.
- The failure would affect users and agents opening downstream workspaces where
  lifecycle commands run in login-shell-like environments.

## Root Cause

Docker `ENV PATH=/opt/research-venv/bin:$PATH` is not sufficient when inherited
login shell startup files overwrite `PATH`. The image needed a profile-level
runtime path export as well as Docker metadata.

## Evidence

Instrumentation inside the smoke path showed:

```text
before task: /usr/local/bin/python3
PATH=/usr/local/python/current/bin:/usr/local/py-utils/bin:...
```

After adding `/etc/profile.d/polyglot-research-venv.sh`, the research smoke
test passed and `task init` observed `/opt/research-venv/bin/python3`.

## Prevention

### Design Changes

- For global language runtimes installed outside the base image defaults, add
  both Docker `ENV PATH=...` and a profile script under `/etc/profile.d`.
- Keep starter smoke tests on `bash -lc`; they catch login-shell path drift
  that direct `docker run image command` misses.
- Avoid absolute workspace paths in template tests; validate `test -w .` so
  mounted downstream workspaces under `/workspaces/<name>` pass.

### Monitoring

Image smoke tests should include:

```bash
bash scripts/smoke_test_published_starter.sh --image <image>
```

and template-local `task ci` inside a mounted workspace.

## Recommendation

Any published image that changes the default interpreter or task runtime should
prove the runtime under `bash -lc`, not only through Docker `ENV` inspection.
