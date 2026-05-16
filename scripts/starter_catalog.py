#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import os
import shlex
import shutil
import subprocess
import sys
import tempfile
import tomllib
import zipfile
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = next(parent for parent in Path(__file__).resolve().parents if (parent / "AGENTS.md").exists())
CATALOG_PATH = ROOT / "starters" / "catalog.toml"
DEFAULT_PROOF_ROOT = ROOT / ".tmp" / "starter-proving"
DEFAULT_REPORT_ROOT = ROOT / ".artifacts" / "starters"
DEFAULT_RELEASE_ROOT = ROOT / ".artifacts" / "starter-releases"
DEFAULT_PUBLIC_ARTIFACT_ROOT = ROOT / ".artifacts" / "starter-downloads"
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
ZIP_FIXED_TIMESTAMP = (2026, 1, 1, 0, 0, 0)


@dataclass(frozen=True)
class CompositionProfile:
    profile_id: str
    description: str
    features: list[str]
    scenarios: list[str]
    proof_scenarios: list[str]


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
    scenarios: list[str]
    default_profile: str
    composition_profiles: dict[str, CompositionProfile]
    proof_commands: list[str]
    proof_paths: list[str]
    published_image: str | None = None
    published_image_bootstrap_supported: bool = False


@dataclass(frozen=True)
class ReleaseSnapshot:
    catalog_version: str
    source_git_sha: str
    exported_at: str
    catalog_path: Path
    definitions: dict[str, StarterDefinition]


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def current_git_sha() -> str:
    try:
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=ROOT,
            check=True,
            capture_output=True,
            text=True,
        )
    except (FileNotFoundError, subprocess.CalledProcessError):
        return "unknown"
    return result.stdout.strip() or "unknown"


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
    if starter.default_profile not in starter.composition_profiles:
        raise SystemExit(
            f"starter {starter.starter_id!r} default_profile "
            f"{starter.default_profile!r} is not declared in composition_profiles"
        )

    for profile_id, profile in starter.composition_profiles.items():
        unsupported_features = set(profile.features).difference(starter.features)
        if unsupported_features:
            unsupported = ", ".join(sorted(unsupported_features))
            raise SystemExit(
                f"starter {starter.starter_id!r} profile {profile_id!r} "
                f"references unsupported features: {unsupported}"
            )
        unsupported_scenarios = set(profile.scenarios).difference(starter.scenarios)
        if unsupported_scenarios:
            unsupported = ", ".join(sorted(unsupported_scenarios))
            raise SystemExit(
                f"starter {starter.starter_id!r} profile {profile_id!r} "
                f"references unsupported scenarios: {unsupported}"
            )
        unsupported_proof_scenarios = set(profile.proof_scenarios).difference(profile.scenarios)
        if unsupported_proof_scenarios:
            unsupported = ", ".join(sorted(unsupported_proof_scenarios))
            raise SystemExit(
                f"starter {starter.starter_id!r} profile {profile_id!r} "
                f"references proof scenarios outside the profile scenario set: {unsupported}"
            )

    for required_file in ("Taskfile.yml", "README.md"):
        if not (template_path / required_file).exists():
            raise SystemExit(
                f"starter {starter.starter_id!r} source template is missing {required_file}"
            )


def _profile_from_payload(starter_id: str, profile_id: str, profile_value: object) -> CompositionProfile:
    if not isinstance(profile_value, dict):
        raise SystemExit(
            f"starter {starter_id!r} composition profile {profile_id!r} must be a table"
        )
    return CompositionProfile(
        profile_id=profile_id,
        description=str(profile_value["description"]),
        features=[str(value) for value in profile_value.get("features", [])],
        scenarios=[str(value) for value in profile_value.get("scenarios", [])],
        proof_scenarios=[str(value) for value in profile_value.get("proof_scenarios", [])],
    )


def _starter_from_payload(starter_id: str, raw_value: object) -> StarterDefinition:
    if not isinstance(raw_value, dict):
        raise SystemExit(f"starter entry {starter_id!r} must be a table")
    profile_payload = raw_value.get("composition_profiles", {})
    if not isinstance(profile_payload, dict) or not profile_payload:
        raise SystemExit(f"starter {starter_id!r} must declare one or more composition_profiles")
    composition_profiles = {
        profile_id: _profile_from_payload(starter_id, profile_id, profile_value)
        for profile_id, profile_value in profile_payload.items()
    }
    starter = StarterDefinition(
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
        scenarios=[str(value) for value in raw_value.get("scenarios", [])],
        default_profile=str(raw_value["default_profile"]),
        composition_profiles=composition_profiles,
        proof_commands=[str(value) for value in raw_value.get("proof_commands", [])],
        proof_paths=[str(value) for value in raw_value.get("proof_paths", [])],
        published_image=str(raw_value["published_image"]) if "published_image" in raw_value else None,
        published_image_bootstrap_supported=bool(
            raw_value.get("published_image_bootstrap_supported", False)
        ),
    )
    validate_starter_definition(starter)
    return starter


def load_catalog(catalog_path: Path = CATALOG_PATH) -> dict[str, StarterDefinition]:
    payload = tomllib.loads(catalog_path.read_text(encoding="utf-8"))
    schema_version = payload.get("schema_version")
    if schema_version != 1:
        raise SystemExit(f"unsupported starter catalog schema_version: {schema_version!r}")
    starters = payload.get("starters", {})
    if not isinstance(starters, dict):
        raise SystemExit(f"expected [starters.*] entries in {catalog_path}")
    return {
        starter_id: _starter_from_payload(starter_id, raw_value)
        for starter_id, raw_value in starters.items()
    }


def serialize_starter(starter: StarterDefinition) -> dict[str, Any]:
    payload = asdict(starter)
    payload["composition_profiles"] = {
        profile_id: asdict(profile)
        for profile_id, profile in starter.composition_profiles.items()
    }
    return payload


def serialize_catalog(definitions: dict[str, StarterDefinition]) -> dict[str, Any]:
    return {
        "schema_version": 1,
        "starters": {
            starter_id: serialize_starter(definitions[starter_id])
            for starter_id in sorted(definitions)
        },
    }


def release_directory(release_root: Path, catalog_version: str) -> Path:
    return release_root / catalog_version


def release_manifest_path(release_root: Path, catalog_version: str) -> Path:
    return release_directory(release_root, catalog_version) / "release.json"


def release_catalog_path(release_root: Path, catalog_version: str) -> Path:
    return release_directory(release_root, catalog_version) / "catalog.toml"


def export_release_snapshot(
    definitions: dict[str, StarterDefinition],
    catalog_version: str,
    *,
    release_root: Path = DEFAULT_RELEASE_ROOT,
) -> ReleaseSnapshot:
    release_dir = release_directory(release_root, catalog_version)
    if release_dir.exists():
        shutil.rmtree(release_dir)
    release_dir.mkdir(parents=True, exist_ok=True)
    snapshot_catalog = release_catalog_path(release_root, catalog_version)
    snapshot_catalog.write_text(CATALOG_PATH.read_text(encoding="utf-8"), encoding="utf-8")
    manifest = {
        "catalog_version": catalog_version,
        "schema_version": 1,
        "source_git_sha": current_git_sha(),
        "exported_at": utc_now_iso(),
        "catalog_path": str(snapshot_catalog.relative_to(ROOT)),
    }
    write_json(release_manifest_path(release_root, catalog_version), manifest)
    return ReleaseSnapshot(
        catalog_version=catalog_version,
        source_git_sha=str(manifest["source_git_sha"]),
        exported_at=str(manifest["exported_at"]),
        catalog_path=snapshot_catalog,
        definitions=definitions,
    )


def list_release_versions(release_root: Path = DEFAULT_RELEASE_ROOT) -> list[str]:
    if not release_root.exists():
        return []
    versions: list[str] = []
    for child in sorted(release_root.iterdir()):
        if child.is_dir() and (child / "catalog.toml").exists() and (child / "release.json").exists():
            versions.append(child.name)
    return versions


def load_release_snapshot(
    catalog_version: str,
    *,
    release_root: Path = DEFAULT_RELEASE_ROOT,
) -> ReleaseSnapshot:
    manifest_path = release_manifest_path(release_root, catalog_version)
    catalog_path = release_catalog_path(release_root, catalog_version)
    if not manifest_path.exists() or not catalog_path.exists():
        available = ", ".join(list_release_versions(release_root)) or "none"
        raise SystemExit(
            f"released catalog version {catalog_version!r} is not available; available versions: {available}"
        )
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    return ReleaseSnapshot(
        catalog_version=str(manifest["catalog_version"]),
        source_git_sha=str(manifest["source_git_sha"]),
        exported_at=str(manifest["exported_at"]),
        catalog_path=catalog_path,
        definitions=load_catalog(catalog_path),
    )


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


def resolve_profile(starter: StarterDefinition, profile_id: str | None) -> CompositionProfile:
    selected = profile_id or starter.default_profile
    try:
        return starter.composition_profiles[selected]
    except KeyError as error:
        available = ", ".join(sorted(starter.composition_profiles))
        raise SystemExit(
            f"composition profile {selected!r} is not supported for {starter.starter_id}; "
            f"available profiles: {available}"
        ) from error


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


def write_generated_stamp(
    output_path: Path,
    starter: StarterDefinition,
    generation_mode: str,
    profile: CompositionProfile,
    *,
    relative_path: str = ".polyglot-starter.json",
) -> None:
    payload = {
        "starter_id": starter.starter_id,
        "title": starter.title,
        "generation_mode": generation_mode,
        "composition_profile": profile.profile_id,
        "composition_description": profile.description,
        "source_template": starter.source_template,
        "published_image": starter.published_image,
        "published_image_bootstrap_supported": starter.published_image_bootstrap_supported,
        "runtime_guidance": starter.runtime_guidance,
        "task_contract": starter.task_contract,
        "supported_features": starter.features,
        "selected_features": profile.features,
        "supported_scenarios": starter.scenarios,
        "selected_scenarios": profile.scenarios,
        "proof_scenarios": profile.proof_scenarios,
        "proof_commands": starter.proof_commands,
        "proof_paths": starter.proof_paths,
        "catalog_path": str(CATALOG_PATH.relative_to(ROOT)),
    }
    stamp_path = output_path / relative_path
    stamp_path.parent.mkdir(parents=True, exist_ok=True)
    stamp_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def generate_source_template(starter: StarterDefinition, output_path: Path) -> None:
    source_path = resolve_repo_relative(starter.source_template)
    shutil.copytree(source_path, output_path, ignore=ignore_copy_entries)


def default_published_image_ref(starter: StarterDefinition) -> str:
    if not starter.published_image:
        raise SystemExit(f"starter {starter.starter_id!r} does not declare a published_image")
    if ":" in starter.published_image.rsplit("/", 1)[-1]:
        return starter.published_image
    return f"{starter.published_image}:main"


def proof_image_override_env_name(starter: StarterDefinition) -> str:
    normalized = starter.starter_id.upper().replace("-", "_")
    return f"POLYGLOT_STARTER_PROOF_IMAGE_{normalized}"


def proof_image_ref(starter: StarterDefinition) -> str:
    return os.environ.get(proof_image_override_env_name(starter), default_published_image_ref(starter))


def generate_published_image_workspace(
    starter: StarterDefinition,
    profile: CompositionProfile,
    output_path: Path,
) -> None:
    output_path.mkdir(parents=True, exist_ok=True)
    devcontainer_dir = output_path / ".devcontainer"
    devcontainer_dir.mkdir(parents=True, exist_ok=True)
    devcontainer_payload = {
        "name": f"{starter.starter_id}-{profile.profile_id}",
        "image": default_published_image_ref(starter),
    }
    (devcontainer_dir / "devcontainer.json").write_text(
        json.dumps(devcontainer_payload, indent=2) + "\n",
        encoding="utf-8",
    )
    write_generated_stamp(
        output_path,
        starter,
        "published-image-bootstrap",
        profile,
        relative_path=".devcontainer/.polyglot-starter-request.json",
    )


def generate_workspace(
    starter: StarterDefinition,
    profile: CompositionProfile,
    output_path: Path,
    generation_mode: str,
    *,
    force: bool,
) -> Path:
    validate_empty_or_force(output_path, force)
    if generation_mode == "source-template":
        generate_source_template(starter, output_path)
        write_generated_stamp(output_path, starter, generation_mode, profile)
    elif generation_mode == "published-image-bootstrap":
        generate_published_image_workspace(starter, profile, output_path)
    else:
        raise SystemExit(f"unsupported generation mode: {generation_mode}")
    return output_path


def deterministic_zip_path(zip_file: zipfile.ZipFile, source_path: Path, arcname: str) -> None:
    info = zipfile.ZipInfo(arcname)
    info.date_time = ZIP_FIXED_TIMESTAMP
    info.compress_type = zipfile.ZIP_DEFLATED
    info.create_system = 3
    info.external_attr = 0o100644 << 16
    zip_file.writestr(info, source_path.read_bytes())


def create_deterministic_zip(source_root: Path, zip_path: Path) -> None:
    zip_path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(zip_path, "w") as archive:
        for path in sorted(source_root.rglob("*")):
            if path.is_dir():
                continue
            arcname = path.relative_to(source_root).as_posix()
            deterministic_zip_path(archive, path, arcname)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def public_artifact_payload(
    snapshot: ReleaseSnapshot,
    starter: StarterDefinition,
    profile: CompositionProfile,
    generation_mode: str,
) -> dict[str, str]:
    return {
        "catalog_version": snapshot.catalog_version,
        "source_git_sha": snapshot.source_git_sha,
        "starter": starter.starter_id,
        "profile": profile.profile_id,
        "mode": generation_mode,
    }


def public_artifact_id(
    snapshot: ReleaseSnapshot,
    starter: StarterDefinition,
    profile: CompositionProfile,
    generation_mode: str,
) -> str:
    payload = json.dumps(
        public_artifact_payload(snapshot, starter, profile, generation_mode),
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()[:16]


def public_artifact_download_path(catalog_version: str, artifact_id: str) -> str:
    return f"/api/public/download/{catalog_version}/{artifact_id}"


def public_artifact_paths(
    artifact_root: Path,
    catalog_version: str,
    artifact_id: str,
) -> tuple[Path, Path]:
    version_root = artifact_root / catalog_version
    return (
        version_root / f"{artifact_id}.zip",
        version_root / f"{artifact_id}.json",
    )


def generate_public_artifact(
    snapshot: ReleaseSnapshot,
    starter: StarterDefinition,
    profile: CompositionProfile,
    generation_mode: str,
    *,
    artifact_root: Path = DEFAULT_PUBLIC_ARTIFACT_ROOT,
) -> dict[str, Any]:
    artifact_id = public_artifact_id(snapshot, starter, profile, generation_mode)
    zip_path, metadata_path = public_artifact_paths(
        artifact_root,
        snapshot.catalog_version,
        artifact_id,
    )
    if metadata_path.exists() and zip_path.exists():
        metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
        metadata["cached"] = True
        return metadata

    stable_stamp = public_artifact_payload(snapshot, starter, profile, generation_mode)
    stable_stamp["artifact_id"] = artifact_id

    artifact_root.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="public-starter-", dir=artifact_root) as temp_dir:
        workspace = Path(temp_dir) / "workspace"
        generate_workspace(starter, profile, workspace, generation_mode, force=True)
        write_json(workspace / ".polyglot-starter-artifact.json", stable_stamp)
        create_deterministic_zip(workspace, zip_path)

    metadata = {
        **stable_stamp,
        "download_url": public_artifact_download_path(snapshot.catalog_version, artifact_id),
        "sha256": sha256_file(zip_path),
        "size_bytes": zip_path.stat().st_size,
        "cached": False,
    }
    write_json(metadata_path, metadata)
    return metadata


def command_result(command: str, workdir: Path) -> dict[str, Any]:
    args = shlex.split(command)
    subprocess.run(args, cwd=workdir, check=True, text=True)
    return {"command": command, "status": "passed"}


def scenario_result(starter: StarterDefinition, scenario_id: str, workdir: Path) -> dict[str, Any]:
    script_path = workdir / "scripts" / "run_scenario.py"
    scenario_path = workdir / "scenarios" / f"{scenario_id}.json"
    json_output = workdir / ".artifacts" / "scenarios" / f"{scenario_id}.json"
    markdown_output = workdir / ".artifacts" / "scenarios" / f"{scenario_id}.md"
    args = [
        sys.executable,
        str(script_path),
        "--workspace-root",
        str(workdir),
        "--scenario",
        str(scenario_path),
        "--json-output",
        str(json_output),
        "--markdown-output",
        str(markdown_output),
    ]
    subprocess.run(args, cwd=workdir, check=True, text=True)
    return {
        "scenario": scenario_id,
        "status": "passed",
        "json_output": str(json_output),
        "markdown_output": str(markdown_output),
    }


def published_image_result(
    starter: StarterDefinition,
    profile: CompositionProfile,
    workdir: Path,
) -> dict[str, Any]:
    if Path("/.dockerenv").exists() or Path("/run/.containerenv").exists():
        subprocess.run(
            ["bash", str(ROOT / "scripts" / "start_docker_daemon.sh")],
            cwd=ROOT,
            check=True,
            text=True,
            env=os.environ.copy(),
        )
    image = proof_image_ref(starter)
    script_path = ROOT / "scripts" / "smoke_test_published_starter.sh"
    args = [
        "bash",
        str(script_path),
        "--image",
        image,
        "--workspace",
        str(workdir),
    ]
    if profile.proof_scenarios:
        args.append("--run-scenarios")
    subprocess.run(args, cwd=ROOT, check=True, text=True)
    return {"image": image, "status": "passed"}


def required_paths_for_mode(starter: StarterDefinition, generation_mode: str) -> list[str]:
    if generation_mode == "source-template":
        return list(starter.proof_paths)
    if generation_mode == "published-image-bootstrap":
        filtered = [path for path in starter.proof_paths if path != ".polyglot-starter.json"]
        return [
            ".devcontainer/devcontainer.json",
            ".devcontainer/.polyglot-starter-request.json",
            ".polyglot-bootstrap.json",
            *filtered,
        ]
    raise SystemExit(f"unsupported generation mode: {generation_mode}")


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
        f"- composition profile: `{result['composition_profile']}`",
        f"- workspace: `{result['workspace']}`",
        f"- status: `{result['status']}`",
        "",
        "## Runtime Guidance",
        "",
    ]

    for page in result.get("runtime_guidance", []):
        lines.append(f"- `man {page}`")

    lines.extend(["", "## Selected Composition", ""])
    if result.get("selected_features"):
        lines.append(f"- features: `{', '.join(result['selected_features'])}`")
    else:
        lines.append("- features: `none`")
    if result.get("selected_scenarios"):
        lines.append(f"- scenarios: `{', '.join(result['selected_scenarios'])}`")
    else:
        lines.append("- scenarios: `none`")
    if result.get("proof_scenarios"):
        lines.append(f"- proof scenarios: `{', '.join(result['proof_scenarios'])}`")
    else:
        lines.append("- proof scenarios: `none`")

    lines.extend(["", "## Commands", ""])
    for command in result.get("commands", []):
        lines.append(f"- `{command['command']}`: `{command['status']}`")

    published_image = result.get("published_image_result")
    if published_image:
        lines.extend(["", "## Published Image", ""])
        lines.append(f"- `{published_image['image']}`: `{published_image['status']}`")

    lines.extend(["", "## Required Paths", ""])
    for path_result in result.get("path_results", []):
        lines.append(f"- `{path_result['path']}`: `{path_result['status']}`")

    lines.extend(["", "## Scenario Proofs", ""])
    for scenario in result.get("scenario_results", []):
        lines.append(f"- `{scenario['scenario']}`: `{scenario['status']}`")

    if result.get("failure"):
        lines.extend(["", "## Failure", "", result["failure"]])

    return lines


def write_markdown(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(markdown_lines(payload)) + "\n", encoding="utf-8")


def prove_starter(
    starter: StarterDefinition,
    profile: CompositionProfile,
    generation_mode: str,
    *,
    workspace_root: Path,
    report_root: Path,
) -> int:
    workspace = workspace_root / generation_mode / starter.starter_id / profile.profile_id
    workspace.parent.mkdir(parents=True, exist_ok=True)
    generate_workspace(starter, profile, workspace, generation_mode, force=True)

    result: dict[str, Any] = {
        "starter_id": starter.starter_id,
        "title": starter.title,
        "generation_mode": generation_mode,
        "composition_profile": profile.profile_id,
        "selected_features": profile.features,
        "selected_scenarios": profile.scenarios,
        "proof_scenarios": profile.proof_scenarios,
        "workspace": str(workspace),
        "runtime_guidance": starter.runtime_guidance,
        "commands": [],
        "path_results": [],
        "scenario_results": [],
        "published_image_result": None,
        "status": "passed",
    }

    try:
        if generation_mode == "published-image-bootstrap":
            result["published_image_result"] = published_image_result(starter, profile, workspace)
        else:
            for command in starter.proof_commands:
                result["commands"].append(command_result(command, workspace))
            for scenario_id in profile.proof_scenarios:
                result["scenario_results"].append(scenario_result(starter, scenario_id, workspace))
        for relative_path in required_paths_for_mode(starter, generation_mode):
            result["path_results"].append(check_required_path(workspace, relative_path))
        if any(path_result["status"] != "passed" for path_result in result["path_results"]):
            result["status"] = "failed"
            result["failure"] = "one or more required paths were not created"
    except subprocess.CalledProcessError as error:
        result["status"] = "failed"
        result["failure"] = f"command failed: {' '.join(error.cmd)}"

    json_output = report_root / generation_mode / starter.starter_id / profile.profile_id / "proof.json"
    markdown_output = report_root / generation_mode / starter.starter_id / profile.profile_id / "proof.md"
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
    show_parser.add_argument("--profile")

    generate_parser = subparsers.add_parser("generate")
    generate_parser.add_argument("--starter", required=True)
    generate_parser.add_argument("--output", type=Path, required=True)
    generate_parser.add_argument("--mode")
    generate_parser.add_argument("--profile")
    generate_parser.add_argument("--force", action="store_true")

    export_parser = subparsers.add_parser("export-release")
    export_parser.add_argument("--version", required=True)
    export_parser.add_argument("--release-root", type=Path, default=DEFAULT_RELEASE_ROOT)

    prove_parser = subparsers.add_parser("prove")
    prove_target = prove_parser.add_mutually_exclusive_group(required=True)
    prove_target.add_argument("--starter")
    prove_target.add_argument("--all", action="store_true")
    prove_parser.add_argument("--mode")
    prove_parser.add_argument("--profile")
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
                f"profile={starter.default_profile} template={starter.source_template}",
                flush=True,
            )
        return 0

    if args.command == "show":
        starter = require_starter(definitions, args.starter)
        profile = resolve_profile(starter, args.profile)
        payload = serialize_starter(starter)
        payload["resolved_profile"] = asdict(profile)
        print(json.dumps(payload, indent=2))
        return 0

    if args.command == "generate":
        starter = require_starter(definitions, args.starter)
        generation_mode = ensure_generation_mode(starter, args.mode)
        profile = resolve_profile(starter, args.profile)
        output_path = args.output if args.output.is_absolute() else (ROOT / args.output)
        workspace = generate_workspace(
            starter,
            profile,
            output_path,
            generation_mode,
            force=args.force,
        )
        print(
            "[starter-generate] "
            f"starter={starter.starter_id} mode={generation_mode} "
            f"profile={profile.profile_id} output={workspace}",
            flush=True,
        )
        return 0

    if args.command == "export-release":
        release_root = args.release_root if args.release_root.is_absolute() else ROOT / args.release_root
        snapshot = export_release_snapshot(
            definitions,
            args.version,
            release_root=release_root,
        )
        print(
            "[starter-release] "
            f"version={snapshot.catalog_version} git_sha={snapshot.source_git_sha} "
            f"catalog={snapshot.catalog_path}",
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
            profile = resolve_profile(starter, args.profile)
            current_exit = prove_starter(
                starter,
                profile,
                generation_mode,
                workspace_root=args.workspace_root if args.workspace_root.is_absolute() else ROOT / args.workspace_root,
                report_root=args.report_root if args.report_root.is_absolute() else ROOT / args.report_root,
            )
            exit_code = max(exit_code, current_exit)
        return exit_code

    raise SystemExit(f"unsupported command: {args.command}")


if __name__ == "__main__":
    raise SystemExit(main())
