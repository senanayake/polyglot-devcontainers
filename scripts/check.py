#!/usr/bin/env python3
"""Read-only compliance checker for Polyglot Devcontainers workspaces.

Inspects artifacts already produced by task scan / task ci.
Does not execute any tools.

Usage:
    python scripts/check.py
    python scripts/check.py --workspace examples/security-remediation-demo
    python scripts/check.py --json
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import tomllib
from dataclasses import dataclass
from pathlib import Path
from typing import Any

PASS = "pass"
WARN = "warn"
FAIL = "fail"
SKIP = "skip"

_LABEL = {PASS: "PASS", WARN: "WARN", FAIL: "FAIL", SKIP: "SKIP"}
_RANK = {PASS: 0, SKIP: 0, WARN: 1, FAIL: 2}

_REQUIRED_VERBS = ["init", "lint", "test", "scan", "ci"]


@dataclass
class CheckResult:
    name: str
    status: str
    detail: str
    artifact: str = ""


def _load_json(path: Path) -> dict[str, Any] | None:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else None
    except (OSError, json.JSONDecodeError):
        return None


def _rel(path: Path, workspace: Path) -> str:
    try:
        return path.relative_to(workspace).as_posix()
    except ValueError:
        return str(path)


def check_devcontainer(workspace: Path) -> CheckResult:
    candidates = [
        workspace / ".devcontainer" / "devcontainer.json",
        workspace / ".devcontainer.json",
    ]
    for path in candidates:
        if path.exists():
            return CheckResult("Devcontainer", PASS, _rel(path, workspace))
    return CheckResult("Devcontainer", FAIL, "no .devcontainer/devcontainer.json found")


def check_taskfile(workspace: Path) -> CheckResult:
    path = workspace / "Taskfile.yml"
    if not path.exists():
        return CheckResult("Taskfile", FAIL, "Taskfile.yml not found")

    content = path.read_text(encoding="utf-8")
    missing = [
        v for v in _REQUIRED_VERBS
        if not re.search(rf"^\s+{re.escape(v)}:\s*$", content, re.MULTILINE)
    ]
    if missing:
        return CheckResult("Taskfile", FAIL, f"missing verbs: {', '.join(missing)}", "Taskfile.yml")
    return CheckResult("Taskfile", PASS, ", ".join(_REQUIRED_VERBS), "Taskfile.yml")


def check_secret_scan(workspace: Path) -> CheckResult:
    path = workspace / ".artifacts" / "scans" / "gitleaks.sarif"
    if not path.exists():
        return CheckResult("Secret scan", WARN, "gitleaks.sarif not found — run task scan")

    rel = _rel(path, workspace)
    data = _load_json(path)
    if data is None:
        return CheckResult("Secret scan", WARN, "gitleaks.sarif unreadable", rel)

    results: list[Any] = []
    for run in data.get("runs", []):
        results.extend(run.get("results", []))

    if results:
        return CheckResult("Secret scan", FAIL, f"{len(results)} finding(s)", rel)
    return CheckResult("Secret scan", PASS, "0 findings", rel)


def _check_pip_audit_policy(path: Path, workspace: Path) -> CheckResult | None:
    data = _load_json(path)
    if data is None:
        return None
    rel = _rel(path, workspace)
    violations = data.get("violations", 0)
    finding_count = data.get("finding_count", 0)
    if violations > 0:
        blocked = [
            f"{f['package_name']} {f['vulnerability_id']}"
            for f in data.get("findings", [])
            if f.get("decision") == "policy_blocked"
        ]
        detail = f"{violations} violation(s): {', '.join(blocked[:3])}"
        if len(blocked) > 3:
            detail += f" (+{len(blocked) - 3} more)"
        return CheckResult("Vuln scan", FAIL, detail, rel)
    if finding_count > 0:
        return CheckResult("Vuln scan", WARN, f"{finding_count} advisory finding(s), 0 violations", rel)
    return CheckResult("Vuln scan", PASS, "0 findings", rel)


def _check_trivy_summaries(paths: list[Path], workspace: Path) -> CheckResult | None:
    critical = high = 0
    for p in paths:
        data = _load_json(p)
        if data:
            critical += data.get("critical_count", 0)
            high += data.get("high_count", 0)
    rel = _rel(paths[0].parent, workspace) + "/trivy-*-summary.json"
    if critical > 0:
        return CheckResult("Vuln scan", FAIL, f"{critical} critical, {high} high", rel)
    if high > 0:
        return CheckResult("Vuln scan", WARN, f"0 critical, {high} high (upstream residual)", rel)
    return CheckResult("Vuln scan", PASS, f"{len(paths)} image(s) scanned, 0 critical", rel)


def check_vuln_scan(workspace: Path) -> CheckResult:
    scans_dir = workspace / ".artifacts" / "scans"

    policy_path = scans_dir / "pip-audit-policy.json"
    if policy_path.exists():
        result = _check_pip_audit_policy(policy_path, workspace)
        if result is not None:
            return result

    if scans_dir.exists():
        summaries = sorted(scans_dir.glob("trivy-*-summary.json"))
        if summaries:
            result = _check_trivy_summaries(summaries, workspace)
            if result is not None:
                return result

    if not scans_dir.exists():
        return CheckResult("Vuln scan", WARN, "no .artifacts/scans/ — run task scan")
    return CheckResult("Vuln scan", WARN, "no vulnerability scan artifact found — run task scan")


def check_contract(workspace: Path) -> CheckResult:
    path = workspace / ".polyglot-contract.yaml"
    if not path.exists():
        return CheckResult("Contract", SKIP, "no .polyglot-contract.yaml (not yet adopted)")
    return CheckResult("Contract", PASS, _rel(path, workspace))


def _published_image_artifact_names(catalog_path: Path) -> list[str]:
    payload = tomllib.loads(catalog_path.read_text(encoding="utf-8"))
    images = payload.get("images")
    if payload.get("catalog_version") != 1 or not isinstance(images, dict):
        return []

    artifact_names: list[str] = []
    for entry in images.values():
        if not isinstance(entry, dict):
            continue
        artifact_name = entry.get("artifact_name")
        if isinstance(artifact_name, str) and artifact_name:
            artifact_names.append(artifact_name)
    return sorted(set(artifact_names))


def check_release_workflow_catalog_coverage(workspace: Path) -> CheckResult:
    catalog_path = workspace / "published-image-catalog.toml"
    workflow_path = workspace / ".github" / "workflows" / "release-images.yml"
    if not catalog_path.exists() or not workflow_path.exists():
        return CheckResult("Release image notes", SKIP, "no release image catalog/workflow")

    artifact_names = _published_image_artifact_names(catalog_path)
    if not artifact_names:
        return CheckResult("Release image notes", FAIL, "published image catalog has no artifact names")

    workflow_text = workflow_path.read_text(encoding="utf-8")
    required_dynamic_fragments = [
        "scripts/build_residual_risk_report.py",
        "scripts/build_release_security_summary.py",
        "scripts/published_image_pipeline.py stage-release-security-assets",
    ]
    missing_fragments = [
        fragment for fragment in required_dynamic_fragments if fragment not in workflow_text
    ]
    if workflow_text.count("scripts/published_image_pipeline.py release-security-args") < 3:
        missing_fragments.append("three release-security-args invocations")
    if missing_fragments:
        return CheckResult(
            "Release image notes",
            FAIL,
            f"release workflow is not catalog-driven: {', '.join(missing_fragments)}",
            _rel(workflow_path, workspace),
        )

    hard_coded_patterns = [
        pattern
        for artifact_name in artifact_names
        for pattern in (
            f"--report {artifact_name}=",
            f"--summary {artifact_name}=",
            f"trivy-{artifact_name}-summary.",
            f"sbom-{artifact_name}.spdx.json",
            f"release-security-{artifact_name}-summary.",
            f"release-security-{artifact_name}-sbom.spdx.json",
        )
        if pattern in workflow_text
    ]
    if hard_coded_patterns:
        return CheckResult(
            "Release image notes",
            FAIL,
            "release workflow hard-codes catalog artifacts: "
            + ", ".join(hard_coded_patterns[:5]),
            _rel(workflow_path, workspace),
        )

    return CheckResult(
        "Release image notes",
        PASS,
        f"release security aggregation is catalog-driven for {len(artifact_names)} image artifacts",
        _rel(workflow_path, workspace),
    )


def _overall(results: list[CheckResult]) -> str:
    rank = max(_RANK[r.status] for r in results)
    return (PASS, WARN, FAIL)[rank]


def _render_console(workspace: Path, results: list[CheckResult], overall: str) -> None:
    print(f"[check] {workspace}")
    print()
    width = max(len(r.name) for r in results) + 2
    for r in results:
        artifact = f"  ({r.artifact})" if r.artifact else ""
        print(f"  {r.name:<{width}} {_LABEL[r.status]:<4}  {r.detail}{artifact}")
    print()
    failures = sum(1 for r in results if r.status == FAIL)
    warnings = sum(1 for r in results if r.status == WARN)
    print(f"Overall: {_LABEL[overall]}  ({failures} failure(s), {warnings} warning(s))")


def _render_json(workspace: Path, results: list[CheckResult], overall: str) -> None:
    print(json.dumps({
        "workspace": str(workspace),
        "overall": overall,
        "checks": [
            {"name": r.name, "status": r.status, "detail": r.detail, "artifact": r.artifact}
            for r in results
        ],
    }, indent=2))


def main() -> int:
    parser = argparse.ArgumentParser(description="Read-only compliance check for a Polyglot workspace")
    parser.add_argument(
        "--workspace", type=Path, default=Path.cwd(),
        help="workspace root to check (default: cwd)",
    )
    parser.add_argument("--json", action="store_true", help="emit JSON output")
    args = parser.parse_args()

    workspace = args.workspace.resolve()

    results = [
        check_devcontainer(workspace),
        check_taskfile(workspace),
        check_secret_scan(workspace),
        check_vuln_scan(workspace),
        check_contract(workspace),
        check_release_workflow_catalog_coverage(workspace),
    ]

    overall = _overall(results)

    if args.json:
        _render_json(workspace, results, overall)
    else:
        _render_console(workspace, results, overall)

    return 0 if overall != FAIL else 1


if __name__ == "__main__":
    raise SystemExit(main())
