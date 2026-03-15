from __future__ import annotations

from collections import Counter

import httpx
from packaging.version import Version

from .models import DependencyFinding

SEVERITY_ORDER = ("critical", "high", "medium", "low")


def summarize_by_severity(findings: list[DependencyFinding]) -> dict[str, int]:
    counts = Counter(finding.severity for finding in findings)
    return {
        "critical": counts["critical"],
        "high": counts["high"],
        "medium": counts["medium"],
        "low": counts["low"],
    }


def highest_severity(findings: list[DependencyFinding]) -> str:
    counts = summarize_by_severity(findings)
    for severity in SEVERITY_ORDER:
        if counts[severity] > 0:
            return severity
    return "none"


def render_summary(project_name: str, findings: list[DependencyFinding]) -> str:
    counts = summarize_by_severity(findings)
    parts = [f"{severity}={count}" for severity, count in counts.items() if count > 0]
    if not parts:
        return f"{project_name}: no findings"
    return f"{project_name}: " + ", ".join(parts)


def sorted_fix_versions(findings: list[DependencyFinding]) -> list[str]:
    versions = {version for finding in findings for version in finding.fixed_versions}
    return [str(version) for version in sorted(Version(item) for item in versions)]


def build_report_endpoint(
    project_name: str, findings: list[DependencyFinding], base_url: str
) -> httpx.URL:
    return httpx.URL(base_url).copy_with(
        path=f"/api/projects/{project_name}/findings",
        params={
            "count": str(len(findings)),
            "highest": highest_severity(findings),
        },
    )
