from __future__ import annotations

import json
import os
import subprocess
import sys
import tomllib
import urllib.request
from pathlib import Path

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


def upgrade() -> None:
    SCANS_DIR.mkdir(parents=True, exist_ok=True)
    data = tomllib.loads(PYPROJECT.read_text(encoding="utf-8"))
    dependencies = data["project"]["optional-dependencies"]["dev"]
    updates: list[dict[str, str]] = []
    content = PYPROJECT.read_text(encoding="utf-8")

    for dependency in dependencies:
        name, current_version = dependency.split("==", maxsplit=1)
        latest_version = latest_pypi_version(name)
        updates.append(
            {
                "name": name,
                "current_version": current_version,
                "latest_version": latest_version,
                "updated": str(current_version != latest_version).lower(),
            }
        )
        if current_version != latest_version:
            content = content.replace(
                f'"{name}=={current_version}"',
                f'"{name}=={latest_version}"',
            )

    PYPROJECT.write_text(content, encoding="utf-8")
    (SCANS_DIR / "pypi-upgrades.json").write_text(
        json.dumps({"dependencies": updates}, indent=2) + "\n",
        encoding="utf-8",
    )


COMMANDS = {
    "format": format_code,
    "init": init,
    "lint": lint,
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
