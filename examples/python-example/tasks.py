from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
TMP_DIR = ROOT / ".tmp"
VENV_DIR = ROOT / ".venv"
ARTIFACTS_DIR = ROOT / ".artifacts"
SCANS_DIR = ARTIFACTS_DIR / "scans"
REPO_ROOT = next(
    parent for parent in Path(__file__).resolve().parents if (parent / "AGENTS.md").exists()
)
RUNTIME_GUARD = REPO_ROOT / "scripts" / "require_maintainer_container.py"
PYTHON_AUDIT_POLICY = REPO_ROOT / "security-scan-policy.toml"
PYTHON_AUDIT_EVALUATOR = REPO_ROOT / "scripts" / "evaluate_python_audit_policy.py"
PYTHON = VENV_DIR / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
UV = "uv.exe" if os.name == "nt" else "uv"


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
        command,
        cwd=ROOT,
        check=check,
        text=True,
        capture_output=capture_output,
        env=env,
    )


def require_maintainer() -> None:
    subprocess.run([sys.executable, str(RUNTIME_GUARD)], cwd=ROOT, check=True)


def init() -> None:
    run([UV, "sync", "--frozen", "--extra", "dev"])


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
    audit_report = SCANS_DIR / "pip-audit.json"
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
    run(
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
        ]
    )


COMMANDS = {
    "format": format_code,
    "init": init,
    "lint": lint,
    "test": test,
    "scan": scan,
}


def main() -> int:
    if len(sys.argv) != 2 or sys.argv[1] not in COMMANDS:
        print(f"usage: {Path(sys.argv[0]).name} [{'|'.join(COMMANDS)}]")
        return 1

    require_maintainer()
    COMMANDS[sys.argv[1]]()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
