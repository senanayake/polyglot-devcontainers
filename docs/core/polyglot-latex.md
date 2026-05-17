---
title: polyglot-latex
section: 7
header: Polyglot Devcontainers
footer: Runtime Documentation
---

# NAME

polyglot-latex - reproducible LaTeX paper build workflow

# PURPOSE

This page explains the supported workflow for the LaTeX image.

# WHEN TO USE

Use this image for academic paper repositories that need headless,
container-first PDF builds with LaTeX, BibTeX, TikZ, and `latexmk`.

# PRIMARY COMMANDS

```bash
task init
task build
task lint
task test
task ci
```

# WORKFLOW

The image provides a focused TeX Live environment plus the universal Polyglot
tooling contract:

- `pdflatex`
- `bibtex`
- `latexmk`
- `pdfinfo`
- `chktex`
- `texcount`
- `task`
- `git`
- `gitleaks`
- `pre-commit`

The expected project convention is that `main.tex` lives at the workspace root.
Multi-file documents should use relative paths such as:

```tex
\input{sections/introduction}
```

The normal build command is:

```bash
latexmk -pdf -interaction=nonstopmode main.tex
```

# OUTPUTS / ARTIFACTS

LaTeX builds produce `main.pdf` and intermediate files such as `main.aux`,
`main.bbl`, and `main.log`. Use `task clean` to remove generated files when
needed.

# COMMON FAILURES

- Running `latexmk` from a directory other than the document root.
- Missing bibliography files referenced by `\bibliography{...}`.
- Depending on packages that are not installed in the image.
- Committing generated PDFs before verifying the reproducible build path.

# GUIDANCE

- Keep source files and bibliography files in the repository.
- Treat generated PDFs as release artifacts unless the project explicitly
  chooses to version them.
- Use `pdfinfo` in `task test` to verify that the PDF was actually produced.

# SEE ALSO

- `polyglot(7)`
- `polyglot-task-contract(7)`
- `polyglot-security(7)`
