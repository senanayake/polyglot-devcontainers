#!/usr/bin/env python3
"""Validate that a built image embeds expected devcontainer metadata."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

from oci_runtime import configured_runtimes, runtime_status


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


def inspect_image_labels(image: str, runtime: str) -> dict[str, str]:
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


def candidate_runtimes(explicit_runtime: str | None) -> list[str]:
    if explicit_runtime:
        return [explicit_runtime]

    healthy_runtimes: list[str] = []
    for runtime in configured_runtimes():
        ok, _ = runtime_status(runtime)
        if ok and runtime not in healthy_runtimes:
            healthy_runtimes.append(runtime)
    return healthy_runtimes


def inspect_image_labels_with_fallback(image: str, explicit_runtime: str | None) -> dict[str, str]:
    failures: list[str] = []

    for runtime in candidate_runtimes(explicit_runtime):
        try:
            return inspect_image_labels(image, runtime)
        except subprocess.CalledProcessError as exc:
            stderr = (exc.stderr or exc.stdout or "").strip()
            if stderr:
                failures.append(f"{runtime}: {stderr}")
            else:
                failures.append(f"{runtime}: image inspect exited with status {exc.returncode}")

    failure_detail = "; ".join(failures) if failures else "no healthy OCI runtime available"
    raise RuntimeError(f"unable to inspect image {image!r}: {failure_detail}")


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
    parser.add_argument(
        "--runtime",
        help="OCI runtime that owns the built image store (for example: docker or podman).",
    )
    args = parser.parse_args()

    devcontainer_path = Path(args.devcontainer_json)
    expected = expected_metadata(devcontainer_path)
    try:
        labels = inspect_image_labels_with_fallback(args.image, args.runtime)
    except RuntimeError as exc:
        print(str(exc), file=sys.stderr)
        return 1
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
