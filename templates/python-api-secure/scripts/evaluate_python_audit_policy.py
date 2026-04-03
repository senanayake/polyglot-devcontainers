#!/usr/bin/env python3
"""Evaluate pip-audit findings against the repo security policy."""

from __future__ import annotations

import argparse
import json
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Any

import tomllib


@dataclass(frozen=True)
class AcceptedAdvisory:
    advisory_id: str
    reason: str
    expires_on: date | None


SEVERITY_ORDER = ("CRITICAL", "HIGH", "MODERATE", "MEDIUM", "LOW", "UNKNOWN")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--audit-report", type=Path, required=True)
    parser.add_argument("--policy", type=Path, required=True)
    parser.add_argument("--json-output", type=Path, required=True)
    parser.add_argument("--markdown-output", type=Path, required=True)
    return parser.parse_args()


def load_policy(path: Path) -> dict[str, Any]:
    payload = tomllib.loads(path.read_text(encoding="utf-8"))
    section = payload.get("python_package_audit", {})
    accepted_rows = []
    for row in section.get("accepted_advisories", []):
        advisory_id = str(row.get("id", "")).strip()
        if not advisory_id:
            continue
        expires_on_raw = str(row.get("expires_on", "")).strip()
        accepted_rows.append(
            AcceptedAdvisory(
                advisory_id=advisory_id,
                reason=str(row.get("reason", "")).strip(),
                expires_on=date.fromisoformat(expires_on_raw)
                if expires_on_raw
                else None,
            )
        )

    return {
        "fail_on_severities": [
            str(value).upper() for value in section.get("fail_on_severities", [])
        ],
        "allow_no_fix_advisories": bool(section.get("allow_no_fix_advisories", False)),
        "accepted_advisories": accepted_rows,
    }


def advisory_ids(vulnerability: dict[str, Any]) -> list[str]:
    seen: set[str] = set()
    values: list[str] = []
    for candidate in [vulnerability.get("id"), *(vulnerability.get("aliases") or [])]:
        if not candidate:
            continue
        advisory_id = str(candidate)
        if advisory_id in seen:
            continue
        seen.add(advisory_id)
        values.append(advisory_id)
    return values


def resolve_osv_metadata(
    advisory_id: str, cache: dict[str, dict[str, Any] | None]
) -> dict[str, Any] | None:
    if advisory_id in cache:
        return cache[advisory_id]

    url = f"https://api.osv.dev/v1/vulns/{urllib.parse.quote(advisory_id, safe='')}"
    request = urllib.request.Request(url, headers={"Accept": "application/json"})
    try:
        with urllib.request.urlopen(request, timeout=20) as response:
            payload = json.load(response)
    except urllib.error.HTTPError as error:
        if error.code == 404:
            cache[advisory_id] = None
            return None
        raise

    cache[advisory_id] = payload
    return payload


def advisory_severity(advisory: dict[str, Any] | None) -> str:
    if not advisory:
        return "UNKNOWN"

    database_specific = advisory.get("database_specific", {})
    severity = str(database_specific.get("severity", "")).strip().upper()
    if severity:
        if severity == "MEDIUM":
            return "MODERATE"
        return severity
    return "UNKNOWN"


def advisory_review_state(advisory: dict[str, Any] | None) -> str:
    if not advisory:
        return "unknown"

    database_specific = advisory.get("database_specific", {})
    if "github_reviewed" in database_specific:
        return "reviewed" if database_specific.get("github_reviewed") else "unreviewed"
    return "unknown"


def accepted_exception(
    ids: list[str],
    accepted_advisories: list[AcceptedAdvisory],
    today: date,
) -> AcceptedAdvisory | None:
    id_set = set(ids)
    for accepted in accepted_advisories:
        if accepted.advisory_id not in id_set:
            continue
        if accepted.expires_on and today > accepted.expires_on:
            continue
        return accepted
    return None


def evaluate_findings(
    audit_payload: dict[str, Any], policy: dict[str, Any]
) -> dict[str, Any]:
    osv_cache: dict[str, dict[str, Any] | None] = {}
    findings: list[dict[str, Any]] = []
    violations = 0
    continued_no_fix = 0
    accepted_count = 0
    unresolved_count = 0
    today = date.today()

    for dependency in audit_payload.get("dependencies", []):
        for vulnerability in dependency.get("vulns", []):
            ids = advisory_ids(vulnerability)
            advisory = None
            resolved_id = None
            for advisory_id in ids:
                advisory = resolve_osv_metadata(advisory_id, osv_cache)
                if advisory:
                    resolved_id = advisory_id
                    break

            severity = advisory_severity(advisory)
            review_state = advisory_review_state(advisory)
            fix_versions = [
                str(value) for value in vulnerability.get("fix_versions", [])
            ]
            no_fix = len(fix_versions) == 0
            accepted = accepted_exception(ids, policy["accepted_advisories"], today)

            if accepted:
                decision = "accepted_exception"
                reason = accepted.reason or "Accepted by policy override."
                accepted_count += 1
            elif policy["allow_no_fix_advisories"] and no_fix:
                decision = "continued_no_fix"
                reason = "Allowed by policy because no fixed version is available."
                continued_no_fix += 1
            elif severity == "UNKNOWN":
                decision = "policy_blocked"
                reason = "Severity could not be resolved from advisory metadata."
                violations += 1
                unresolved_count += 1
            elif severity in policy["fail_on_severities"]:
                decision = "policy_blocked"
                reason = f"Severity {severity} matches the hard-fail policy."
                violations += 1
            else:
                decision = "continued"
                reason = f"Severity {severity} is below the hard-fail threshold."

            findings.append(
                {
                    "package_name": str(dependency.get("name", "unknown")),
                    "installed_version": str(dependency.get("version", "unknown")),
                    "vulnerability_id": str(vulnerability.get("id", "unknown")),
                    "aliases": ids[1:],
                    "resolved_advisory_id": resolved_id,
                    "severity": severity,
                    "review_state": review_state,
                    "fix_versions": fix_versions,
                    "decision": decision,
                    "reason": reason,
                }
            )

    findings.sort(
        key=lambda row: (
            row["decision"] != "policy_blocked",
            SEVERITY_ORDER.index(row["severity"])
            if row["severity"] in SEVERITY_ORDER
            else len(SEVERITY_ORDER),
            row["package_name"],
            row["vulnerability_id"],
        )
    )

    return {
        "policy": {
            "fail_on_severities": policy["fail_on_severities"],
            "allow_no_fix_advisories": policy["allow_no_fix_advisories"],
            "accepted_advisories": [
                {
                    "id": accepted.advisory_id,
                    "reason": accepted.reason,
                    "expires_on": accepted.expires_on.isoformat()
                    if accepted.expires_on
                    else None,
                }
                for accepted in policy["accepted_advisories"]
            ],
        },
        "finding_count": len(findings),
        "violations": violations,
        "continued_no_fix": continued_no_fix,
        "accepted": accepted_count,
        "unresolved_severity": unresolved_count,
        "findings": findings,
    }


def markdown_report(
    summary: dict[str, Any], report_path: Path, policy_path: Path
) -> str:
    lines = [
        "# Python Audit Policy Report",
        "",
        f"- source report: `{report_path}`",
        f"- policy: `{policy_path}`",
        f"- findings: `{summary['finding_count']}`",
        f"- policy violations: `{summary['violations']}`",
        f"- continued because no fix is available: `{summary['continued_no_fix']}`",
        f"- accepted by explicit exception: `{summary['accepted']}`",
        f"- unresolved severities: `{summary['unresolved_severity']}`",
        "",
        "## Policy",
        "",
        f"- hard fail severities: `{', '.join(summary['policy']['fail_on_severities']) or 'none'}`",
        f"- allow no-fix advisories: `{summary['policy']['allow_no_fix_advisories']}`",
        "",
        "| Package | Version | Advisory | Severity | Fix Versions | Decision | Reason |",
        "| --- | --- | --- | --- | --- | --- | --- |",
    ]

    for row in summary["findings"]:
        fix_versions = ", ".join(row["fix_versions"]) or "none"
        lines.append(
            f"| `{row['package_name']}` | `{row['installed_version']}` | "
            f"`{row['vulnerability_id']}` | `{row['severity']}` | `{fix_versions}` | "
            f"`{row['decision']}` | {row['reason']} |"
        )

    if not summary["findings"]:
        lines.append(
            "| `none` | `-` | `-` | `-` | `-` | `continued` | No Python package advisories were reported. |"
        )

    lines.append("")
    return "\n".join(lines)


def main() -> int:
    args = parse_args()
    policy = load_policy(args.policy)
    audit_payload = json.loads(args.audit_report.read_text(encoding="utf-8"))
    summary = evaluate_findings(audit_payload, policy)

    args.json_output.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    args.markdown_output.write_text(
        markdown_report(summary, args.audit_report, args.policy) + "\n",
        encoding="utf-8",
    )

    print(
        "[python-audit-policy] "
        f"findings={summary['finding_count']} violations={summary['violations']} "
        f"continued_no_fix={summary['continued_no_fix']} accepted={summary['accepted']} "
        f"unresolved={summary['unresolved_severity']}",
        flush=True,
    )

    return 1 if summary["violations"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
