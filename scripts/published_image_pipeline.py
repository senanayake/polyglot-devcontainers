#!/usr/bin/env python3
"""Plan and execute published-image validation lanes."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import tomllib
from dataclasses import dataclass
from pathlib import Path
from typing import Any


ROOT = next(parent for parent in Path(__file__).resolve().parents if (parent / "AGENTS.md").exists())
CATALOG_PATH = ROOT / "published-image-catalog.toml"
IMAGE_ARTIFACT_ROOT = ROOT / ".artifacts" / "images"
IMAGE_SCAN_ROOT = ROOT / ".artifacts" / "scans" / "image-security"
RUNTIME_GUIDANCE_COMMAND = "man polyglot >/dev/null && man polyglot-scenarios >/dev/null"
SUPPORTED_PROFILES = ("fast", "medium", "full-release")


@dataclass(frozen=True)
class StarterProof:
    starter_id: str
    profile_id: str


@dataclass(frozen=True)
class ImageTarget:
    package_name: str
    target_id: str
    description: str
    context: str
    dockerfile: str
    devcontainer_json: str
    workdir: str
    verify_tag: str
    artifact_name: str
    medium_lane: bool
    smoke_test: bool
    smoke_test_run_scenarios: bool
    starter_proofs: tuple[StarterProof, ...]


@dataclass(frozen=True)
class BuildBehavior:
    save: bool
    smoke: bool
    inner_ci: bool


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("list")

    matrix_parser = subparsers.add_parser("matrix")
    matrix_parser.add_argument("--profile", choices=SUPPORTED_PROFILES, required=True)
    matrix_parser.add_argument("--image", action="append", default=[])

    build_parser = subparsers.add_parser("build")
    build_parser.add_argument("--profile", choices=SUPPORTED_PROFILES, default="fast")
    build_parser.add_argument("--image", action="append", default=[])
    build_parser.add_argument("--save", action=argparse.BooleanOptionalAction, default=None)
    build_parser.add_argument("--smoke", action=argparse.BooleanOptionalAction, default=None)
    build_parser.add_argument("--inner-ci", action=argparse.BooleanOptionalAction, default=None)
    build_parser.add_argument("--disk-label-prefix")

    starter_parser = subparsers.add_parser("starter-proof")
    starter_parser.add_argument("--profile", choices=SUPPORTED_PROFILES, default="medium")
    starter_parser.add_argument("--build-profile", choices=SUPPORTED_PROFILES, default="fast")
    starter_parser.add_argument("--image", action="append", default=[])
    starter_parser.add_argument("--disk-label-prefix")

    scan_parser = subparsers.add_parser("scan")
    scan_parser.add_argument("--profile", choices=SUPPORTED_PROFILES, default="full-release")
    scan_parser.add_argument("--image", action="append", default=[])

    return parser.parse_args()


def catalog_payload() -> dict[str, Any]:
    payload = tomllib.loads(CATALOG_PATH.read_text(encoding="utf-8"))
    if payload.get("catalog_version") != 1:
        raise SystemExit(
            f"unsupported catalog_version in {CATALOG_PATH}: {payload.get('catalog_version')!r}"
        )
    images = payload.get("images")
    if not isinstance(images, dict):
        raise SystemExit(f"expected [images] table in {CATALOG_PATH}")
    return images


def starter_proofs_from_value(raw: object) -> tuple[StarterProof, ...]:
    if not isinstance(raw, list):
        raise SystemExit("starter_proofs must be a list")
    proofs: list[StarterProof] = []
    for entry in raw:
        if not isinstance(entry, dict):
            raise SystemExit("starter_proofs entries must be inline tables")
        starter_id = entry.get("starter")
        profile_id = entry.get("profile")
        if not isinstance(starter_id, str) or not starter_id:
            raise SystemExit("starter_proofs entry missing starter")
        if not isinstance(profile_id, str) or not profile_id:
            raise SystemExit("starter_proofs entry missing profile")
        proofs.append(StarterProof(starter_id=starter_id, profile_id=profile_id))
    return tuple(proofs)


def load_targets() -> list[ImageTarget]:
    targets: list[ImageTarget] = []
    for package_name, entry in catalog_payload().items():
        if not isinstance(entry, dict):
            raise SystemExit(f"catalog entry for {package_name!r} must be a table")
        target = ImageTarget(
            package_name=str(package_name),
            target_id=require_string(entry, "target_id", package_name),
            description=require_string(entry, "description", package_name),
            context=require_string(entry, "context", package_name),
            dockerfile=require_string(entry, "dockerfile", package_name),
            devcontainer_json=require_string(entry, "devcontainer_json", package_name),
            workdir=require_string(entry, "workdir", package_name),
            verify_tag=require_string(entry, "verify_tag", package_name),
            artifact_name=require_string(entry, "artifact_name", package_name),
            medium_lane=require_bool(entry, "medium_lane", package_name),
            smoke_test=require_bool(entry, "smoke_test", package_name),
            smoke_test_run_scenarios=require_bool(entry, "smoke_test_run_scenarios", package_name),
            starter_proofs=starter_proofs_from_value(entry.get("starter_proofs", [])),
        )
        validate_target_paths(target)
        targets.append(target)
    return sorted(targets, key=lambda item: item.target_id)


def require_string(entry: dict[str, Any], key: str, package_name: str) -> str:
    value = entry.get(key)
    if not isinstance(value, str) or not value:
        raise SystemExit(f"catalog entry {package_name!r} is missing {key}")
    return value


def require_bool(entry: dict[str, Any], key: str, package_name: str) -> bool:
    value = entry.get(key)
    if not isinstance(value, bool):
        raise SystemExit(f"catalog entry {package_name!r} is missing boolean {key}")
    return value


def validate_target_paths(target: ImageTarget) -> None:
    for relative in (target.context, target.dockerfile, target.devcontainer_json):
        path = (ROOT / relative).resolve()
        try:
            path.relative_to(ROOT.resolve())
        except ValueError as error:
            raise SystemExit(f"path escapes repository root: {relative}") from error
        if not path.exists():
            raise SystemExit(f"catalog path does not exist: {relative}")


def build_defaults(profile: str) -> BuildBehavior:
    if profile == "fast":
        return BuildBehavior(save=False, smoke=False, inner_ci=False)
    if profile == "medium":
        return BuildBehavior(save=False, smoke=True, inner_ci=False)
    if profile == "full-release":
        return BuildBehavior(save=True, smoke=True, inner_ci=True)
    raise SystemExit(f"unsupported profile: {profile}")


def resolve_targets(image_filters: list[str], profile: str) -> list[ImageTarget]:
    targets = load_targets()
    if image_filters:
        resolved: list[ImageTarget] = []
        for raw in image_filters:
            selected = find_target(targets, raw)
            if selected not in resolved:
                resolved.append(selected)
        return resolved

    if profile == "full-release":
        return targets

    selected = [target for target in targets if target.medium_lane]
    if not selected:
        raise SystemExit(f"profile {profile!r} resolved no targets")
    return selected


def find_target(targets: list[ImageTarget], raw: str) -> ImageTarget:
    lowered = raw.strip().lower()
    for target in targets:
        candidates = {
            target.target_id.lower(),
            target.package_name.lower(),
            target.artifact_name.lower(),
            target.verify_tag.lower(),
        }
        if lowered in candidates:
            return target
    available = ", ".join(target.target_id for target in targets)
    raise SystemExit(f"unknown image target {raw!r}; available: {available}")


def starter_override_env_name(starter_id: str) -> str:
    normalized = starter_id.upper().replace("-", "_")
    return f"POLYGLOT_STARTER_PROOF_IMAGE_{normalized}"


def matrix_payload(targets: list[ImageTarget]) -> dict[str, Any]:
    include: list[dict[str, Any]] = []
    for target in targets:
        include.append(
            {
                "target_id": target.target_id,
                "package_name": target.package_name,
                "description": target.description,
                "context": target.context,
                "dockerfile": target.dockerfile,
                "devcontainer_json": target.devcontainer_json,
                "workdir": target.workdir,
                "verify_tag": target.verify_tag,
                "artifact_name": target.artifact_name,
                "medium_lane": target.medium_lane,
                "smoke_test": target.smoke_test,
                "smoke_test_run_scenarios": target.smoke_test_run_scenarios,
                "starter_proofs": [
                    {"starter": proof.starter_id, "profile": proof.profile_id}
                    for proof in target.starter_proofs
                ],
            }
        )
    return {"include": include}


def run(command: list[str], *, env: dict[str, str] | None = None) -> None:
    subprocess.run(command, cwd=ROOT, check=True, text=True, env=env)


def run_disk_snapshot(label: str) -> None:
    run([sys.executable, "scripts/report_disk_usage.py", "--label", label])


def build_targets(
    targets: list[ImageTarget],
    *,
    behavior: BuildBehavior,
    disk_label_prefix: str | None,
) -> None:
    IMAGE_ARTIFACT_ROOT.mkdir(parents=True, exist_ok=True)
    if disk_label_prefix:
        run_disk_snapshot(f"{disk_label_prefix}-pre-build")

    try:
        for target in targets:
            artifact_path = IMAGE_ARTIFACT_ROOT / f"{target.artifact_name}.tar"
            if behavior.save:
                artifact_path.unlink(missing_ok=True)

            run(
                [
                    sys.executable,
                    "scripts/oci_runtime.py",
                    "build",
                    "--pull",
                    "--file",
                    target.dockerfile,
                    "--tag",
                    target.verify_tag,
                    target.context,
                ]
            )
            run(
                [
                    sys.executable,
                    "scripts/validate_devcontainer_metadata.py",
                    "--image",
                    target.verify_tag,
                    "--devcontainer-json",
                    target.devcontainer_json,
                ]
            )

            if behavior.save:
                run(
                    [
                        sys.executable,
                        "scripts/oci_runtime.py",
                        "save",
                        "--output",
                        str(artifact_path),
                        target.verify_tag,
                    ]
                )

            if behavior.smoke and target.smoke_test:
                smoke_command = [
                    "bash",
                    "scripts/smoke_test_published_starter.sh",
                    "--image",
                    target.verify_tag,
                ]
                if target.smoke_test_run_scenarios:
                    smoke_command.append("--run-scenarios")
                run(smoke_command)

            if behavior.inner_ci:
                run(
                    [
                        sys.executable,
                        "scripts/oci_runtime.py",
                        "run",
                        "--rm",
                        "-u",
                        "root",
                        "-v",
                        f"{ROOT}:/workspaces/polyglot-devcontainers",
                        "-w",
                        target.workdir,
                        target.verify_tag,
                        "bash",
                        "-lc",
                        (
                            "git config --global --add safe.directory /workspaces/polyglot-devcontainers"
                            f" && {RUNTIME_GUIDANCE_COMMAND} && task ci"
                        ),
                    ]
                )
    finally:
        if disk_label_prefix:
            run_disk_snapshot(f"{disk_label_prefix}-post-build")


def starter_proof_targets(targets: list[ImageTarget]) -> list[ImageTarget]:
    selected = [target for target in targets if target.starter_proofs]
    if not selected:
        raise SystemExit("selected image targets do not define published-image starter proofs")
    return selected


def run_starter_proofs(
    targets: list[ImageTarget],
    *,
    build_profile: str,
    disk_label_prefix: str | None,
) -> None:
    build_targets(
        starter_proof_targets(targets),
        behavior=build_defaults(build_profile),
        disk_label_prefix=disk_label_prefix,
    )

    for target in starter_proof_targets(targets):
        for proof in target.starter_proofs:
            environment = os.environ.copy()
            environment[starter_override_env_name(proof.starter_id)] = target.verify_tag
            command = [
                sys.executable,
                "scripts/starter_catalog.py",
                "prove",
                "--starter",
                proof.starter_id,
                "--mode",
                "published-image-bootstrap",
                "--profile",
                proof.profile_id,
            ]
            run(command, env=environment)


def run_scan(targets: list[ImageTarget]) -> None:
    selected = [target for target in targets if (IMAGE_ARTIFACT_ROOT / f"{target.artifact_name}.tar").exists()]
    if len(selected) != len(targets):
        missing = [
            target.target_id
            for target in targets
            if not (IMAGE_ARTIFACT_ROOT / f"{target.artifact_name}.tar").exists()
        ]
        missing_text = ", ".join(missing)
        raise SystemExit(
            f"missing saved image tar artifacts for: {missing_text}. "
            "Run build with --save first."
        )

    IMAGE_SCAN_ROOT.mkdir(parents=True, exist_ok=True)
    report_args: list[str] = []
    for target in selected:
        tar_path = IMAGE_ARTIFACT_ROOT / f"{target.artifact_name}.tar"
        report_path = IMAGE_SCAN_ROOT / f"trivy-{target.artifact_name}.json"
        summary_json = IMAGE_SCAN_ROOT / f"trivy-{target.artifact_name}-summary.json"
        summary_markdown = IMAGE_SCAN_ROOT / f"trivy-{target.artifact_name}-summary.md"

        run(
            [
                "trivy",
                "image",
                "--input",
                str(tar_path),
                "--format",
                "json",
                "--severity",
                "HIGH,CRITICAL",
                "--ignore-unfixed",
                "--vuln-type",
                "os,library",
                "--output",
                str(report_path),
            ]
        )
        run(
            [
                sys.executable,
                "scripts/summarize_trivy_report.py",
                "--report",
                str(report_path),
                "--image-name",
                target.artifact_name,
                "--image-ref",
                target.verify_tag,
                "--json-output",
                str(summary_json),
                "--markdown-output",
                str(summary_markdown),
            ]
        )
        report_args.extend(["--report", f"{target.artifact_name}={report_path}"])

    run(
        [
            sys.executable,
            "scripts/build_residual_risk_report.py",
            *report_args,
            "--json-output",
            str(IMAGE_SCAN_ROOT / "residual-risk.json"),
            "--markdown-output",
            str(IMAGE_SCAN_ROOT / "residual-risk.md"),
        ]
    )


def handle_list() -> int:
    rows = []
    for target in load_targets():
        lanes = ["full-release"]
        if target.medium_lane:
            lanes.insert(0, "medium")
            lanes.insert(0, "fast")
        starter_ids = ",".join(proof.starter_id for proof in target.starter_proofs) or "-"
        rows.append(
            f"{target.target_id}\t{target.verify_tag}\t{','.join(lanes)}\t{starter_ids}"
        )
    print("target_id\tverify_tag\tdefault_lanes\tstarter_proofs")
    for row in rows:
        print(row)
    return 0


def handle_matrix(args: argparse.Namespace) -> int:
    print(json.dumps(matrix_payload(resolve_targets(args.image, args.profile)), indent=2))
    return 0


def handle_build(args: argparse.Namespace) -> int:
    defaults = build_defaults(args.profile)
    behavior = BuildBehavior(
        save=defaults.save if args.save is None else args.save,
        smoke=defaults.smoke if args.smoke is None else args.smoke,
        inner_ci=defaults.inner_ci if args.inner_ci is None else args.inner_ci,
    )
    build_targets(
        resolve_targets(args.image, args.profile),
        behavior=behavior,
        disk_label_prefix=args.disk_label_prefix,
    )
    return 0


def handle_starter_proof(args: argparse.Namespace) -> int:
    run_starter_proofs(
        resolve_targets(args.image, args.profile),
        build_profile=args.build_profile,
        disk_label_prefix=args.disk_label_prefix,
    )
    return 0


def handle_scan(args: argparse.Namespace) -> int:
    run_scan(resolve_targets(args.image, args.profile))
    return 0


def main() -> int:
    args = parse_args()
    if args.command == "list":
        return handle_list()
    if args.command == "matrix":
        return handle_matrix(args)
    if args.command == "build":
        return handle_build(args)
    if args.command == "starter-proof":
        return handle_starter_proof(args)
    if args.command == "scan":
        return handle_scan(args)
    raise SystemExit(f"unsupported command: {args.command}")


if __name__ == "__main__":
    raise SystemExit(main())
