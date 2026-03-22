#!/usr/bin/env python3
"""Fail fast when repo workflows run outside the maintainer container."""

from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
from pathlib import Path


ROLE_ENV = "POLYGLOT_CONTAINER_ROLE"
EXPECTED_ROLE = "maintainer"


def in_container() -> bool:
    return Path("/.dockerenv").exists() or Path("/run/.containerenv").exists()


def docker_available() -> tuple[bool, str]:
    if shutil.which("docker") is None:
        return False, "docker CLI is not installed in the maintainer container"
    try:
        subprocess.run(
            ["docker", "info"],
            check=True,
            capture_output=True,
            text=True,
            timeout=20,
        )
    except subprocess.TimeoutExpired:
        return False, "docker info timed out inside the maintainer container"
    except subprocess.CalledProcessError:
        return False, "docker daemon is not reachable inside the maintainer container"
    return True, ""


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--require-docker", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    errors: list[str] = []

    if not in_container():
        errors.append("this workflow must run inside the maintainer container, not on the host")

    role = os.environ.get(ROLE_ENV)
    if role != EXPECTED_ROLE:
        errors.append(
            f"{ROLE_ENV} must be set to '{EXPECTED_ROLE}' inside the maintainer container"
        )

    if args.require_docker:
        ok, message = docker_available()
        if not ok:
            errors.append(message)

    if errors:
        for error in errors:
            print(f"[maintainer-runtime] {error}", file=sys.stderr)
        return 1

    requirement = "maintainer+docker" if args.require_docker else "maintainer"
    print(f"[maintainer-runtime] ok requirement={requirement}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
