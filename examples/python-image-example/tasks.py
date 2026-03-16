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


def find_matching_files(pattern: str) -> list[str]:
    return sorted(str(path.relative_to(ROOT)) for path in ROOT.rglob(pattern))


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
        upgrade_command_candidates = ["pip-compile <requirements.in> --upgrade"]
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
    if not PYTHON.exists():
        run([sys.executable, "-m", "venv", str(VENV_DIR)])
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
    artifact = build_inventory_artifact()
    write_json_artifact(SCANS_DIR / "dependency-inventory.json", artifact)
    return artifact


def plan() -> dict[str, Any]:
    SCANS_DIR.mkdir(parents=True, exist_ok=True)
    artifact = build_plan_artifact()
    write_json_artifact(SCANS_DIR / "dependency-plan.json", artifact)
    return artifact


def upgrade() -> None:
    SCANS_DIR.mkdir(parents=True, exist_ok=True)
    dependency_plan = plan()
    strategy = dependency_plan["strategy_detection"]["strategy"]

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
        return

    if strategy != "pyproject-exact-pins":
        raise SystemExit(
            "task upgrade currently supports only the 'pyproject-exact-pins' strategy; "
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
