from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
BACKEND_DIR = ROOT / "backend"
TMP_DIR = ROOT / ".tmp"
ARTIFACTS_DIR = ROOT / ".artifacts"
SCANS_DIR = ARTIFACTS_DIR / "scans"
PYTHON_AUDIT_POLICY = ROOT / "security-scan-policy.toml"
PYTHON_AUDIT_EVALUATOR = ROOT / "scripts" / "evaluate_python_audit_policy.py"
VENV_DIR = ROOT / ".venv"
PYTHON = VENV_DIR / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
UV = "uv.exe" if os.name == "nt" else "uv"
COREPACK = "corepack.cmd" if os.name == "nt" else "corepack"
PNPM = [COREPACK, "pnpm"]
GITLEAKS_FALLBACK_PATHS = [
    BACKEND_DIR,
    ROOT / "frontend",
    ROOT / ".devcontainer",
    ROOT / "Taskfile.yml",
    ROOT / "tasks.py",
    ROOT / "security-scan-policy.toml",
    ROOT / "pyproject.toml",
    ROOT / "uv.lock",
    ROOT / "package.json",
    ROOT / "pnpm-lock.yaml",
    ROOT / "tsconfig.json",
    ROOT / "eslint.config.mjs",
    ROOT / "prettier.config.mjs",
    ROOT / "vitest.config.ts",
    ROOT / ".pre-commit-config.yaml",
    ROOT / "README.md",
    ROOT / "man",
    ROOT / "scenarios",
    ROOT / "scripts",
]


def run(command: list[str], *, check: bool = True) -> subprocess.CompletedProcess[str]:
    TMP_DIR.mkdir(exist_ok=True)
    SCANS_DIR.mkdir(parents=True, exist_ok=True)
    env = os.environ.copy()
    env["TMP"] = str(TMP_DIR.resolve())
    env["TEMP"] = str(TMP_DIR.resolve())
    env["TMPDIR"] = str(TMP_DIR.resolve())
    return subprocess.run(command, cwd=ROOT, check=check, text=True, env=env)


def reset_invalid_venv() -> None:
    if VENV_DIR.exists() and not PYTHON.exists():
        shutil.rmtree(VENV_DIR)


def prepare_gitleaks_dir_fallback() -> Path:
    scan_root = TMP_DIR / "gitleaks-source-scan"
    if scan_root.exists():
        shutil.rmtree(scan_root)
    scan_root.mkdir(parents=True)

    for source in GITLEAKS_FALLBACK_PATHS:
        if not source.exists():
            continue
        destination = scan_root / source.relative_to(ROOT)
        destination.parent.mkdir(parents=True, exist_ok=True)
        if source.is_dir():
            shutil.copytree(source, destination)
        else:
            shutil.copy2(source, destination)

    return scan_root


def write_json_artifact(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def init() -> None:
    reset_invalid_venv()
    run([UV, "sync", "--frozen", "--extra", "dev"])
    run(PNPM + ["install", "--frozen-lockfile", "--force"])


def lint() -> None:
    reset_invalid_venv()
    if not PYTHON.exists():
        init()
    python_paths = [str(BACKEND_DIR / "src"), str(BACKEND_DIR / "tests"), "tasks.py", "scripts"]
    run([str(PYTHON), "-m", "ruff", "check", *python_paths])
    run([str(PYTHON), "-m", "ruff", "format", "--check", *python_paths])
    run([str(PYTHON), "-m", "mypy", *python_paths])
    run(PNPM + ["lint"])
    run(PNPM + ["format:check"])
    run(PNPM + ["typecheck"])


def format_code() -> None:
    reset_invalid_venv()
    if not PYTHON.exists():
        init()
    python_paths = [str(BACKEND_DIR / "src"), str(BACKEND_DIR / "tests"), "tasks.py", "scripts"]
    run([str(PYTHON), "-m", "ruff", "check", "--fix", *python_paths])
    run([str(PYTHON), "-m", "ruff", "format", *python_paths])
    run(PNPM + ["format"])


def test() -> None:
    """Fast suite - skips Python integration tests."""
    reset_invalid_venv()
    if not PYTHON.exists():
        init()
    run([str(PYTHON), "-m", "pytest", "-q", "-s", "-m", "not integration"])
    run(PNPM + ["test"])


def test_integration() -> None:
    """Live Python integration tests only."""
    reset_invalid_venv()
    if not PYTHON.exists():
        init()
    run([str(PYTHON), "-m", "pytest", "-q", "-s", "-m", "integration"])


def test_all() -> None:
    """Full suite."""
    reset_invalid_venv()
    if not PYTHON.exists():
        init()
    run([str(PYTHON), "-m", "pytest", "-q", "-s"])
    run(PNPM + ["test"])


def scan() -> None:
    reset_invalid_venv()
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
    with (SCANS_DIR / "pnpm-audit.json").open("w", encoding="utf-8") as report:
        subprocess.run(
            PNPM + ["audit", "--prod", "--audit-level", "high", "--json"],
            cwd=ROOT,
            check=True,
            text=True,
            env=os.environ.copy(),
            stdout=report,
        )
    gitleaks_target = prepare_gitleaks_dir_fallback()
    gitleaks_mode = "dir"

    write_json_artifact(
        SCANS_DIR / "gitleaks-mode.json",
        {
            "mode": gitleaks_mode,
            "target": str(gitleaks_target),
        },
    )

    try:
        run(
            [
                "gitleaks",
                gitleaks_mode,
                str(gitleaks_target),
                "--no-banner",
                "--redact",
                "--report-format",
                "sarif",
                "--report-path",
                str(SCANS_DIR / "gitleaks.sarif"),
            ]
        )
    finally:
        if gitleaks_target.is_relative_to(TMP_DIR) and gitleaks_target.exists():
            shutil.rmtree(gitleaks_target, ignore_errors=True)


COMMANDS = {
    "format": format_code,
    "init": init,
    "lint": lint,
    "scan": scan,
    "test": test,
    "test_all": test_all,
    "test_integration": test_integration,
}


def main() -> int:
    if len(sys.argv) != 2 or sys.argv[1] not in COMMANDS:
        print(f"usage: {Path(sys.argv[0]).name} [{'|'.join(COMMANDS)}]")
        return 1
    COMMANDS[sys.argv[1]]()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
