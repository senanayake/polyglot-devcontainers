#!/usr/bin/env python3
"""Discover and optionally pin published-image base references."""

from __future__ import annotations

import argparse
import json
import re
import sys
import urllib.error
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parent.parent
PUBLISHED_DOCKERFILES = [
    ROOT / ".devcontainer" / "Containerfile",
    ROOT / "templates" / "java-secure" / ".devcontainer" / "Containerfile",
    ROOT / "templates" / "diagram-secure" / ".devcontainer" / "Containerfile",
    ROOT / "templates" / "python-node-secure" / ".devcontainer" / "Containerfile",
]
MANIFEST_ACCEPT = ", ".join(
    [
        "application/vnd.oci.image.index.v1+json",
        "application/vnd.docker.distribution.manifest.list.v2+json",
        "application/vnd.oci.image.manifest.v1+json",
        "application/vnd.docker.distribution.manifest.v2+json",
    ]
)
FROM_PATTERN = re.compile(
    r"^(?P<indent>\s*)FROM\s+(?P<image>\S+)(?:\s+AS\s+(?P<alias>\S+))?\s*$",
    re.IGNORECASE,
)


@dataclass(frozen=True)
class ImageReference:
    registry: str
    repository: str
    tag: str
    digest: str | None

    @property
    def image_without_digest(self) -> str:
        return f"{self.registry}/{self.repository}:{self.tag}"

    @property
    def image_with_digest(self) -> str:
        if self.digest is None:
            raise ValueError("digest is required")
        return f"{self.image_without_digest}@{self.digest}"


def parse_image_reference(reference: str) -> ImageReference:
    image_no_digest, _, digest = reference.partition("@")
    registry, repository = split_registry_and_repository(image_no_digest)
    repository, tag = split_repository_and_tag(repository)
    return ImageReference(
        registry=registry,
        repository=repository,
        tag=tag,
        digest=digest or None,
    )


def split_registry_and_repository(reference: str) -> tuple[str, str]:
    first, _, rest = reference.partition("/")
    if not rest:
        return "docker.io", reference
    if "." in first or ":" in first or first == "localhost":
        return first, rest
    return "docker.io", reference


def split_repository_and_tag(reference: str) -> tuple[str, str]:
    last_slash = reference.rfind("/")
    last_colon = reference.rfind(":")
    if last_colon > last_slash:
        return reference[:last_colon], reference[last_colon + 1 :]
    return reference, "latest"


def resolve_digest(reference: ImageReference) -> str:
    url = f"https://{reference.registry}/v2/{reference.repository}/manifests/{reference.tag}"
    request = urllib.request.Request(
        url,
        method="HEAD",
        headers={"Accept": MANIFEST_ACCEPT, "User-Agent": "polyglot-devcontainers"},
    )
    try:
        with urllib.request.urlopen(request) as response:
            digest = response.headers.get("Docker-Content-Digest")
    except urllib.error.HTTPError as exc:
        raise SystemExit(
            f"failed to resolve digest for {reference.image_without_digest}: "
            f"{exc.code} {exc.reason}"
        ) from exc
    if not digest:
        raise SystemExit(f"registry did not return a digest for {reference.image_without_digest}")
    return digest


def discover_entries(dockerfiles: list[Path]) -> list[dict[str, Any]]:
    entries: list[dict[str, Any]] = []
    for dockerfile in dockerfiles:
        lines = dockerfile.read_text(encoding="utf-8").splitlines()
        for line_number, line in enumerate(lines, start=1):
            match = FROM_PATTERN.match(line)
            if not match:
                continue
            raw_reference = match.group("image")
            alias = match.group("alias")
            reference = parse_image_reference(raw_reference)
            latest_digest = resolve_digest(reference)
            entries.append(
                {
                    "file": str(dockerfile.relative_to(ROOT)).replace("\\", "/"),
                    "absolute_file": str(dockerfile),
                    "line": line_number,
                    "alias": alias,
                    "reference": raw_reference,
                    "normalized_reference": reference.image_without_digest,
                    "registry": reference.registry,
                    "repository": reference.repository,
                    "tag": reference.tag,
                    "current_digest": reference.digest,
                    "latest_digest": latest_digest,
                    "is_pinned": reference.digest is not None,
                    "needs_update": reference.digest != latest_digest,
                }
            )
    return entries


def apply_updates(entries: list[dict[str, Any]]) -> list[str]:
    updated_files: list[str] = []
    by_file: dict[str, list[dict[str, Any]]] = {}
    for entry in entries:
        if not entry["needs_update"]:
            continue
        by_file.setdefault(entry["absolute_file"], []).append(entry)

    for absolute_file, file_entries in by_file.items():
        path = Path(absolute_file)
        lines = path.read_text(encoding="utf-8").splitlines()
        for entry in file_entries:
            index = int(entry["line"]) - 1
            match = FROM_PATTERN.match(lines[index])
            if match is None:
                raise SystemExit(f"expected a FROM line at {path}:{entry['line']}")
            new_reference = (
                f"{entry['registry']}/{entry['repository']}:{entry['tag']}@{entry['latest_digest']}"
            )
            alias = match.group("alias")
            replacement = f"{match.group('indent')}FROM {new_reference}"
            if alias:
                replacement += f" AS {alias}"
            lines[index] = replacement
        path.write_text("\n".join(lines) + "\n", encoding="utf-8")
        updated_files.append(str(path.relative_to(ROOT)).replace("\\", "/"))

    return sorted(updated_files)


def annotation(level: str, entry: dict[str, Any], message: str) -> None:
    if level == "none":
        return
    print(
        f"::{level} file={entry['file']},line={entry['line']}::{message}",
        flush=True,
    )


def build_summary(entries: list[dict[str, Any]], updated_files: list[str]) -> dict[str, Any]:
    pinned = sum(1 for entry in entries if entry["is_pinned"])
    outdated = sum(1 for entry in entries if entry["needs_update"])
    return {
        "scope": "published",
        "entry_count": len(entries),
        "pinned_count": pinned,
        "unpinned_count": len(entries) - pinned,
        "outdated_count": outdated,
        "updated_files": updated_files,
        "entries": entries,
    }


def markdown_lines(summary: dict[str, Any]) -> list[str]:
    lines = [
        "# Base Image Pin Report",
        "",
        f"- scope: `{summary['scope']}`",
        f"- entries: `{summary['entry_count']}`",
        f"- pinned: `{summary['pinned_count']}`",
        f"- unpinned: `{summary['unpinned_count']}`",
        f"- outdated: `{summary['outdated_count']}`",
    ]
    if summary["updated_files"]:
        lines.extend(["", "## Updated files", ""])
        for path in summary["updated_files"]:
            lines.append(f"- `{path}`")

    lines.extend(
        [
            "",
            "## Published image bases",
            "",
            "| File | Line | Reference | Pinned | Needs update | Latest digest |",
            "| --- | ---: | --- | --- | --- | --- |",
        ]
    )
    for entry in summary["entries"]:
        lines.append(
            "| `{file}` | {line} | `{reference}` | `{pinned}` | `{needs}` | `{digest}` |".format(
                file=entry["file"],
                line=entry["line"],
                reference=entry["reference"],
                pinned="yes" if entry["is_pinned"] else "no",
                needs="yes" if entry["needs_update"] else "no",
                digest=entry["latest_digest"],
            )
        )
    return lines


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def write_markdown(path: Path, lines: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--json-output", type=Path, required=True)
    parser.add_argument("--markdown-output", type=Path, required=True)
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--check-pinned", action="store_true")
    parser.add_argument(
        "--annotation-level",
        choices=("none", "warning", "error"),
        default="none",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    entries = discover_entries(PUBLISHED_DOCKERFILES)

    for entry in entries:
        if not entry["is_pinned"]:
            annotation(
                args.annotation_level,
                entry,
                f"published image base is not digest pinned: {entry['reference']}",
            )
        elif entry["needs_update"]:
            annotation(
                args.annotation_level,
                entry,
                f"published image base digest is stale; latest is {entry['latest_digest']}",
            )

    updated_files: list[str] = []
    if args.write:
        updated_files = apply_updates(entries)
        entries = discover_entries(PUBLISHED_DOCKERFILES)

    summary = build_summary(entries, updated_files)
    write_json(args.json_output, summary)
    write_markdown(args.markdown_output, markdown_lines(summary))

    print(
        "[base-image-pins] "
        f"entries={summary['entry_count']} "
        f"pinned={summary['pinned_count']} "
        f"unpinned={summary['unpinned_count']} "
        f"outdated={summary['outdated_count']} "
        f"json={args.json_output} markdown={args.markdown_output}",
        flush=True,
    )

    if args.check_pinned and summary["unpinned_count"] > 0:
        print("published image FROM lines must be digest pinned", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
