#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import signal
import subprocess
import sys
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import urlopen

import starter_site


ROOT = starter_site.ROOT
DEFAULT_HOST = starter_site.DEFAULT_HOST
DEFAULT_PORT = starter_site.DEFAULT_PORT
TMP_ROOT = ROOT / ".tmp"


@dataclass
class SiteRecord:
    host: str
    port: int
    pid: int
    stdout_log: str
    stderr_log: str
    started_at: float


def record_suffix(host: str, port: int) -> str:
    if host == DEFAULT_HOST and port == DEFAULT_PORT:
        return ""
    safe_host = "".join(character if character.isalnum() else "_" for character in host)
    return f"-{safe_host}-{port}"


def record_path(host: str, port: int) -> Path:
    return TMP_ROOT / f"starter-site{record_suffix(host, port)}.pid.json"


def stdout_log_path(host: str, port: int) -> Path:
    return TMP_ROOT / f"starter-site{record_suffix(host, port)}.stdout.log"


def stderr_log_path(host: str, port: int) -> Path:
    return TMP_ROOT / f"starter-site{record_suffix(host, port)}.stderr.log"


def health_url(host: str, port: int) -> str:
    return f"http://{host}:{port}/healthz"


def load_record(host: str, port: int) -> SiteRecord | None:
    path = record_path(host, port)
    if not path.exists():
        return None
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise SystemExit(f"invalid starter-site record at {path}: {error}") from error
    return SiteRecord(
        host=str(payload["host"]),
        port=int(payload["port"]),
        pid=int(payload["pid"]),
        stdout_log=str(payload["stdout_log"]),
        stderr_log=str(payload["stderr_log"]),
        started_at=float(payload["started_at"]),
    )


def save_record(record: SiteRecord) -> None:
    TMP_ROOT.mkdir(parents=True, exist_ok=True)
    record_path(record.host, record.port).write_text(
        json.dumps(asdict(record), indent=2) + "\n",
        encoding="utf-8",
    )


def remove_record(host: str, port: int) -> None:
    path = record_path(host, port)
    if path.exists():
        path.unlink()


def is_pid_running(pid: int) -> bool:
    if os.name == "nt":
        result = subprocess.run(
            ["tasklist", "/FI", f"PID eq {pid}", "/FO", "CSV", "/NH"],
            check=False,
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            return False
        output = result.stdout.strip()
        return bool(output) and "No tasks are running" not in output
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    return True


def is_healthy(host: str, port: int, timeout: float = 1.0) -> bool:
    try:
        with urlopen(health_url(host, port), timeout=timeout) as response:  # noqa: S310
            return response.status == 200
    except (HTTPError, URLError, OSError):
        return False


def describe_state(host: str, port: int) -> tuple[str, SiteRecord | None, bool, bool]:
    record = load_record(host, port)
    healthy = is_healthy(host, port)
    pid_running = bool(record and is_pid_running(record.pid))
    if record and pid_running and healthy:
        return ("running-managed", record, True, True)
    if record and pid_running and not healthy:
        return ("starting-or-degraded", record, False, True)
    if record and not pid_running and healthy:
        return ("running-with-stale-record", record, True, False)
    if record:
        return ("stopped-with-stale-record", record, False, False)
    if healthy:
        return ("running-unmanaged", None, True, False)
    return ("stopped", None, False, False)


def terminate_pid(pid: int) -> None:
    if os.name == "nt":
        try:
            os.kill(pid, signal.SIGTERM)
        except ProcessLookupError:
            return
    else:
        os.kill(pid, signal.SIGTERM)


def kill_pid(pid: int) -> None:
    if os.name == "nt":
        subprocess.run(
            ["taskkill", "/PID", str(pid), "/T", "/F"],
            check=False,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        return
    os.kill(pid, signal.SIGKILL)


def wait_for_shutdown(host: str, port: int, pid: int, timeout: float) -> bool:
    deadline = time.time() + timeout
    while time.time() < deadline:
        if not is_pid_running(pid) and not is_healthy(host, port, timeout=0.5):
            return True
        time.sleep(0.25)
    return False


def command_status(host: str, port: int) -> int:
    state, record, healthy, pid_running = describe_state(host, port)
    if record:
        print(
            json.dumps(
                {
                    "status": state,
                    "managed": True,
                    "healthy": healthy,
                    "pid_running": pid_running,
                    "pid": record.pid,
                    "url": health_url(host, port).removesuffix("/healthz"),
                    "stdout_log": record.stdout_log,
                    "stderr_log": record.stderr_log,
                },
                indent=2,
            )
        )
        return 0
    print(
        json.dumps(
            {
                "status": state,
                "managed": False,
                "healthy": healthy,
                "pid_running": pid_running,
                "url": health_url(host, port).removesuffix("/healthz"),
            },
            indent=2,
        )
    )
    return 0


def command_start(host: str, port: int) -> int:
    state, record, healthy, pid_running = describe_state(host, port)
    url = health_url(host, port).removesuffix("/healthz")
    if state == "running-managed" and record:
        print(f"starter-site already running at {url} (pid {record.pid})")
        return 0
    if state == "running-unmanaged":
        raise SystemExit(
            f"starter-site already responding at {url} without a managed pid record; stop it manually or choose another port"
        )
    if state == "starting-or-degraded" and record and pid_running and not healthy:
        raise SystemExit(
            f"managed starter-site process {record.pid} exists for {url} but is not healthy; run stop first or inspect the logs"
        )
    if state == "running-with-stale-record" and record:
        raise SystemExit(
            f"stale starter-site record points at pid {record.pid}, but another process is serving {url}; remove the record or use another port"
        )
    if state == "stopped-with-stale-record":
        remove_record(host, port)

    TMP_ROOT.mkdir(parents=True, exist_ok=True)
    stdout_path = stdout_log_path(host, port)
    stderr_path = stderr_log_path(host, port)
    command = [
        sys.executable,
        str(ROOT / "scripts" / "starter_site.py"),
        "--host",
        host,
        "--port",
        str(port),
    ]
    creationflags = 0
    start_new_session = False
    if os.name == "nt":
        creationflags = subprocess.CREATE_NEW_PROCESS_GROUP | subprocess.DETACHED_PROCESS
    else:
        start_new_session = True

    with stdout_path.open("ab") as stdout_handle, stderr_path.open("ab") as stderr_handle:
        process = subprocess.Popen(
            command,
            cwd=ROOT,
            stdin=subprocess.DEVNULL,
            stdout=stdout_handle,
            stderr=stderr_handle,
            creationflags=creationflags,
            start_new_session=start_new_session,
        )

    deadline = time.time() + 20
    while time.time() < deadline:
        if process.poll() is not None:
            raise SystemExit(
                f"starter-site exited before becoming healthy; inspect {stderr_path}"
            )
        if is_healthy(host, port):
            record = SiteRecord(
                host=host,
                port=port,
                pid=process.pid,
                stdout_log=str(stdout_path),
                stderr_log=str(stderr_path),
                started_at=time.time(),
            )
            save_record(record)
            print(f"starter-site started at {url} (pid {process.pid})")
            return 0
        time.sleep(0.25)

    try:
        terminate_pid(process.pid)
    except ProcessLookupError:
        pass
    raise SystemExit(f"starter-site did not become healthy at {url}; inspect {stderr_path}")


def command_stop(host: str, port: int) -> int:
    state, record, healthy, _ = describe_state(host, port)
    url = health_url(host, port).removesuffix("/healthz")
    if state == "stopped":
        print(f"starter-site is not running at {url}")
        return 0
    if state == "running-unmanaged":
        raise SystemExit(
            f"starter-site is responding at {url} without a managed pid record; stop it manually"
        )
    if state == "stopped-with-stale-record":
        remove_record(host, port)
        print(f"removed stale starter-site record for {url}")
        return 0
    if record is None:
        raise SystemExit(f"missing starter-site record for {url}")

    if is_pid_running(record.pid):
        terminate_pid(record.pid)
        if not wait_for_shutdown(host, port, record.pid, timeout=10):
            kill_pid(record.pid)
            if not wait_for_shutdown(host, port, record.pid, timeout=5):
                raise SystemExit(
                    f"failed to stop starter-site process {record.pid}; inspect {record.stderr_log}"
                )
    elif healthy:
        raise SystemExit(
            f"starter-site record for {url} is stale and another process is still responding"
        )

    remove_record(host, port)
    print(f"starter-site stopped at {url}")
    return 0


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=["start", "stop", "status"])
    parser.add_argument("--host", default=DEFAULT_HOST)
    parser.add_argument("--port", type=int, default=DEFAULT_PORT)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.command == "start":
        return command_start(args.host, args.port)
    if args.command == "stop":
        return command_stop(args.host, args.port)
    return command_status(args.host, args.port)


if __name__ == "__main__":
    raise SystemExit(main())
