#!/usr/bin/env python3
"""Build release-level security summary assets from image scan summaries."""

from __future__ import annotations

import argparse
import json
import re
import tomllib
from pathlib import Path
from typing import Any


START_MARKER = "<!-- release-security:start -->"
END_MARKER = "<!-- release-security:end -->"
IMAGE_REF_PATTERN = re.compile(r"^ghcr\.io/(?P<owner>[^/]+)/(?P<package>[^@:]+)(?:[:@].+)?$")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", required=True, help="GitHub repository in owner/name form")
    parser.add_argument("--tag", required=True, help="Release tag")
    parser.add_argument(
        "--docs-base-url",
        required=True,
        help="Browser-viewable base URL for published release docs",
    )
    parser.add_argument(
        "--image-catalog",
        type=Path,
        required=True,
        help="TOML catalog that maps published images to related repo entry points",
    )
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


def load_image_catalog(path: Path, repo: str, ref: str) -> dict[str, dict[str, list[dict[str, str]]]]:
    payload = tomllib.loads(path.read_text(encoding="utf-8"))
    if payload.get("catalog_version") != 1:
        raise SystemExit(f"unsupported catalog_version in {path}: {payload.get('catalog_version')!r}")

    images = payload.get("images")
    if not isinstance(images, dict):
        raise SystemExit(f"expected [images] table in {path}")

    catalog: dict[str, dict[str, list[dict[str, str]]]] = {}
    for package_name, entry in images.items():
        if not isinstance(entry, dict):
            raise SystemExit(f"catalog entry for {package_name!r} must be a table")

        catalog[str(package_name)] = {
            "docs": parse_catalog_links(entry.get("docs", []), path=path, repo=repo, ref=ref),
            "examples": parse_catalog_links(entry.get("examples", []), path=path, repo=repo, ref=ref),
            "templates": parse_catalog_links(entry.get("templates", []), path=path, repo=repo, ref=ref),
        }

    return catalog


def parse_catalog_links(
    raw_links: Any,
    *,
    path: Path,
    repo: str,
    ref: str,
) -> list[dict[str, str]]:
    if not isinstance(raw_links, list):
        raise SystemExit(f"catalog field in {path} must be a list")

    parsed: list[dict[str, str]] = []
    for item in raw_links:
        if not isinstance(item, dict):
            raise SystemExit(f"catalog link entry in {path} must be an inline table")

        label = item.get("label")
        target_path = item.get("path")
        if not isinstance(label, str) or not label:
            raise SystemExit(f"catalog link entry in {path} is missing a string label")
        if not isinstance(target_path, str) or not target_path:
            raise SystemExit(f"catalog link entry in {path} is missing a string path")
        if not Path(target_path).exists():
            raise SystemExit(f"catalog path does not exist in checkout {ref}: {target_path}")

        parsed.append(
            {
                "label": label,
                "path": target_path,
                "url": repo_blob_url(repo, ref, target_path),
            }
        )

    return parsed


def docs_asset_url(docs_base_url: str, asset_name: str) -> str:
    return f"{docs_base_url.rstrip('/')}/{asset_name}"


def repo_blob_url(repo: str, ref: str, path: str) -> str:
    normalized = path.strip().replace("\\", "/")
    return f"https://github.com/{repo}/blob/{ref}/{normalized}"


def summary_asset_name(image_name: str, suffix: str) -> str:
    return f"release-security-{image_name}-{suffix}"


def package_page_url(repo: str, package_name: str) -> str:
    return f"https://github.com/{repo}/pkgs/container/{package_name}"


def parse_package_details(summary: dict[str, Any]) -> tuple[str, str]:
    image_ref = str(summary.get("image_ref", ""))
    match = IMAGE_REF_PATTERN.fullmatch(image_ref)
    if match is None:
        raise SystemExit(f"unsupported image_ref format in summary: {image_ref!r}")
    return match.group("owner"), match.group("package")


def release_pull_ref(summary: dict[str, Any], tag: str) -> str:
    owner, package_name = parse_package_details(summary)
    return f"ghcr.io/{owner}/{package_name}:{tag}"


def format_catalog_links(links: list[dict[str, str]]) -> str:
    if not links:
        return "—"
    return ", ".join(f"[{item['label']}]({item['url']})" for item in links)


def build_published_images_section(
    repo: str,
    tag: str,
    summary_map: list[tuple[str, dict[str, Any]]],
    image_catalog: dict[str, dict[str, list[dict[str, str]]]],
) -> list[str]:
    lines = [
        "## Published Images",
        "",
        "The links below point to the released package and the matching repo entry points for this tag.",
        "",
    ]

    for _, summary in summary_map:
        _, package_name = parse_package_details(summary)
        catalog_entry = image_catalog.get(package_name)
        if catalog_entry is None:
            raise SystemExit(f"published image missing from catalog: {package_name}")

        lines.extend(
            [
                f"### `{package_name}`",
                "",
                f"- Package page: [View package]({package_page_url(repo, package_name)})",
                f"- Pull: `docker pull {release_pull_ref(summary, tag)}`",
                f"- Starter templates: {format_catalog_links(catalog_entry['templates'])}",
                f"- Examples: {format_catalog_links(catalog_entry['examples'])}",
            ]
        )
        if catalog_entry["docs"]:
            lines.append(f"- Related docs: {format_catalog_links(catalog_entry['docs'])}")
        lines.append("")
    return lines


def build_fragment(
    repo: str,
    tag: str,
    docs_base_url: str,
    summary_map: list[tuple[str, dict[str, Any]]],
    image_catalog: dict[str, dict[str, list[dict[str, str]]]],
    residual_risk_markdown: Path,
) -> list[str]:
    total_critical = sum(int(summary["critical"]) for _, summary in summary_map)
    total_high = sum(int(summary["high"]) for _, summary in summary_map)
    total_findings = sum(int(summary["total"]) for _, summary in summary_map)
    residual_asset = "release-security-residual-risk.md"
    overview_asset = "release-security-overview.md"

    lines = [
        *build_published_images_section(repo, tag, summary_map, image_catalog),
        "",
        "## Security Status",
        "",
        f"- Published image scans for `{tag}` reported `{total_critical}` critical, `{total_high}` high, and `{total_findings}` total HIGH/CRITICAL findings.",
        f"- Release security overview: [{overview_asset}]({docs_asset_url(docs_base_url, overview_asset)})",
        f"- Residual critical-risk report: [{residual_asset}]({docs_asset_url(docs_base_url, residual_asset)})",
        "",
        "| Image | Critical | High | Total | Summary | Machine-readable | SBOM |",
        "| --- | ---: | ---: | ---: | --- | --- | --- |",
    ]

    for image_name, summary in summary_map:
        summary_md = summary_asset_name(image_name, "summary.md")
        summary_json = summary_asset_name(image_name, "summary.json")
        sbom_json = summary_asset_name(image_name, "sbom.spdx.json")
        _, package_name = parse_package_details(summary)
        lines.append(
            "| `{image}` | {critical} | {high} | {total} | [{summary_md}]({summary_md_url}) | [{summary_json}]({summary_json_url}) | [{sbom_json}]({sbom_url}) |".format(
                image=package_name,
                critical=summary["critical"],
                high=summary["high"],
                total=summary["total"],
                summary_md=summary_md,
                summary_md_url=docs_asset_url(docs_base_url, summary_md),
                summary_json=summary_json,
                summary_json_url=docs_asset_url(docs_base_url, summary_json),
                sbom_json=sbom_json,
                sbom_url=docs_asset_url(docs_base_url, sbom_json),
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
            f"Browser-viewable copies live in `docs/releases/{tag}/`. Downloadable copies remain attached to the GitHub Release.",
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
    image_catalog = load_image_catalog(args.image_catalog, repo=args.repo, ref=args.tag)

    fragment_lines = build_fragment(
        repo=args.repo,
        tag=args.tag,
        docs_base_url=args.docs_base_url,
        summary_map=summary_map,
        image_catalog=image_catalog,
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
