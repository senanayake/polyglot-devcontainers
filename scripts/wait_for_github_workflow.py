#!/usr/bin/env python3
"""Wait for a GitHub Actions workflow run to start and complete."""

from __future__ import annotations

import argparse
import json
import os
import time
from pathlib import Path
from urllib.parse import quote, urlencode
from urllib.request import Request, urlopen


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--api-url", required=True)
    parser.add_argument("--repo", required=True, help="owner/name")
    parser.add_argument("--workflow", required=True, help="Workflow file name or id")
    parser.add_argument("--head-branch", required=True)
    parser.add_argument("--head-sha", required=True)
    parser.add_argument("--requested-after", required=True)
    parser.add_argument("--server-url", required=True)
    parser.add_argument(
        "--event",
        default="workflow_dispatch",
        help="Workflow event name to filter on",
    )
    parser.add_argument(
        "--poll-interval-seconds",
        type=int,
        default=5,
        help="Polling interval in seconds",
    )
    parser.add_argument(
        "--timeout-seconds",
        type=int,
        default=300,
        help="Maximum time to wait for the workflow run",
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


def get_json(url: str, token: str) -> dict:
    request = Request(
        url,
        headers={
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {token}",
            "User-Agent": "polyglot-devcontainers-workflow-wait",
        },
    )
    with urlopen(request) as response:
        return json.load(response)


def write_github_outputs(path: Path, values: dict[str, str]) -> None:
    with path.open("a", encoding="utf-8") as handle:
        for key, value in values.items():
            handle.write(f"{key}={value}\n")


def main() -> int:
    args = parse_args()
    token = os.environ.get(args.token_env)
    if not token:
        raise SystemExit(f"missing token environment variable: {args.token_env}")

    workflow = quote(args.workflow, safe="")
    query = urlencode({"event": args.event, "per_page": 20})
    runs_url = f"{args.api_url}/repos/{args.repo}/actions/workflows/{workflow}/runs?{query}"

    deadline = time.monotonic() + args.timeout_seconds
    run: dict | None = None
    while time.monotonic() < deadline:
        data = get_json(runs_url, token)
        candidates = [
            item
            for item in data.get("workflow_runs", [])
            if item.get("head_branch") == args.head_branch
            and item.get("head_sha") == args.head_sha
            and item.get("created_at", "") >= args.requested_after
        ]
        if candidates:
            candidates.sort(key=lambda item: item["created_at"])
            run = candidates[0]
            break
        time.sleep(args.poll_interval_seconds)

    if run is None:
        raise SystemExit("Timed out waiting for workflow run to start")

    run_id = str(run["id"])
    run_url = str(run["html_url"])

    while time.monotonic() < deadline:
        current = get_json(f"{args.api_url}/repos/{args.repo}/actions/runs/{run_id}", token)
        status = str(current.get("status"))
        conclusion = str(current.get("conclusion"))
        print(
            f"workflow={args.workflow} run_id={run_id} status={status} conclusion={conclusion}",
            flush=True,
        )
        if status == "completed":
            outputs = {
                "conclusion": conclusion,
                "run_id": run_id,
                "run_url": run_url,
                "status": status,
            }
            if args.github_output:
                write_github_outputs(args.github_output, outputs)
            if conclusion != "success":
                raise SystemExit(
                    f"{args.workflow} failed: {args.server_url}/{args.repo}/actions/runs/{run_id}"
                )
            print(json.dumps(outputs, indent=2), flush=True)
            return 0
        time.sleep(max(args.poll_interval_seconds, 10))

    raise SystemExit(
        f"Timed out waiting for {args.workflow} to complete: {args.server_url}/{args.repo}/actions/runs/{run_id}"
    )


if __name__ == "__main__":
    raise SystemExit(main())
