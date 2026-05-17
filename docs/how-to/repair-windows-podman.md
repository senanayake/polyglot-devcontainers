# Repair Windows Podman Runtime Health

Use this guide when Windows, Podman Desktop, or the Dev Containers CLI reports
runtime failures before a devcontainer can start.

The goal is to distinguish repository failures from host-runtime failures. Do
not treat a failed `devcontainer up` as evidence about an image until Podman can
run a small container.

## Preflight

Run the read-only preflight first:

```powershell
powershell -ExecutionPolicy Bypass -File scripts\windows-podman-preflight.ps1
```

For deeper WSL service inspection:

```powershell
powershell -ExecutionPolicy Bypass -File scripts\windows-podman-preflight.ps1 -InspectMachineInternals
```

For an end-to-end runtime probe that pulls and runs Alpine:

```powershell
powershell -ExecutionPolicy Bypass -File scripts\windows-podman-preflight.ps1 -RunContainerProbe
```

The preflight writes JSON and Markdown diagnostics under:

```text
.artifacts/diagnostics/windows-podman/
```

The most important health check is:

```powershell
podman ps
```

If `podman ps` fails, Dev Containers CLI and Podman Desktop are expected to fail
too.

## Cleanup Report

When disk pressure is suspected, run the cleanup report:

```powershell
powershell -ExecutionPolicy Bypass -File scripts\windows-podman-cleanup-report.ps1
```

For a faster report that avoids recursive size calculation:

```powershell
powershell -ExecutionPolicy Bypass -File scripts\windows-podman-cleanup-report.ps1 -SkipDeepSize -SkipVhdxScan
```

The report is diagnostic only. It does not delete files.

Prefer cleanup in this order:

```powershell
podman system prune
podman machine reset -f
```

Avoid deleting all of:

```text
C:\Users\<user>\.local
```

That directory can contain non-Podman user state. If manual deletion is
unavoidable, stop Podman, run `wsl --shutdown`, and remove only the targeted
Podman machine/storage paths that the report identifies.

## Repair

Run the repair script without `-Apply` first:

```powershell
powershell -ExecutionPolicy Bypass -File scripts\windows-podman-repair.ps1
```

The dry run prints the actions it would take. To apply the known safe repair
steps:

```powershell
powershell -ExecutionPolicy Bypass -File scripts\windows-podman-repair.ps1 -Apply
```

The repair script:

- ensures host WSL cgroup v2 boot settings are present when no conflicting
  `kernelCommandLine` already exists
- enables systemd in the Podman machine WSL distro
- restarts WSL so boot settings apply
- starts the Podman machine
- aligns `sshd_config` with the SSH port in `podman machine inspect`
- enables and restarts `sshd` and `podman.socket`
- selects the rootful Podman connection
- verifies `podman ps`

It does not delete machine data and does not run `podman machine reset`.

## Dev Containers CLI

Always pass Podman explicitly:

```powershell
devcontainer up --docker-path podman --workspace-folder .
devcontainer exec --docker-path podman --workspace-folder . task ci
```

If using the pinned fallback:

```powershell
npx -y @devcontainers/cli@0.86.0 up --docker-path podman --workspace-folder .
npx -y @devcontainers/cli@0.86.0 exec --docker-path podman --workspace-folder . task ci
```

Without `--docker-path podman`, the Dev Containers CLI may call `docker ps` and
fail on hosts that intentionally use Podman.

## Known Failure Signals

The following signals indicate host-runtime failure, not repository failure:

- `podman ps` cannot connect to `127.0.0.1:<port>`
- Podman Desktop changes from `Starting` to `Stopped`
- `podman machine list` shows stale metadata while `wsl --list --verbose` shows
  the distro running
- `systemctl is-system-running` fails inside the Podman WSL distro
- no SSH host keys exist under `/etc/ssh/ssh_host_*`
- `sshd` is listening on a different port from `podman machine inspect`
- Dev Containers CLI reports `docker ps` errors because `--docker-path podman`
  was omitted

## Related Knowledge

- `.kbriefs/KB-2026-027-windows-podman-machine-control-path-failure.md`
- `.kbriefs/KB-2026-071-windows-podman-image-validation-storage-exhaustion.md`
- `.kbriefs/KB-2026-073-windows-podman-upgrade-and-wsl-bootstrap-drift.md`
