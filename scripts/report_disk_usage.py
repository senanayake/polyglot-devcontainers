#!/usr/bin/env python3
"""Capture host or container disk-usage diagnostics for CI investigation."""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = next(parent for parent in Path(__file__).resolve().parents if (parent / "AGENTS.md").exists())
DEFAULT_OUTPUT_ROOT = ROOT / ".artifacts" / "diagnostics"
DEFAULT_PATHS = [
    ".artifacts/images",
    ".artifacts/scans",
    ".artifacts/scenarios",
    ".tmp/starter-proving",
]
RUNTIME_CANDIDATE_ENV_VARS = ("POLYGLOT_OCI_RUNTIME", "POLYGLOT_CONTAINER_RUNTIME")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--label", required=True)
    parser.add_argument("--output-root", type=Path, default=DEFAULT_OUTPUT_ROOT)
    return parser.parse_args()


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def slugify(value: str) -> str:
    safe = []
    for char in value.lower():
        if char.isalnum():
            safe.append(char)
        else:
            safe.append("-")
    slug = "".join(safe).strip("-")
    return slug or "snapshot"


def in_container() -> bool:
    return Path("/.dockerenv").exists() or Path("/run/.containerenv").exists()


def run_command(
    command: list[str],
    *,
    cwd: Path | None = None,
    timeout_seconds: int = 180,
) -> dict[str, Any]:
    try:
        completed = subprocess.run(
            command,
            cwd=cwd,
            capture_output=True,
            text=True,
            check=False,
            timeout=timeout_seconds,
        )
    except FileNotFoundError as exc:
        return {
            "command": command,
            "ok": False,
            "error": str(exc),
        }
    except subprocess.TimeoutExpired as exc:
        return {
            "command": command,
            "ok": False,
            "error": f"timed out after {exc.timeout} seconds",
        }

    return {
        "command": command,
        "ok": completed.returncode == 0,
        "returncode": completed.returncode,
        "stdout": completed.stdout,
        "stderr": completed.stderr,
    }


def collect_path_usage(paths: list[str]) -> list[dict[str, Any]]:
    results: list[dict[str, Any]] = []
    for relative in paths:
        resolved = ROOT / relative
        entry: dict[str, Any] = {
            "path": relative,
            "exists": resolved.exists(),
        }
        if not resolved.exists():
            results.append(entry)
            continue

        bytes_result = run_command(["du", "-sb", str(resolved)])
        bytes_value = None
        if bytes_result.get("ok"):
            raw_value = bytes_result.get("stdout", "").strip().split(maxsplit=1)
            if raw_value:
                bytes_value = raw_value[0]
        entry["bytes"] = bytes_value
        entry["human"] = humanize_bytes(int(bytes_value)) if bytes_value and bytes_value.isdigit() else None
        entry["bytes_error"] = None if bytes_result.get("ok") else bytes_result.get("error") or bytes_result.get("stderr", "").strip()
        results.append(entry)
    return results


def humanize_bytes(value: int) -> str:
    suffixes = ["B", "KiB", "MiB", "GiB", "TiB"]
    amount = float(value)
    for suffix in suffixes:
        if amount < 1024.0 or suffix == suffixes[-1]:
            if suffix == "B":
                return f"{int(amount)} {suffix}"
            return f"{amount:.1f} {suffix}"
        amount /= 1024.0
    return f"{value} B"


def configured_runtimes() -> list[str]:
    for env_var in RUNTIME_CANDIDATE_ENV_VARS:
        configured = os.environ.get(env_var)
        if configured:
            return [configured]
    return ["podman", "docker"]


def preferred_runtime_quick() -> str:
    failures: list[str] = []
    for runtime_name in configured_runtimes():
        if shutil.which(runtime_name) is None:
            failures.append(f"{runtime_name} CLI is not installed")
            continue
        result = run_command([runtime_name, "info"], timeout_seconds=10)
        if result.get("ok"):
            return runtime_name
        failures.append(
            result.get("error")
            or result.get("stderr", "").strip()
            or f"{runtime_name} runtime is not reachable"
        )
    raise RuntimeError("; ".join(failures) or "no healthy OCI runtime found")


def collect_oci_runtime_usage() -> dict[str, Any]:
    try:
        runtime_name = preferred_runtime_quick()
    except RuntimeError as exc:
        return {
            "available": False,
            "error": str(exc),
        }

    system_df = run_command([runtime_name, "system", "df"])
    image_ls = run_command([runtime_name, "image", "ls", "--format", "{{.Repository}}:{{.Tag}}\t{{.Size}}"])
    return {
        "available": True,
        "runtime": runtime_name,
        "system_df": system_df,
        "image_ls": image_ls,
    }


def collect_snapshot(label: str) -> dict[str, Any]:
    return {
        "label": label,
        "captured_at": utc_now(),
        "cwd": str(Path.cwd()),
        "repo_root": str(ROOT),
        "in_container": in_container(),
        "environment": {
            "POLYGLOT_CONTAINER_RUNTIME": os.environ.get("POLYGLOT_CONTAINER_RUNTIME"),
            "POLYGLOT_OCI_RUNTIME": os.environ.get("POLYGLOT_OCI_RUNTIME"),
            "POLYGLOT_MAINTAINER_IMAGE": os.environ.get("POLYGLOT_MAINTAINER_IMAGE"),
        },
        "df_human": run_command(["df", "-h"]),
        "df_bytes": run_command(["df", "-B1"]),
        "path_usage": collect_path_usage(DEFAULT_PATHS),
        "oci_runtime": collect_oci_runtime_usage(),
    }


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def markdown_command(title: str, result: dict[str, Any]) -> list[str]:
    lines = [f"## {title}", ""]
    if not result.get("ok"):
        lines.append(f"- status: `failed`")
        error = result.get("error") or result.get("stderr", "").strip() or "unknown error"
        lines.append(f"- error: `{error}`")
        lines.append("")
        return lines

    lines.append("- status: `ok`")
    lines.append("")
    output = result.get("stdout", "").strip()
    if output:
        lines.append("```text")
        lines.append(output)
        lines.append("```")
        lines.append("")
    stderr = result.get("stderr", "").strip()
    if stderr:
        lines.append("stderr:")
        lines.append("```text")
        lines.append(stderr)
        lines.append("```")
        lines.append("")
    return lines


def write_markdown(path: Path, snapshot: dict[str, Any]) -> None:
    lines = [
        f"# Disk Usage Snapshot: {snapshot['label']}",
        "",
        f"- captured_at: `{snapshot['captured_at']}`",
        f"- cwd: `{snapshot['cwd']}`",
        f"- in_container: `{snapshot['in_container']}`",
        f"- runtime_env: `{snapshot['environment']['POLYGLOT_CONTAINER_RUNTIME'] or ''}`",
        f"- oci_env: `{snapshot['environment']['POLYGLOT_OCI_RUNTIME'] or ''}`",
        f"- maintainer_image: `{snapshot['environment']['POLYGLOT_MAINTAINER_IMAGE'] or ''}`",
        "",
        "## Targeted Paths",
        "",
        "| Path | Exists | Bytes | Human |",
        "|------|--------|-------|-------|",
    ]

    for entry in snapshot["path_usage"]:
        lines.append(
            f"| `{entry['path']}` | `{entry['exists']}` | "
            f"`{entry.get('bytes') or ''}` | `{entry.get('human') or ''}` |"
        )

    lines.append("")
    lines.extend(markdown_command("df -h", snapshot["df_human"]))
    lines.extend(markdown_command("df -B1", snapshot["df_bytes"]))

    oci_runtime = snapshot["oci_runtime"]
    lines.append("## OCI Runtime")
    lines.append("")
    if not oci_runtime.get("available"):
        lines.append(f"- status: `unavailable`")
        lines.append(f"- error: `{oci_runtime.get('error', 'unknown error')}`")
        lines.append("")
    else:
        lines.append(f"- runtime: `{oci_runtime['runtime']}`")
        lines.append("")
        lines.extend(markdown_command(f"{oci_runtime['runtime']} system df", oci_runtime["system_df"]))
        lines.extend(markdown_command(f"{oci_runtime['runtime']} image ls", oci_runtime["image_ls"]))

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def print_summary(snapshot: dict[str, Any], json_path: Path, markdown_path: Path) -> None:
    runtime_name = snapshot["oci_runtime"].get("runtime") if snapshot["oci_runtime"].get("available") else "unavailable"
    print(
        "[disk-usage] "
        f"label={snapshot['label']} "
        f"in_container={snapshot['in_container']} "
        f"runtime={runtime_name} "
        f"json={json_path} "
        f"markdown={markdown_path}",
        flush=True,
    )
    for entry in snapshot["path_usage"]:
        if entry["exists"]:
            print(
                "[disk-usage] "
                f"label={snapshot['label']} "
                f"path={entry['path']} "
                f"bytes={entry.get('bytes') or 'unknown'} "
                f"human={entry.get('human') or 'unknown'}",
                flush=True,
            )


def main() -> int:
    args = parse_args()
    output_root = args.output_root if args.output_root.is_absolute() else ROOT / args.output_root
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    slug = slugify(args.label)
    json_path = output_root / f"{timestamp}-{slug}.json"
    markdown_path = output_root / f"{timestamp}-{slug}.md"

    snapshot = collect_snapshot(args.label)
    write_json(json_path, snapshot)
    write_markdown(markdown_path, snapshot)
    print_summary(snapshot, json_path, markdown_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
