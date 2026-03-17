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


def dependency_list(payload: dict[str, Any]) -> list[dict[str, Any]]:
    dependencies = payload.get("dependencies", [])
    if not isinstance(dependencies, list):
        return []
    return [dependency for dependency in dependencies if isinstance(dependency, dict)]


def truthy(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.lower() == "true"
    return False


def summarize_updates(dependencies: list[dict[str, Any]]) -> dict[str, int]:
    counts: Counter[str] = Counter()
    for dependency in dependencies:
        if truthy(dependency.get("will_update")) or truthy(dependency.get("updated")):
            counts[str(dependency.get("update_type") or "unknown")] += 1
    return dict(sorted(counts.items()))


def summarize_scopes(dependencies: list[dict[str, Any]]) -> dict[str, int]:
    counts: Counter[str] = Counter()
    for dependency in dependencies:
        counts[str(dependency.get("scope") or "unknown")] += 1
    return dict(sorted(counts.items()))


def summarize_compatibility(dependencies: list[dict[str, Any]]) -> dict[str, int]:
    counts: Counter[str] = Counter()
    for dependency in dependencies:
        compatibility = dependency.get("python_compatibility")
        if isinstance(compatibility, dict):
            counts[str(compatibility.get("status") or "unknown")] += 1
    return dict(sorted(counts.items()))


def summarize_plan(plan_payload: dict[str, Any]) -> dict[str, Any]:
    dependencies = dependency_list(plan_payload)
    planned_updates = [
        dependency for dependency in dependencies if truthy(dependency.get("will_update"))
    ]
    summary: dict[str, Any] = {
        "dependency_count": len(dependencies),
        "planned_update_count": len(planned_updates),
        "planned_update_types": summarize_updates(dependencies),
        "scope_counts": summarize_scopes(dependencies),
    }

    compatibility_counts = summarize_compatibility(dependencies)
    if compatibility_counts:
        summary["python_compatibility_counts"] = compatibility_counts

    blocked = plan_payload.get("blocked")
    if isinstance(blocked, dict):
        summary["blocked"] = blocked

    gradle = plan_payload.get("gradle")
    if isinstance(gradle, dict):
        summary["gradle"] = gradle

    return summary


def build_report(
    *,
    inventory_payload: dict[str, Any],
    plan_payload: dict[str, Any],
) -> dict[str, Any]:
    strategy_detection = plan_payload.get("strategy_detection")
    report: dict[str, Any] = {
        "ecosystem": plan_payload.get("ecosystem") or inventory_payload.get("ecosystem"),
        "source": plan_payload.get("source") or inventory_payload.get("source"),
        "inventory": {
            "dependency_count": len(dependency_list(inventory_payload)),
            "scope_counts": summarize_scopes(dependency_list(inventory_payload)),
        },
        "plan": summarize_plan(plan_payload),
    }

    if isinstance(strategy_detection, dict):
        report["strategy_detection"] = strategy_detection

    return report


def markdown_lines(report: dict[str, Any]) -> list[str]:
    plan = report["plan"]
    inventory = report["inventory"]
    lines = [
        "# Dependency Report",
        "",
        f"- ecosystem: `{report.get('ecosystem', 'unknown')}`",
        f"- source: `{report.get('source', 'unknown')}`",
        f"- inventory dependencies: `{inventory['dependency_count']}`",
        f"- planned updates: `{plan['planned_update_count']}`",
    ]

    strategy = report.get("strategy_detection")
    if isinstance(strategy, dict):
        lines.append(f"- strategy: `{strategy.get('strategy', 'unknown')}`")

    blocked = plan.get("blocked")
    if isinstance(blocked, dict):
        lines.append(f"- blocked: `{blocked.get('kind', 'unknown')}`")
        if blocked.get("message"):
            lines.append(f"- blocker message: {blocked['message']}")

    lines.extend(["", "## Inventory scope counts", ""])
    for scope, count in inventory["scope_counts"].items():
        lines.append(f"- `{scope}`: `{count}`")

    lines.extend(["", "## Planned update types", ""])
    planned_update_types = plan["planned_update_types"]
    if planned_update_types:
        for update_type, count in planned_update_types.items():
            lines.append(f"- `{update_type}`: `{count}`")
    else:
        lines.append("- none")

    lines.extend(["", "## Planned scope counts", ""])
    for scope, count in plan["scope_counts"].items():
        lines.append(f"- `{scope}`: `{count}`")

    compatibility_counts = plan.get("python_compatibility_counts")
    if isinstance(compatibility_counts, dict):
        lines.extend(["", "## Python compatibility assessment", ""])
        for status, count in compatibility_counts.items():
            lines.append(f"- `{status}`: `{count}`")

    gradle = plan.get("gradle")
    if isinstance(gradle, dict):
        lines.extend(["", "## Gradle", ""])
        lines.append(f"- current version: `{gradle.get('current_version')}`")
        lines.append(f"- latest version: `{gradle.get('latest_version')}`")
        lines.append(f"- update type: `{gradle.get('update_type')}`")
        lines.append(f"- will update: `{gradle.get('will_update')}`")

    return lines


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def write_markdown(path: Path, lines: list[str]) -> None:
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--inventory", type=Path, required=True)
    parser.add_argument("--plan", type=Path, required=True)
    parser.add_argument("--json-output", type=Path, required=True)
    parser.add_argument("--markdown-output", type=Path, required=True)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    inventory_payload = load_json(args.inventory)
    plan_payload = load_json(args.plan)
    report = build_report(inventory_payload=inventory_payload, plan_payload=plan_payload)
    args.json_output.parent.mkdir(parents=True, exist_ok=True)
    args.markdown_output.parent.mkdir(parents=True, exist_ok=True)
    write_json(args.json_output, report)
    write_markdown(args.markdown_output, markdown_lines(report))
    print(
        "[dependency-report] "
        f"ecosystem={report.get('ecosystem')} "
        f"planned_updates={report['plan']['planned_update_count']} "
        f"json={args.json_output} markdown={args.markdown_output}",
        flush=True,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
