#!/usr/bin/env python3
"""Generate an executive remediation summary from before/after pip-audit artifacts."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))  # type: ignore[return-value]


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def extract_vulnerabilities(audit_report: dict[str, Any]) -> list[dict[str, Any]]:
    vulns = []
    for dep in audit_report.get("dependencies", []):
        for vuln in dep.get("vulns", []):
            vulns.append(
                {
                    "package": dep["name"],
                    "version": dep["version"],
                    "id": vuln["id"],
                    "aliases": vuln.get("aliases", []),
                    "description": vuln.get("description", ""),
                    "fix_versions": vuln.get("fix_versions", []),
                }
            )
    return vulns


def build_summary(
    before_vulns: list[dict[str, Any]],
    after_vulns: list[dict[str, Any]],
    upgrades: list[dict[str, Any]],
) -> dict[str, Any]:
    before_ids = {v["id"] for v in before_vulns}
    after_ids = {v["id"] for v in after_vulns}
    resolved_ids = before_ids - after_ids
    introduced_ids = after_ids - before_ids

    resolved_vulns = sorted(
        [v for v in before_vulns if v["id"] in resolved_ids], key=lambda x: x["id"]
    )
    introduced_vulns = sorted(
        [v for v in after_vulns if v["id"] in introduced_ids], key=lambda x: x["id"]
    )
    remaining_vulns = sorted(
        [v for v in after_vulns if v["id"] not in introduced_ids], key=lambda x: x["id"]
    )

    return {
        "before": {
            "total_advisories": len(before_vulns),
            "packages_with_advisories": len({v["package"] for v in before_vulns}),
        },
        "after": {
            "total_advisories": len(after_vulns),
            "packages_with_advisories": len({v["package"] for v in after_vulns}),
        },
        "resolved": len(resolved_ids),
        "introduced": len(introduced_ids),
        "packages_upgraded": len(upgrades),
        "resolved_advisories": resolved_vulns,
        "introduced_advisories": introduced_vulns,
        "remaining_advisories": remaining_vulns,
        "upgrades": upgrades,
    }


def render_markdown(summary: dict[str, Any]) -> str:
    before = summary["before"]
    after = summary["after"]
    resolved = summary["resolved"]
    remaining = after["total_advisories"]
    upgraded = summary["packages_upgraded"]
    upgrades: list[dict[str, Any]] = summary["upgrades"]
    resolved_advisories: list[dict[str, Any]] = summary["resolved_advisories"]
    remaining_advisories: list[dict[str, Any]] = summary["remaining_advisories"]
    introduced_advisories: list[dict[str, Any]] = summary["introduced_advisories"]

    lines = [
        "# Security Remediation Summary",
        "",
        "## Risk Reduction",
        "",
        "| Metric | Before | After |",
        "|--------|--------|-------|",
        f"| Security advisories | **{before['total_advisories']}** | **{after['total_advisories']}** |",
        f"| Affected packages | {before['packages_with_advisories']} | {after['packages_with_advisories']} |",
        f"| Advisories resolved | — | {resolved} |",
        f"| Packages upgraded | — | {upgraded} |",
        "",
    ]

    if upgrades:
        lines += [
            "## Packages Upgraded",
            "",
            "| Package | From | To | Update Type |",
            "|---------|------|----|-------------|",
        ]
        for u in sorted(upgrades, key=lambda x: x["name"]):
            lines.append(
                f"| {u['name']} | {u['current_version']} | {u['latest_version']} | {u['update_type']} |"
            )
        lines.append("")

    if resolved_advisories:
        lines += [
            "## Resolved Advisories",
            "",
            "| Advisory | Package | Aliases | Fixed In |",
            "|----------|---------|---------|----------|",
        ]
        for v in resolved_advisories:
            aliases = ", ".join(v["aliases"]) if v["aliases"] else "—"
            fixed = ", ".join(v["fix_versions"]) if v["fix_versions"] else "—"
            lines.append(f"| {v['id']} | {v['package']} {v['version']} | {aliases} | {fixed} |")
        lines.append("")

    if introduced_advisories:
        lines += [
            "## Introduced Advisories",
            "> These advisories were not present before remediation.",
            "",
            "| Advisory | Package | Aliases |",
            "|----------|---------|---------|",
        ]
        for v in introduced_advisories:
            aliases = ", ".join(v["aliases"]) if v["aliases"] else "—"
            lines.append(f"| {v['id']} | {v['package']} {v['version']} | {aliases} |")
        lines.append("")

    if remaining_advisories:
        lines += [
            "## Remaining Advisories",
            "",
            "| Advisory | Package | Aliases | Description |",
            "|----------|---------|---------|-------------|",
        ]
        for v in remaining_advisories:
            aliases = ", ".join(v["aliases"]) if v["aliases"] else "—"
            desc = v["description"]
            if len(desc) > 80:
                desc = desc[:77] + "..."
            lines.append(f"| {v['id']} | {v['package']} {v['version']} | {aliases} | {desc} |")
        lines.append("")
    else:
        lines += ["## Remaining Advisories", "", "None.", ""]

    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate CVE remediation executive summary")
    parser.add_argument("--before", type=Path, required=True, help="pip-audit JSON before upgrade")
    parser.add_argument("--after", type=Path, required=True, help="pip-audit JSON after upgrade")
    parser.add_argument("--upgrades", type=Path, help="pypi-upgrades JSON artifact")
    parser.add_argument("--json-output", type=Path, required=True)
    parser.add_argument("--markdown-output", type=Path, required=True)
    args = parser.parse_args()

    before_report = load_json(args.before)
    after_report = load_json(args.after)

    upgrades: list[dict[str, Any]] = []
    if args.upgrades and args.upgrades.exists():
        upgrades_data = load_json(args.upgrades)
        upgrades = [d for d in upgrades_data.get("dependencies", []) if d.get("updated") == "true"]

    before_vulns = extract_vulnerabilities(before_report)
    after_vulns = extract_vulnerabilities(after_report)
    summary = build_summary(before_vulns, after_vulns, upgrades)

    write_json(args.json_output, summary)
    args.markdown_output.parent.mkdir(parents=True, exist_ok=True)
    args.markdown_output.write_text(render_markdown(summary), encoding="utf-8")

    print(
        f"[remediation-summary] "
        f"before={summary['before']['total_advisories']} "
        f"resolved={summary['resolved']} "
        f"remaining={summary['after']['total_advisories']} "
        f"upgraded={summary['packages_upgraded']} "
        f"report={args.markdown_output}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
