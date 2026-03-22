#!/usr/bin/env python3
"""Pull and run the published maintainer container."""

from __future__ import annotations

import argparse
import os
import shlex
import shutil
import subprocess
import sys
from pathlib import Path


DEFAULT_IMAGE = "ghcr.io/senanayake/polyglot-devcontainers-maintainer:main"
WORKSPACE_PATH = "/workspaces/polyglot-devcontainers"
ROLE_ENV = "POLYGLOT_CONTAINER_ROLE"


def repo_root() -> Path:
    return next(parent for parent in Path(__file__).resolve().parents if (parent / "AGENTS.md").exists())


def image_ref() -> str:
    return os.environ.get("POLYGLOT_MAINTAINER_IMAGE", DEFAULT_IMAGE)


def runtime() -> str:
    configured = os.environ.get("POLYGLOT_CONTAINER_RUNTIME")
    candidates = [configured] if configured else ["docker", "podman"]

    for candidate in candidates:
        if not candidate or shutil.which(candidate) is None:
            continue
        try:
            subprocess.run(
                [candidate, "info"],
                check=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                timeout=15,
            )
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired):
            continue
        return candidate

    print(
        "[maintainer-runtime] no healthy container runtime found; tried docker and podman",
        file=sys.stderr,
    )
    raise SystemExit(1)


def container_runtime(*args: str) -> int:
    completed = subprocess.run([runtime(), *args], check=False)
    return completed.returncode


def pull() -> int:
    return container_runtime("pull", image_ref())


def shell() -> int:
    command = [
        "run",
        "--rm",
        "--interactive",
        "--tty",
        "--privileged",
        "-u",
        "root",
        "-e",
        f"{ROLE_ENV}=maintainer",
        "-v",
        f"{repo_root()}:{WORKSPACE_PATH}",
        "-w",
        WORKSPACE_PATH,
        image_ref(),
        "bash",
        "-lc",
        f"git config --global --add safe.directory {WORKSPACE_PATH} && exec bash",
    ]
    return container_runtime(*command)


def exec_command(argv: list[str]) -> int:
    if not argv:
        print("usage: run_in_maintainer_container.py exec -- <command...>", file=sys.stderr)
        return 2

    command = [
        "run",
        "--rm",
        "--privileged",
        "-u",
        "root",
        "-e",
        f"{ROLE_ENV}=maintainer",
        "-v",
        f"{repo_root()}:{WORKSPACE_PATH}",
        "-w",
        WORKSPACE_PATH,
        image_ref(),
        "bash",
        "-lc",
        f"git config --global --add safe.directory {WORKSPACE_PATH} && {' '.join(shlex.quote(arg) for arg in argv)}",
    ]
    return container_runtime(*command)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("pull")
    subparsers.add_parser("shell")

    exec_parser = subparsers.add_parser("exec")
    exec_parser.add_argument("argv", nargs=argparse.REMAINDER)

    return parser.parse_args()


def main() -> int:
    args = parse_args()

    if args.command == "pull":
        return pull()
    if args.command == "shell":
        return shell()
    if args.command == "exec":
        argv = args.argv
        if argv and argv[0] == "--":
            argv = argv[1:]
        return exec_command(argv)

    return 2


if __name__ == "__main__":
    raise SystemExit(main())
