#!/usr/bin/env python3
"""Enter the maintainer devcontainer through the official Dev Containers CLI."""

from __future__ import annotations

import argparse
import base64
import json
import os
import shutil
import hashlib
import subprocess
import sys
import tempfile
from pathlib import Path
from urllib.parse import urlparse


DEFAULT_IMAGE = "ghcr.io/senanayake/polyglot-devcontainers-maintainer:main"
DEFAULT_DEVCONTAINER_CLI_VERSION = "0.84.1"
WORKSPACE_PATH = "/workspaces/polyglot-devcontainers"
ROLE_ENV = "POLYGLOT_CONTAINER_ROLE"
ROLE_VALUE = "maintainer"


def repo_root() -> Path:
    return next(parent for parent in Path(__file__).resolve().parents if (parent / "AGENTS.md").exists())


def image_ref() -> str:
    return os.environ.get("POLYGLOT_MAINTAINER_IMAGE", DEFAULT_IMAGE)


def devcontainer_cli_version() -> str:
    return os.environ.get("POLYGLOT_DEVCONTAINER_CLI_VERSION", DEFAULT_DEVCONTAINER_CLI_VERSION)


def runtime() -> str:
    configured = os.environ.get("POLYGLOT_CONTAINER_RUNTIME")
    candidates = [configured] if configured else ["docker", "podman"]

    for candidate in candidates:
        if not candidate or shutil.which(candidate) is None:
            continue
        try:
            subprocess.run(
                [candidate, "info"],
                check=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                timeout=20,
            )
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired):
            continue
        return candidate

    print(
        "[maintainer-runtime] no healthy container runtime found; tried docker and podman",
        file=sys.stderr,
    )
    raise SystemExit(1)


def resolve_executable(*names: str) -> str | None:
    for name in names:
        resolved = shutil.which(name)
        if resolved:
            return resolved
    return None


def devcontainer_command() -> list[str]:
    devcontainer_path = resolve_executable("devcontainer.cmd", "devcontainer.exe", "devcontainer")
    if devcontainer_path:
        try:
            subprocess.run(
                [devcontainer_path, "--version"],
                check=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                timeout=20,
            )
            return [devcontainer_path]
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired, FileNotFoundError):
            pass

    npm_path = resolve_executable("npm.cmd", "npm.exe", "npm")
    if npm_path is None:
        print(
            "[maintainer-runtime] npm is required to bootstrap the pinned Dev Containers CLI",
            file=sys.stderr,
        )
        raise SystemExit(1)

    return [
        npm_path,
        "exec",
        "--yes",
        f"--package=@devcontainers/cli@{devcontainer_cli_version()}",
        "--",
        "devcontainer",
    ]


def run(command: list[str], *, check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(command, check=check, text=True)


def run_capture(command: list[str]) -> str:
    completed = subprocess.run(
        command,
        check=True,
        capture_output=True,
        text=True,
    )
    return completed.stdout.strip()


def git_mount_flags() -> list[str]:
    flags = ["--mount-workspace-git-root"]

    try:
        git_dir = run_capture(["git", "rev-parse", "--git-dir"])
        git_common_dir = run_capture(["git", "rev-parse", "--git-common-dir"])
    except (subprocess.CalledProcessError, FileNotFoundError):
        return flags

    if git_dir == git_common_dir:
        return flags

    dotgit = repo_root() / ".git"
    if not dotgit.is_file():
        return flags

    contents = dotgit.read_text(encoding="utf-8", errors="replace").strip()
    if not contents.startswith("gitdir:"):
        return flags

    gitdir_path = Path(contents.partition(":")[2].strip())
    if gitdir_path.is_absolute():
        print(
            "[maintainer-runtime] git worktrees require relative paths for container-authoritative "
            "git. Recreate this worktree with `git worktree add --relative-paths` or use a normal "
            "clone / WSL checkout.",
            file=sys.stderr,
        )
        raise SystemExit(1)

    flags.append("--mount-git-worktree-common-dir")
    return flags


def override_config_path() -> str | None:
    if image_ref() == DEFAULT_IMAGE:
        return None

    devcontainer_json = repo_root() / ".devcontainer" / "devcontainer.json"
    config = json.loads(devcontainer_json.read_text(encoding="utf-8"))
    config["image"] = image_ref()
    config.pop("build", None)

    handle = tempfile.NamedTemporaryFile(
        mode="w",
        suffix=".devcontainer.json",
        delete=False,
        encoding="utf-8",
    )
    with handle:
        json.dump(config, handle, indent=2)
        handle.write("\n")
    return handle.name


def common_cli_args(override_config: str | None) -> list[str]:
    image_hash = hashlib.sha256(image_ref().encode("utf-8")).hexdigest()
    args = [
        "--docker-path",
        runtime(),
        "--workspace-folder",
        str(repo_root()),
        "--id-label",
        f"polyglot.maintainer.workspace={repo_root()}",
        "--id-label",
        f"polyglot.maintainer.image={image_hash}",
        "--remote-env",
        f"{ROLE_ENV}={ROLE_VALUE}",
        *git_mount_flags(),
    ]
    if override_config:
        args.extend(["--override-config", override_config])
    return args


def remote_env_args(environment: dict[str, str] | None) -> list[str]:
    if not environment:
        return []

    args: list[str] = []
    for key, value in environment.items():
        args.extend(["--remote-env", f"{key}={value}"])
    return args


def up(override_config: str | None) -> int:
    command = [
        *devcontainer_command(),
        "up",
        *common_cli_args(override_config),
        "--skip-post-create",
    ]
    return run(command, check=False).returncode


def configure_git(override_config: str | None) -> int:
    commands = [
        [
            *devcontainer_command(),
            "exec",
            *common_cli_args(override_config),
            "git",
            "config",
            "--global",
            "core.autocrlf",
            "input",
        ],
        [
            *devcontainer_command(),
            "exec",
            *common_cli_args(override_config),
            "git",
            "config",
            "--global",
            "--add",
            "safe.directory",
            WORKSPACE_PATH,
        ],
    ]

    for command in commands:
        if run(command, check=False).returncode != 0:
            return 1
    return 0


def ensure_up(override_config: str | None) -> int:
    exit_code = up(override_config)
    if exit_code != 0:
        return exit_code
    return configure_git(override_config)


def shell(override_config: str | None) -> int:
    exit_code = ensure_up(override_config)
    if exit_code != 0:
        return exit_code
    command = [
        *devcontainer_command(),
        "exec",
        *common_cli_args(override_config),
        "bash",
        "-l",
    ]
    return run(command, check=False).returncode


def exec_command(argv: list[str], override_config: str | None) -> int:
    if not argv:
        print("usage: run_in_maintainer_container.py exec -- <command...>", file=sys.stderr)
        return 2

    exit_code = ensure_up(override_config)
    if exit_code != 0:
        return exit_code

    command = [
        *devcontainer_command(),
        "exec",
        *common_cli_args(override_config),
        *argv,
    ]
    return run(command, check=False).returncode


def default_remote_name() -> str:
    try:
        branch = run_capture(["git", "branch", "--show-current"])
        if branch:
            configured = run_capture(["git", "config", f"branch.{branch}.remote"])
            if configured:
                return configured
    except subprocess.CalledProcessError:
        pass
    return "origin"


def first_positional_argument(argv: list[str]) -> str | None:
    for value in argv[1:]:
        if value.startswith("-"):
            continue
        return value
    return None


def remote_url_for_git_command(argv: list[str]) -> str | None:
    if not argv:
        return None

    operation = argv[0]
    if operation not in {"push", "fetch", "pull", "ls-remote"}:
        return None

    remote = first_positional_argument(argv) or default_remote_name()
    if "://" in remote:
        return remote

    get_url = ["git", "remote", "get-url"]
    if operation == "push":
        get_url.append("--push")
    get_url.append(remote)
    try:
        return run_capture(get_url)
    except subprocess.CalledProcessError:
        return None


def git_credentials_for_remote(remote_url: str) -> tuple[str, str] | None:
    parsed = urlparse(remote_url)
    if parsed.scheme != "https" or not parsed.hostname:
        return None

    request = [f"protocol={parsed.scheme}", f"host={parsed.hostname}"]
    if parsed.path:
        request.append(f"path={parsed.path.lstrip('/')}")

    try:
        completed = subprocess.run(
            ["git", "credential", "fill"],
            input="\n".join([*request, "", ""]),
            check=True,
            capture_output=True,
            text=True,
        )
    except subprocess.CalledProcessError:
        return None

    values: dict[str, str] = {}
    for line in completed.stdout.splitlines():
        if "=" not in line:
            continue
        key, _, value = line.partition("=")
        values[key] = value

    username = values.get("username")
    password = values.get("password")
    if not username or not password:
        return None
    return username, password


def git_auth_remote_env(argv: list[str]) -> dict[str, str] | None:
    remote_url = remote_url_for_git_command(argv)
    if not remote_url:
        return None

    credentials = git_credentials_for_remote(remote_url)
    if not credentials:
        return None

    parsed = urlparse(remote_url)
    scope = f"{parsed.scheme}://{parsed.netloc}/"
    token = base64.b64encode(f"{credentials[0]}:{credentials[1]}".encode("utf-8")).decode("ascii")
    return {
        "GIT_TERMINAL_PROMPT": "0",
        "GIT_CONFIG_COUNT": "2",
        "GIT_CONFIG_KEY_0": "credential.helper",
        "GIT_CONFIG_VALUE_0": "",
        "GIT_CONFIG_KEY_1": f"http.{scope}.extraheader",
        "GIT_CONFIG_VALUE_1": f"AUTHORIZATION: basic {token}",
    }


def git_command(argv: list[str], override_config: str | None) -> int:
    if not argv:
        print("usage: run_in_maintainer_container.py git -- <args...>", file=sys.stderr)
        return 2

    exit_code = ensure_up(override_config)
    if exit_code != 0:
        return exit_code

    auth_env = git_auth_remote_env(argv)

    command = [
        *devcontainer_command(),
        "exec",
        *common_cli_args(override_config),
        *remote_env_args(auth_env),
        "git",
        "-c",
        "core.autocrlf=input",
        *argv,
    ]
    return run(command, check=False).returncode


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("up")
    subparsers.add_parser("pull")
    subparsers.add_parser("shell")

    exec_parser = subparsers.add_parser("exec")
    exec_parser.add_argument("argv", nargs=argparse.REMAINDER)

    git_parser = subparsers.add_parser("git")
    git_parser.add_argument("argv", nargs=argparse.REMAINDER)

    return parser.parse_args()


def main() -> int:
    args = parse_args()
    override = override_config_path()

    try:
        if args.command in {"up", "pull"}:
            return up(override)
        if args.command == "shell":
            return shell(override)
        if args.command == "exec":
            argv = args.argv
            if argv and argv[0] == "--":
                argv = argv[1:]
            return exec_command(argv, override)
        if args.command == "git":
            argv = args.argv
            if argv and argv[0] == "--":
                argv = argv[1:]
            return git_command(argv, override)
        return 2
    finally:
        if override:
            try:
                Path(override).unlink(missing_ok=True)
            except OSError:
                pass


if __name__ == "__main__":
    raise SystemExit(main())
