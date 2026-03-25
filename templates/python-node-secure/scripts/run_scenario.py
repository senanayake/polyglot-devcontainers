#!/usr/bin/env python3
"""Run starter-local scenarios and write compact result artifacts."""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]


def load_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise SystemExit(f"expected JSON object in {path}")
    return payload


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def lookup_dotted(payload: Any, dotted_path: str) -> Any:
    current = payload
    for part in dotted_path.split("."):
        if isinstance(current, dict) and part in current:
            current = current[part]
            continue
        raise KeyError(dotted_path)
    return current


def in_git_repo(path: Path) -> bool:
    completed = subprocess.run(
        ["git", "rev-parse", "--is-inside-work-tree"],
        cwd=path,
        check=False,
        text=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    return completed.returncode == 0


def create_workspace_copy(excluded_names: set[str]) -> Path:
    target = Path(tempfile.mkdtemp(prefix="polyglot-scenario-"))

    for entry in ROOT.iterdir():
        if entry.name in excluded_names:
            continue
        destination = target / entry.name
        if entry.is_dir():
            shutil.copytree(entry, destination)
        else:
            shutil.copy2(entry, destination)

    return target


def run_command(command: str, workdir: Path) -> dict[str, Any]:
    subprocess.run(command, cwd=workdir, shell=True, check=True)
    return {"command": command, "status": "passed"}


def check_artifact(spec: dict[str, Any], workdir: Path) -> dict[str, Any]:
    relative_path = str(spec["path"])
    path = workdir / relative_path
    result: dict[str, Any] = {"path": relative_path, "exists": path.exists(), "checks": []}

    if not path.exists():
        result["status"] = "failed"
        result["reason"] = "missing"
        return result

    payload: Any | None = None
    if spec.get("json_equals") or spec.get("json_paths_exist"):
        payload = load_json(path)

    for dotted_path, expected in spec.get("json_equals", {}).items():
        try:
            actual = lookup_dotted(payload, dotted_path)
            passed = actual == expected
        except KeyError:
            actual = None
            passed = False
        result["checks"].append(
            {
                "type": "json_equals",
                "path": dotted_path,
                "expected": expected,
                "actual": actual,
                "passed": passed,
            }
        )

    for dotted_path in spec.get("json_paths_exist", []):
        try:
            actual = lookup_dotted(payload, dotted_path)
            passed = actual is not None
        except KeyError:
            actual = None
            passed = False
        result["checks"].append(
            {
                "type": "json_path_exists",
                "path": dotted_path,
                "actual": actual,
                "passed": passed,
            }
        )

    result["status"] = "passed" if all(check["passed"] for check in result["checks"]) else "failed"
    return result


def capture_artifacts(paths: list[str], workdir: Path, scenario_name: str) -> list[str]:
    if not paths:
        return []

    capture_root = ROOT / ".artifacts" / "scenarios" / scenario_name / "captured"
    if capture_root.exists():
        shutil.rmtree(capture_root)

    captured: list[str] = []
    for relative_path in paths:
        source = workdir / relative_path
        if not source.exists():
            continue
        destination = capture_root / relative_path
        destination.parent.mkdir(parents=True, exist_ok=True)
        if source.is_dir():
            shutil.copytree(source, destination)
        else:
            shutil.copy2(source, destination)
        captured.append(str(Path("captured") / relative_path))

    return captured


def markdown_lines(result: dict[str, Any]) -> list[str]:
    lines = [
        f"# Scenario Result: {result['name']}",
        "",
        f"- intent: `{result['intent']}`",
        f"- status: `{result['status']}`",
        f"- workspace mode: `{result['workspace_mode']}`",
        f"- git repo before run: `{result['git_repo_before']}`",
        "",
        "## Runtime guidance",
        "",
    ]

    for page in result.get("runtime_guidance", []):
        lines.append(f"- `man {page}`")

    lines.extend(["", "## Commands", ""])
    for command in result.get("commands", []):
        lines.append(f"- `{command}`")

    lines.extend(["", "## Artifact checks", ""])
    for artifact in result["artifact_results"]:
        lines.append(f"- `{artifact['path']}`: `{artifact['status']}`")
        for check in artifact.get("checks", []):
            lines.append(f"  - {check['type']} `{check['path']}` -> `{check['passed']}`")

    captured_artifacts = result.get("captured_artifacts", [])
    if captured_artifacts:
        lines.extend(["", "## Captured artifacts", ""])
        for relative_path in captured_artifacts:
            lines.append(f"- `{relative_path}`")

    if result.get("failure"):
        lines.extend(["", "## Failure", "", result["failure"]])

    return lines


def write_markdown(path: Path, lines: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--scenario", type=Path, required=True)
    parser.add_argument("--json-output", type=Path, required=True)
    parser.add_argument("--markdown-output", type=Path, required=True)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    manifest = load_json(args.scenario)

    excluded_names = set(manifest.get("exclude_from_copy", []))
    copied_workspace = bool(manifest.get("copy_workspace", False))
    if manifest.get("remove_git", False):
        excluded_names.add(".git")

    workdir = create_workspace_copy(excluded_names) if copied_workspace else ROOT
    workspace_mode = "copied" if copied_workspace else "in-place"

    result: dict[str, Any] = {
        "name": manifest["name"],
        "intent": manifest["intent"],
        "runtime_guidance": manifest.get("runtime_guidance", []),
        "knowledge_units": manifest.get("knowledge_units", []),
        "commands": manifest.get("commands", []),
        "status": "passed",
        "workspace_mode": workspace_mode,
        "git_repo_before": in_git_repo(workdir),
        "artifact_results": [],
        "captured_artifacts": [],
    }

    expect_git_repo = manifest.get("expect_git_repo")
    if expect_git_repo is not None and result["git_repo_before"] != bool(expect_git_repo):
        result["status"] = "failed"
        result["failure"] = (
            f"expected git repo state {bool(expect_git_repo)} but found {result['git_repo_before']}"
        )
        write_json(args.json_output, result)
        write_markdown(args.markdown_output, markdown_lines(result))
        if copied_workspace:
            shutil.rmtree(workdir, ignore_errors=True)
        return 1

    try:
        for command in manifest.get("commands", []):
            run_command(str(command), workdir)
        for spec in manifest.get("artifacts", []):
            result["artifact_results"].append(check_artifact(spec, workdir))
        if any(artifact["status"] != "passed" for artifact in result["artifact_results"]):
            result["status"] = "failed"
            result["failure"] = "one or more artifact checks failed"
            write_json(args.json_output, result)
            write_markdown(args.markdown_output, markdown_lines(result))
            return 1
        result["captured_artifacts"] = capture_artifacts(
            list(manifest.get("captured_artifacts", [])),
            workdir,
            str(manifest["name"]),
        )
    except subprocess.CalledProcessError as error:
        result["status"] = "failed"
        result["failure"] = f"command failed: {error.cmd}"
        write_json(args.json_output, result)
        write_markdown(args.markdown_output, markdown_lines(result))
        return error.returncode or 1
    finally:
        if copied_workspace:
            shutil.rmtree(workdir, ignore_errors=True)

    write_json(args.json_output, result)
    write_markdown(args.markdown_output, markdown_lines(result))
    print(
        "[scenario] "
        f"name={result['name']} "
        f"status={result['status']} "
        f"json={args.json_output} markdown={args.markdown_output}",
        flush=True,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
