#!/usr/bin/env python3
"""Fail fast when repo workflows run outside the maintainer container."""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

from oci_runtime import preferred_runtime


ROLE_ENV = "POLYGLOT_CONTAINER_ROLE"
EXPECTED_ROLE = "maintainer"


def in_container() -> bool:
    return Path("/.dockerenv").exists() or Path("/run/.containerenv").exists()


def oci_runtime_available() -> tuple[bool, str]:
    try:
        runtime = preferred_runtime()
    except RuntimeError as exc:
        return False, str(exc)
    return True, runtime


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--require-oci-runtime", action="store_true")
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

    require_oci_runtime = args.require_oci_runtime or args.require_docker
    runtime_name = ""
    if require_oci_runtime:
        ok, message = oci_runtime_available()
        if not ok:
            errors.append(message)
        else:
            runtime_name = message

    if errors:
        for error in errors:
            print(f"[maintainer-runtime] {error}", file=sys.stderr)
        return 1

    requirement = "maintainer+oci-runtime" if require_oci_runtime else "maintainer"
    if runtime_name:
        print(f"[maintainer-runtime] ok requirement={requirement} runtime={runtime_name}", flush=True)
    else:
        print(f"[maintainer-runtime] ok requirement={requirement}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
