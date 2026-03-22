#!/usr/bin/env python3
"""Build release-level security summary assets from image scan summaries."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


START_MARKER = "<!-- release-security:start -->"
END_MARKER = "<!-- release-security:end -->"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", required=True, help="GitHub repository in owner/name form")
    parser.add_argument("--tag", required=True, help="Release tag")
    parser.add_argument(
        "--summary",
        action="append",
        required=True,
        metavar="IMAGE=PATH",
        help="Image name and summary JSON path",
    )
    parser.add_argument(
        "--residual-risk-markdown",
        type=Path,
        required=True,
        help="Residual-risk Markdown report path",
    )
    parser.add_argument(
        "--overview-output",
        type=Path,
        required=True,
        help="Markdown overview asset output path",
    )
    parser.add_argument(
        "--notes-fragment-output",
        type=Path,
        required=True,
        help="Markdown release-notes fragment output path",
    )
    parser.add_argument(
        "--existing-notes",
        type=Path,
        help="Existing release notes Markdown path",
    )
    parser.add_argument(
        "--release-notes-output",
        type=Path,
        help="Updated release notes Markdown path",
    )
    return parser.parse_args()


def parse_summary_arg(raw: str) -> tuple[str, Path]:
    image_name, separator, path_text = raw.partition("=")
    if not separator or not image_name or not path_text:
        raise SystemExit(f"invalid --summary value: {raw!r}; expected IMAGE=PATH")
    return image_name, Path(path_text)


def load_summary(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise SystemExit(f"expected a JSON object in {path}")
    return payload


def asset_url(repo: str, tag: str, asset_name: str) -> str:
    return f"https://github.com/{repo}/releases/download/{tag}/{asset_name}"


def summary_asset_name(image_name: str, suffix: str) -> str:
    return f"release-security-{image_name}-{suffix}"


def build_fragment(
    repo: str,
    tag: str,
    summary_map: list[tuple[str, dict[str, Any]]],
    residual_risk_markdown: Path,
) -> list[str]:
    total_critical = sum(int(summary["critical"]) for _, summary in summary_map)
    total_high = sum(int(summary["high"]) for _, summary in summary_map)
    total_findings = sum(int(summary["total"]) for _, summary in summary_map)
    residual_asset = "release-security-residual-risk.md"
    overview_asset = "release-security-overview.md"

    lines = [
        "## Security Status",
        "",
        f"- Published image scans for `{tag}` reported `{total_critical}` critical, `{total_high}` high, and `{total_findings}` total HIGH/CRITICAL findings.",
        f"- Release security overview: [{overview_asset}]({asset_url(repo, tag, overview_asset)})",
        f"- Residual critical-risk report: [{residual_asset}]({asset_url(repo, tag, residual_asset)})",
        "",
        "| Image | Critical | High | Total | Summary | Machine-readable | SBOM |",
        "| --- | ---: | ---: | ---: | --- | --- | --- |",
    ]

    for image_name, summary in summary_map:
        summary_md = summary_asset_name(image_name, "summary.md")
        summary_json = summary_asset_name(image_name, "summary.json")
        sbom_json = summary_asset_name(image_name, "sbom.spdx.json")
        lines.append(
            "| `{image}` | {critical} | {high} | {total} | [{summary_md}]({summary_md_url}) | [{summary_json}]({summary_json_url}) | [{sbom_json}]({sbom_url}) |".format(
                image=image_name,
                critical=summary["critical"],
                high=summary["high"],
                total=summary["total"],
                summary_md=summary_md,
                summary_md_url=asset_url(repo, tag, summary_md),
                summary_json=summary_json,
                summary_json_url=asset_url(repo, tag, summary_json),
                sbom_json=sbom_json,
                sbom_url=asset_url(repo, tag, sbom_json),
            )
        )

    residual_text = residual_risk_markdown.read_text(encoding="utf-8")
    critical_line = next(
        (line for line in residual_text.splitlines() if line.startswith("- critical findings:")),
        "- critical findings: `unknown`",
    )

    lines.extend(
        [
            "",
            f"Residual-risk summary: {critical_line.removeprefix('- ')}",
            "",
            "These assets are generated from the release workflow's Trivy scans and are the supported entry point for release security status.",
        ]
    )
    return lines


def build_overview(
    repo: str,
    tag: str,
    fragment_lines: list[str],
) -> list[str]:
    return [
        f"# Release Security Overview: {tag}",
        "",
        f"- release: `{tag}`",
        f"- repository: `{repo}`",
        "",
        *fragment_lines,
        "",
    ]


def replace_security_block(notes_text: str, fragment_text: str) -> str:
    block = "\n".join([START_MARKER, fragment_text.rstrip(), END_MARKER]).rstrip()
    start = notes_text.find(START_MARKER)
    end = notes_text.find(END_MARKER)
    if start != -1 and end != -1 and end >= start:
        end += len(END_MARKER)
        updated = notes_text[:start] + block + notes_text[end:]
    else:
        updated = notes_text.rstrip() + "\n\n" + block + "\n"
    return updated


def main() -> int:
    args = parse_args()
    summary_map = []
    for image_name, path in sorted((parse_summary_arg(raw) for raw in args.summary), key=lambda item: item[0]):
        summary_map.append((image_name, load_summary(path)))

    fragment_lines = build_fragment(
        repo=args.repo,
        tag=args.tag,
        summary_map=summary_map,
        residual_risk_markdown=args.residual_risk_markdown,
    )
    fragment_text = "\n".join(fragment_lines).rstrip() + "\n"
    overview_text = "\n".join(build_overview(args.repo, args.tag, fragment_lines))

    args.notes_fragment_output.parent.mkdir(parents=True, exist_ok=True)
    args.overview_output.parent.mkdir(parents=True, exist_ok=True)
    args.notes_fragment_output.write_text(fragment_text, encoding="utf-8")
    args.overview_output.write_text(overview_text, encoding="utf-8")

    if bool(args.existing_notes) != bool(args.release_notes_output):
        raise SystemExit("existing-notes and release-notes-output must be passed together")

    if args.existing_notes and args.release_notes_output:
        notes_text = args.existing_notes.read_text(encoding="utf-8")
        updated_notes = replace_security_block(notes_text, fragment_text)
        args.release_notes_output.parent.mkdir(parents=True, exist_ok=True)
        args.release_notes_output.write_text(updated_notes, encoding="utf-8")

    print(
        "[release-security] "
        f"repo={args.repo} tag={args.tag} images={len(summary_map)} "
        f"overview={args.overview_output} fragment={args.notes_fragment_output}",
        flush=True,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
