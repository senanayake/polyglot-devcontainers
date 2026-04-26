#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import shlex
import shutil
import subprocess
import sys
import tomllib
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any


ROOT = next(parent for parent in Path(__file__).resolve().parents if (parent / "AGENTS.md").exists())
CATALOG_PATH = ROOT / "starters" / "catalog.toml"
DEFAULT_PROOF_ROOT = ROOT / ".tmp" / "starter-proving"
DEFAULT_REPORT_ROOT = ROOT / ".artifacts" / "starters"
REQUIRED_TASKS = {"init", "lint", "test", "scan", "ci"}
SUPPORTED_GENERATION_MODES = {"source-template", "published-image-bootstrap"}
IGNORED_COPY_NAMES = {
    ".artifacts",
    ".coverage",
    ".git",
    ".gradle",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    ".tmp",
    ".venv",
    "__pycache__",
    "build",
    "coverage",
    "node_modules",
}


@dataclass(frozen=True)
class StarterDefinition:
    starter_id: str
    title: str
    description: str
    language: str
    source_template: str
    generation_modes: list[str]
    default_generation_mode: str
    runtime_guidance: list[str]
    task_contract: list[str]
    features: list[str]
    proof_commands: list[str]
    proof_paths: list[str]
    published_image: str | None = None
    published_image_bootstrap_supported: bool = False


def validate_starter_definition(starter: StarterDefinition) -> None:
    template_path = resolve_repo_relative(starter.source_template)
    if not template_path.is_dir():
        raise SystemExit(
            f"starter {starter.starter_id!r} source_template is not a directory: "
            f"{starter.source_template}"
        )

    missing_required = REQUIRED_TASKS.difference(starter.task_contract)
    if missing_required:
        missing = ", ".join(sorted(missing_required))
        raise SystemExit(
            f"starter {starter.starter_id!r} task_contract is missing required tasks: {missing}"
        )

    unsupported_modes = set(starter.generation_modes).difference(SUPPORTED_GENERATION_MODES)
    if unsupported_modes:
        unsupported = ", ".join(sorted(unsupported_modes))
        raise SystemExit(
            f"starter {starter.starter_id!r} has unsupported generation modes: {unsupported}"
        )

    if starter.default_generation_mode not in starter.generation_modes:
        raise SystemExit(
            f"starter {starter.starter_id!r} default_generation_mode "
            f"{starter.default_generation_mode!r} is not listed in generation_modes"
        )

    if starter.published_image_bootstrap_supported and not starter.published_image:
        raise SystemExit(
            f"starter {starter.starter_id!r} enables published_image_bootstrap_supported "
            "but does not declare a published_image"
        )

    if not starter.runtime_guidance:
        raise SystemExit(f"starter {starter.starter_id!r} must declare runtime_guidance")
    if not starter.proof_commands:
        raise SystemExit(f"starter {starter.starter_id!r} must declare proof_commands")
    if not starter.proof_paths:
        raise SystemExit(f"starter {starter.starter_id!r} must declare proof_paths")

    for required_file in ("Taskfile.yml", "README.md"):
        if not (template_path / required_file).exists():
            raise SystemExit(
                f"starter {starter.starter_id!r} source template is missing {required_file}"
            )


def load_catalog() -> dict[str, StarterDefinition]:
    payload = tomllib.loads(CATALOG_PATH.read_text(encoding="utf-8"))
    schema_version = payload.get("schema_version")
    if schema_version != 1:
        raise SystemExit(f"unsupported starter catalog schema_version: {schema_version!r}")
    starters = payload.get("starters", {})
    if not isinstance(starters, dict):
        raise SystemExit(f"expected [starters.*] entries in {CATALOG_PATH}")

    definitions: dict[str, StarterDefinition] = {}
    for starter_id, raw_value in starters.items():
        if not isinstance(raw_value, dict):
            raise SystemExit(f"starter entry {starter_id!r} must be a table")
        definitions[starter_id] = StarterDefinition(
            starter_id=starter_id,
            title=str(raw_value["title"]),
            description=str(raw_value["description"]),
            language=str(raw_value["language"]),
            source_template=str(raw_value["source_template"]),
            generation_modes=[str(value) for value in raw_value["generation_modes"]],
            default_generation_mode=str(raw_value["default_generation_mode"]),
            runtime_guidance=[str(value) for value in raw_value.get("runtime_guidance", [])],
            task_contract=[str(value) for value in raw_value.get("task_contract", [])],
            features=[str(value) for value in raw_value.get("features", [])],
            proof_commands=[str(value) for value in raw_value.get("proof_commands", [])],
            proof_paths=[str(value) for value in raw_value.get("proof_paths", [])],
            published_image=(
                str(raw_value["published_image"]) if "published_image" in raw_value else None
            ),
            published_image_bootstrap_supported=bool(
                raw_value.get("published_image_bootstrap_supported", False)
            ),
        )
        validate_starter_definition(definitions[starter_id])
    return definitions


def require_starter(definitions: dict[str, StarterDefinition], starter_id: str) -> StarterDefinition:
    try:
        return definitions[starter_id]
    except KeyError as error:
        available = ", ".join(sorted(definitions))
        raise SystemExit(f"unknown starter {starter_id!r}; available: {available}") from error


def ensure_generation_mode(starter: StarterDefinition, mode: str | None) -> str:
    selected = mode or starter.default_generation_mode
    if selected not in starter.generation_modes:
        available = ", ".join(starter.generation_modes)
        raise SystemExit(
            f"generation mode {selected!r} is not supported for {starter.starter_id}; "
            f"available modes: {available}"
        )
    return selected


def resolve_repo_relative(path_value: str) -> Path:
    resolved = (ROOT / path_value).resolve()
    try:
        resolved.relative_to(ROOT.resolve())
    except ValueError as error:
        raise SystemExit(f"path escapes repository root: {path_value}") from error
    return resolved


def validate_empty_or_force(output_path: Path, force: bool) -> None:
    if output_path.exists():
        if not force:
            raise SystemExit(f"output path already exists: {output_path}")
        if output_path.is_dir():
            output_path = output_path.resolve()
            try:
                output_path.relative_to(ROOT.resolve())
            except ValueError as error:
                raise SystemExit(f"refusing to delete path outside repository: {output_path}") from error
            shutil.rmtree(output_path)
        else:
            output_path.unlink()
    output_path.parent.mkdir(parents=True, exist_ok=True)


def ignore_copy_entries(_: str, names: list[str]) -> set[str]:
    return {name for name in names if name in IGNORED_COPY_NAMES}


def write_generated_stamp(output_path: Path, starter: StarterDefinition, generation_mode: str) -> None:
    payload = {
        "starter_id": starter.starter_id,
        "title": starter.title,
        "generation_mode": generation_mode,
        "source_template": starter.source_template,
        "published_image": starter.published_image,
        "published_image_bootstrap_supported": starter.published_image_bootstrap_supported,
        "runtime_guidance": starter.runtime_guidance,
        "task_contract": starter.task_contract,
        "features": starter.features,
        "proof_commands": starter.proof_commands,
        "proof_paths": starter.proof_paths,
        "catalog_path": str(CATALOG_PATH.relative_to(ROOT)),
    }
    stamp_path = output_path / ".polyglot-starter.json"
    stamp_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def generate_source_template(starter: StarterDefinition, output_path: Path) -> None:
    source_path = resolve_repo_relative(starter.source_template)
    shutil.copytree(source_path, output_path, ignore=ignore_copy_entries)


def generate_workspace(
    starter: StarterDefinition, output_path: Path, generation_mode: str, *, force: bool
) -> Path:
    validate_empty_or_force(output_path, force)
    if generation_mode != "source-template":
        raise SystemExit(f"unsupported generation mode: {generation_mode}")
    generate_source_template(starter, output_path)
    write_generated_stamp(output_path, starter, generation_mode)
    return output_path


def command_result(command: str, workdir: Path) -> dict[str, Any]:
    args = shlex.split(command)
    subprocess.run(args, cwd=workdir, check=True, text=True)
    return {"command": command, "status": "passed"}


def check_required_path(workdir: Path, relative_path: str) -> dict[str, Any]:
    path = workdir / relative_path
    return {
        "path": relative_path,
        "exists": path.exists(),
        "status": "passed" if path.exists() else "failed",
    }


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def markdown_lines(result: dict[str, Any]) -> list[str]:
    lines = [
        f"# Starter Proof: {result['starter_id']}",
        "",
        f"- title: `{result['title']}`",
        f"- generation mode: `{result['generation_mode']}`",
        f"- workspace: `{result['workspace']}`",
        f"- status: `{result['status']}`",
        "",
        "## Runtime Guidance",
        "",
    ]

    for page in result.get("runtime_guidance", []):
        lines.append(f"- `man {page}`")

    lines.extend(["", "## Commands", ""])
    for command in result.get("commands", []):
        lines.append(f"- `{command['command']}`: `{command['status']}`")

    lines.extend(["", "## Required Paths", ""])
    for path_result in result.get("path_results", []):
        lines.append(f"- `{path_result['path']}`: `{path_result['status']}`")

    if result.get("failure"):
        lines.extend(["", "## Failure", "", result["failure"]])

    return lines


def write_markdown(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(markdown_lines(payload)) + "\n", encoding="utf-8")


def prove_starter(
    starter: StarterDefinition,
    generation_mode: str,
    *,
    workspace_root: Path,
    report_root: Path,
) -> int:
    workspace = workspace_root / starter.starter_id
    workspace.parent.mkdir(parents=True, exist_ok=True)
    generate_workspace(starter, workspace, generation_mode, force=True)

    result: dict[str, Any] = {
        "starter_id": starter.starter_id,
        "title": starter.title,
        "generation_mode": generation_mode,
        "workspace": str(workspace),
        "runtime_guidance": starter.runtime_guidance,
        "commands": [],
        "path_results": [],
        "status": "passed",
    }

    try:
        for command in starter.proof_commands:
            result["commands"].append(command_result(command, workspace))
        for relative_path in starter.proof_paths:
            result["path_results"].append(check_required_path(workspace, relative_path))
        if any(path_result["status"] != "passed" for path_result in result["path_results"]):
            result["status"] = "failed"
            result["failure"] = "one or more required paths were not created"
    except subprocess.CalledProcessError as error:
        result["status"] = "failed"
        result["failure"] = f"command failed: {' '.join(error.cmd)}"

    json_output = report_root / starter.starter_id / "proof.json"
    markdown_output = report_root / starter.starter_id / "proof.md"
    write_json(json_output, result)
    write_markdown(markdown_output, result)
    print(
        "[starter-proof] "
        f"starter={starter.starter_id} status={result['status']} "
        f"json={json_output} markdown={markdown_output}",
        flush=True,
    )
    return 0 if result["status"] == "passed" else 1


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("list")
    subparsers.add_parser("validate")

    show_parser = subparsers.add_parser("show")
    show_parser.add_argument("--starter", required=True)

    generate_parser = subparsers.add_parser("generate")
    generate_parser.add_argument("--starter", required=True)
    generate_parser.add_argument("--output", type=Path, required=True)
    generate_parser.add_argument("--mode")
    generate_parser.add_argument("--force", action="store_true")

    prove_parser = subparsers.add_parser("prove")
    prove_target = prove_parser.add_mutually_exclusive_group(required=True)
    prove_target.add_argument("--starter")
    prove_target.add_argument("--all", action="store_true")
    prove_parser.add_argument("--mode")
    prove_parser.add_argument("--workspace-root", type=Path, default=DEFAULT_PROOF_ROOT)
    prove_parser.add_argument("--report-root", type=Path, default=DEFAULT_REPORT_ROOT)

    return parser.parse_args()


def main() -> int:
    args = parse_args()
    definitions = load_catalog()

    if args.command == "list":
        for starter_id in sorted(definitions):
            starter = definitions[starter_id]
            print(
                f"{starter.starter_id}\t{starter.language}\t{starter.default_generation_mode}\t"
                f"{starter.title}"
            )
        return 0

    if args.command == "validate":
        for starter_id in sorted(definitions):
            starter = definitions[starter_id]
            print(
                "[starter-validate] "
                f"starter={starter.starter_id} mode={starter.default_generation_mode} "
                f"template={starter.source_template}",
                flush=True,
            )
        return 0

    if args.command == "show":
        starter = require_starter(definitions, args.starter)
        print(json.dumps(asdict(starter), indent=2))
        return 0

    if args.command == "generate":
        starter = require_starter(definitions, args.starter)
        generation_mode = ensure_generation_mode(starter, args.mode)
        output_path = args.output if args.output.is_absolute() else (ROOT / args.output)
        workspace = generate_workspace(starter, output_path, generation_mode, force=args.force)
        print(
            "[starter-generate] "
            f"starter={starter.starter_id} mode={generation_mode} output={workspace}",
            flush=True,
        )
        return 0

    if args.command == "prove":
        starters = (
            [definitions[starter_id] for starter_id in sorted(definitions)]
            if args.all
            else [require_starter(definitions, args.starter)]
        )
        exit_code = 0
        for starter in starters:
            generation_mode = ensure_generation_mode(starter, args.mode)
            current_exit = prove_starter(
                starter,
                generation_mode,
                workspace_root=args.workspace_root if args.workspace_root.is_absolute() else ROOT / args.workspace_root,
                report_root=args.report_root if args.report_root.is_absolute() else ROOT / args.report_root,
            )
            exit_code = max(exit_code, current_exit)
        return exit_code

    raise SystemExit(f"unsupported command: {args.command}")


if __name__ == "__main__":
    raise SystemExit(main())
