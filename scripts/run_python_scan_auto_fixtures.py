#!/usr/bin/env python3
"""Materialize and validate the Python scan:auto fixture matrix."""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
import tomllib
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parent.parent
SPEC_PATH = Path(__file__).with_name("python_scan_auto_fixture_matrix.toml")
WORK_ROOT = Path(tempfile.gettempdir()) / "polyglot-python-scan-auto-fixtures"
ARTIFACTS_DIR = REPO_ROOT / ".artifacts" / "scans"
IGNORE_NAMES = {
    ".artifacts",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    ".tmp",
    ".venv",
    "__pycache__",
}


def load_spec() -> dict[str, Any]:
    return tomllib.loads(SPEC_PATH.read_text(encoding="utf-8"))


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def write_markdown(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content.rstrip() + "\n", encoding="utf-8")


def copy_template(source: Path, target: Path) -> None:
    if target.exists():
        shutil.rmtree(target)
    shutil.copytree(
        source,
        target,
        ignore=shutil.ignore_patterns(*sorted(IGNORE_NAMES)),
        dirs_exist_ok=False,
    )


def run_command(
    command: list[str], *, cwd: Path, check: bool = True
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        command,
        cwd=cwd,
        check=check,
        text=True,
        capture_output=True,
    )


def apply_replacements(target_dir: Path, operations: list[dict[str, str]]) -> None:
    for operation in operations:
        path = target_dir / str(operation["path"])
        find = str(operation["find"])
        replace = str(operation["replace"])
        content = path.read_text(encoding="utf-8")
        if find not in content:
            raise ValueError(f"could not find replacement text in {path}: {find!r}")
        path.write_text(content.replace(find, replace, 1), encoding="utf-8")


def apply_appends(target_dir: Path, operations: list[dict[str, str]]) -> None:
    for operation in operations:
        path = target_dir / str(operation["path"])
        path.parent.mkdir(parents=True, exist_ok=True)
        existing = path.read_text(encoding="utf-8") if path.exists() else ""
        payload = str(operation["text"]).lstrip("\n")
        path.write_text(existing + payload, encoding="utf-8")


def initialize_git_repository(target_dir: Path) -> None:
    run_command(["git", "init", "-b", "main"], cwd=target_dir)
    run_command(["git", "config", "user.name", "Fixture Runner"], cwd=target_dir)
    run_command(["git", "config", "user.email", "fixtures@example.com"], cwd=target_dir)
    run_command(["git", "add", "."], cwd=target_dir)
    run_command(["git", "commit", "-m", "fixture baseline"], cwd=target_dir)


def remediation_report_path(target_dir: Path) -> Path:
    return target_dir / ".artifacts" / "scans" / "dependency-remediation-report.json"


def load_remediation_report(target_dir: Path) -> dict[str, Any]:
    path = remediation_report_path(target_dir)
    return json.loads(path.read_text(encoding="utf-8"))


def latest_commit_message(target_dir: Path) -> str:
    completed = run_command(["git", "log", "-1", "--pretty=%s"], cwd=target_dir)
    return completed.stdout.strip()


def current_branch(target_dir: Path) -> str:
    completed = run_command(["git", "branch", "--show-current"], cwd=target_dir)
    return completed.stdout.strip()


def git_status_porcelain(target_dir: Path) -> str:
    completed = run_command(["git", "status", "--porcelain"], cwd=target_dir)
    return completed.stdout.strip()


def accepted_values(report: dict[str, Any], key: str) -> set[str]:
    return {str(item.get(key, "")) for item in report.get("accepted", [])}


def rolled_back_values(report: dict[str, Any], key: str) -> set[str]:
    return {str(item.get(key, "")) for item in report.get("rolled_back", [])}


def validate_fixture(
    fixture: dict[str, Any],
    *,
    target_dir: Path,
    report: dict[str, Any],
    command_result: subprocess.CompletedProcess[str],
) -> list[str]:
    errors: list[str] = []
    expect = fixture.get("expect", {})

    def require(condition: bool, message: str) -> None:
        if not condition:
            errors.append(message)

    if "exit_code" in expect:
        require(command_result.returncode == int(expect["exit_code"]), "unexpected exit code")
    if "status" in expect:
        require(report["status"] == str(expect["status"]), "unexpected remediation status")
    if "accepted" in expect:
        require(report["summary"]["accepted"] == int(expect["accepted"]), "unexpected accepted count")
    if "rolled_back" in expect:
        require(
            report["summary"]["rolled_back"] == int(expect["rolled_back"]),
            "unexpected rolled back count",
        )
    if "min_accepted" in expect:
        require(
            report["summary"]["accepted"] >= int(expect["min_accepted"]),
            "accepted count was below the fixture minimum",
        )
    if "max_rolled_back" in expect:
        require(
            report["summary"]["rolled_back"] <= int(expect["max_rolled_back"]),
            "rolled back count exceeded the fixture maximum",
        )
    if "min_rolled_back" in expect:
        require(
            report["summary"]["rolled_back"] >= int(expect["min_rolled_back"]),
            "rolled back count was below the fixture minimum",
        )
    if "remaining_apply_candidates" in expect:
        require(
            report["summary"]["remaining_apply_candidates"] == int(expect["remaining_apply_candidates"]),
            "unexpected remaining apply candidate count",
        )

    required_target_types = set(expect.get("required_accepted_target_types", []))
    require(
        required_target_types.issubset(accepted_values(report, "target_type")),
        "missing required accepted target types",
    )
    required_packages = set(expect.get("required_accepted_packages", []))
    require(
        required_packages.issubset(accepted_values(report, "package_name")),
        "missing required accepted package names",
    )
    required_target_dependencies = set(expect.get("required_accepted_target_dependencies", []))
    require(
        required_target_dependencies.issubset(accepted_values(report, "target_dependency_name")),
        "missing required accepted target dependencies",
    )
    required_rolled_back = set(expect.get("required_rolled_back_packages", []))
    require(
        required_rolled_back.issubset(rolled_back_values(report, "package_name")),
        "missing required rolled back package names",
    )

    for snippet in expect.get("require_skip_reason_contains", []):
        require(
            any(snippet in str(candidate.get("reason", "")) for candidate in report["remaining_candidates"]),
            f"no remaining candidate reason contained {snippet!r}",
        )

    if bool(expect.get("require_post_test_pass", False)):
        post_test = run_command([sys.executable, "tasks.py", "test"], cwd=target_dir, check=False)
        require(post_test.returncode == 0, "post-remediation tests did not pass")

    if fixture.get("mode") == "scan-pr":
        expected_branch_prefix = str(expect.get("expected_branch_prefix", ""))
        if expected_branch_prefix:
            require(
                current_branch(target_dir).startswith(expected_branch_prefix),
                "scan:pr did not leave the repo on the expected branch prefix",
            )
        expected_commit_message = str(expect.get("expected_commit_message", ""))
        if expected_commit_message:
            require(
                latest_commit_message(target_dir) == expected_commit_message,
                "scan:pr wrote an unexpected commit message",
            )
        if bool(expect.get("expect_clean_git", False)):
            require(not git_status_porcelain(target_dir), "scan:pr left a dirty git worktree")

    return errors


def run_fixture(fixture: dict[str, Any]) -> dict[str, Any]:
    target_dir = WORK_ROOT / str(fixture["name"])
    try:
        source_dir = REPO_ROOT / str(fixture["source"])
        copy_template(source_dir, target_dir)
        apply_replacements(target_dir, list(fixture.get("replace", [])))
        apply_appends(target_dir, list(fixture.get("append", [])))
        if bool(fixture.get("refresh_lock", True)):
            run_command(["uv", "lock"], cwd=target_dir)

        if bool(fixture.get("initialize_git", False)) or fixture.get("mode") == "scan-pr":
            initialize_git_repository(target_dir)

        run_command([sys.executable, "tasks.py", "init"], cwd=target_dir)
        run_command([sys.executable, "tasks.py", "scan_plan"], cwd=target_dir)
        task_name = "scan_pr" if fixture.get("mode") == "scan-pr" else "scan_auto"
        command_result = run_command(
            [sys.executable, "tasks.py", task_name], cwd=target_dir, check=False
        )
        report = load_remediation_report(target_dir)
        errors = validate_fixture(
            fixture, target_dir=target_dir, report=report, command_result=command_result
        )
        return {
            "name": fixture["name"],
            "mode": fixture.get("mode", "scan-auto"),
            "status": "passed" if not errors else "failed",
            "exit_code": command_result.returncode,
            "report_status": report["status"],
            "accepted": report["summary"]["accepted"],
            "rolled_back": report["summary"]["rolled_back"],
            "remaining_apply_candidates": report["summary"]["remaining_apply_candidates"],
            "errors": errors,
        }
    except Exception as error:  # noqa: BLE001
        return {
            "name": fixture["name"],
            "mode": fixture.get("mode", "scan-auto"),
            "status": "failed",
            "exit_code": -1,
            "report_status": "setup-failed",
            "accepted": 0,
            "rolled_back": 0,
            "remaining_apply_candidates": 0,
            "errors": [str(error)],
        }


def markdown_summary(payload: dict[str, Any]) -> str:
    lines = [
        "# Python scan:auto Fixture Matrix",
        "",
        f"- total fixtures: `{payload['summary']['total']}`",
        f"- passed: `{payload['summary']['passed']}`",
        f"- failed: `{payload['summary']['failed']}`",
        "",
    ]
    for result in payload["results"]:
        lines.extend(
            [
                f"## {result['name']}",
                "",
                f"- mode: `{result['mode']}`",
                f"- status: `{result['status']}`",
                f"- command exit code: `{result['exit_code']}`",
                f"- remediation status: `{result['report_status']}`",
                f"- accepted fixes: `{result['accepted']}`",
                f"- rolled back fixes: `{result['rolled_back']}`",
                f"- remaining apply candidates: `{result['remaining_apply_candidates']}`",
            ]
        )
        if result["errors"]:
            lines.append(f"- errors: `{' | '.join(result['errors'])}`")
        lines.append("")
    return "\n".join(lines)


def main() -> int:
    ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)
    WORK_ROOT.mkdir(parents=True, exist_ok=True)
    spec = load_spec()
    results = [run_fixture(fixture) for fixture in spec.get("fixture", [])]
    payload = {
        "results": results,
        "summary": {
            "total": len(results),
            "passed": sum(1 for result in results if result["status"] == "passed"),
            "failed": sum(1 for result in results if result["status"] == "failed"),
        },
    }
    write_json(ARTIFACTS_DIR / "python-scan-auto-fixtures.json", payload)
    write_markdown(ARTIFACTS_DIR / "python-scan-auto-fixtures.md", markdown_summary(payload))
    return 1 if payload["summary"]["failed"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
