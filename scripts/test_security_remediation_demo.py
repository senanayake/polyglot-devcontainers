#!/usr/bin/env python3
"""Integration test harness for the security-remediation-demo fixture.

Validates the full before → upgrade → after flow without requiring a human
to inspect output.  Safe to run repeatedly: pyproject.toml is always restored
to the vulnerable state on exit.

Usage (from inside the devcontainer):
    python scripts/test_security_remediation_demo.py

Or via Task:
    task -t examples/security-remediation-demo/Taskfile.yml test:integration
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path

REPO_ROOT = next(
    parent for parent in Path(__file__).resolve().parents if (parent / "AGENTS.md").exists()
)
DEFAULT_WORKSPACE = REPO_ROOT / "examples" / "security-remediation-demo"


def run_quiet(command: list[str], cwd: Path, check: bool = True) -> subprocess.CompletedProcess[str]:
    """Run a command, suppressing output unless it fails."""
    result = subprocess.run(command, cwd=cwd, check=False, text=True, capture_output=True)
    if result.returncode != 0 and check:
        sys.stdout.write(result.stdout)
        sys.stderr.write(result.stderr)
        raise subprocess.CalledProcessError(result.returncode, result.args)
    return result


def run_visible(command: list[str], cwd: Path, check: bool = True) -> subprocess.CompletedProcess[str]:
    """Run a command, showing its output."""
    return subprocess.run(command, cwd=cwd, check=check, text=True)


def assert_artifact(path: Path) -> None:
    if not path.exists():
        raise AssertionError(f"expected artifact missing: {path}")
    if path.suffix == ".json":
        try:
            json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            raise AssertionError(f"artifact is not valid JSON: {path}: {exc}") from exc


def assert_json_key(path: Path, *keys: str) -> None:
    data = json.loads(path.read_text(encoding="utf-8"))
    for key in keys:
        if key not in data:
            raise AssertionError(f"key {key!r} missing from {path}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Integration test for security-remediation-demo")
    parser.add_argument(
        "--workspace",
        type=Path,
        default=DEFAULT_WORKSPACE,
        help="Path to the security-remediation-demo workspace directory",
    )
    parser.add_argument(
        "--verbose", "-v", action="store_true",
        help="Show all subprocess output (default: suppress install noise)",
    )
    args = parser.parse_args()

    workspace = args.workspace.resolve()
    pyproject = workspace / "pyproject.toml"
    venv = workspace / ".venv"
    artifacts = workspace / ".artifacts"
    tasks_py = workspace / "tasks.py"
    uv = "uv.exe" if sys.platform == "win32" else "uv"
    python_bin = venv / ("Scripts/python.exe" if sys.platform == "win32" else "bin/python")

    run = run_visible if args.verbose else run_quiet

    if not pyproject.exists():
        print(f"[harness] ABORT: workspace not found: {workspace}")
        return 1

    original_pyproject = pyproject.read_text(encoding="utf-8")
    failures: list[str] = []
    summary: dict[str, object] = {}

    try:
        print("[harness] reset  — restoring vulnerable pins, clearing venv and artifacts")
        pyproject.write_text(original_pyproject, encoding="utf-8")
        if venv.exists():
            shutil.rmtree(venv)
        if artifacts.exists():
            shutil.rmtree(artifacts)

        print("[harness] init   — installing pinned 2023-era dependencies")
        run(["python", str(tasks_py), "init"], cwd=workspace)

        print("[harness] scan   — before upgrade (expect FAIL)")
        run(["python", str(tasks_py), "scan"], cwd=workspace, check=False)

        policy_json = artifacts / "scans" / "pip-audit-policy.json"
        assert_artifact(policy_json)
        assert_json_key(policy_json, "violations", "findings", "finding_count")

        policy_before = json.loads(policy_json.read_text(encoding="utf-8"))
        before_violations = policy_before["violations"]
        before_findings = policy_before["finding_count"]
        summary["before"] = {"findings": before_findings, "violations": before_violations}

        blocked_before = [
            f"{f['package_name']} {f['vulnerability_id']} ({f['severity']})"
            for f in policy_before.get("findings", [])
            if f.get("decision") == "policy_blocked"
        ]
        print(f"         findings={before_findings}  violations={before_violations}")
        for b in blocked_before:
            print(f"         blocked: {b}")

        if before_violations == 0:
            failures.append(
                f"SCAN BEFORE: expected violations > 0 but got 0 "
                f"(findings={before_findings}) — the fixture may already be upgraded"
            )

        assert_artifact(artifacts / "scans" / "pip-audit.json")
        assert_artifact(artifacts / "scans" / "pip-audit-policy.md")

        print("[harness] upgrade — rewriting exact pins to latest")
        run(["python", str(tasks_py), "upgrade"], cwd=workspace)

        print("[harness] resync  — installing upgraded packages into venv")
        run([uv, "pip", "install", "--python", str(python_bin), "-e", ".[dev]"], cwd=workspace)

        upgrades_json = artifacts / "scans" / "pypi-upgrades.json"
        assert_artifact(upgrades_json)
        assert_json_key(upgrades_json, "ecosystem", "dependencies")

        upgrades_data = json.loads(upgrades_json.read_text(encoding="utf-8"))
        if upgrades_data.get("ecosystem") != "python":
            failures.append(
                f"UPGRADE: ecosystem expected 'python', got {upgrades_data.get('ecosystem')!r}"
            )

        updated_packages = [
            d for d in upgrades_data.get("dependencies", []) if d.get("updated") == "true"
        ]
        summary["upgraded"] = [
            f"{d['name']} {d['current_version']} → {d['latest_version']}"
            for d in updated_packages
        ]

        if not updated_packages:
            failures.append("UPGRADE: no packages were upgraded — pins may not have changed")
        else:
            for pkg in updated_packages:
                print(f"         {pkg['name']}  {pkg['current_version']} → {pkg['latest_version']}")

        print("[harness] scan   — after upgrade (expect PASS)")
        run(["python", str(tasks_py), "scan"], cwd=workspace)

        policy_after = json.loads(policy_json.read_text(encoding="utf-8"))
        after_violations = policy_after["violations"]
        after_findings = policy_after["finding_count"]
        summary["after"] = {"findings": after_findings, "violations": after_violations}

        print(f"         findings={after_findings}  violations={after_violations}")

        if after_violations > 0:
            failing_ids = [
                f"{f['package_name']} {f['vulnerability_id']} ({f['severity']})"
                for f in policy_after.get("findings", [])
                if f.get("decision") == "policy_blocked"
            ]
            failures.append(
                f"SCAN AFTER: expected 0 violations but got {after_violations}: {failing_ids}"
            )

        for expected in [
            artifacts / "scans" / "pip-audit.json",
            artifacts / "scans" / "pip-audit-policy.json",
            artifacts / "scans" / "pip-audit-policy.md",
            artifacts / "scans" / "pypi-upgrades.json",
        ]:
            assert_artifact(expected)

    except AssertionError as exc:
        failures.append(str(exc))
    except subprocess.CalledProcessError as exc:
        failures.append(
            f"command failed (exit {exc.returncode}): {' '.join(str(a) for a in exc.cmd)}"
        )
    finally:
        print("[harness] restore — pyproject.toml returned to vulnerable state")
        pyproject.write_text(original_pyproject, encoding="utf-8")

    print()
    if failures:
        print(f"[harness] FAILED — {len(failures)} assertion(s):")
        for i, msg in enumerate(failures, 1):
            print(f"  {i}. {msg}")
        return 1

    before = summary.get("before", {})
    after = summary.get("after", {})
    upgraded = summary.get("upgraded", [])
    print(
        f"[harness] PASSED\n"
        f"  before:   {before.get('findings')} findings, {before.get('violations')} violations\n"
        f"  upgraded: {len(upgraded)} package(s) — {', '.join(str(u) for u in upgraded)}\n"
        f"  after:    {after.get('findings')} findings, {after.get('violations')} violations"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
