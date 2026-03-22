#!/usr/bin/env python3
"""Summarize a Trivy JSON image report."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


def load_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise SystemExit(f"expected a JSON object in {path}")
    return payload


def summarize(report: dict[str, Any], image_name: str, image_ref: str) -> dict[str, Any]:
    critical = 0
    high = 0
    medium = 0
    low = 0
    fixable = 0
    unfixed = 0
    total = 0
    by_type: dict[str, dict[str, int]] = {}
    package_counts: dict[str, int] = {}
    critical_rows: list[dict[str, str]] = []

    for result in report.get("Results", []):
        result_type = str(result.get("Type", "unknown"))
        for vulnerability in result.get("Vulnerabilities", []) or []:
            total += 1
            severity = str(vulnerability.get("Severity", "")).upper()
            if severity == "CRITICAL":
                critical += 1
            elif severity == "HIGH":
                high += 1
            elif severity == "MEDIUM":
                medium += 1
            elif severity == "LOW":
                low += 1

            package_name = (
                vulnerability.get("PkgName")
                or vulnerability.get("PkgID")
                or "unknown"
            )
            package_name = str(package_name)
            package_counts[package_name] = package_counts.get(package_name, 0) + 1

            by_type.setdefault(
                result_type,
                {"total": 0, "critical": 0, "high": 0, "fixable": 0},
            )
            by_type[result_type]["total"] += 1
            if severity == "CRITICAL":
                by_type[result_type]["critical"] += 1
            elif severity == "HIGH":
                by_type[result_type]["high"] += 1

            fixed_version = vulnerability.get("FixedVersion")
            if fixed_version:
                by_type[result_type]["fixable"] += 1
                fixable += 1
            else:
                unfixed += 1

            if severity == "CRITICAL":
                critical_rows.append(
                    {
                        "vulnerability_id": str(
                            vulnerability.get("VulnerabilityID", "unknown")
                        ),
                        "package_name": package_name,
                        "installed_version": str(
                            vulnerability.get("InstalledVersion", "unknown")
                        ),
                        "fixed_version": str(fixed_version or "none"),
                        "type": result_type,
                    }
                )

    critical_rows.sort(
        key=lambda row: (row["fixed_version"] == "none", row["package_name"], row["vulnerability_id"])
    )
    top_packages = sorted(package_counts.items(), key=lambda item: (-item[1], item[0]))[:10]

    return {
        "image_name": image_name,
        "image_ref": image_ref,
        "critical": critical,
        "high": high,
        "medium": medium,
        "low": low,
        "fixable": fixable,
        "unfixed": unfixed,
        "total": total,
        "by_type": dict(sorted(by_type.items())),
        "top_packages": top_packages,
        "critical_rows": critical_rows,
    }


def markdown_lines(summary: dict[str, Any]) -> list[str]:
    lines = [
        f"# Image Security Summary: {summary['image_name']}",
        "",
        f"- image: `{summary['image_ref']}`",
        "",
        "| Severity | Count |",
        "| --- | ---: |",
        f"| Critical | {summary['critical']} |",
        f"| High | {summary['high']} |",
        f"| Medium | {summary['medium']} |",
        f"| Low | {summary['low']} |",
        f"| Fixable | {summary['fixable']} |",
        f"| Unfixed | {summary['unfixed']} |",
        f"| Total | {summary['total']} |",
        "",
        "## By type",
        "",
        "| Type | Total | Critical | High | Fixable |",
        "| --- | ---: | ---: | ---: | ---: |",
    ]
    for result_type, entry in summary["by_type"].items():
        lines.append(
            f"| `{result_type}` | {entry['total']} | {entry['critical']} | {entry['high']} | {entry['fixable']} |"
        )

    lines.extend(["", "## Top packages", "", "| Package | Findings |", "| --- | ---: |"])
    for package_name, count in summary["top_packages"]:
        lines.append(f"| `{package_name}` | {count} |")

    lines.extend(["", "## Critical CVEs", ""])
    if summary["critical_rows"]:
        lines.extend(["| CVE | Package | Installed | Fixed | Type |", "| --- | --- | --- | --- | --- |"])
        for row in summary["critical_rows"]:
            lines.append(
                f"| `{row['vulnerability_id']}` | `{row['package_name']}` | `{row['installed_version']}` | `{row['fixed_version']}` | `{row['type']}` |"
            )
    else:
        lines.append("No critical CVEs found.")

    return lines


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--image-name", required=True)
    parser.add_argument("--image-ref", required=True)
    parser.add_argument("--json-output", type=Path, required=True)
    parser.add_argument("--markdown-output", type=Path, required=True)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    report = load_json(args.report)
    summary = summarize(report, image_name=args.image_name, image_ref=args.image_ref)
    args.json_output.parent.mkdir(parents=True, exist_ok=True)
    args.markdown_output.parent.mkdir(parents=True, exist_ok=True)
    args.json_output.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    args.markdown_output.write_text("\n".join(markdown_lines(summary)) + "\n", encoding="utf-8")
    print(
        "[trivy-summary] "
        f"image={summary['image_name']} "
        f"critical={summary['critical']} "
        f"high={summary['high']} "
        f"json={args.json_output} markdown={args.markdown_output}",
        flush=True,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
