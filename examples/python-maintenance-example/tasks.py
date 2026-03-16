from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import tomllib
import urllib.request
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent
TMP_DIR = ROOT / ".tmp"
ARTIFACTS_DIR = ROOT / ".artifacts"
SCANS_DIR = ARTIFACTS_DIR / "scans"
VENV_DIR = ROOT / ".venv"
PYTHON = VENV_DIR / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
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


def run(command: list[str]) -> None:
    TMP_DIR.mkdir(exist_ok=True)
    SCANS_DIR.mkdir(parents=True, exist_ok=True)
    env = os.environ.copy()
    env["TMP"] = str(TMP_DIR.resolve())
    env["TEMP"] = str(TMP_DIR.resolve())
    env["TMPDIR"] = str(TMP_DIR.resolve())
    subprocess.run(command, cwd=ROOT, check=True, text=True, env=env)


def read_project_metadata() -> dict[str, Any]:
    return tomllib.loads(PYPROJECT.read_text(encoding="utf-8"))


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


def iter_declared_dependencies() -> list[dict[str, str]]:
    metadata = read_project_metadata()
    project = metadata.get("project", {})
    dependencies: list[dict[str, str]] = []

    for dependency in project.get("dependencies", []):
        dependencies.append({"scope": "runtime", "specifier": dependency})

    for scope, scoped_dependencies in project.get("optional-dependencies", {}).items():
        for dependency in scoped_dependencies:
            dependencies.append({"scope": scope, "specifier": dependency})

    for scope, scoped_dependencies in metadata.get("dependency-groups", {}).items():
        for dependency in scoped_dependencies:
            if isinstance(dependency, str):
                dependencies.append({"scope": scope, "specifier": dependency})

    return dependencies


def parse_exact_pin(specifier: str) -> tuple[str, str | None]:
    if "==" in specifier:
        name, version = specifier.split("==", maxsplit=1)
        return name, version
    return specifier, None


def write_json_artifact(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def print_status(message: str) -> None:
    print(f"[python-deps] {message}", flush=True)


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


def build_uv_plan_dependencies() -> list[dict[str, Any]]:
    original_lock = UV_LOCK.read_text(encoding="utf-8")
    current_dependencies = build_uv_package_map()
    run(["uv", "lock", "--upgrade"])
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

    return dependencies


def ensure_venv() -> None:
    if not PYTHON.exists():
        run([sys.executable, "-m", "venv", str(VENV_DIR)])


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
    dependencies = []

    for dependency in inventory_artifact["dependencies"]:
        current_version = dependency["current_version"]
        latest_version = None
        update_type = "native-workflow-required"
        will_update = False

        if strategy == "uv-lock":
            dependencies = build_uv_plan_dependencies()
            return {
                "ecosystem": "python",
                "source": str(PYPROJECT.name),
                "strategy_detection": inventory_artifact["strategy_detection"],
                "dependencies": dependencies,
            }

        if strategy == "pip-tools":
            dependencies = build_pip_tools_plan()
            return {
                "ecosystem": "python",
                "source": str(PYPROJECT.name),
                "strategy_detection": inventory_artifact["strategy_detection"],
                "dependencies": dependencies,
            }

        if strategy == "pyproject-exact-pins" and current_version is not None:
            latest_version = latest_pypi_version(dependency["name"])
            update_type = classify_update(current_version, latest_version)
            will_update = current_version != latest_version

        dependencies.append(
            {
                "name": dependency["name"],
                "scope": dependency["scope"],
                "specifier": dependency["specifier"],
                "current_version": current_version,
                "latest_version": latest_version,
                "update_type": update_type,
                "will_update": will_update,
            }
        )

    return {
        "ecosystem": "python",
        "source": str(PYPROJECT.name),
        "strategy_detection": inventory_artifact["strategy_detection"],
        "dependencies": dependencies,
    }


def init() -> None:
    ensure_venv()
    run([str(PYTHON), "-m", "pip", "install", "--upgrade", "pip==26.0.1"])
    run([str(PYTHON), "-m", "pip", "install", "-e", ".[dev]"])


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


def test() -> None:
    if not PYTHON.exists():
        init()
    run([str(PYTHON), "-m", "pytest", "-q", "-s"])


def scan() -> None:
    if not PYTHON.exists():
        init()
    run(
        [
            str(PYTHON),
            "-m",
            "pip_audit",
            "--format",
            "json",
            "--output",
            str(SCANS_DIR / "pip-audit.json"),
        ]
    )


def latest_pypi_version(package_name: str) -> str:
    request_url = f"https://pypi.org/pypi/{package_name}/json"
    with urllib.request.urlopen(request_url, timeout=30) as response:
        data = json.load(response)
    return str(data["info"]["version"])


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
    print_status(
        "plan complete: "
        f"strategy={artifact['strategy_detection']['strategy']} "
        f"planned_updates={planned_updates} "
        f"artifact={plan_path}"
    )
    return artifact


def upgrade() -> None:
    SCANS_DIR.mkdir(parents=True, exist_ok=True)
    dependency_plan = plan()
    strategy = dependency_plan["strategy_detection"]["strategy"]
    print_status(f"starting dependency upgrade with strategy={strategy}")

    if strategy == "uv-lock":
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
        updates.append(
            {
                "name": dependency["name"],
                "scope": dependency["scope"],
                "current_version": current_version,
                "latest_version": latest_version,
                "update_type": dependency["update_type"],
                "updated": str(current_version != latest_version).lower(),
            }
        )
        if current_version != latest_version:
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


COMMANDS = {
    "format": format_code,
    "init": init,
    "inventory": inventory,
    "lint": lint,
    "plan": plan,
    "scan": scan,
    "test": test,
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
