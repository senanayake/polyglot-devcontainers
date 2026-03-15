from __future__ import annotations

from python_maintenance_example.models import DependencyFinding
from python_maintenance_example.reporting import (
    build_report_endpoint,
    render_summary,
    sorted_fix_versions,
    summarize_by_severity,
)


def sample_findings() -> list[DependencyFinding]:
    return [
        DependencyFinding(
            package="httpx",
            severity="high",
            current_version="0.27.2",
            fixed_versions=["0.28.1"],
            advisory_id="GHSA-example-httpx",
            summary="Upgrade the HTTP client dependency.",
        ),
        DependencyFinding(
            package="pydantic",
            severity="medium",
            current_version="2.9.2",
            fixed_versions=["2.10.6", "2.11.1"],
            advisory_id="GHSA-example-pydantic",
            summary="Refresh the model validation dependency.",
        ),
        DependencyFinding(
            package="packaging",
            severity="medium",
            current_version="24.1",
            fixed_versions=["24.2"],
            advisory_id="GHSA-example-packaging",
            summary="Upgrade the version parsing dependency.",
        ),
    ]


def test_summarize_by_severity_counts_known_findings() -> None:
    assert summarize_by_severity(sample_findings()) == {
        "critical": 0,
        "high": 1,
        "medium": 2,
        "low": 0,
    }


def test_render_summary_prefers_human_readable_severity_counts() -> None:
    assert render_summary("python-maintenance-example", sample_findings()) == (
        "python-maintenance-example: high=1, medium=2"
    )


def test_sorted_fix_versions_returns_unique_sorted_versions() -> None:
    assert sorted_fix_versions(sample_findings()) == ["0.28.1", "2.10.6", "2.11.1", "24.2"]


def test_build_report_endpoint_includes_project_context() -> None:
    endpoint = build_report_endpoint(
        "python-maintenance-example",
        sample_findings(),
        "https://scanner.internal.example",
    )

    assert str(endpoint) == (
        "https://scanner.internal.example/api/projects/python-maintenance-example/findings"
        "?count=3&highest=high"
    )
