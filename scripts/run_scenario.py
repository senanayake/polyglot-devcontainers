from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path
from typing import Any


ROOT = next(parent for parent in Path(__file__).resolve().parents if (parent / "AGENTS.md").exists())


def load_json(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as handle:
        payload = json.load(handle)
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


def markdown_lines(result: dict[str, Any]) -> list[str]:
    lines = [
        f"# Scenario Result: {result['name']}",
        "",
        f"- scenario set: `{result['scenario_set']}`",
        f"- intent: `{result['intent']}`",
        f"- language: `{result['language']}`",
        f"- workspace: `{result['workspace']}`",
        f"- status: `{result['status']}`",
        "",
        "## Runtime guidance",
        "",
    ]

    for page in result.get("runtime_guidance", []):
        lines.append(f"- `man {page}`")

    lines.extend(["", "## Commands", ""])
    for command in result.get("commands", []):
        lines.append(f"- `{command}`")

    follow_on = result.get("follow_on_commands", [])
    if follow_on:
        lines.extend(["", "## Follow-on commands", ""])
        for command in follow_on:
            lines.append(f"- `{command}`")

    lines.extend(["", "## Artifact checks", ""])
    for artifact in result["artifact_results"]:
        lines.append(f"- `{artifact['path']}`: `{artifact['status']}`")
        for check in artifact.get("checks", []):
            lines.append(
                f"  - {check['type']} `{check['path']}` -> `{check['passed']}`"
            )

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
    workdir = ROOT / str(manifest["workspace"])

    result: dict[str, Any] = {
        "name": manifest["name"],
        "scenario_set": manifest["scenario_set"],
        "intent": manifest["intent"],
        "language": manifest["language"],
        "workspace": manifest["workspace"],
        "runtime_guidance": manifest.get("runtime_guidance", []),
        "knowledge_units": manifest.get("knowledge_units", []),
        "commands": manifest.get("commands", []),
        "follow_on_commands": manifest.get("follow_on_commands", []),
        "status": "passed",
        "artifact_results": [],
    }

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
    except subprocess.CalledProcessError as error:
        result["status"] = "failed"
        result["failure"] = f"command failed: {error.cmd}"
        write_json(args.json_output, result)
        write_markdown(args.markdown_output, markdown_lines(result))
        return error.returncode or 1

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
