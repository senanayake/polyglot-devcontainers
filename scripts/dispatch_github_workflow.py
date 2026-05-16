#!/usr/bin/env python3
"""Dispatch a GitHub Actions workflow using the REST API."""

from __future__ import annotations

import argparse
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import quote
from urllib.request import Request, urlopen


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--api-url", required=True)
    parser.add_argument("--repo", required=True, help="owner/name")
    parser.add_argument("--workflow", required=True, help="Workflow file name or id")
    parser.add_argument("--ref", required=True, help="Git ref to run the workflow on")
    parser.add_argument(
        "--input",
        action="append",
        default=[],
        metavar="KEY=VALUE",
        help="Workflow input value",
    )
    parser.add_argument(
        "--github-output",
        type=Path,
        help="Optional GitHub Actions output file path",
    )
    parser.add_argument(
        "--token-env",
        default="GH_TOKEN",
        help="Environment variable that contains the GitHub token",
    )
    return parser.parse_args()


def parse_inputs(raw_values: list[str]) -> dict[str, str]:
    parsed: dict[str, str] = {}
    for raw in raw_values:
        key, separator, value = raw.partition("=")
        if not separator or not key:
            raise SystemExit(f"invalid --input value: {raw!r}; expected KEY=VALUE")
        parsed[key] = value
    return parsed


def write_github_outputs(path: Path, values: dict[str, str]) -> None:
    with path.open("a", encoding="utf-8") as handle:
        for key, value in values.items():
            handle.write(f"{key}={value}\n")


def main() -> int:
    args = parse_args()
    token = os.environ.get(args.token_env)
    if not token:
        raise SystemExit(f"missing token environment variable: {args.token_env}")

    requested_at = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    if requested_at.endswith("+00:00"):
        requested_at = requested_at.removesuffix("+00:00") + "Z"

    payload = json.dumps(
        {
            "ref": args.ref,
            "inputs": parse_inputs(args.input),
        }
    ).encode("utf-8")

    workflow = quote(args.workflow, safe="")
    request = Request(
        f"{args.api_url}/repos/{args.repo}/actions/workflows/{workflow}/dispatches",
        data=payload,
        method="POST",
        headers={
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "User-Agent": "polyglot-devcontainers-workflow-dispatch",
        },
    )

    with urlopen(request) as response:
        if response.status not in (201, 204):
            raise SystemExit(f"Unexpected workflow dispatch status: {response.status}")

    outputs = {
        "requested_at": requested_at,
    }
    if args.github_output:
        write_github_outputs(args.github_output, outputs)

    print(
        json.dumps(
            {
                "inputs": parse_inputs(args.input),
                "ref": args.ref,
                "repo": args.repo,
                "requested_at": requested_at,
                "workflow": args.workflow,
            },
            indent=2,
        ),
        flush=True,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
