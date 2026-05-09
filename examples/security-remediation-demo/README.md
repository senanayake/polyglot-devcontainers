# security-remediation-demo

This example is a demonstration fixture for the Polyglot CVE and EOL remediation
workflow. It represents a Python service that was last updated in 2023 and has
accumulated security advisories in its pinned dependencies.

**This example starts in a known-vulnerable state. `task scan` will fail on
initial checkout by design.** That failure is the starting point of the demo.

## What it demonstrates

- **Before**: exact-pinned dependencies from 2023 → pip-audit finds security advisories
- **Remediation**: `task upgrade` rewrites the pins to latest, re-syncs, verifies
- **After**: re-scan shows advisories resolved, `task ci` passes

## The demo scenario

Run the full end-to-end flow:

```bash
task demo
```

This runs four steps and prints a remediation report to the terminal:

1. `task demo:capture-before` — installs old deps, scans, saves baseline artifacts
2. `task demo:remediate` — upgrades pins, re-syncs venv, verifies lint and tests
3. `task demo:capture-after` — re-scans, saves post-remediation artifacts
4. `task demo:report` — generates `demo-report.md` comparing before/after

Or run the steps individually to walk through the flow live:

```bash
task init                    # install pinned dependencies (2023 state)
task scan                    # expect policy FAILURE: HIGH advisories found
task deps:report             # see what is outdated and why
task upgrade                 # rewrite pins to latest, re-sync, lint, test
task scan                    # expect PASS: advisories resolved
task ci                      # full clean verification
```

## Why the scan fails initially

The scan policy (`scan-policy.toml`) fails on CRITICAL and HIGH advisories.
`requests==2.28.0` pulls in older transitive dependencies — `urllib3` and
`certifi` — that have documented HIGH-severity advisories in the OSV advisory
database.

After `task upgrade`, all direct and transitive dependencies are updated and
the advisories are resolved.

## Artifacts

After running `task demo`:

```
.artifacts/
  demo-before/
    pip-audit.json            baseline advisory scan
    pip-audit-policy.json     policy evaluation (FAIL state)
    pip-audit-policy.md       human-readable policy report
  demo-after/
    pip-audit.json            post-remediation scan
    pip-audit-policy.json     policy evaluation (PASS state)
    pip-audit-policy.md       human-readable policy report
  scans/
    pypi-upgrades.json        packages upgraded with version changes
    dependency-report.md      full upgrade plan
  demo-report.json            machine-readable summary
  demo-report.md              executive markdown summary
```

## Connection to the Java fixture

A Java equivalent (`java-spring-boot-eol-demo`) follows the same pattern using
a pinned Spring Boot version and Gradle's dependency update plugin. Run the
Python demo first to validate the workflow, then extend to Java.

## This example is not in root CI

This example starts in a failing state by design. It is not included in the
root `task ci` pipeline. Run it standalone with `task demo` or
`task -t examples/security-remediation-demo/Taskfile.yml demo`.
