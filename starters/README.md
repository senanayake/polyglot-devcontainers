# Starter Catalog

This directory contains the experimental starter catalog for the first
generator/proving thin slice.

Current intent:

- define a small, reviewable metadata surface for starters
- generate source-complete starter workspaces from templates
- prove generated starters headlessly through the task contract

Current limitations:

- generation is source-template-first only
- published starter image references are stored as metadata, but thin
  image-backed starter generation is not yet a supported default path
- the current catalog covers only:
  - `python-secure`
  - `python-node-secure`

Use the catalog through the root tasks:

```bash
task starters:list
task starters:show -- --starter python-secure
task starters:prove -- --all
```

The generator writes a `.polyglot-starter.json` stamp into generated workspaces
so the output can describe which catalog entry produced it.
