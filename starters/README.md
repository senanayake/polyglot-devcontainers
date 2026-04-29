# Starter Catalog

This directory contains the experimental starter catalog for the first
generator/proving thin slice.

Current intent:

- define a small, reviewable metadata surface for starters
- generate either source-complete starter workspaces or published-image bootstrap
  seeds
- prove generated starters headlessly through the task contract and selected
  starter-local scenarios

Current limitations:

- source-template remains the default generation mode
- published-image bootstrap is proven only for starters whose images already
  expose the bootstrap contract
- the current catalog currently covers:
  - `python-secure`
  - `python-node-secure`
  - `java-secure`

Use the catalog through the root tasks:

```bash
task starters:list
task starters:validate
task starters:show -- --starter python-node-secure --profile polyglot-default
task starters:verify
task starters:generate -- --starter java-secure --mode published-image-bootstrap --output .tmp/java-image-seed
task starters:serve -- --host 127.0.0.1 --port 8877
```

The generator writes a `.polyglot-starter.json` stamp into generated workspaces
so the output can describe which catalog entry produced it.

The current compatibility model is intentionally curated rather than inferred.
Each starter declares named composition profiles that pin the supported feature
and scenario set for that starter. Use profiles to reject unsupported
combinations before generation instead of guessing from template structure.

Profiles may also declare a smaller `proof_scenarios` subset. That allows the
catalog to prove one or more starter-local scenarios directly from the
generated workspace without forcing every supported scenario into the default
proof lane.

For published-image bootstrap generation, the seed workspace keeps generator
metadata inside `.devcontainer` so `task init` can still scaffold into an
otherwise empty workspace.

The minimal local UI lives under `starters/site/` and is served by
`scripts/starter_site.py`. It is intentionally thin: it lists the proven
catalog metadata and issues generation requests against the same catalog code
used by the CLI.
