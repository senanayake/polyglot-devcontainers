# Record An Architecture Decision

Use an ADR when a technical choice should remain discoverable after the chat,
issue, or PR is gone.

## Command

```bash
task init:adr -- full-test-bar-with-zoom-in-verbs
```

Example:

```bash
task init:adr -- adopt-bdd-for-acceptance-tests
```

Hyphenated slugs are the simplest form and are titleized in the generated ADR.
Quoted multi-word titles also work when you want to preserve the full wording
at creation time.

## Output

The scaffold creates a numbered file under:

```text
docs/explanation/decisions/
```

Example:

```text
docs/explanation/decisions/ADR-0001-full-test-bar-with-zoom-in-verbs.md
```

The index in `docs/explanation/decisions/README.md` is also updated.

## What To Fill In

An ADR is complete when it states:

- the context that forced a decision
- the chosen option
- the alternatives that were seriously considered
- the consequences of the choice
- the verification and validation impact
- the related K-Briefs and requirements

## ADRs And K-Briefs

Use both when appropriate:

- ADR: what the repository decided to do
- K-Brief: what the repository learned while deciding
