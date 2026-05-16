#!/usr/bin/env python3
"""Resolve the next semantic release tag from the local Git tag set."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
from pathlib import Path


TAG_PATTERN = re.compile(r"^v(?P<major>\d+)\.(?P<minor>\d+)\.(?P<patch>\d+)$")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--increment",
        required=True,
        choices=("patch", "minor", "major"),
        help="Semantic version component to increment",
    )
    parser.add_argument(
        "--github-output",
        type=Path,
        help="Optional GitHub Actions output file path",
    )
    return parser.parse_args()


def git_output(*args: str) -> str:
    result = subprocess.run(
        ["git", *args],
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout.strip()


def latest_release_tag() -> str:
    tags = git_output("tag", "--list", "v*.*.*", "--sort=-version:refname").splitlines()
    return tags[0] if tags else ""


def compute_next_tag(previous_tag: str, increment: str) -> str:
    if previous_tag:
        match = TAG_PATTERN.fullmatch(previous_tag)
        if match is None:
            raise SystemExit(
                f"Latest tag does not match vMAJOR.MINOR.PATCH: {previous_tag}"
            )
        major = int(match.group("major"))
        minor = int(match.group("minor"))
        patch = int(match.group("patch"))
    else:
        major = 0
        minor = 0
        patch = 0

    if increment == "patch":
        next_major = major
        next_minor = minor
        next_patch = patch + 1
    elif increment == "minor":
        next_major = major
        next_minor = minor + 1
        next_patch = 0
    else:
        next_major = major + 1
        next_minor = 0
        next_patch = 0

    return f"v{next_major}.{next_minor}.{next_patch}"


def write_github_outputs(path: Path, values: dict[str, str]) -> None:
    with path.open("a", encoding="utf-8") as handle:
        for key, value in values.items():
            handle.write(f"{key}={value}\n")


def main() -> int:
    args = parse_args()
    previous_tag = latest_release_tag()
    next_tag = compute_next_tag(previous_tag, args.increment)

    payload = {
        "increment": args.increment,
        "next_tag": next_tag,
        "previous_tag": previous_tag,
    }

    if args.github_output:
        write_github_outputs(args.github_output, payload)

    print(json.dumps(payload, indent=2), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
