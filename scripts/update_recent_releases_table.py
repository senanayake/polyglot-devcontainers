#!/usr/bin/env python3
"""Update the recent releases table in README.md from GitHub Releases."""

from __future__ import annotations

import argparse
import json
import os
import urllib.request
from datetime import datetime
from pathlib import Path
from typing import Any


START_MARKER = "<!-- recent-releases:start -->"
END_MARKER = "<!-- recent-releases:end -->"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", required=True, help="owner/name")
    parser.add_argument("--readme", type=Path, default=Path("README.md"))
    parser.add_argument("--limit", type=int, default=5)
    return parser.parse_args()


def github_request(url: str) -> Any:
    headers = {"User-Agent": "polyglot-devcontainers"}
    token = os.environ.get("GITHUB_TOKEN")
    if token:
        headers["Authorization"] = f"Bearer {token}"
    request = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(request, timeout=30) as response:
        return json.load(response)


def load_releases(repo: str, limit: int) -> list[dict[str, Any]]:
    payload = github_request(
        f"https://api.github.com/repos/{repo}/releases?per_page={limit}"
    )
    if not isinstance(payload, list):
        raise SystemExit("expected GitHub releases API to return a list")
    releases = []
    for release in payload:
        if release.get("draft") or release.get("prerelease"):
            continue
        releases.append(release)
        if len(releases) >= limit:
            break
    return releases


def format_date(raw: str | None) -> str:
    if not raw:
        return "unknown"
    parsed = datetime.fromisoformat(raw.replace("Z", "+00:00"))
    return parsed.strftime("%Y-%m-%d")


def build_section(repo: str, releases: list[dict[str, Any]]) -> str:
    lines = [
        START_MARKER,
        "## Recent Releases",
        "",
        "Recent published release notes are available here:",
        "",
    ]

    if releases:
        lines.extend(
            [
                "| Version | Date | Release Notes |",
                "| --- | --- | --- |",
            ]
        )
        for release in releases:
            tag_name = release.get("tag_name", "unknown")
            title = release.get("name") or tag_name
            html_url = release.get("html_url") or f"https://github.com/{repo}/releases"
            date = format_date(release.get("published_at"))
            lines.append(f"| `{tag_name}` | {date} | [{title}]({html_url}) |")
    else:
        lines.append(
            f"No GitHub Releases published yet. See [tags](https://github.com/{repo}/tags) until the first release notes are published."
        )

    lines.extend(["", END_MARKER])
    return "\n".join(lines)


def replace_section(readme_text: str, section_text: str) -> str:
    start = readme_text.find(START_MARKER)
    end = readme_text.find(END_MARKER)
    if start == -1 or end == -1 or end < start:
        raise SystemExit("README.md is missing recent release markers")
    end += len(END_MARKER)
    return readme_text[:start] + section_text + readme_text[end:]


def main() -> int:
    args = parse_args()
    releases = load_releases(args.repo, args.limit)
    readme_text = args.readme.read_text(encoding="utf-8")
    section_text = build_section(args.repo, releases)
    updated_text = replace_section(readme_text, section_text)
    args.readme.write_text(updated_text, encoding="utf-8")
    print(
        f"[recent-releases] repo={args.repo} count={len(releases)} readme={args.readme}",
        flush=True,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
