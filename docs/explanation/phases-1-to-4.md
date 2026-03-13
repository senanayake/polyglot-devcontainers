# Phases 1 to 5

The roadmap progression through Phase 4 follows a simple sequence.

## Phase 1

First, harden the Python baseline that already exists.

That is lower risk than adding more languages immediately.

## Phase 2

Next, extract the validated patterns into a reusable Python template.

## Phase 3

After the workflow shape is stable, add a Node/TypeScript template that keeps
the same task contract.

## Phase 4

Finally, formalize the reusable installation units as Features so templates do
not depend on a large custom Dockerfile.

## Phase 5

With the single-language templates and reusable Features in place, the next
step is a focused polyglot template. The repository starts with Python plus
Node / TypeScript because it is a common pairing and can be implemented by
composing an official Node Feature with the existing local feature set.
