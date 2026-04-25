#!/usr/bin/env python3
"""Resolve and proxy a healthy OCI runtime, preferring Podman over Docker."""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
from typing import Sequence


PREFERRED_RUNTIME_ENV = "POLYGLOT_OCI_RUNTIME"
LEGACY_RUNTIME_ENV = "POLYGLOT_CONTAINER_RUNTIME"
DEFAULT_RUNTIMES = ("podman", "docker")


def configured_runtimes() -> list[str]:
    configured = os.environ.get(PREFERRED_RUNTIME_ENV) or os.environ.get(LEGACY_RUNTIME_ENV)
    if configured:
        return [configured]
    return list(DEFAULT_RUNTIMES)


def runtime_status(runtime: str) -> tuple[bool, str]:
    if shutil.which(runtime) is None:
        return False, f"{runtime} CLI is not installed"
    try:
        subprocess.run(
            [runtime, "info"],
            check=True,
            capture_output=True,
            text=True,
            timeout=30,
        )
    except subprocess.TimeoutExpired:
        return False, f"{runtime} info timed out"
    except subprocess.CalledProcessError:
        return False, f"{runtime} runtime is not reachable"
    return True, ""


def preferred_runtime() -> str:
    failures: list[str] = []
    for runtime in configured_runtimes():
        ok, message = runtime_status(runtime)
        if ok:
            return runtime
        failures.append(message)
    raise RuntimeError("; ".join(failures) or "no healthy OCI runtime found")


def run_with_runtime(arguments: Sequence[str]) -> int:
    runtime = preferred_runtime()
    completed = subprocess.run([runtime, *arguments], check=False)
    return completed.returncode


def main() -> int:
    if len(sys.argv) == 2 and sys.argv[1] == "--print":
        try:
            print(preferred_runtime())
        except RuntimeError as exc:
            print(f"[oci-runtime] {exc}", file=sys.stderr)
            return 1
        return 0

    if len(sys.argv) == 2 and sys.argv[1] == "--check":
        try:
            runtime = preferred_runtime()
        except RuntimeError as exc:
            print(f"[oci-runtime] {exc}", file=sys.stderr)
            return 1
        print(f"[oci-runtime] ready runtime={runtime}")
        return 0

    if len(sys.argv) < 2:
        print(
            "usage: oci_runtime.py [--print|--check|<runtime-args...>]",
            file=sys.stderr,
        )
        return 2

    try:
        return run_with_runtime(sys.argv[1:])
    except RuntimeError as exc:
        print(f"[oci-runtime] {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
