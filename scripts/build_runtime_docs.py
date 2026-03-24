from __future__ import annotations

import shutil
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
CORE_DIR = ROOT / "docs" / "core"
MAN_DIR = ROOT / "man" / "man7"
TEMPLATE_MAN_DIRS = [
    ROOT / "templates" / "python-secure" / "man" / "man7",
    ROOT / "templates" / "python-node-secure" / "man" / "man7",
    ROOT / "templates" / "java-secure" / "man" / "man7",
]
TEMPLATE_SCRIPT_DIRS = [
    ROOT / "templates" / "python-secure" / "scripts",
    ROOT / "templates" / "python-node-secure" / "scripts",
    ROOT / "templates" / "java-secure" / "scripts",
]
INSTALL_SCRIPT = ROOT / "scripts" / "install_runtime_docs.sh"


def run(command: list[str]) -> None:
    subprocess.run(command, cwd=ROOT, check=True)


def pandoc_command(source: Path, output: Path) -> list[str]:
    if shutil.which("pandoc"):
        return ["pandoc", "--standalone", "--to", "man", str(source), "--output", str(output)]

    for runtime in ("podman", "docker"):
        if shutil.which(runtime):
            return [
                runtime,
                "run",
                "--rm",
                "-v",
                f"{ROOT}:/data",
                "-w",
                "/data",
                "docker.io/pandoc/core",
                "--standalone",
                "--to",
                "man",
                str(source.relative_to(ROOT)).replace("\\", "/"),
                "--output",
                str(output.relative_to(ROOT)).replace("\\", "/"),
            ]

    raise SystemExit("pandoc, podman, or docker is required to build runtime docs")


def main() -> int:
    MAN_DIR.mkdir(parents=True, exist_ok=True)

    for source in sorted(CORE_DIR.glob("*.md")):
        output = MAN_DIR / f"{source.stem}.7"
        run(pandoc_command(source, output))

    for template_man_dir in TEMPLATE_MAN_DIRS:
        template_man_dir.mkdir(parents=True, exist_ok=True)
        for page in MAN_DIR.glob("*.7"):
            shutil.copy2(page, template_man_dir / page.name)

    for template_script_dir in TEMPLATE_SCRIPT_DIRS:
        template_script_dir.mkdir(parents=True, exist_ok=True)
        shutil.copy2(INSTALL_SCRIPT, template_script_dir / INSTALL_SCRIPT.name)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
