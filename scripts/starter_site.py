#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

import starter_catalog as catalog


ROOT = catalog.ROOT
DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 8877
SITE_ROOT = ROOT / "starters" / "site"


def catalog_payload() -> dict[str, object]:
    definitions = catalog.load_catalog()
    starters: list[dict[str, object]] = []
    for starter_id in sorted(definitions):
        starter = definitions[starter_id]
        payload = asdict(starter)
        payload["profiles"] = {
            profile_id: asdict(profile)
            for profile_id, profile in starter.composition_profiles.items()
        }
        starters.append(payload)
    return {"starters": starters}


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


class StarterSiteHandler(BaseHTTPRequestHandler):
    server_version = "PolyglotStarterSite/0.1"

    def do_GET(self) -> None:  # noqa: N802
        parsed = urlparse(self.path)
        if parsed.path in {"/", "/index.html"}:
            self.serve_file(SITE_ROOT / "index.html", "text/html; charset=utf-8")
            return
        if parsed.path == "/app.js":
            self.serve_file(SITE_ROOT / "app.js", "application/javascript; charset=utf-8")
            return
        if parsed.path == "/styles.css":
            self.serve_file(SITE_ROOT / "styles.css", "text/css; charset=utf-8")
            return
        if parsed.path == "/api/catalog":
            self.write_json(HTTPStatus.OK, catalog_payload())
            return
        if parsed.path == "/healthz":
            self.write_json(HTTPStatus.OK, {"status": "ok"})
            return
        self.write_json(HTTPStatus.NOT_FOUND, {"error": "not found"})

    def do_POST(self) -> None:  # noqa: N802
        parsed = urlparse(self.path)
        if parsed.path != "/api/generate":
            self.write_json(HTTPStatus.NOT_FOUND, {"error": "not found"})
            return

        try:
            content_length = int(self.headers.get("Content-Length", "0"))
        except ValueError:
            self.write_json(HTTPStatus.BAD_REQUEST, {"error": "invalid content length"})
            return

        try:
            payload = json.loads(self.rfile.read(content_length).decode("utf-8"))
        except json.JSONDecodeError as error:
            self.write_json(HTTPStatus.BAD_REQUEST, {"error": f"invalid json: {error.msg}"})
            return

        if not isinstance(payload, dict):
            self.write_json(HTTPStatus.BAD_REQUEST, {"error": "expected json object"})
            return

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

    def serve_file(self, path: Path, content_type: str) -> None:
        if not path.exists():
            self.write_json(HTTPStatus.NOT_FOUND, {"error": "not found"})
            return
        body = path.read_bytes()
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
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


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", default=DEFAULT_HOST)
    parser.add_argument("--port", type=int, default=DEFAULT_PORT)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    server = ThreadingHTTPServer((args.host, args.port), StarterSiteHandler)
    print(f"[starter-site] serving http://{args.host}:{args.port}", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        return 0
    finally:
        server.server_close()


if __name__ == "__main__":
    raise SystemExit(main())
