#!/usr/bin/env python3
"""Build a residual-risk report from Trivy image reports."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


UPSTREAM_MANAGED_GOBINARIES = {
    "usr/local/bin/d2": {
        "tool": "d2",
        "upstream_release_source": "terrastruct/d2",
    },
    "usr/bin/trivy": {
        "tool": "trivy",
        "upstream_release_source": "aquasecurity/trivy",
    },
    "usr/local/bin/gitleaks": {
        "tool": "gitleaks",
        "upstream_release_source": "gitleaks/gitleaks",
    },
    "usr/local/bin/task": {
        "tool": "task",
        "upstream_release_source": "go-task/task",
    },
    "usr/local/libexec/polyglot-devcontainers/task-real": {
        "tool": "task",
        "upstream_release_source": "go-task/task",
    },
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--report",
        action="append",
        required=True,
        metavar="IMAGE=PATH",
        help="image name and Trivy JSON report path",
    )
    parser.add_argument("--json-output", type=Path, required=True)
    parser.add_argument("--markdown-output", type=Path, required=True)
    return parser.parse_args()


def load_report(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise SystemExit(f"expected a JSON object in {path}")
    return payload


def parse_report_arg(raw: str) -> tuple[str, Path]:
    image_name, separator, path_text = raw.partition("=")
    if not separator or not image_name or not path_text:
        raise SystemExit(f"invalid --report value: {raw!r}; expected IMAGE=PATH")
    return image_name, Path(path_text)


def classify_entry(result_type: str, target: str) -> tuple[str, str, str | None, str]:
    if result_type == "gobinary" and target in UPSTREAM_MANAGED_GOBINARIES:
        policy = UPSTREAM_MANAGED_GOBINARIES[target]
        return (
            "upstream_residual",
            "wait_for_upstream_release",
            policy["upstream_release_source"],
            (
                "Latest upstream-supported release is in use for this managed binary; "
                "track the finding and wait for the vendor to publish a refreshed release."
            ),
        )
    return (
        "review_required",
        "fix_in_repo_or_investigate",
        None,
        (
            "Finding is not covered by the upstream-managed binary policy and "
            "requires repository-side remediation or manual investigation."
        ),
    )


def build_summary(report_map: list[tuple[str, Path]]) -> dict[str, Any]:
    residuals: list[dict[str, str]] = []

    for image_name, report_path in report_map:
        report = load_report(report_path)
        for result in report.get("Results", []):
            result_type = str(result.get("Type", "unknown"))
            target = str(result.get("Target", "unknown"))
            for vulnerability in result.get("Vulnerabilities", []) or []:
                severity = str(vulnerability.get("Severity", "")).upper()
                if severity != "CRITICAL":
                    continue
                classification, action, upstream_release_source, rationale = classify_entry(
                    result_type, target
                )
                residuals.append(
                    {
                        "image_name": image_name,
                        "target": target,
                        "type": result_type,
                        "classification": classification,
                        "action": action,
                        "upstream_release_source": upstream_release_source or "",
                        "vulnerability_id": str(
                            vulnerability.get("VulnerabilityID", "unknown")
                        ),
                        "package_name": str(vulnerability.get("PkgName", "unknown")),
                        "installed_version": str(
                            vulnerability.get("InstalledVersion", "unknown")
                        ),
                        "fixed_version": str(
                            vulnerability.get("FixedVersion") or "none"
                        ),
                        "rationale": rationale,
                    }
                )

    residuals.sort(
        key=lambda row: (
            row["classification"] != "upstream_residual",
            row["image_name"],
            row["target"],
            row["package_name"],
            row["vulnerability_id"],
        )
    )

    counts: dict[str, int] = {}
    for row in residuals:
        counts[row["classification"]] = counts.get(row["classification"], 0) + 1

    return {
        "critical_count": len(residuals),
        "classification_counts": counts,
        "residuals": residuals,
    }


def markdown_lines(summary: dict[str, Any]) -> list[str]:
    lines = [
        "# Residual Risk Report",
        "",
        f"- critical findings: `{summary['critical_count']}`",
        "",
        "| Classification | Count |",
        "| --- | ---: |",
    ]
    for classification, count in sorted(summary["classification_counts"].items()):
        lines.append(f"| `{classification}` | {count} |")

    lines.extend(
        [
            "",
            "## Critical findings",
            "",
            "| Image | Classification | Action | Target | Package | CVE | Installed | Fixed | Upstream release source |",
            "| --- | --- | --- | --- | --- | --- | --- | --- | --- |",
        ]
    )

    for row in summary["residuals"]:
        lines.append(
            "| `{image_name}` | `{classification}` | `{action}` | `{target}` | `{package_name}` | `{vulnerability_id}` | `{installed_version}` | `{fixed_version}` | `{upstream_release_source}` |".format(
                **row
            )
        )
        lines.append("")
        lines.append(f"Rationale: {row['rationale']}")
        lines.append("")

    if not summary["residuals"]:
        lines.append("No critical findings remain.")

    return lines


def main() -> int:
    args = parse_args()
    report_map = [parse_report_arg(raw) for raw in args.report]
    summary = build_summary(report_map)

    args.json_output.parent.mkdir(parents=True, exist_ok=True)
    args.markdown_output.parent.mkdir(parents=True, exist_ok=True)
    args.json_output.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    args.markdown_output.write_text(
        "\n".join(markdown_lines(summary)) + "\n",
        encoding="utf-8",
    )

    print(
        "[residual-risk] "
        f"critical={summary['critical_count']} "
        f"json={args.json_output} markdown={args.markdown_output}",
        flush=True,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
