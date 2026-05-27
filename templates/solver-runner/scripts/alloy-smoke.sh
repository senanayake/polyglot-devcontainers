#!/usr/bin/env bash
set -euo pipefail

workspace="$(mktemp -d)"
trap 'rm -rf "${workspace}"' EXIT

model="models/smoke.als"
receipt="${workspace}/out/receipt.json"

alloy commands "${model}" | grep -q "sat_example"
alloy exec --force --solver sat4j --type json --output "${workspace}/out" "${model}"

python3 - "${receipt}" <<'PY'
import json
import sys
from pathlib import Path

receipt = Path(sys.argv[1])
payload = json.loads(receipt.read_text(encoding="utf-8"))
commands = payload["commands"]

if payload.get("solver") != "sat4j":
    raise SystemExit(f"expected solver=sat4j, got {payload.get('solver')!r}")

if "solution" not in commands["sat_example"]:
    raise SystemExit("expected sat_example to produce a solution")

if "solution" in commands["unsat_example"]:
    raise SystemExit("expected unsat_example to be unsatisfiable")

print("alloy-smoke: SAT4J receipt verified")
PY

