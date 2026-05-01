#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict, dataclass
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

import starter_catalog as catalog


ROOT = catalog.ROOT
DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 8877
SITE_ROOT = ROOT / "starters" / "site"


@dataclass(frozen=True)
class StarterSiteConfig:
    site_root: Path = SITE_ROOT
    release_root: Path = catalog.DEFAULT_RELEASE_ROOT
    public_artifact_root: Path = catalog.DEFAULT_PUBLIC_ARTIFACT_ROOT


class StarterSiteServer(ThreadingHTTPServer):
    site_config: StarterSiteConfig


def serialize_catalog_for_site(definitions: dict[str, catalog.StarterDefinition]) -> list[dict[str, object]]:
    starters: list[dict[str, object]] = []
    for starter_id in sorted(definitions):
        starter = definitions[starter_id]
        payload = catalog.serialize_starter(starter)
        payload["profiles"] = {
            profile_id: asdict(profile)
            for profile_id, profile in starter.composition_profiles.items()
        }
        starters.append(payload)
    return starters


def catalog_payload() -> dict[str, object]:
    definitions = catalog.load_catalog()
    return {"starters": serialize_catalog_for_site(definitions)}


def default_output_path(starter_id: str, mode: str, profile_id: str) -> Path:
    return ROOT / ".tmp" / "starter-ui" / mode / starter_id / profile_id


def generate_payload(request_payload: dict[str, object]) -> dict[str, object]:
    definitions = catalog.load_catalog()
    starter_id = str(request_payload["starter"])
    starter = catalog.require_starter(definitions, starter_id)
    generation_mode = catalog.ensure_generation_mode(
        starter,
        str(request_payload["mode"]) if request_payload.get("mode") else None,
    )
    profile = catalog.resolve_profile(
        starter,
        str(request_payload["profile"]) if request_payload.get("profile") else None,
    )
    output_value = request_payload.get("output")
    output_path = (
        Path(str(output_value))
        if output_value
        else default_output_path(starter.starter_id, generation_mode, profile.profile_id)
    )
    if not output_path.is_absolute():
        output_path = ROOT / output_path
    workspace = catalog.generate_workspace(
        starter,
        profile,
        output_path,
        generation_mode,
        force=bool(request_payload.get("force", True)),
    )
    stamp_path = (
        workspace / ".polyglot-starter.json"
        if generation_mode == "source-template"
        else workspace / ".devcontainer" / ".polyglot-starter-request.json"
    )
    return {
        "starter": starter.starter_id,
        "profile": profile.profile_id,
        "mode": generation_mode,
        "output": str(workspace),
        "stamp": str(stamp_path),
        "published_image": starter.published_image,
    }


def public_catalog_index_payload(config: StarterSiteConfig) -> dict[str, object]:
    versions = catalog.list_release_versions(config.release_root)
    return {
        "versions": versions,
        "latest": versions[-1] if versions else None,
    }


def public_catalog_version_payload(config: StarterSiteConfig, catalog_version: str) -> dict[str, object]:
    snapshot = catalog.load_release_snapshot(catalog_version, release_root=config.release_root)
    return {
        "catalog_version": snapshot.catalog_version,
        "source_git_sha": snapshot.source_git_sha,
        "exported_at": snapshot.exported_at,
        "starters": serialize_catalog_for_site(snapshot.definitions),
    }


def validate_public_request(request_payload: dict[str, object]) -> None:
    allowed_keys = {"catalog_version", "starter", "profile", "mode"}
    unexpected = sorted(set(request_payload).difference(allowed_keys))
    if unexpected:
        raise SystemExit(
            f"public generate request contains unsupported fields: {', '.join(unexpected)}"
        )
    for required_key in ("catalog_version", "starter"):
        if required_key not in request_payload:
            raise KeyError(required_key)


def public_generate_payload(
    request_payload: dict[str, object],
    config: StarterSiteConfig,
) -> dict[str, object]:
    validate_public_request(request_payload)
    snapshot = catalog.load_release_snapshot(
        str(request_payload["catalog_version"]),
        release_root=config.release_root,
    )
    starter = catalog.require_starter(snapshot.definitions, str(request_payload["starter"]))
    generation_mode = catalog.ensure_generation_mode(
        starter,
        str(request_payload["mode"]) if request_payload.get("mode") else None,
    )
    profile = catalog.resolve_profile(
        starter,
        str(request_payload["profile"]) if request_payload.get("profile") else None,
    )
    artifact = catalog.generate_public_artifact(
        snapshot,
        starter,
        profile,
        generation_mode,
        artifact_root=config.public_artifact_root,
    )
    return artifact


def download_artifact(
    config: StarterSiteConfig,
    catalog_version: str,
    artifact_id: str,
) -> tuple[Path, str]:
    zip_path, _ = catalog.public_artifact_paths(
        config.public_artifact_root,
        catalog_version,
        artifact_id,
    )
    if not zip_path.exists():
        raise SystemExit(
            f"artifact {artifact_id!r} for catalog version {catalog_version!r} was not found"
        )
    return zip_path, "application/zip"


class StarterSiteHandler(BaseHTTPRequestHandler):
    server_version = "PolyglotStarterSite/0.2"

    @property
    def config(self) -> StarterSiteConfig:
        return self.server.site_config  # type: ignore[attr-defined]

    def do_GET(self) -> None:  # noqa: N802
        parsed = urlparse(self.path)
        if parsed.path in {"/", "/index.html"}:
            self.serve_file(self.config.site_root / "index.html", "text/html; charset=utf-8")
            return
        if parsed.path == "/app.js":
            self.serve_file(
                self.config.site_root / "app.js",
                "application/javascript; charset=utf-8",
            )
            return
        if parsed.path == "/styles.css":
            self.serve_file(self.config.site_root / "styles.css", "text/css; charset=utf-8")
            return
        if parsed.path == "/api/catalog":
            self.write_json(HTTPStatus.OK, catalog_payload())
            return
        if parsed.path == "/api/public/catalog":
            self.write_json(HTTPStatus.OK, public_catalog_index_payload(self.config))
            return
        if parsed.path.startswith("/api/public/catalog/"):
            version = parsed.path.removeprefix("/api/public/catalog/").strip("/")
            try:
                self.write_json(HTTPStatus.OK, public_catalog_version_payload(self.config, version))
            except SystemExit as error:
                self.write_json(HTTPStatus.BAD_REQUEST, {"error": str(error)})
            return
        if parsed.path.startswith("/api/public/download/"):
            parts = [part for part in parsed.path.split("/") if part]
            if len(parts) != 5:
                self.write_json(HTTPStatus.NOT_FOUND, {"error": "not found"})
                return
            api_name, scope, action, catalog_version, artifact_id = parts
            if api_name != "api" or scope != "public" or action != "download":
                self.write_json(HTTPStatus.NOT_FOUND, {"error": "not found"})
                return
            try:
                artifact_path, content_type = download_artifact(
                    self.config,
                    catalog_version,
                    artifact_id,
                )
            except SystemExit as error:
                self.write_json(HTTPStatus.NOT_FOUND, {"error": str(error)})
                return
            self.serve_binary(
                artifact_path.read_bytes(),
                content_type,
                download_name=f"{artifact_id}.zip",
            )
            return
        if parsed.path == "/healthz":
            self.write_json(HTTPStatus.OK, {"status": "ok"})
            return
        self.write_json(HTTPStatus.NOT_FOUND, {"error": "not found"})

    def do_POST(self) -> None:  # noqa: N802
        parsed = urlparse(self.path)
        try:
            payload = self.read_json_body()
        except ValueError as error:
            self.write_json(HTTPStatus.BAD_REQUEST, {"error": str(error)})
            return

        if parsed.path == "/api/generate":
            try:
                response = generate_payload(payload)
            except KeyError as error:
                self.write_json(HTTPStatus.BAD_REQUEST, {"error": f"missing field: {error.args[0]}"})
                return
            except SystemExit as error:
                self.write_json(HTTPStatus.BAD_REQUEST, {"error": str(error)})
                return
            except Exception as error:  # pragma: no cover - safety net for UI callers
                self.write_json(HTTPStatus.INTERNAL_SERVER_ERROR, {"error": str(error)})
                return

            self.write_json(HTTPStatus.OK, response)
            return

        if parsed.path == "/api/public/generate":
            try:
                response = public_generate_payload(payload, self.config)
            except KeyError as error:
                self.write_json(HTTPStatus.BAD_REQUEST, {"error": f"missing field: {error.args[0]}"})
                return
            except SystemExit as error:
                self.write_json(HTTPStatus.BAD_REQUEST, {"error": str(error)})
                return
            except Exception as error:  # pragma: no cover - safety net for UI callers
                self.write_json(HTTPStatus.INTERNAL_SERVER_ERROR, {"error": str(error)})
                return
            self.write_json(HTTPStatus.OK, response)
            return

        self.write_json(HTTPStatus.NOT_FOUND, {"error": "not found"})

    def read_json_body(self) -> dict[str, object]:
        try:
            content_length = int(self.headers.get("Content-Length", "0"))
        except ValueError as error:
            raise ValueError("invalid content length") from error

        try:
            payload = json.loads(self.rfile.read(content_length).decode("utf-8"))
        except json.JSONDecodeError as error:
            raise ValueError(f"invalid json: {error.msg}") from error

        if not isinstance(payload, dict):
            raise ValueError("expected json object")
        return payload

    def serve_file(self, path: Path, content_type: str) -> None:
        if not path.exists():
            self.write_json(HTTPStatus.NOT_FOUND, {"error": "not found"})
            return
        self.serve_binary(path.read_bytes(), content_type)

    def serve_binary(
        self,
        body: bytes,
        content_type: str,
        *,
        download_name: str | None = None,
    ) -> None:
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        if download_name:
            self.send_header(
                "Content-Disposition",
                f'attachment; filename="{download_name}"',
            )
        self.end_headers()
        self.wfile.write(body)

    def write_json(self, status: HTTPStatus, payload: dict[str, object]) -> None:
        body = json.dumps(payload, indent=2).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format: str, *args: object) -> None:
        sys.stderr.write("[starter-site] " + format % args + "\n")


def build_server(
    host: str,
    port: int,
    *,
    config: StarterSiteConfig | None = None,
) -> StarterSiteServer:
    server = StarterSiteServer((host, port), StarterSiteHandler)
    server.site_config = config or StarterSiteConfig()
    return server


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", default=DEFAULT_HOST)
    parser.add_argument("--port", type=int, default=DEFAULT_PORT)
    parser.add_argument("--release-root", type=Path, default=catalog.DEFAULT_RELEASE_ROOT)
    parser.add_argument(
        "--public-artifact-root",
        type=Path,
        default=catalog.DEFAULT_PUBLIC_ARTIFACT_ROOT,
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    config = StarterSiteConfig(
        site_root=SITE_ROOT,
        release_root=args.release_root if args.release_root.is_absolute() else ROOT / args.release_root,
        public_artifact_root=(
            args.public_artifact_root
            if args.public_artifact_root.is_absolute()
            else ROOT / args.public_artifact_root
        ),
    )
    server = build_server(args.host, args.port, config=config)
    print(f"[starter-site] serving http://{args.host}:{args.port}", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        return 0
    finally:
        server.server_close()


if __name__ == "__main__":
    raise SystemExit(main())
