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
    project = read_project_metadata()["project"]
    dependencies: list[dict[str, str]] = []

    for dependency in project.get("dependencies", []):
        dependencies.append({"scope": "runtime", "specifier": dependency})

    for scope, scoped_dependencies in project.get("optional-dependencies", {}).items():
        for dependency in scoped_dependencies:
            dependencies.append({"scope": scope, "specifier": dependency})

    return dependencies


def parse_exact_pin(specifier: str) -> tuple[str, str | None]:
    if "==" in specifier:
        name, version = specifier.split("==", maxsplit=1)
        return name, version
    return specifier, None


def write_json_artifact(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


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
    dependencies = []

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

    artifact = {
        "ecosystem": "python",
        "source": str(PYPROJECT.name),
        "dependencies": dependencies,
    }
    write_json_artifact(SCANS_DIR / "dependency-inventory.json", artifact)
    return artifact


def plan() -> dict[str, Any]:
    SCANS_DIR.mkdir(parents=True, exist_ok=True)
    dependencies = []

    for dependency in iter_declared_dependencies():
        name, current_version = parse_exact_pin(dependency["specifier"])
        latest_version = latest_pypi_version(name) if current_version is not None else None
        dependencies.append(
            {
                "name": name,
                "scope": dependency["scope"],
                "specifier": dependency["specifier"],
                "current_version": current_version,
                "latest_version": latest_version,
                "update_type": (
                    classify_update(current_version, latest_version)
                    if current_version is not None and latest_version is not None
                    else "unmanaged"
                ),
                "will_update": (
                    current_version is not None
                    and latest_version is not None
                    and current_version != latest_version
                ),
            }
        )

    artifact = {
        "ecosystem": "python",
        "source": str(PYPROJECT.name),
        "dependencies": dependencies,
    }
    write_json_artifact(SCANS_DIR / "dependency-plan.json", artifact)
    return artifact


def upgrade() -> None:
    SCANS_DIR.mkdir(parents=True, exist_ok=True)
    dependency_plan = plan()
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
        {"ecosystem": "python", "source": str(PYPROJECT.name), "dependencies": updates},
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
