#!/usr/bin/env python3
from __future__ import annotations

import json
import tempfile
import threading
import urllib.error
import urllib.request
import zipfile
from pathlib import Path

import starter_catalog as catalog
import starter_site


def get_json(url: str) -> tuple[int, dict[str, object]]:
    request = urllib.request.Request(url, method="GET")
    try:
        with urllib.request.urlopen(request, timeout=10) as response:  # noqa: S310
            return response.status, json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as error:
        return error.code, json.loads(error.read().decode("utf-8"))


def post_json(url: str, payload: dict[str, object]) -> tuple[int, dict[str, object]]:
    request = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=20) as response:  # noqa: S310
            return response.status, json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as error:
        return error.code, json.loads(error.read().decode("utf-8"))


def download_bytes(url: str) -> bytes:
    request = urllib.request.Request(url, method="GET")
    with urllib.request.urlopen(request, timeout=20) as response:  # noqa: S310
        return response.read()


def assert_true(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit(message)


def main() -> int:
    definitions = catalog.load_catalog()
    tmp_root = catalog.ROOT / ".tmp"
    tmp_root.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="starter-public-api-", dir=tmp_root) as temp_dir:
        temp_root = Path(temp_dir)
        release_root = temp_root / "releases"
        artifact_root = temp_root / "artifacts"
        catalog_version = "validation-001"
        snapshot = catalog.export_release_snapshot(
            definitions,
            catalog_version,
            release_root=release_root,
        )

        config = starter_site.StarterSiteConfig(
            site_root=starter_site.SITE_ROOT,
            release_root=release_root,
            public_artifact_root=artifact_root,
        )
        server = starter_site.build_server("127.0.0.1", 0, config=config)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        base_url = f"http://127.0.0.1:{server.server_address[1]}"

        try:
            status, payload = get_json(f"{base_url}/api/public/catalog")
            assert_true(status == 200, "public catalog index did not return 200")
            assert_true(payload["latest"] == catalog_version, "public catalog latest version mismatch")
            assert_true(catalog_version in payload["versions"], "public catalog index missing exported version")

            status, payload = get_json(f"{base_url}/api/public/catalog/{catalog_version}")
            assert_true(status == 200, "versioned public catalog did not return 200")
            assert_true(payload["catalog_version"] == catalog_version, "versioned public catalog mismatch")
            assert_true(payload["source_git_sha"] == snapshot.source_git_sha, "public catalog git sha mismatch")
            starters = payload["starters"]
            assert_true(isinstance(starters, list) and starters, "public catalog starters payload missing")

            status, payload = post_json(
                f"{base_url}/api/public/generate",
                {
                    "catalog_version": catalog_version,
                    "starter": "python-secure",
                    "profile": "baseline",
                    "mode": "source-template",
                },
            )
            assert_true(status == 200, "public source-template generate did not return 200")
            assert_true("output" not in payload and "stamp" not in payload, "public generate leaked local paths")
            response_text = json.dumps(payload)
            assert_true(str(catalog.ROOT) not in response_text, "public generate leaked repository root")
            download_url = payload["download_url"]
            assert_true(isinstance(download_url, str), "public generate did not return download_url")
            source_zip = download_bytes(f"{base_url}{download_url}")
            source_zip_path = temp_root / "python-secure.zip"
            source_zip_path.write_bytes(source_zip)
            with zipfile.ZipFile(source_zip_path) as archive:
                names = archive.namelist()
                assert_true("Taskfile.yml" in names, "source-template artifact missing Taskfile.yml")
                assert_true("README.md" in names, "source-template artifact missing README.md")
                assert_true(".polyglot-starter.json" in names, "source-template artifact missing starter stamp")
                assert_true(
                    ".polyglot-starter-artifact.json" in names,
                    "source-template artifact missing public artifact stamp",
                )
                assert_true(all(not name.startswith("/") for name in names), "zip contains absolute path entries")
                assert_true(
                    all(":" not in name for name in names),
                    "zip contains host path separators",
                )

            status, payload = post_json(
                f"{base_url}/api/public/generate",
                {
                    "catalog_version": catalog_version,
                    "starter": "java-secure",
                    "mode": "published-image-bootstrap",
                },
            )
            assert_true(status == 200, "public published-image generate did not return 200")
            image_zip = download_bytes(f"{base_url}{payload['download_url']}")
            image_zip_path = temp_root / "java-secure-image.zip"
            image_zip_path.write_bytes(image_zip)
            with zipfile.ZipFile(image_zip_path) as archive:
                names = archive.namelist()
                assert_true(
                    ".devcontainer/devcontainer.json" in names,
                    "image-backed artifact missing devcontainer.json",
                )
                assert_true(
                    ".devcontainer/.polyglot-starter-request.json" in names,
                    "image-backed artifact missing request stamp",
                )
                assert_true(
                    ".polyglot-starter-artifact.json" in names,
                    "image-backed artifact missing public artifact stamp",
                )

            status, payload = post_json(
                f"{base_url}/api/public/generate",
                {
                    "catalog_version": catalog_version,
                    "starter": "python-secure",
                    "output": ".tmp/not-allowed",
                },
            )
            assert_true(status == 400, "public generate should reject unsupported output field")
            assert_true("unsupported fields" in str(payload.get("error", "")), "unexpected output rejection message")

            status, payload = post_json(
                f"{base_url}/api/public/generate",
                {
                    "catalog_version": "missing-version",
                    "starter": "python-secure",
                },
            )
            assert_true(status == 400, "public generate should reject missing released catalog version")
            assert_true("not available" in str(payload.get("error", "")), "missing version rejection message mismatch")

            status, payload = post_json(
                f"{base_url}/api/public/generate",
                {
                    "catalog_version": catalog_version,
                    "starter": "python-secure",
                    "profile": "baseline",
                    "mode": "source-template",
                },
            )
            assert_true(status == 200, "cached public generate did not return 200")
            assert_true(payload["cached"] is True, "repeated public generate should report cached artifact")
            print(
                "[starter-public-validate] "
                f"catalog_version={catalog_version} source_artifact={source_zip_path.name} "
                f"image_artifact={image_zip_path.name}",
                flush=True,
            )
            return 0
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=5)


if __name__ == "__main__":
    raise SystemExit(main())
