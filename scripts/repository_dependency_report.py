from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path
from typing import Any


def load_json(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as handle:
        payload = json.load(handle)
    if not isinstance(payload, dict):
        raise SystemExit(f"expected a JSON object in {path}")
    return payload


def normalize_report(path: Path) -> dict[str, Any]:
    report = load_json(path)
    plan = report.get("plan", {})
    if not isinstance(plan, dict):
        plan = {}
    return {
        "path": str(path),
        "ecosystem": report.get("ecosystem", "unknown"),
        "source": report.get("source", "unknown"),
        "strategy": (
            report.get("strategy_detection", {}).get("strategy")
            if isinstance(report.get("strategy_detection"), dict)
            else None
        ),
        "planned_update_count": int(plan.get("planned_update_count", 0)),
        "planned_update_types": (
            plan.get("planned_update_types", {})
            if isinstance(plan.get("planned_update_types"), dict)
            else {}
        ),
        "blocked": plan.get("blocked") if isinstance(plan.get("blocked"), dict) else None,
    }


def build_aggregate(report_paths: list[Path]) -> dict[str, Any]:
    reports = [normalize_report(path) for path in report_paths]
    ecosystem_counts: Counter[str] = Counter()
    update_type_counts: Counter[str] = Counter()
    blocked_counts: Counter[str] = Counter()

    total_planned_updates = 0
    for report in reports:
        ecosystem_counts[report["ecosystem"]] += 1
        total_planned_updates += report["planned_update_count"]
        for update_type, count in report["planned_update_types"].items():
            update_type_counts[str(update_type)] += int(count)
        if report["blocked"] is not None:
            blocked_counts[str(report["blocked"].get("kind", "unknown"))] += 1

    return {
        "report_count": len(reports),
        "total_planned_updates": total_planned_updates,
        "ecosystem_counts": dict(sorted(ecosystem_counts.items())),
        "planned_update_type_counts": dict(sorted(update_type_counts.items())),
        "blocked_counts": dict(sorted(blocked_counts.items())),
        "reports": reports,
    }


def markdown_lines(aggregate: dict[str, Any]) -> list[str]:
    lines = [
        "# Repository Dependency Report",
        "",
        f"- report count: `{aggregate['report_count']}`",
        f"- total planned updates: `{aggregate['total_planned_updates']}`",
    ]

    lines.extend(["", "## Ecosystems", ""])
    for ecosystem, count in aggregate["ecosystem_counts"].items():
        lines.append(f"- `{ecosystem}`: `{count}`")

    lines.extend(["", "## Planned update types", ""])
    if aggregate["planned_update_type_counts"]:
        for update_type, count in aggregate["planned_update_type_counts"].items():
            lines.append(f"- `{update_type}`: `{count}`")
    else:
        lines.append("- none")

    if aggregate["blocked_counts"]:
        lines.extend(["", "## Blocked reports", ""])
        for kind, count in aggregate["blocked_counts"].items():
            lines.append(f"- `{kind}`: `{count}`")

    lines.extend(["", "## Per-path summary", ""])
    for report in aggregate["reports"]:
        strategy_suffix = (
            f" strategy=`{report['strategy']}`" if report["strategy"] is not None else ""
        )
        lines.append(
            f"- `{report['path']}`: ecosystem=`{report['ecosystem']}` "
            f"planned_updates=`{report['planned_update_count']}`{strategy_suffix}"
        )
        if report["blocked"] is not None:
            lines.append(f"  blocker=`{report['blocked'].get('kind', 'unknown')}`")

    return lines


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def write_markdown(path: Path, lines: list[str]) -> None:
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--json-output", type=Path, required=True)
    parser.add_argument("--markdown-output", type=Path, required=True)
    parser.add_argument("reports", nargs="+", type=Path)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    aggregate = build_aggregate(args.reports)
    args.json_output.parent.mkdir(parents=True, exist_ok=True)
    args.markdown_output.parent.mkdir(parents=True, exist_ok=True)
    write_json(args.json_output, aggregate)
    write_markdown(args.markdown_output, markdown_lines(aggregate))
    print(
        "[repository-dependency-report] "
        f"reports={aggregate['report_count']} "
        f"planned_updates={aggregate['total_planned_updates']} "
        f"json={args.json_output} markdown={args.markdown_output}",
        flush=True,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
