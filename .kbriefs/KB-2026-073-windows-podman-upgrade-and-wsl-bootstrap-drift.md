---
id: KB-2026-073
type: failure-mode
status: active
created: 2026-05-17
updated: 2026-05-17
tags:
  - windows
  - podman
  - wsl
  - devcontainers
  - runtime-health
  - kbpd
related:
  - KB-2026-027
  - KB-2026-071
---

# Windows Podman Upgrade Can Leave WSL Machine Bootstrap Incomplete

## Context

After Windows Podman storage exhaustion was mitigated by removing large Podman
container state, a Podman CLI upgrade and machine recreation still did not
restore a healthy runtime. Podman Desktop showed the machine moving from
`Starting` to `Stopped`, and Dev Containers CLI failed before the paper
devcontainer could start.

The LaTeX image and downstream paper repository were not the root cause. Once
the runtime path was repaired, the paper devcontainer started and `task ci`
successfully built and validated `main.pdf`.

## System/Component

- Windows host
- WSL 2
- Podman CLI and Podman Desktop
- WSL-backed `podman-machine-default`
- Dev Containers CLI using `--docker-path podman`

## Failure Description

### Symptoms

- `podman machine init` imports the machine image successfully.
- `podman machine start` reports:
  - Docker API forwarding cannot claim `\\.\pipe\docker_engine`
  - `machine did not transition into running state`
  - SSH error because the machine is not in running state
- Podman Desktop changes the machine state from `Starting` to `Stopped`.
- `podman ps` fails with a refused connection to the configured SSH port.
- Inside the WSL distro:
  - `/init` is PID 1
  - `systemctl is-system-running` cannot connect to the system bus
  - SSH host keys are missing
  - `sshd` is not listening
  - `podman.socket` is not active

### Failure Scenario

- The old Podman machine backing data was removed during storage recovery.
- Podman was upgraded and a new WSL-backed machine was initialized.
- The fresh Fedora WSL machine imported correctly but did not boot with the
  systemd/cgroup behavior Podman expected.
- Podman machine metadata existed, but the SSH and Podman API services inside
  the distro were not healthy.
- Manual WSL inspection started the distro enough to create SSH port drift:
  Podman reassigned the machine SSH port, while `sshd` still listened on the
  old port.

### Impact

- Devcontainer launch failed before image validation could begin.
- Podman Desktop exposed only a generic start/stop symptom.
- Repeated reinstall or machine recreation attempts risked losing more runtime
  evidence without addressing the WSL bootstrap condition.
- The user could not distinguish image correctness from host-runtime failure
  without lower-level probes.

## Root Cause

### Primary Cause

The WSL-backed Podman machine booted without the systemd and cgroup v2 behavior
required for Podman's managed machine services.

### Contributing Factors

- Podman Desktop hides lower-level WSL/systemd/SSH/socket state.
- `podman machine list` can report stale machine metadata.
- Docker API forwarding errors can distract from the real Podman SSH/socket
  failure when `--docker-path podman` is the intended control path.
- Manual WSL startup can leave Podman machine metadata and `sshd_config` on
  different SSH ports.

### Failure Mechanism

```text
Podman machine imports into WSL
-> WSL starts without systemd as PID 1
-> sshd and podman.socket do not start
-> Windows Podman client cannot connect over SSH
-> Podman Desktop reports stopped and devcontainer launch fails
```

## Evidence

Observed inside the failed machine:

```text
systemctl is-system-running
Failed to connect to system scope bus via local transport

ps -ef
PID 1 /init

ls -l /etc/ssh/ssh_host_*
no host keys

ss -ltnp
no listener on the Podman machine SSH port
```

After enabling WSL systemd and cgroup v2 behavior:

```text
systemctl is-system-running
running

ls -l /etc/ssh/ssh_host_*
ssh host keys exist

ss -ltnp | grep <port>
sshd is listening
```

After aligning `sshd_config` to the port in `podman machine inspect`:

```text
podman ps
CONTAINER ID  IMAGE  COMMAND  CREATED  STATUS  PORTS  NAMES
```

The downstream acceptance path then succeeded:

```text
devcontainer up --docker-path podman --workspace-folder paper
task ci
main.pdf built and validated with pdfinfo
gitleaks found no leaks
```

## Prevention

### Design Changes

- Add Windows Podman preflight, cleanup report, and repair scripts.
- Make `podman ps` the primary local runtime health check.
- Keep Dev Containers CLI examples explicit about `--docker-path podman`.
- Treat Podman Desktop state as a UI signal, not as authoritative runtime
  evidence.

### Operational Controls

- Before devcontainer work on Windows Podman, run:

```powershell
powershell -ExecutionPolicy Bypass -File scripts\windows-podman-preflight.ps1
```

- When disk pressure is suspected, run:

```powershell
powershell -ExecutionPolicy Bypass -File scripts\windows-podman-cleanup-report.ps1
```

- Repair from dry-run first:

```powershell
powershell -ExecutionPolicy Bypass -File scripts\windows-podman-repair.ps1
powershell -ExecutionPolicy Bypass -File scripts\windows-podman-repair.ps1 -Apply
```

## Detection

### Early Warning Signs

- `podman ps` fails while `podman --version` succeeds.
- `podman machine start` reports SSH or running-state errors.
- `systemctl is-system-running` fails inside `podman-machine-default`.
- `sshd` listens on a different port from `podman machine inspect`.
- Dev Containers CLI reports `docker ps` because `--docker-path podman` was
  omitted.

### Detection Methods

- `scripts/windows-podman-preflight.ps1`
- `scripts/windows-podman-cleanup-report.ps1`
- `scripts/windows-podman-repair.ps1` dry-run

## Mitigation

### Immediate Response

1. Stop treating the devcontainer or image as suspect until `podman ps` works.
2. Run the preflight script and capture diagnostics.
3. Enable WSL systemd/cgroup v2 behavior if systemd is not running.
4. Align `sshd_config` to the SSH port in `podman machine inspect` if needed.
5. Verify `podman run --rm alpine:3.20 echo podman-ok`.
6. Retry `devcontainer up --docker-path podman`.

### Recovery Procedure

Use the guarded repair script:

```powershell
powershell -ExecutionPolicy Bypass -File scripts\windows-podman-repair.ps1 -Apply
```

If the machine is still unhealthy, prefer:

```powershell
podman machine reset -f
```

over deleting broad user-profile directories.

## Lessons Learned

- On Windows, Podman health is a layered system: CLI, machine metadata, WSL,
  systemd, SSH, socket activation, and optional Docker API forwarding.
- A successful machine import is not proof that the Podman engine is reachable.
- The most reliable local acceptance check is `podman ps`, followed by a small
  `podman run`.
- Repository scripts should encode the diagnostic order so maintainers do not
  have to rediscover WSL/systemd/SSH failure modes.

## Applicability

### This Failure Mode Applies To

- Windows hosts using Podman machine with WSL.
- Dev Containers CLI workflows using Podman.
- Podman Desktop start/stop failures after upgrade, cleanup, or machine reset.

### This Failure Mode Does Not Apply To

- Native Linux Podman installations without a WSL-backed machine.
- Docker Desktop-only workflows where Docker is the intended runtime.

## Status

- [x] Documented
- [x] Prevention implemented with preflight and cleanup reporting
- [x] Detection implemented with Windows Podman diagnostics
- [x] Mitigation scripted with guarded repair
- [ ] Long-term CI coverage for PowerShell scripts added

## Related Knowledge

- [KB-2026-027](KB-2026-027-windows-podman-machine-control-path-failure.md)
- [KB-2026-071](KB-2026-071-windows-podman-image-validation-storage-exhaustion.md)
