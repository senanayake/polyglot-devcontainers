#!/usr/bin/env python3
"""Validate that a built image embeds expected devcontainer metadata."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

from oci_runtime import preferred_runtime


STORABLE_KEYS = {
    "forwardPorts",
    "portsAttributes",
    "otherPortsAttributes",
    "containerEnv",
    "remoteEnv",
    "remoteUser",
    "containerUser",
    "updateRemoteUserUID",
    "userEnvProbe",
    "overrideCommand",
    "shutdownAction",
    "init",
    "privileged",
    "capAdd",
    "securityOpt",
    "mounts",
    "customizations",
    "onCreateCommand",
    "updateContentCommand",
    "postCreateCommand",
    "postStartCommand",
    "postAttachCommand",
    "waitFor",
    "workspaceFolder",
}


def deep_merge(base: dict[str, Any], overlay: dict[str, Any]) -> dict[str, Any]:
    merged = dict(base)
    for key, value in overlay.items():
        if isinstance(value, dict) and isinstance(merged.get(key), dict):
            merged[key] = deep_merge(merged[key], value)
        else:
            merged[key] = value
    return merged


def expected_metadata(devcontainer_path: Path) -> dict[str, Any]:
    data = json.loads(devcontainer_path.read_text(encoding="utf-8"))
    return {key: value for key, value in data.items() if key in STORABLE_KEYS}


def inspect_image_labels(image: str) -> dict[str, str]:
    runtime = preferred_runtime()
    result = subprocess.run(
        [
            runtime,
            "image",
            "inspect",
            image,
            "--format",
            "{{json .Config.Labels}}",
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    return json.loads(result.stdout)


def actual_metadata(labels: dict[str, str]) -> dict[str, Any]:
    raw = labels.get("devcontainer.metadata")
    if not raw:
        raise ValueError("image is missing the devcontainer.metadata label")

    snippets = json.loads(raw)
    if not isinstance(snippets, list):
        raise ValueError("devcontainer.metadata must contain a JSON array")

    merged: dict[str, Any] = {}
    for snippet in snippets:
        if not isinstance(snippet, dict):
            raise ValueError("each devcontainer.metadata entry must be an object")
        merged = deep_merge(merged, snippet)
    return merged


def subset_mismatches(expected: Any, actual: Any, path: str = "") -> list[str]:
    if isinstance(expected, dict):
        if not isinstance(actual, dict):
            return [f"{path or '<root>'}: expected object, found {type(actual).__name__}"]
        mismatches: list[str] = []
        for key, value in expected.items():
            child_path = f"{path}.{key}" if path else key
            if key not in actual:
                mismatches.append(f"{child_path}: missing from image metadata")
                continue
            mismatches.extend(subset_mismatches(value, actual[key], child_path))
        return mismatches

    if expected != actual:
        return [f"{path}: expected {expected!r}, found {actual!r}"]

    return []


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--image", required=True, help="Built image reference to inspect.")
    parser.add_argument(
        "--devcontainer-json",
        required=True,
        help="Path to the source devcontainer.json file.",
    )
    args = parser.parse_args()

    devcontainer_path = Path(args.devcontainer_json)
    expected = expected_metadata(devcontainer_path)
    labels = inspect_image_labels(args.image)
    actual = actual_metadata(labels)
    mismatches = subset_mismatches(expected, actual)

    if mismatches:
        print(f"Metadata validation failed for {args.image}", file=sys.stderr)
        for mismatch in mismatches:
            print(f"- {mismatch}", file=sys.stderr)
        return 1

    print(f"Metadata validation passed for {args.image}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
