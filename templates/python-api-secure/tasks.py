"""Task automation for python-api-secure scenario.

TODO: Code Duplication Technical Debt
======================================
This file (~866 lines) is duplicated across all Python scenarios.

Current state:
- python-api-secure/tasks.py - 866 lines
- python-secure/tasks.py - 866 lines
- Total duplication: ~1,732 lines

Decision: Wait until 5+ scenarios exist, then refactor to shared package.

Refactoring plan (when threshold reached):
1. Create packages/polyglot-tasks/ shared package
2. Implement unified task verb system (check/fix pairs)
3. Create bundling script for standalone distribution
4. Migrate scenarios incrementally

See KB-2026-009 "Code Duplication vs Portability Trade-Off" for full analysis.

Monitoring signals:
- Bug fixes applied multiple times
- Feature additions require N updates
- 5+ scenarios exist

When 2+ signals present: Time to refactor.
"""

from __future__ import annotations

import json
import os
import re
import shlex
import shutil
import subprocess
import sys
import tomllib
import urllib.request
from datetime import datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent
TMP_DIR = ROOT / ".tmp"
ARTIFACTS_DIR = ROOT / ".artifacts"
SCANS_DIR = ARTIFACTS_DIR / "scans"
try:
    REPO_ROOT = next(
        parent for parent in Path(__file__).resolve().parents if (parent / "AGENTS.md").exists()
    )
except StopIteration:
    # Fallback for standalone usage: use template directory as root
    REPO_ROOT = ROOT
PYTHON_AUDIT_POLICY = REPO_ROOT / "security-scan-policy.toml"
PYTHON_AUDIT_EVALUATOR = REPO_ROOT / "scripts" / "evaluate_python_audit_policy.py"
VENV_DIR = ROOT / ".venv"
PYTHON = VENV_DIR / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
UV = "uv.exe" if os.name == "nt" else "uv"
PYPROJECT = ROOT / "pyproject.toml"
UV_LOCK = ROOT / "uv.lock"
LOCKFILE_CANDIDATES = ("uv.lock", "poetry.lock", "Pipfile.lock", "pdm.lock")
IGNORED_SEARCH_PARTS = {
    ".artifacts",
    ".git",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    ".tmp",
    ".venv",
    "build",
    "dist",
    "node_modules",
}
DEPENDENCY_NAME_RE = re.compile(r"^\s*([A-Za-z0-9][A-Za-z0-9._-]*)")
EXACT_PIN_RE = re.compile(r"^\s*([A-Za-z0-9][A-Za-z0-9._-]*)(?:\[[^\]]+\])?\s*==\s*([^,;\s]+)")
DECLARED_REQUIREMENT_RE = re.compile(r"^\s*([A-Za-z0-9][A-Za-z0-9._-]*(?:\[[^\]]+\])?)")
ANSI_ESCAPE_RE = re.compile(r"\x1b\[[0-9;]*[A-Za-z]")
MINIMUM_VERSION_RE = re.compile(r">=\s*(\d+(?:\.\d+)*)")
NORMALIZED_NAME_RE = re.compile(r"[-_.]+")
PYPI_PACKAGE_INFO_CACHE: dict[str, dict[str, Any]] = {}
UPDATE_PRIORITY = {"none": 0, "patch": 1, "minor": 2, "major": 3}
CANDIDATE_PRIORITY = {"direct": 0, "transitive-parent": 1}


def run(
    command: list[str], *, capture_output: bool = False, check: bool = True
) -> subprocess.CompletedProcess[str]:
    TMP_DIR.mkdir(exist_ok=True)
    SCANS_DIR.mkdir(parents=True, exist_ok=True)
    env = os.environ.copy()
    env["TMP"] = str(TMP_DIR.resolve())
    env["TEMP"] = str(TMP_DIR.resolve())
    env["TMPDIR"] = str(TMP_DIR.resolve())
    return subprocess.run(
        command, cwd=ROOT, check=check, text=True, env=env, capture_output=capture_output
    )


def reset_invalid_venv() -> None:
    if VENV_DIR.exists() and not PYTHON.exists():
        shutil.rmtree(VENV_DIR)


def read_project_metadata() -> dict[str, Any]:
    return tomllib.loads(PYPROJECT.read_text(encoding="utf-8"))


def project_requires_python() -> str | None:
    metadata = read_project_metadata()
    project = metadata.get("project", {})
    requires_python = project.get("requires-python")
    return str(requires_python) if requires_python else None


def version_parts(version: str) -> list[int]:
    return [int(part) for part in re.findall(r"\d+", version)]


def classify_update(current_version: str, latest_version: str) -> str:
    current_parts = version_parts(current_version)
    latest_parts = version_parts(latest_version)
    for index, label in enumerate(("major", "minor", "patch")):
        current_part = current_parts[index] if len(current_parts) > index else 0
        latest_part = latest_parts[index] if len(latest_parts) > index else 0
        if current_part != latest_part:
            return label
    return "none"


def parse_minimum_version(specifier: str | None) -> tuple[int, ...] | None:
    if not specifier:
        return None
    match = MINIMUM_VERSION_RE.search(specifier)
    if not match:
        return None
    return tuple(int(part) for part in match.group(1).split("."))


def format_version_tuple(version: tuple[int, ...]) -> str:
    return ".".join(str(part) for part in version)


def iter_declared_dependencies() -> list[dict[str, str]]:
    metadata = read_project_metadata()
    project = metadata.get("project", {})
    dependencies: list[dict[str, str]] = []

    for dependency in project.get("dependencies", []):
        dependencies.append({"scope": "runtime", "specifier": dependency, "declaration": "runtime"})

    for scope, scoped_dependencies in project.get("optional-dependencies", {}).items():
        for dependency in scoped_dependencies:
            dependencies.append(
                {"scope": scope, "specifier": dependency, "declaration": "optional"}
            )

    for scope, scoped_dependencies in metadata.get("dependency-groups", {}).items():
        for dependency in scoped_dependencies:
            if isinstance(dependency, str):
                dependencies.append(
                    {"scope": scope, "specifier": dependency, "declaration": "group"}
                )

    return dependencies


def parse_exact_pin(specifier: str) -> tuple[str, str | None]:
    exact_match = EXACT_PIN_RE.match(specifier)
    if exact_match:
        return exact_match.group(1), exact_match.group(2)

    name_match = DEPENDENCY_NAME_RE.match(specifier)
    if name_match:
        return name_match.group(1), None

    return specifier.strip(), None


def normalize_dependency_name(name: str) -> str:
    return NORMALIZED_NAME_RE.sub("-", name).lower()


def build_declared_dependency_index() -> dict[str, list[dict[str, str]]]:
    dependency_index: dict[str, list[dict[str, str]]] = {}
    for dependency in iter_declared_dependencies():
        name, _ = parse_exact_pin(dependency["specifier"])
        normalized_name = normalize_dependency_name(name)
        dependency_index.setdefault(normalized_name, []).append(dependency)
    return dependency_index


def build_fix_requirement(specifier: str, fix_version: str) -> str:
    base_specifier, separator, marker = specifier.partition(";")
    match = DECLARED_REQUIREMENT_RE.match(base_specifier)
    if not match:
        raise ValueError(f"Unsupported dependency specifier: {specifier}")

    _, exact_pin = parse_exact_pin(base_specifier)
    operator = "==" if exact_pin is not None else ">="
    updated_specifier = f"{match.group(1)}{operator}{fix_version}"

    if separator and marker.strip():
        return f"{updated_specifier}; {marker.strip()}"
    return updated_specifier


def build_uv_add_command(dependency: dict[str, str], requirement: str) -> list[str]:
    command = [UV, "add"]
    declaration = dependency.get("declaration")
    scope = dependency.get("scope")
    if declaration == "optional" and scope:
        command.extend(["--optional", scope])
    elif declaration == "group" and scope:
        command.extend(["--group", scope])
    command.append(requirement)
    return command


def write_json_artifact(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def write_markdown_artifact(path: Path, content: str) -> None:
    path.write_text(content.rstrip() + "\n", encoding="utf-8")


def print_status(message: str) -> None:
    print(f"[python-deps] {message}", flush=True)


def version_sort_key(version: str) -> tuple[int, ...]:
    return tuple(version_parts(version))


def choose_fix_version(vulnerabilities: list[dict[str, Any]]) -> str | None:
    fix_versions = [
        str(version)
        for vulnerability in vulnerabilities
        for version in vulnerability.get("fix_versions", [])
    ]
    if not fix_versions:
        return None
    return max(fix_versions, key=version_sort_key)


def extract_vulnerability_ids(vulnerabilities: list[dict[str, Any]]) -> list[str]:
    seen: set[str] = set()
    vulnerability_ids: list[str] = []
    for vulnerability in vulnerabilities:
        advisory_id = str(vulnerability.get("id", "")).strip()
        if not advisory_id or advisory_id in seen:
            continue
        seen.add(advisory_id)
        vulnerability_ids.append(advisory_id)
    return vulnerability_ids


def summarize_audit_dependencies(audit_dependencies: list[dict[str, Any]]) -> dict[str, Any]:
    packages = []
    vulnerability_count = 0
    for dependency in audit_dependencies:
        vulnerabilities = list(dependency.get("vulns", []))
        if not vulnerabilities:
            continue
        vulnerability_ids = extract_vulnerability_ids(vulnerabilities)
        vulnerability_count += len(vulnerability_ids)
        packages.append(
            {
                "name": str(dependency.get("name", "unknown")),
                "version": str(dependency.get("version", "unknown")),
                "vulnerability_ids": vulnerability_ids,
            }
        )
    return {
        "vulnerable_package_count": len(packages),
        "vulnerability_count": vulnerability_count,
        "packages": packages,
    }


def load_remediation_policy() -> dict[str, Any]:
    policy = tomllib.loads(PYTHON_AUDIT_POLICY.read_text(encoding="utf-8"))
    section = policy.get("python_package_remediation", {})
    pr_section = section.get("pr", {})
    maximum_update_type = str(section.get("maximum_update_type", "minor")).lower()
    if maximum_update_type not in UPDATE_PRIORITY:
        maximum_update_type = "minor"

    allowed_scopes = [str(scope) for scope in section.get("allowed_scopes", ["runtime", "dev"])]
    if not allowed_scopes:
        allowed_scopes = ["runtime", "dev"]

    return {
        "allowed_scopes": allowed_scopes,
        "maximum_update_type": maximum_update_type,
        "allow_exact_pin_updates": bool(section.get("allow_exact_pin_updates", True)),
        "allow_transitive_parent_remediation": bool(
            section.get("allow_transitive_parent_remediation", True)
        ),
        "pr": {
            "branch_prefix": str(pr_section.get("branch_prefix", "codex/scan-remediation")),
            "commit_message": str(
                pr_section.get("commit_message", "chore(deps): remediate Python CVEs")
            ),
            "push_branch": bool(pr_section.get("push_branch", False)),
            "open_pull_request": bool(pr_section.get("open_pull_request", False)),
            "base_branch": str(pr_section.get("base_branch", "main")),
            "pull_request_title": str(
                pr_section.get(
                    "pull_request_title", "chore(deps): automated Python CVE remediation"
                )
            ),
        },
    }


def update_type_allowed(update_type: str, maximum_update_type: str) -> bool:
    return (
        UPDATE_PRIORITY.get(update_type, UPDATE_PRIORITY["major"])
        <= UPDATE_PRIORITY[maximum_update_type]
    )


def candidate_sort_key(candidate: dict[str, Any]) -> tuple[int, int, str, str]:
    return (
        CANDIDATE_PRIORITY.get(candidate.get("target_type", ""), len(CANDIDATE_PRIORITY)),
        UPDATE_PRIORITY.get(candidate.get("update_type", "major"), UPDATE_PRIORITY["major"]),
        str(candidate.get("target_dependency_name", "")),
        str(candidate.get("package_name", "")),
    )


def find_matching_files(pattern: str) -> list[str]:
    matches = []
    for path in ROOT.rglob(pattern):
        if any(part in IGNORED_SEARCH_PARTS for part in path.parts):
            continue
        matches.append(str(path.relative_to(ROOT)))
    return sorted(matches)


def read_uv_lock_metadata() -> dict[str, Any]:
    return tomllib.loads(UV_LOCK.read_text(encoding="utf-8"))


def iter_uv_locked_dependencies() -> list[dict[str, Any]]:
    dependencies = []

    for package in read_uv_lock_metadata().get("package", []):
        if not isinstance(package, dict):
            continue
        name = str(package.get("name", ""))
        version = str(package.get("version", ""))
        source = package.get("source", {})
        dependencies.append(
            {
                "name": name,
                "scope": "locked",
                "specifier": f"{name}=={version}",
                "current_version": version,
                "exact_pin": True,
                "source": source.get("registry") if isinstance(source, dict) else None,
            }
        )

    return dependencies


def build_uv_package_map() -> dict[str, dict[str, Any]]:
    return {dependency["name"]: dependency for dependency in iter_uv_locked_dependencies()}


def build_normalized_uv_package_map() -> dict[str, dict[str, Any]]:
    return {
        normalize_dependency_name(dependency["name"]): dependency
        for dependency in iter_uv_locked_dependencies()
    }


def iter_package_dependency_names(package: dict[str, Any]) -> list[str]:
    dependencies: list[str] = []

    def extend_from_values(values: Any) -> None:
        if not isinstance(values, list):
            return
        for entry in values:
            if not isinstance(entry, dict) or "name" not in entry:
                continue
            dependencies.append(normalize_dependency_name(str(entry["name"])))

    extend_from_values(package.get("dependencies"))

    optional_dependencies = package.get("optional-dependencies", {})
    if isinstance(optional_dependencies, dict):
        for values in optional_dependencies.values():
            extend_from_values(values)

    dev_dependencies = package.get("dev-dependencies", {})
    if isinstance(dev_dependencies, dict):
        for values in dev_dependencies.values():
            extend_from_values(values)

    return dependencies


def build_uv_dependency_graph() -> dict[str, set[str]]:
    graph: dict[str, set[str]] = {}
    for package in read_uv_lock_metadata().get("package", []):
        if not isinstance(package, dict):
            continue
        package_name = normalize_dependency_name(str(package.get("name", "")))
        if not package_name:
            continue
        graph[package_name] = set(iter_package_dependency_names(package))
    return graph


def build_transitive_root_index() -> dict[str, list[dict[str, str]]]:
    graph = build_uv_dependency_graph()
    root_index: dict[str, list[dict[str, str]]] = {}
    for direct_dependency in iter_declared_dependencies():
        name, _ = parse_exact_pin(direct_dependency["specifier"])
        root_name = normalize_dependency_name(name)
        queue = sorted(graph.get(root_name, set()))
        visited: set[str] = set()

        while queue:
            current = queue.pop(0)
            if current in visited or current == root_name:
                continue
            visited.add(current)
            root_index.setdefault(current, []).append(direct_dependency)
            queue.extend(sorted(graph.get(current, set()) - visited))

    return root_index


def classify_uv_blocker(message: str) -> str:
    lowered = message.lower()
    if "rust and cargo" in lowered:
        return "build-environment-missing"
    if "name is shadowed by your project" in lowered or "depends on your project" in lowered:
        return "workspace-shadowing"
    return "native-command-failed"


def summarize_uv_error(message: str) -> str:
    for line in message.splitlines():
        stripped = ANSI_ESCAPE_RE.sub("", line).strip()
        if not stripped:
            continue
        lowered = stripped.lower()
        if lowered.startswith("using cpython"):
            continue
        if lowered.startswith("uv :"):
            continue
        if lowered.startswith("at line:"):
            continue
        if lowered.startswith("+ "):
            continue
        if lowered.startswith("categoryinfo"):
            continue
        if lowered.startswith("fullyqualifiederrorid"):
            continue
        if stripped.startswith("Resolved ") or stripped.startswith("Audited "):
            continue
        if "depends on your project" in lowered:
            return stripped
        if "name is shadowed by your project" in lowered:
            return stripped
        if "requires rust and cargo" in lowered:
            return stripped
        if "cargo, the rust package manager" in lowered:
            return stripped
        return stripped
    return message.splitlines()[0] if message else ""


def build_uv_blocker(command: list[str], error: subprocess.CalledProcessError) -> dict[str, Any]:
    stderr = (error.stderr or "").strip()
    stdout = (error.stdout or "").strip()
    message = stderr or stdout or str(error)
    return {
        "tool": "uv",
        "command": " ".join(command),
        "kind": classify_uv_blocker(message),
        "message": summarize_uv_error(message) or str(error),
    }


def build_uv_plan_dependencies() -> tuple[list[dict[str, Any]], dict[str, Any] | None]:
    original_lock = UV_LOCK.read_text(encoding="utf-8")
    current_dependencies = build_uv_package_map()
    try:
        run(["uv", "lock", "--upgrade"], capture_output=True)
    except subprocess.CalledProcessError as error:
        UV_LOCK.write_text(original_lock, encoding="utf-8")
        dependencies = []
        for name, dependency in current_dependencies.items():
            dependencies.append(
                {
                    "name": name,
                    "scope": dependency["scope"],
                    "specifier": dependency["specifier"],
                    "current_version": dependency["current_version"],
                    "latest_version": None,
                    "update_type": "native-command-failed",
                    "will_update": False,
                }
            )
        return dependencies, build_uv_blocker(["uv", "lock", "--upgrade"], error)

    upgraded_dependencies = build_uv_package_map()
    UV_LOCK.write_text(original_lock, encoding="utf-8")

    dependencies = []
    for name, dependency in current_dependencies.items():
        latest_version = upgraded_dependencies.get(name, dependency)["current_version"]
        current_version = dependency["current_version"]
        dependencies.append(
            {
                "name": name,
                "scope": dependency["scope"],
                "specifier": dependency["specifier"],
                "current_version": current_version,
                "latest_version": latest_version,
                "update_type": classify_update(current_version, latest_version),
                "will_update": current_version != latest_version,
            }
        )

    return dependencies, None


def ensure_venv() -> None:
    reset_invalid_venv()
    if not PYTHON.exists():
        run([UV, "sync", "--frozen", "--extra", "dev"])


def ensure_piptools() -> None:
    ensure_venv()
    run([str(PYTHON), "-m", "pip", "install", "--upgrade", "pip==26.0.1"])
    run([str(PYTHON), "-m", "pip", "install", "pip-tools==7.5.1"])


def requirement_lines(path: Path) -> list[str]:
    entries = []
    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        entries.append(stripped)
    return entries


def parse_compiled_requirements(path: Path) -> dict[str, str]:
    compiled = {}
    pattern = re.compile(r"^([A-Za-z0-9_.-]+)==([^ ;]+)")
    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or stripped.startswith("--"):
            continue
        match = pattern.match(stripped)
        if match:
            compiled[match.group(1).lower()] = match.group(2)
    return compiled


def pip_tools_targets() -> list[dict[str, Any]]:
    targets = []
    for relative_source in find_matching_files("requirements*.in"):
        source_path = ROOT / relative_source
        default_target = source_path.with_suffix(".txt")
        targets.append(
            {
                "source": source_path,
                "source_rel": relative_source,
                "target": default_target,
                "target_rel": str(default_target.relative_to(ROOT)),
                "target_exists": default_target.exists(),
            }
        )
    return targets


def compile_requirements(source_path: Path, output_path: Path, upgrade: bool) -> None:
    ensure_piptools()
    command = [
        str(PYTHON),
        "-m",
        "piptools",
        "compile",
        str(source_path),
        "--output-file",
        str(output_path),
    ]
    if upgrade:
        command.append("--upgrade")
    run(command)


def build_pip_tools_inventory() -> list[dict[str, Any]]:
    dependencies = []
    for target in pip_tools_targets():
        compiled_versions = (
            parse_compiled_requirements(target["target"]) if target["target_exists"] else {}
        )
        for specifier in requirement_lines(target["source"]):
            name, version = parse_exact_pin(specifier)
            dependencies.append(
                {
                    "name": name,
                    "scope": target["source_rel"],
                    "specifier": specifier,
                    "current_version": compiled_versions.get(name.lower(), version),
                    "exact_pin": version is not None,
                    "compiled_target": target["target_rel"],
                    "compiled_target_exists": target["target_exists"],
                }
            )
    return dependencies


def build_pip_tools_plan() -> list[dict[str, Any]]:
    dependencies = []
    for target in pip_tools_targets():
        preview_path = SCANS_DIR / f"{target['source'].stem}.preview.txt"
        compile_requirements(target["source"], preview_path, upgrade=True)
        upgraded_versions = parse_compiled_requirements(preview_path)
        current_versions = (
            parse_compiled_requirements(target["target"]) if target["target_exists"] else {}
        )
        for specifier in requirement_lines(target["source"]):
            name, current_pin = parse_exact_pin(specifier)
            current_version = current_versions.get(name.lower(), current_pin)
            latest_version = upgraded_versions.get(name.lower(), current_version)
            dependencies.append(
                {
                    "name": name,
                    "scope": target["source_rel"],
                    "specifier": specifier,
                    "current_version": current_version,
                    "latest_version": latest_version,
                    "update_type": (
                        classify_update(current_version, latest_version)
                        if current_version is not None and latest_version is not None
                        else "compile-generated"
                    ),
                    "will_update": current_version != latest_version,
                    "compiled_target": target["target_rel"],
                    "compiled_target_exists": target["target_exists"],
                    "preview_file": str(preview_path.relative_to(ROOT)),
                }
            )
    return dependencies


def detect_python_strategy() -> dict[str, Any]:
    metadata = read_project_metadata()
    project = metadata.get("project", {})
    lock_files = [name for name in LOCKFILE_CANDIDATES if (ROOT / name).exists()]
    requirements_in = find_matching_files("requirements*.in")
    requirements_txt = find_matching_files("requirements*.txt")
    dependency_groups = metadata.get("dependency-groups", {})
    optional_dependencies = project.get("optional-dependencies", {})
    declared_dependencies = iter_declared_dependencies()
    exact_pins = sum(
        1
        for dependency in declared_dependencies
        if parse_exact_pin(dependency["specifier"])[1] is not None
    )

    if "uv.lock" in lock_files:
        strategy = "uv-lock"
        upgrade_command_candidates = ["uv lock --upgrade"]
    elif requirements_in:
        strategy = "pip-tools"
        upgrade_command_candidates = ["python -m piptools compile <requirements.in> --upgrade"]
    elif exact_pins > 0:
        strategy = "pyproject-exact-pins"
        upgrade_command_candidates = ["rewrite exact pins in pyproject.toml"]
    elif PYPROJECT.exists():
        strategy = "plain-pyproject"
        upgrade_command_candidates = []
    else:
        strategy = "unrecognized"
        upgrade_command_candidates = []

    return {
        "strategy": strategy,
        "manifest_files": [str(PYPROJECT.name)] if PYPROJECT.exists() else [],
        "lock_files": lock_files,
        "requirements_in_files": requirements_in,
        "requirements_txt_files": requirements_txt,
        "dependency_groups": sorted(dependency_groups.keys()),
        "optional_dependency_groups": sorted(optional_dependencies.keys()),
        "declared_dependency_count": len(declared_dependencies),
        "exact_pin_count": exact_pins,
        "upgrade_command_candidates": upgrade_command_candidates,
    }


def build_inventory_artifact() -> dict[str, Any]:
    strategy = detect_python_strategy()
    dependencies = []

    if strategy["strategy"] == "uv-lock":
        dependencies = iter_uv_locked_dependencies()
    elif strategy["strategy"] == "pip-tools":
        dependencies = build_pip_tools_inventory()
    else:
        for dependency in iter_declared_dependencies():
            name, version = parse_exact_pin(dependency["specifier"])
            dependencies.append(
                {
                    "name": name,
                    "scope": dependency["scope"],
                    "specifier": dependency["specifier"],
                    "current_version": version,
                    "exact_pin": version is not None,
                }
            )

    return {
        "ecosystem": "python",
        "source": str(PYPROJECT.name),
        "strategy_detection": strategy,
        "dependencies": dependencies,
    }


def build_plan_artifact() -> dict[str, Any]:
    inventory_artifact = build_inventory_artifact()
    strategy = inventory_artifact["strategy_detection"]["strategy"]
    project_python_specifier = project_requires_python()
    dependencies: list[dict[str, Any]] = []

    for dependency in inventory_artifact["dependencies"]:
        current_version = dependency["current_version"]
        latest_version = None
        update_type = "native-workflow-required"
        will_update = False

        if strategy == "uv-lock":
            dependencies, blocker = build_uv_plan_dependencies()
            artifact = {
                "ecosystem": "python",
                "source": str(PYPROJECT.name),
                "strategy_detection": inventory_artifact["strategy_detection"],
                "dependencies": dependencies,
            }
            if blocker is not None:
                artifact["blocked"] = blocker
            return artifact

        if strategy == "pip-tools":
            dependencies = build_pip_tools_plan()
            return {
                "ecosystem": "python",
                "source": str(PYPROJECT.name),
                "strategy_detection": inventory_artifact["strategy_detection"],
                "dependencies": dependencies,
            }

        if strategy == "pyproject-exact-pins" and current_version is not None:
            package_info = fetch_pypi_package_info(dependency["name"])
            latest_version = str(package_info["info"]["version"])
            update_type = classify_update(current_version, latest_version)
            python_compatibility = build_python_compatibility(
                project_specifier=project_python_specifier,
                package_name=dependency["name"],
                package_specifier=package_info["info"].get("requires_python"),
            )
            will_update = (
                current_version != latest_version
                and python_compatibility["status"] != "incompatible"
            )
        else:
            python_compatibility = None

        planned_dependency = {
            "name": dependency["name"],
            "scope": dependency["scope"],
            "specifier": dependency["specifier"],
            "current_version": current_version,
            "latest_version": latest_version,
            "update_type": update_type,
            "will_update": will_update,
        }
        if python_compatibility is not None:
            planned_dependency["python_compatibility"] = python_compatibility
        dependencies.append(planned_dependency)

    return {
        "ecosystem": "python",
        "source": str(PYPROJECT.name),
        "strategy_detection": inventory_artifact["strategy_detection"],
        "dependencies": dependencies,
    }


def sync_dev_environment() -> None:
    run([UV, "sync", "--frozen", "--extra", "dev"])


def run_pip_audit() -> Path:
    audit_report = SCANS_DIR / "pip-audit.json"
    audit_report.unlink(missing_ok=True)
    completed = run(
        [
            str(PYTHON),
            "-m",
            "pip_audit",
            "--format",
            "json",
            "--output",
            str(audit_report),
        ],
        check=False,
    )
    if completed.returncode not in (0, 1):
        raise subprocess.CalledProcessError(completed.returncode, completed.args)
    if not audit_report.exists():
        raise RuntimeError(
            "pip-audit did not produce a report. Re-run `task init` to restore the dev environment."
        )
    return audit_report


def load_audit_dependencies() -> tuple[Path, list[dict[str, Any]]]:
    audit_report = run_pip_audit()
    with audit_report.open(encoding="utf-8") as handle:
        audit_data = json.load(handle)
    return audit_report, list(audit_data.get("dependencies", []))


def backup_project_state() -> dict[Path, Path]:
    backups: dict[Path, Path] = {}
    for path in (PYPROJECT, UV_LOCK):
        if not path.exists():
            continue
        backup_path = ROOT / f".{path.name}.scan-fix.backup"
        shutil.copy2(path, backup_path)
        backups[path] = backup_path
    return backups


def cleanup_project_backups(backups: dict[Path, Path]) -> None:
    for backup_path in backups.values():
        backup_path.unlink(missing_ok=True)


def restore_project_state(backups: dict[Path, Path]) -> None:
    for original_path, backup_path in backups.items():
        if backup_path.exists():
            shutil.copy2(backup_path, original_path)
    cleanup_project_backups(backups)
    sync_dev_environment()


def run_verification_tests() -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    env.pop("TMP", None)
    env.pop("TEMP", None)
    env.pop("TMPDIR", None)
    return subprocess.run(
        [str(PYTHON), "-m", "pytest", "-q", "-x", "-m", "not integration", "tests"],
        cwd=ROOT,
        check=False,
        text=True,
        env=env,
    )


def evaluate_python_audit_policy(
    audit_report: Path, *, check: bool = True
) -> subprocess.CompletedProcess[str]:
    return run(
        [
            sys.executable,
            str(PYTHON_AUDIT_EVALUATOR),
            "--audit-report",
            str(audit_report),
            "--policy",
            str(PYTHON_AUDIT_POLICY),
            "--json-output",
            str(SCANS_DIR / "pip-audit-policy.json"),
            "--markdown-output",
            str(SCANS_DIR / "pip-audit-policy.md"),
        ],
        check=check,
    )


def run_git_command(
    args: list[str], *, capture_output: bool = False, check: bool = True
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args],
        cwd=ROOT,
        check=check,
        text=True,
        capture_output=capture_output,
    )


def git_worktree_is_clean() -> bool:
    completed = run_git_command(["status", "--porcelain"], capture_output=True)
    return not completed.stdout.strip()


def current_git_branch() -> str:
    completed = run_git_command(["branch", "--show-current"], capture_output=True)
    branch_name = completed.stdout.strip()
    return branch_name or "HEAD"


def tracked_git_changes() -> str:
    completed = run_git_command(
        ["status", "--porcelain", "--untracked-files=no"], capture_output=True
    )
    return completed.stdout.strip()


def unique_scan_pr_branch_name(prefix: str) -> str:
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    candidate = f"{prefix}-{ROOT.name}-{timestamp}"
    while True:
        completed = run_git_command(
            ["show-ref", "--verify", "--quiet", f"refs/heads/{candidate}"], check=False
        )
        if completed.returncode != 0:
            return candidate
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        candidate = f"{prefix}-{ROOT.name}-{timestamp}"


def build_scan_pr_body(report: dict[str, Any]) -> str:
    accepted = report["summary"]["accepted"]
    rolled_back = report["summary"]["rolled_back"]
    remaining = report["summary"]["remaining_vulnerability_ids"]
    lines = [
        "## Automated Python remediation",
        "",
        f"- accepted fixes: `{accepted}`",
        f"- rolled back fixes: `{rolled_back}`",
        f"- remaining vulnerability ids: `{remaining}`",
        "",
        "Generated by `task scan:pr`.",
    ]
    return "\n".join(lines)


def open_pull_request_with_gh(
    *, title: str, body: str, base_branch: str, head_branch: str
) -> str | None:
    gh_check = subprocess.run(
        ["gh", "--version"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    if gh_check.returncode != 0:
        return None

    completed = subprocess.run(
        [
            "gh",
            "pr",
            "create",
            "--base",
            base_branch,
            "--head",
            head_branch,
            "--title",
            title,
            "--body",
            body,
        ],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    if completed.returncode != 0:
        raise SystemExit(
            "scan:pr created a remediation branch and commit, but `gh pr create` failed:\n"
            f"{completed.stderr.strip() or completed.stdout.strip()}"
        )

    pr_url = completed.stdout.strip().splitlines()[-1].strip()
    return pr_url or None


def init() -> None:
    reset_invalid_venv()
    sync_dev_environment()


def lint() -> None:
    if not PYTHON.exists():
        init()
    run([str(PYTHON), "-m", "ruff", "check", "src", "tests", "tasks.py"])
    run([str(PYTHON), "-m", "ruff", "format", "--check", "src", "tests", "tasks.py"])
    run([str(PYTHON), "-m", "mypy", "src", "tests", "tasks.py"])


def format_code() -> None:
    if not PYTHON.exists():
        init()
    run([str(PYTHON), "-m", "ruff", "check", "--fix", "src", "tests", "tasks.py"])
    run([str(PYTHON), "-m", "ruff", "format", "src", "tests", "tasks.py"])


def run_pytest_suite(*paths: str, marker: str | None = None) -> None:
    if not PYTHON.exists():
        init()

    command = [str(PYTHON), "-m", "pytest", "-q", "-s"]
    if marker is not None:
        command.extend(["-m", marker])
    command.extend(paths)
    run(command)


def test() -> None:
    """Full automated test suite."""
    run_pytest_suite("tests")


def test_fast() -> None:
    """Fast feedback suite for inner-loop work."""
    run_pytest_suite("tests/unit", "tests/property")


def test_unit() -> None:
    """Unit tests only."""
    run_pytest_suite("tests/unit")


def test_acceptance() -> None:
    """Executable specification and BDD tests."""
    run_pytest_suite("tests/acceptance", marker="acceptance")


def test_property() -> None:
    """Property-based tests."""
    run_pytest_suite("tests/property", marker="property")


def test_integration() -> None:
    """Live integration tests only."""
    run_pytest_suite("tests/integration", marker="integration")


def test_all() -> None:
    """Alias for the full suite."""
    test()


def scan() -> None:
    if not PYTHON.exists():
        init()
    audit_report = run_pip_audit()
    evaluate_python_audit_policy(audit_report)


def scan_fix() -> None:
    """Interactive security vulnerability fix workflow (Phase 1).

    Human-interactive mode:
    - Parse pip-audit findings
    - Prompt human for each fix
    - Apply fix with uv
    - Run tests to verify
    - Rollback on failure
    """
    if not PYTHON.exists():
        init()

    # Run scan first to get vulnerabilities
    print("Running security scan...")
    _, audit_dependencies = load_audit_dependencies()
    vulnerabilities = [item for item in audit_dependencies if item.get("vulns")]

    if not vulnerabilities:
        print("No vulnerabilities found.")
        return

    declared_dependency_index = build_declared_dependency_index()
    total_vulnerabilities = len(vulnerabilities)

    print(f"\nFound {total_vulnerabilities} vulnerable package(s)\n")

    # Track results
    fixed_count = 0
    skipped_count = 0
    failed_count = 0

    # Process each vulnerable package
    for idx, vuln_pkg in enumerate(vulnerabilities, 1):
        package_name = vuln_pkg.get("name", "unknown")
        current_version = vuln_pkg.get("version", "unknown")
        vulns = vuln_pkg.get("vulns", [])

        # Get fix version (use first vulnerability's fix version)
        fix_version = None
        cve_ids = []
        for vuln in vulns:
            cve_ids.append(vuln.get("id", "unknown"))
            fixed_versions = vuln.get("fix_versions", [])
            if fixed_versions:
                fix_version = fixed_versions[0]
                break

        declared_matches = declared_dependency_index.get(
            normalize_dependency_name(package_name), []
        )

        if not declared_matches:
            print(f"[{idx}/{total_vulnerabilities}] Skipped {package_name} {current_version}")
            print(f"  CVEs: {', '.join(cve_ids)}")
            print("  Indirect dependency. Phase 1 scan:fix only updates declared dependencies.\n")
            skipped_count += 1
            continue

        if len(declared_matches) > 1:
            print(f"[{idx}/{total_vulnerabilities}] Skipped {package_name} {current_version}")
            print(f"  CVEs: {', '.join(cve_ids)}")
            print("  Multiple declarations found. Resolve manually to avoid ambiguous edits.\n")
            skipped_count += 1
            continue

        declared_dependency = declared_matches[0]

        if not fix_version:
            print(f"[{idx}/{total_vulnerabilities}] Skipped {package_name} {current_version}")
            print(f"  CVEs: {', '.join(cve_ids)}")
            print("  No fix version available.\n")
            skipped_count += 1
            continue

        try:
            fix_requirement = build_fix_requirement(declared_dependency["specifier"], fix_version)
        except ValueError as error:
            print(f"[{idx}/{total_vulnerabilities}] Skipped {package_name} {current_version}")
            print(f"  CVEs: {', '.join(cve_ids)}")
            print(f"  {error}\n")
            skipped_count += 1
            continue

        # Display vulnerability info
        print(f"[{idx}/{total_vulnerabilities}] {package_name} {current_version} -> {fix_version}")
        print(f"  Declared as: {declared_dependency['specifier']} ({declared_dependency['scope']})")
        print(f"  CVEs: {', '.join(cve_ids)}")

        # Prompt user
        while True:
            response = input("  Apply fix? [y/n/skip/quit]: ").strip().lower()
            if response in ("y", "yes"):
                break
            elif response in ("n", "no", "skip"):
                print("  ⏭️  Skipped\n")
                skipped_count += 1
                break
            elif response in ("q", "quit"):
                print("\n🛑 Aborted by user")
                print(
                    f"\nSummary: {fixed_count} fixed, {skipped_count} skipped, "
                    f"{failed_count} failed"
                )
                return
            else:
                print("  Invalid input. Please enter y/n/skip/quit")

        if response not in ("y", "yes"):
            continue

        backups = backup_project_state()

        try:
            # Apply fix
            print("  Applying fix...")
            run(build_uv_add_command(declared_dependency, fix_requirement), check=True)
            sync_dev_environment()

            # Run tests
            print("  🧪 Running tests...")
            test_result = run_verification_tests()

            if test_result.returncode == 0:
                print("  ✅ Tests passed\n")
                fixed_count += 1
                cleanup_project_backups(backups)
            else:
                print("  ❌ Tests failed")
                print("  🔄 Rolling back...")

                # Rollback
                restore_project_state(backups)

                print("  ⚠️  Fix reverted due to test failures\n")
                failed_count += 1

        except subprocess.CalledProcessError as e:
            print(f"  ❌ Fix failed: {e}")
            print("  🔄 Rolling back...")

            # Rollback
            restore_project_state(backups)

            print("  ⚠️  Fix reverted\n")
            failed_count += 1

    # Summary
    print(f"\n{'=' * 60}")
    print("Summary:")
    print(f"  ✅ Fixed: {fixed_count}")
    print(f"  ⏭️  Skipped: {skipped_count}")
    print(f"  ❌ Failed: {failed_count}")
    print(f"{'=' * 60}\n")

    if fixed_count > 0:
        print("💡 Tip: Run 'task ci' to verify all checks pass")


def test_failure_excerpt(completed: subprocess.CompletedProcess[str]) -> str:
    for stream in (completed.stderr, completed.stdout):
        if not stream:
            continue
        for line in stream.splitlines():
            stripped = line.strip()
            if stripped:
                return stripped
    return "verification command returned a non-zero exit code"


def build_skip_candidate(
    *,
    package_name: str,
    installed_version: str,
    vulnerability_ids: list[str],
    fix_version: str | None,
    target_type: str,
    target_dependency_name: str | None,
    target_scope: str | None,
    target_dependency_specifier: str | None,
    target_dependency_current_version: str | None,
    target_version: str | None,
    update_type: str | None,
    reason: str,
) -> dict[str, Any]:
    target_name = target_dependency_name or package_name
    target_version_value = target_version or fix_version or installed_version
    return {
        "candidate_key": (
            f"{target_type}:{package_name}:{target_name}:{target_version_value or 'none'}"
        ),
        "package_name": package_name,
        "installed_version": installed_version,
        "vulnerability_ids": vulnerability_ids,
        "fix_version": fix_version,
        "target_type": target_type,
        "target_dependency_name": target_dependency_name,
        "target_scope": target_scope,
        "target_dependency_specifier": target_dependency_specifier,
        "target_dependency_current_version": target_dependency_current_version,
        "target_version": target_version,
        "update_type": update_type,
        "action": "skip",
        "reason": reason,
    }


def build_apply_candidate(
    *,
    package_name: str,
    installed_version: str,
    vulnerability_ids: list[str],
    fix_version: str | None,
    target_type: str,
    target_dependency: dict[str, str],
    target_dependency_name: str,
    target_dependency_current_version: str,
    target_version: str,
    update_type: str,
    python_compatibility: dict[str, str],
    requirement: str,
    reason: str,
) -> dict[str, Any]:
    command = build_uv_add_command(target_dependency, requirement)
    return {
        "candidate_key": f"{target_type}:{package_name}:{target_dependency_name}:{target_version}",
        "package_name": package_name,
        "installed_version": installed_version,
        "vulnerability_ids": vulnerability_ids,
        "fix_version": fix_version,
        "target_type": target_type,
        "target_dependency_name": target_dependency_name,
        "target_scope": target_dependency["scope"],
        "target_dependency_specifier": target_dependency["specifier"],
        "target_dependency_current_version": target_dependency_current_version,
        "target_version": target_version,
        "update_type": update_type,
        "python_compatibility": python_compatibility,
        "requirement": requirement,
        "command": " ".join(shlex.quote(part) for part in command),
        "action": "apply",
        "reason": reason,
    }


def build_direct_candidate(
    *,
    vulnerable_dependency: dict[str, Any],
    declared_matches: list[dict[str, str]],
    remediation_policy: dict[str, Any],
    project_python_specifier: str | None,
) -> dict[str, Any]:
    package_name = str(vulnerable_dependency.get("name", "unknown"))
    installed_version = str(vulnerable_dependency.get("version", "unknown"))
    vulnerabilities = list(vulnerable_dependency.get("vulns", []))
    vulnerability_ids = extract_vulnerability_ids(vulnerabilities)
    fix_version = choose_fix_version(vulnerabilities)

    if len(declared_matches) > 1:
        return build_skip_candidate(
            package_name=package_name,
            installed_version=installed_version,
            vulnerability_ids=vulnerability_ids,
            fix_version=fix_version,
            target_type="direct",
            target_dependency_name=package_name,
            target_scope=None,
            target_dependency_specifier=None,
            target_dependency_current_version=installed_version,
            target_version=fix_version,
            update_type=None,
            reason="multiple declared dependency entries map to this package",
        )

    declared_dependency = declared_matches[0]
    dependency_name, exact_pin = parse_exact_pin(declared_dependency["specifier"])
    if exact_pin is not None and not remediation_policy["allow_exact_pin_updates"]:
        return build_skip_candidate(
            package_name=package_name,
            installed_version=installed_version,
            vulnerability_ids=vulnerability_ids,
            fix_version=fix_version,
            target_type="direct",
            target_dependency_name=dependency_name,
            target_scope=declared_dependency["scope"],
            target_dependency_specifier=declared_dependency["specifier"],
            target_dependency_current_version=installed_version,
            target_version=fix_version,
            update_type=None,
            reason="policy disables automatic edits for exact-pinned dependencies",
        )

    if declared_dependency["scope"] not in remediation_policy["allowed_scopes"]:
        return build_skip_candidate(
            package_name=package_name,
            installed_version=installed_version,
            vulnerability_ids=vulnerability_ids,
            fix_version=fix_version,
            target_type="direct",
            target_dependency_name=dependency_name,
            target_scope=declared_dependency["scope"],
            target_dependency_specifier=declared_dependency["specifier"],
            target_dependency_current_version=installed_version,
            target_version=fix_version,
            update_type=None,
            reason=(
                f"scope {declared_dependency['scope']!r} is outside the remediation policy "
                f"{remediation_policy['allowed_scopes']}"
            ),
        )

    if not fix_version:
        return build_skip_candidate(
            package_name=package_name,
            installed_version=installed_version,
            vulnerability_ids=vulnerability_ids,
            fix_version=None,
            target_type="direct",
            target_dependency_name=dependency_name,
            target_scope=declared_dependency["scope"],
            target_dependency_specifier=declared_dependency["specifier"],
            target_dependency_current_version=installed_version,
            target_version=None,
            update_type=None,
            reason="pip-audit did not provide a fix version",
        )

    update_type = classify_update(installed_version, fix_version)
    if not update_type_allowed(update_type, remediation_policy["maximum_update_type"]):
        return build_skip_candidate(
            package_name=package_name,
            installed_version=installed_version,
            vulnerability_ids=vulnerability_ids,
            fix_version=fix_version,
            target_type="direct",
            target_dependency_name=dependency_name,
            target_scope=declared_dependency["scope"],
            target_dependency_specifier=declared_dependency["specifier"],
            target_dependency_current_version=installed_version,
            target_version=fix_version,
            update_type=update_type,
            reason=(
                f"{update_type} updates exceed the configured maximum "
                f"{remediation_policy['maximum_update_type']}"
            ),
        )

    package_info = fetch_pypi_package_info(package_name)
    python_compatibility = build_python_compatibility(
        project_specifier=project_python_specifier,
        package_name=package_name,
        package_specifier=package_info["info"].get("requires_python"),
    )
    if python_compatibility["status"] == "incompatible":
        return build_skip_candidate(
            package_name=package_name,
            installed_version=installed_version,
            vulnerability_ids=vulnerability_ids,
            fix_version=fix_version,
            target_type="direct",
            target_dependency_name=dependency_name,
            target_scope=declared_dependency["scope"],
            target_dependency_specifier=declared_dependency["specifier"],
            target_dependency_current_version=installed_version,
            target_version=fix_version,
            update_type=update_type,
            reason=python_compatibility["reason"],
        )

    try:
        requirement = build_fix_requirement(declared_dependency["specifier"], fix_version)
    except ValueError as error:
        return build_skip_candidate(
            package_name=package_name,
            installed_version=installed_version,
            vulnerability_ids=vulnerability_ids,
            fix_version=fix_version,
            target_type="direct",
            target_dependency_name=dependency_name,
            target_scope=declared_dependency["scope"],
            target_dependency_specifier=declared_dependency["specifier"],
            target_dependency_current_version=installed_version,
            target_version=fix_version,
            update_type=update_type,
            reason=str(error),
        )

    return build_apply_candidate(
        package_name=package_name,
        installed_version=installed_version,
        vulnerability_ids=vulnerability_ids,
        fix_version=fix_version,
        target_type="direct",
        target_dependency=declared_dependency,
        target_dependency_name=dependency_name,
        target_dependency_current_version=installed_version,
        target_version=fix_version,
        update_type=update_type,
        python_compatibility=python_compatibility,
        requirement=requirement,
        reason="declared dependency with a compatible fix version",
    )


def build_transitive_parent_candidate(
    *,
    vulnerable_dependency: dict[str, Any],
    remediation_policy: dict[str, Any],
    project_python_specifier: str | None,
    strategy: str,
    transitive_root_index: dict[str, list[dict[str, str]]],
    locked_package_index: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    package_name = str(vulnerable_dependency.get("name", "unknown"))
    installed_version = str(vulnerable_dependency.get("version", "unknown"))
    vulnerabilities = list(vulnerable_dependency.get("vulns", []))
    vulnerability_ids = extract_vulnerability_ids(vulnerabilities)
    fix_version = choose_fix_version(vulnerabilities)

    if strategy != "uv-lock":
        return build_skip_candidate(
            package_name=package_name,
            installed_version=installed_version,
            vulnerability_ids=vulnerability_ids,
            fix_version=fix_version,
            target_type="transitive-parent",
            target_dependency_name=None,
            target_scope=None,
            target_dependency_specifier=None,
            target_dependency_current_version=None,
            target_version=None,
            update_type=None,
            reason="transitive-parent remediation requires a uv.lock workflow",
        )

    if not remediation_policy["allow_transitive_parent_remediation"]:
        return build_skip_candidate(
            package_name=package_name,
            installed_version=installed_version,
            vulnerability_ids=vulnerability_ids,
            fix_version=fix_version,
            target_type="transitive-parent",
            target_dependency_name=None,
            target_scope=None,
            target_dependency_specifier=None,
            target_dependency_current_version=None,
            target_version=None,
            update_type=None,
            reason="policy disables transitive-parent remediation",
        )

    root_matches = transitive_root_index.get(normalize_dependency_name(package_name), [])
    if not root_matches:
        return build_skip_candidate(
            package_name=package_name,
            installed_version=installed_version,
            vulnerability_ids=vulnerability_ids,
            fix_version=fix_version,
            target_type="transitive-parent",
            target_dependency_name=None,
            target_scope=None,
            target_dependency_specifier=None,
            target_dependency_current_version=None,
            target_version=None,
            update_type=None,
            reason="no unique declared parent dependency reaches this package through uv.lock",
        )

    unique_roots = {
        normalize_dependency_name(parse_exact_pin(match["specifier"])[0]): match
        for match in root_matches
    }
    if len(unique_roots) != 1:
        root_names = sorted(parse_exact_pin(match["specifier"])[0] for match in root_matches)
        return build_skip_candidate(
            package_name=package_name,
            installed_version=installed_version,
            vulnerability_ids=vulnerability_ids,
            fix_version=fix_version,
            target_type="transitive-parent",
            target_dependency_name=", ".join(root_names),
            target_scope=None,
            target_dependency_specifier=None,
            target_dependency_current_version=None,
            target_version=None,
            update_type=None,
            reason=f"multiple direct roots reach this package: {root_names}",
        )

    direct_dependency = next(iter(unique_roots.values()))
    target_dependency_name, exact_pin = parse_exact_pin(direct_dependency["specifier"])
    locked_dependency = locked_package_index.get(normalize_dependency_name(target_dependency_name))
    if locked_dependency is None:
        return build_skip_candidate(
            package_name=package_name,
            installed_version=installed_version,
            vulnerability_ids=vulnerability_ids,
            fix_version=fix_version,
            target_type="transitive-parent",
            target_dependency_name=target_dependency_name,
            target_scope=direct_dependency["scope"],
            target_dependency_specifier=direct_dependency["specifier"],
            target_dependency_current_version=None,
            target_version=None,
            update_type=None,
            reason="the direct parent is not present in uv.lock",
        )

    if exact_pin is not None and not remediation_policy["allow_exact_pin_updates"]:
        return build_skip_candidate(
            package_name=package_name,
            installed_version=installed_version,
            vulnerability_ids=vulnerability_ids,
            fix_version=fix_version,
            target_type="transitive-parent",
            target_dependency_name=target_dependency_name,
            target_scope=direct_dependency["scope"],
            target_dependency_specifier=direct_dependency["specifier"],
            target_dependency_current_version=locked_dependency["current_version"],
            target_version=None,
            update_type=None,
            reason="policy disables automatic edits for exact-pinned dependencies",
        )

    if direct_dependency["scope"] not in remediation_policy["allowed_scopes"]:
        return build_skip_candidate(
            package_name=package_name,
            installed_version=installed_version,
            vulnerability_ids=vulnerability_ids,
            fix_version=fix_version,
            target_type="transitive-parent",
            target_dependency_name=target_dependency_name,
            target_scope=direct_dependency["scope"],
            target_dependency_specifier=direct_dependency["specifier"],
            target_dependency_current_version=locked_dependency["current_version"],
            target_version=None,
            update_type=None,
            reason=(
                f"scope {direct_dependency['scope']!r} is outside the remediation policy "
                f"{remediation_policy['allowed_scopes']}"
            ),
        )

    target_version = latest_pypi_version(target_dependency_name)
    current_version = str(locked_dependency["current_version"])
    update_type = classify_update(current_version, target_version)
    if current_version == target_version:
        return build_skip_candidate(
            package_name=package_name,
            installed_version=installed_version,
            vulnerability_ids=vulnerability_ids,
            fix_version=fix_version,
            target_type="transitive-parent",
            target_dependency_name=target_dependency_name,
            target_scope=direct_dependency["scope"],
            target_dependency_specifier=direct_dependency["specifier"],
            target_dependency_current_version=current_version,
            target_version=target_version,
            update_type="none",
            reason="no newer version is available for the direct parent dependency",
        )

    if not update_type_allowed(update_type, remediation_policy["maximum_update_type"]):
        return build_skip_candidate(
            package_name=package_name,
            installed_version=installed_version,
            vulnerability_ids=vulnerability_ids,
            fix_version=fix_version,
            target_type="transitive-parent",
            target_dependency_name=target_dependency_name,
            target_scope=direct_dependency["scope"],
            target_dependency_specifier=direct_dependency["specifier"],
            target_dependency_current_version=current_version,
            target_version=target_version,
            update_type=update_type,
            reason=(
                f"{update_type} updates exceed the configured maximum "
                f"{remediation_policy['maximum_update_type']}"
            ),
        )

    target_info = fetch_pypi_package_info(target_dependency_name)
    python_compatibility = build_python_compatibility(
        project_specifier=project_python_specifier,
        package_name=target_dependency_name,
        package_specifier=target_info["info"].get("requires_python"),
    )
    if python_compatibility["status"] == "incompatible":
        return build_skip_candidate(
            package_name=package_name,
            installed_version=installed_version,
            vulnerability_ids=vulnerability_ids,
            fix_version=fix_version,
            target_type="transitive-parent",
            target_dependency_name=target_dependency_name,
            target_scope=direct_dependency["scope"],
            target_dependency_specifier=direct_dependency["specifier"],
            target_dependency_current_version=current_version,
            target_version=target_version,
            update_type=update_type,
            reason=python_compatibility["reason"],
        )

    try:
        requirement = build_fix_requirement(direct_dependency["specifier"], target_version)
    except ValueError as error:
        return build_skip_candidate(
            package_name=package_name,
            installed_version=installed_version,
            vulnerability_ids=vulnerability_ids,
            fix_version=fix_version,
            target_type="transitive-parent",
            target_dependency_name=target_dependency_name,
            target_scope=direct_dependency["scope"],
            target_dependency_specifier=direct_dependency["specifier"],
            target_dependency_current_version=current_version,
            target_version=target_version,
            update_type=update_type,
            reason=str(error),
        )

    return build_apply_candidate(
        package_name=package_name,
        installed_version=installed_version,
        vulnerability_ids=vulnerability_ids,
        fix_version=fix_version,
        target_type="transitive-parent",
        target_dependency=direct_dependency,
        target_dependency_name=target_dependency_name,
        target_dependency_current_version=current_version,
        target_version=target_version,
        update_type=update_type,
        python_compatibility=python_compatibility,
        requirement=requirement,
        reason=(
            f"unique direct dependency {target_dependency_name} reaches {package_name} "
            "through uv.lock"
        ),
    )


def latest_pypi_version(package_name: str) -> str:
    return str(fetch_pypi_package_info(package_name)["info"]["version"])


def fetch_pypi_package_info(package_name: str) -> dict[str, Any]:
    normalized_name = package_name.lower()
    if normalized_name in PYPI_PACKAGE_INFO_CACHE:
        return PYPI_PACKAGE_INFO_CACHE[normalized_name]

    request_url = f"https://pypi.org/pypi/{package_name}/json"
    with urllib.request.urlopen(request_url, timeout=30) as response:
        data: dict[str, Any] = json.load(response)
    PYPI_PACKAGE_INFO_CACHE[normalized_name] = data
    return data


def build_python_compatibility(
    *,
    project_specifier: str | None,
    package_name: str,
    package_specifier: str | None,
) -> dict[str, str]:
    project_minimum = parse_minimum_version(project_specifier)
    package_minimum = parse_minimum_version(package_specifier)

    if package_specifier is None:
        return {
            "status": "compatible",
            "reason": f"{package_name} does not publish requires_python metadata",
        }

    if project_minimum is None or package_minimum is None:
        return {
            "status": "unknown",
            "reason": (
                f"could not compare project requires-python {project_specifier!r} "
                f"with package requires_python {package_specifier!r}"
            ),
        }

    if package_minimum > project_minimum:
        return {
            "status": "incompatible",
            "reason": (
                f"{package_name} requires Python >={format_version_tuple(package_minimum)} "
                f"but the project declares {project_specifier}"
            ),
        }

    return {
        "status": "compatible",
        "reason": (
            f"{package_name} requires Python >={format_version_tuple(package_minimum)} "
            f"which fits the project declaration {project_specifier}"
        ),
    }


def build_remediation_plan_artifact(*, run_baseline_tests: bool) -> dict[str, Any]:
    remediation_policy = load_remediation_policy()
    project_python_specifier = project_requires_python()
    strategy_detection = detect_python_strategy()
    declared_dependency_index = build_declared_dependency_index()
    locked_package_index = (
        build_normalized_uv_package_map() if strategy_detection["strategy"] == "uv-lock" else {}
    )
    transitive_root_index = (
        build_transitive_root_index() if strategy_detection["strategy"] == "uv-lock" else {}
    )
    audit_report, audit_dependencies = load_audit_dependencies()
    audit_summary = summarize_audit_dependencies(audit_dependencies)

    preflight: dict[str, Any] = {
        "baseline_tests_passed": None,
        "blocked": False,
        "reasons": [],
        "verification_command": f"{PYTHON} -m pytest -q -x -m 'not integration'",
    }
    if run_baseline_tests:
        test_result = run_verification_tests()
        preflight["baseline_tests_passed"] = test_result.returncode == 0
        if test_result.returncode != 0:
            preflight["blocked"] = True
            preflight["reasons"].append(
                "baseline tests failed before remediation: " + test_failure_excerpt(test_result)
            )

    candidates = []
    for vulnerable_dependency in (item for item in audit_dependencies if item.get("vulns")):
        package_name = str(vulnerable_dependency.get("name", "unknown"))
        declared_matches = declared_dependency_index.get(
            normalize_dependency_name(package_name), []
        )
        if declared_matches:
            candidate = build_direct_candidate(
                vulnerable_dependency=vulnerable_dependency,
                declared_matches=declared_matches,
                remediation_policy=remediation_policy,
                project_python_specifier=project_python_specifier,
            )
        else:
            candidate = build_transitive_parent_candidate(
                vulnerable_dependency=vulnerable_dependency,
                remediation_policy=remediation_policy,
                project_python_specifier=project_python_specifier,
                strategy=strategy_detection["strategy"],
                transitive_root_index=transitive_root_index,
                locked_package_index=locked_package_index,
            )
        candidates.append(candidate)

    candidates.sort(key=candidate_sort_key)

    return {
        "ecosystem": "python",
        "source": str(PYPROJECT.name),
        "strategy_detection": strategy_detection,
        "policy": remediation_policy,
        "audit_report": str(audit_report),
        "audit_summary": audit_summary,
        "preflight": preflight,
        "summary": {
            "apply_candidates": sum(
                1 for candidate in candidates if candidate["action"] == "apply"
            ),
            "skipped_candidates": sum(
                1 for candidate in candidates if candidate["action"] == "skip"
            ),
            "direct_apply_candidates": sum(
                1
                for candidate in candidates
                if candidate["action"] == "apply" and candidate["target_type"] == "direct"
            ),
            "transitive_parent_apply_candidates": sum(
                1
                for candidate in candidates
                if candidate["action"] == "apply"
                and candidate["target_type"] == "transitive-parent"
            ),
        },
        "candidates": candidates,
    }


def remediation_plan_markdown(artifact: dict[str, Any]) -> str:
    lines = [
        "# Python Dependency Remediation Plan",
        "",
        f"- source manifest: `{artifact['source']}`",
        f"- source audit report: `{artifact['audit_report']}`",
        f"- vulnerable packages: `{artifact['audit_summary']['vulnerable_package_count']}`",
        f"- vulnerability ids: `{artifact['audit_summary']['vulnerability_count']}`",
        f"- apply candidates: `{artifact['summary']['apply_candidates']}`",
        f"- skipped candidates: `{artifact['summary']['skipped_candidates']}`",
        "",
    ]

    if artifact["preflight"]["blocked"]:
        lines.extend(
            [
                "## Preflight",
                "",
                f"- blocked: `{artifact['preflight']['blocked']}`",
                f"- reasons: `{' | '.join(artifact['preflight']['reasons'])}`",
                "",
            ]
        )

    for candidate in artifact["candidates"]:
        lines.extend(
            [
                f"## {candidate['package_name']} ({candidate['installed_version']})",
                "",
                f"- action: `{candidate['action']}`",
                f"- target type: `{candidate['target_type']}`",
                f"- target dependency: `{candidate.get('target_dependency_name') or 'n/a'}`",
                f"- target version: `{candidate.get('target_version') or 'n/a'}`",
                f"- update type: `{candidate.get('update_type') or 'n/a'}`",
                f"- vulnerability ids: `{', '.join(candidate['vulnerability_ids'])}`",
                f"- reason: {candidate['reason']}",
                "",
            ]
        )

    if not artifact["candidates"]:
        lines.extend(["No vulnerable packages were found.", ""])

    return "\n".join(lines)


def remaining_target_vulnerability_ids(
    audit_dependencies: list[dict[str, Any]], package_name: str, vulnerability_ids: list[str]
) -> list[str]:
    target_ids = set(vulnerability_ids)
    for dependency in audit_dependencies:
        dependency_name = normalize_dependency_name(str(dependency.get("name", "")))
        if dependency_name != normalize_dependency_name(package_name):
            continue
        current_ids = set(extract_vulnerability_ids(list(dependency.get("vulns", []))))
        return sorted(target_ids & current_ids)
    return []


def inventory() -> dict[str, Any]:
    SCANS_DIR.mkdir(parents=True, exist_ok=True)
    print_status("collecting dependency inventory")
    artifact = build_inventory_artifact()
    inventory_path = SCANS_DIR / "dependency-inventory.json"
    write_json_artifact(inventory_path, artifact)
    print_status(
        "inventory complete: "
        f"strategy={artifact['strategy_detection']['strategy']} "
        f"dependencies={len(artifact['dependencies'])} "
        f"artifact={inventory_path}"
    )
    return artifact


def plan() -> dict[str, Any]:
    SCANS_DIR.mkdir(parents=True, exist_ok=True)
    print_status("building dependency update plan")
    artifact = build_plan_artifact()
    plan_path = SCANS_DIR / "dependency-plan.json"
    write_json_artifact(plan_path, artifact)
    planned_updates = sum(1 for dependency in artifact["dependencies"] if dependency["will_update"])
    blocked = artifact.get("blocked")
    status_suffix = (
        f"blocked={blocked['kind']} artifact={plan_path}" if blocked else f"artifact={plan_path}"
    )
    print_status(
        "plan complete: "
        f"strategy={artifact['strategy_detection']['strategy']} "
        f"planned_updates={planned_updates} "
        f"{status_suffix}"
    )
    return artifact


def scan_plan() -> dict[str, Any]:
    SCANS_DIR.mkdir(parents=True, exist_ok=True)
    print_status("building dependency remediation plan")
    artifact = build_remediation_plan_artifact(run_baseline_tests=True)
    plan_json = SCANS_DIR / "dependency-remediation-plan.json"
    plan_markdown = SCANS_DIR / "dependency-remediation-plan.md"
    write_json_artifact(plan_json, artifact)
    write_markdown_artifact(plan_markdown, remediation_plan_markdown(artifact))
    print_status(
        "remediation plan complete: "
        f"apply_candidates={artifact['summary']['apply_candidates']} "
        f"artifact={plan_json}"
    )
    return artifact


def upgrade() -> None:
    SCANS_DIR.mkdir(parents=True, exist_ok=True)
    dependency_plan = plan()
    strategy = dependency_plan["strategy_detection"]["strategy"]
    print_status(f"starting dependency upgrade with strategy={strategy}")

    if strategy == "uv-lock":
        blocked = dependency_plan.get("blocked")
        if blocked is not None:
            raise SystemExit(
                "task upgrade is blocked for the detected uv workflow: "
                f"{blocked['kind']} ({blocked['message']})"
            )
        before_upgrade = build_uv_package_map()
        run(["uv", "lock", "--upgrade"])
        after_upgrade = build_uv_package_map()
        uv_updates = []
        for name, dependency in before_upgrade.items():
            latest_version = after_upgrade.get(name, dependency)["current_version"]
            current_version = dependency["current_version"]
            uv_updates.append(
                {
                    "name": name,
                    "scope": dependency["scope"],
                    "current_version": current_version,
                    "latest_version": latest_version,
                    "update_type": classify_update(current_version, latest_version),
                    "updated": str(current_version != latest_version).lower(),
                }
            )
        write_json_artifact(
            SCANS_DIR / "pypi-upgrades.json",
            {
                "ecosystem": "python",
                "source": str(UV_LOCK.name),
                "strategy_detection": dependency_plan["strategy_detection"],
                "dependencies": uv_updates,
            },
        )
        print_status(
            "upgrade complete: "
            f"updated={sum(1 for dependency in uv_updates if dependency['updated'] == 'true')} "
            f"artifact={SCANS_DIR / 'pypi-upgrades.json'} "
            f"lockfile={UV_LOCK}"
        )
        return

    if strategy == "pip-tools":
        plan_dependencies = build_pip_tools_plan()
        pip_tools_updates = []
        for target in pip_tools_targets():
            compile_requirements(target["source"], target["target"], upgrade=True)
        for dependency in plan_dependencies:
            pip_tools_updates.append(
                {
                    "name": dependency["name"],
                    "scope": dependency["scope"],
                    "current_version": dependency["current_version"],
                    "latest_version": dependency["latest_version"],
                    "update_type": dependency["update_type"],
                    "updated": str(dependency["will_update"]).lower(),
                    "compiled_target": dependency["compiled_target"],
                }
            )
        write_json_artifact(
            SCANS_DIR / "pypi-upgrades.json",
            {
                "ecosystem": "python",
                "source": "requirements.in",
                "strategy_detection": dependency_plan["strategy_detection"],
                "dependencies": pip_tools_updates,
            },
        )
        updated_targets = sorted(
            {dependency["compiled_target"] for dependency in pip_tools_updates}
        )
        updated_count = sum(
            1 for dependency in pip_tools_updates if dependency["updated"] == "true"
        )
        print_status(
            "upgrade complete: "
            f"updated={updated_count} "
            f"artifact={SCANS_DIR / 'pypi-upgrades.json'} "
            f"compiled_targets={updated_targets}"
        )
        return

    if strategy != "pyproject-exact-pins":
        raise SystemExit(
            "task upgrade currently supports only the 'uv-lock', 'pip-tools', and "
            "'pyproject-exact-pins' strategies; "
            f"detected '{strategy}' and recorded native workflow hints in dependency-plan.json"
        )

    content = PYPROJECT.read_text(encoding="utf-8")
    updates: list[dict[str, str]] = []

    for dependency in dependency_plan["dependencies"]:
        current_version = dependency["current_version"]
        latest_version = dependency["latest_version"]
        if current_version is None or latest_version is None:
            continue
        should_update = bool(dependency["will_update"])
        updates.append(
            {
                "name": dependency["name"],
                "scope": dependency["scope"],
                "current_version": current_version,
                "latest_version": latest_version,
                "update_type": dependency["update_type"],
                "updated": str(should_update).lower(),
            }
        )
        if should_update:
            content = content.replace(
                f'"{dependency["name"]}=={current_version}"',
                f'"{dependency["name"]}=={latest_version}"',
            )

    PYPROJECT.write_text(content, encoding="utf-8")
    write_json_artifact(
        SCANS_DIR / "pypi-upgrades.json",
        {
            "ecosystem": "python",
            "source": str(PYPROJECT.name),
            "strategy_detection": dependency_plan["strategy_detection"],
            "dependencies": updates,
        },
    )
    print_status(
        "upgrade complete: "
        f"updated={sum(1 for dependency in updates if dependency['updated'] == 'true')} "
        f"artifact={SCANS_DIR / 'pypi-upgrades.json'} "
        f"manifest={PYPROJECT}"
    )


def apply_remediation_candidate(
    candidate: dict[str, Any], pre_audit_summary: dict[str, Any]
) -> dict[str, Any]:
    backups = backup_project_state()
    command = [part for part in shlex.split(str(candidate["command"]))]
    outcome = {
        "candidate_key": candidate["candidate_key"],
        "attempt_signature": candidate_attempt_signature(candidate),
        "package_name": candidate["package_name"],
        "target_type": candidate["target_type"],
        "target_dependency_name": candidate["target_dependency_name"],
        "target_version": candidate["target_version"],
        "status": "rolled_back",
        "reason": "",
        "pre_vulnerability_ids": pre_audit_summary["vulnerability_count"],
        "post_vulnerability_ids": pre_audit_summary["vulnerability_count"],
        "remaining_target_vulnerability_ids": list(candidate["vulnerability_ids"]),
    }

    try:
        run(command, check=True)
        sync_dev_environment()

        test_result = run_verification_tests()
        if test_result.returncode != 0:
            restore_project_state(backups)
            outcome["reason"] = (
                "tests failed after applying the candidate fix: "
                + test_failure_excerpt(test_result)
            )
            return outcome

        _, post_audit_dependencies = load_audit_dependencies()
        post_summary = summarize_audit_dependencies(post_audit_dependencies)
        remaining_target_ids = remaining_target_vulnerability_ids(
            post_audit_dependencies,
            str(candidate["package_name"]),
            list(candidate["vulnerability_ids"]),
        )

        if remaining_target_ids:
            restore_project_state(backups)
            outcome["reason"] = (
                "the targeted vulnerability ids remained after the attempted remediation: "
                f"{remaining_target_ids}"
            )
            outcome["remaining_target_vulnerability_ids"] = remaining_target_ids
            outcome["post_vulnerability_ids"] = post_summary["vulnerability_count"]
            return outcome

        if post_summary["vulnerability_count"] >= pre_audit_summary["vulnerability_count"]:
            restore_project_state(backups)
            outcome["reason"] = (
                "the candidate did not reduce the total vulnerability count "
                f"({pre_audit_summary['vulnerability_count']} -> "
                f"{post_summary['vulnerability_count']})"
            )
            outcome["post_vulnerability_ids"] = post_summary["vulnerability_count"]
            outcome["remaining_target_vulnerability_ids"] = remaining_target_ids
            return outcome

        cleanup_project_backups(backups)
        outcome["status"] = "accepted"
        outcome["reason"] = "tests passed and the targeted vulnerability ids were removed"
        outcome["post_vulnerability_ids"] = post_summary["vulnerability_count"]
        outcome["remaining_target_vulnerability_ids"] = []
        return outcome

    except (RuntimeError, subprocess.CalledProcessError) as error:
        restore_project_state(backups)
        message = summarize_uv_error(getattr(error, "stderr", "") or getattr(error, "stdout", ""))
        outcome["reason"] = message or str(error)
        return outcome


def candidate_attempt_signature(candidate: dict[str, Any]) -> str:
    # Equivalent uv add commands should be attempted once, even if multiple
    # vulnerable packages collapse to the same parent upgrade.
    return str(candidate.get("command") or candidate.get("candidate_key"))


def remediation_report_status(
    initial_plan: dict[str, Any],
    final_plan: dict[str, Any],
    accepted: list[dict[str, Any]],
    rolled_back: list[dict[str, Any]],
) -> str:
    if initial_plan["preflight"]["blocked"]:
        return "blocked"
    if final_plan["audit_summary"]["vulnerability_count"] == 0:
        return "clean"
    if not accepted and rolled_back:
        return "failed"
    return "partial"


def build_remediation_report(
    *,
    initial_plan: dict[str, Any],
    final_plan: dict[str, Any],
    accepted: list[dict[str, Any]],
    rolled_back: list[dict[str, Any]],
) -> dict[str, Any]:
    exhausted_reasons = {item["attempt_signature"]: item["reason"] for item in rolled_back}
    exhausted_candidates = []
    remaining_candidates = []
    for candidate in final_plan["candidates"]:
        attempt_signature = candidate_attempt_signature(candidate)
        if attempt_signature in exhausted_reasons and candidate["action"] == "apply":
            exhausted_candidate = dict(candidate)
            exhausted_candidate["action"] = "exhausted"
            exhausted_candidate["reason"] = exhausted_reasons[attempt_signature]
            exhausted_candidates.append(exhausted_candidate)
            continue
        remaining_candidates.append(candidate)

    status = remediation_report_status(initial_plan, final_plan, accepted, rolled_back)
    return {
        "ecosystem": "python",
        "source": str(PYPROJECT.name),
        "status": status,
        "policy": initial_plan["policy"],
        "preflight": initial_plan["preflight"],
        "summary": {
            "accepted": len(accepted),
            "rolled_back": len(rolled_back),
            "initial_vulnerability_ids": initial_plan["audit_summary"]["vulnerability_count"],
            "remaining_vulnerability_ids": final_plan["audit_summary"]["vulnerability_count"],
            "remaining_apply_candidates": sum(
                1 for candidate in remaining_candidates if candidate["action"] == "apply"
            ),
            "remaining_skipped_candidates": sum(
                1 for candidate in remaining_candidates if candidate["action"] == "skip"
            ),
            "exhausted_candidates": len(exhausted_candidates),
        },
        "initial_audit_summary": initial_plan["audit_summary"],
        "final_audit_summary": final_plan["audit_summary"],
        "accepted": accepted,
        "rolled_back": rolled_back,
        "exhausted_candidates": exhausted_candidates,
        "remaining_candidates": remaining_candidates,
    }


def remediation_report_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# Python Dependency Remediation Report",
        "",
        f"- status: `{report['status']}`",
        f"- accepted fixes: `{report['summary']['accepted']}`",
        f"- rolled back fixes: `{report['summary']['rolled_back']}`",
        f"- initial vulnerability ids: `{report['summary']['initial_vulnerability_ids']}`",
        f"- remaining vulnerability ids: `{report['summary']['remaining_vulnerability_ids']}`",
        f"- remaining apply candidates: `{report['summary']['remaining_apply_candidates']}`",
        "",
    ]

    if report["accepted"]:
        lines.extend(["## Accepted", ""])
        for item in report["accepted"]:
            lines.append(
                f"- `{item['target_dependency_name']}` -> `{item['target_version']}` "
                f"for `{item['package_name']}` ({item['target_type']})"
            )
        lines.append("")

    if report["rolled_back"]:
        lines.extend(["## Rolled Back", ""])
        for item in report["rolled_back"]:
            lines.append(
                f"- `{item['target_dependency_name']}` -> `{item['target_version']}` "
                f"for `{item['package_name']}`: {item['reason']}"
            )
        lines.append("")

    if report["exhausted_candidates"]:
        lines.extend(["## Exhausted Candidates", ""])
        for candidate in report["exhausted_candidates"]:
            lines.append(
                f"- `{candidate['package_name']}` via "
                f"`{candidate.get('target_dependency_name') or 'n/a'}`: {candidate['reason']}"
            )
        lines.append("")

    if report["remaining_candidates"]:
        lines.extend(["## Remaining Candidates", ""])
        for candidate in report["remaining_candidates"]:
            lines.append(
                f"- `{candidate['package_name']}`: `{candidate['action']}` "
                f"via `{candidate.get('target_dependency_name') or 'n/a'}` "
                f"because {candidate['reason']}"
            )
        lines.append("")

    return "\n".join(lines)


def write_remediation_report_artifacts(report: dict[str, Any]) -> None:
    write_json_artifact(SCANS_DIR / "dependency-remediation-report.json", report)
    write_markdown_artifact(
        SCANS_DIR / "dependency-remediation-report.md",
        remediation_report_markdown(report),
    )


def execute_scan_auto() -> tuple[dict[str, Any], int]:
    initial_plan = build_remediation_plan_artifact(run_baseline_tests=True)
    accepted: list[dict[str, Any]] = []
    rolled_back: list[dict[str, Any]] = []
    attempted: set[str] = set()
    final_plan = initial_plan

    if not initial_plan["preflight"]["blocked"]:
        while True:
            current_plan = build_remediation_plan_artifact(run_baseline_tests=False)
            pending_candidates = [
                candidate
                for candidate in current_plan["candidates"]
                if candidate["action"] == "apply"
                and candidate_attempt_signature(candidate) not in attempted
            ]
            if not pending_candidates:
                final_plan = current_plan
                break

            candidate = sorted(pending_candidates, key=candidate_sort_key)[0]
            attempted.add(candidate_attempt_signature(candidate))
            print_status(
                f"attempting {candidate['target_type']} remediation "
                f"{candidate['target_dependency_name']} -> {candidate['target_version']} "
                f"for {candidate['package_name']}"
            )
            outcome = apply_remediation_candidate(candidate, current_plan["audit_summary"])
            if outcome["status"] == "accepted":
                accepted.append(outcome)
                print_status(
                    f"accepted remediation for {candidate['package_name']} "
                    f"via {candidate['target_dependency_name']}"
                )
            else:
                rolled_back.append(outcome)
                print_status(
                    f"rolled back remediation for {candidate['package_name']}: {outcome['reason']}"
                )

    final_plan = build_remediation_plan_artifact(run_baseline_tests=False)
    evaluate_python_audit_policy(Path(final_plan["audit_report"]), check=False)
    report = build_remediation_report(
        initial_plan=initial_plan,
        final_plan=final_plan,
        accepted=accepted,
        rolled_back=rolled_back,
    )
    write_remediation_report_artifacts(report)
    exit_code = 0 if report["status"] in {"clean", "partial"} else 1
    return report, exit_code


def scan_auto() -> None:
    SCANS_DIR.mkdir(parents=True, exist_ok=True)
    print_status("starting automated dependency remediation")
    report, exit_code = execute_scan_auto()
    print_status(
        "scan:auto complete: "
        f"status={report['status']} "
        f"accepted={report['summary']['accepted']} "
        f"rolled_back={report['summary']['rolled_back']} "
        f"remaining_vulnerability_ids={report['summary']['remaining_vulnerability_ids']}"
    )
    if exit_code != 0:
        raise SystemExit(exit_code)


def scan_pr() -> None:
    if run_git_command(["rev-parse", "--is-inside-work-tree"], check=False).returncode != 0:
        raise SystemExit("scan:pr requires a git repository")
    if not git_worktree_is_clean():
        raise SystemExit("scan:pr requires a clean git worktree")

    remediation_policy = load_remediation_policy()
    branch_name = unique_scan_pr_branch_name(remediation_policy["pr"]["branch_prefix"])
    print_status(f"creating remediation branch {branch_name}")
    run_git_command(["switch", "-c", branch_name])

    report, exit_code = execute_scan_auto()
    if not tracked_git_changes():
        print_status("scan:pr produced no tracked dependency changes; removing the branch")
        run_git_command(["switch", "-"])
        run_git_command(["branch", "-D", branch_name])
        if exit_code != 0:
            raise SystemExit(exit_code)
        return

    run_git_command(["add", "pyproject.toml"])
    if UV_LOCK.exists():
        run_git_command(["add", "uv.lock"])
    run_git_command(["commit", "-m", remediation_policy["pr"]["commit_message"]])

    pr_url = None
    if remediation_policy["pr"]["push_branch"]:
        run_git_command(["push", "-u", "origin", branch_name])
        if remediation_policy["pr"]["open_pull_request"]:
            pr_url = open_pull_request_with_gh(
                title=remediation_policy["pr"]["pull_request_title"],
                body=build_scan_pr_body(report),
                base_branch=remediation_policy["pr"]["base_branch"],
                head_branch=branch_name,
            )

    if pr_url:
        print_status(f"scan:pr created pull request {pr_url}")
    else:
        print_status(f"scan:pr committed remediation changes on branch={branch_name}")

    if exit_code != 0:
        raise SystemExit(exit_code)


COMMANDS = {
    "format": format_code,
    "init": init,
    "inventory": inventory,
    "lint": lint,
    "plan": plan,
    "scan": scan,
    "scan_fix": scan_fix,
    "scan_auto": scan_auto,
    "scan_plan": scan_plan,
    "scan_pr": scan_pr,
    "test": test,
    "test_fast": test_fast,
    "test_unit": test_unit,
    "test_acceptance": test_acceptance,
    "test_property": test_property,
    "test_all": test_all,
    "test_integration": test_integration,
    "upgrade": upgrade,
}


def main() -> int:
    if len(sys.argv) != 2 or sys.argv[1] not in COMMANDS:
        print(f"usage: {Path(sys.argv[0]).name} [{'|'.join(COMMANDS)}]")
        return 1
    COMMANDS[sys.argv[1]]()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
