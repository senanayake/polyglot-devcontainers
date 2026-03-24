# Executable Scenarios

This page explains why the repository now includes scenarios and why the first
two are deliberately narrow.

## Why scenarios exist

The repository already had two strong ingredients:

- Phase 9b proved the `evidence -> plan -> execution` model for Python and Java
  dependency maintenance
- Phase 9d added a runtime documentation surface through `man polyglot`

That left a practical gap.

The environment could explain the workflow, and it could execute the workflow,
but it still had only a weak bridge between "guidance" and "working example."

Scenarios fill that gap by making a few important situations executable and
verifiable.

## What a scenario is here

In this repository, a scenario is not a new command system or a general engine.

It is a thin repo-owned description of:

- a target workspace
- the existing commands that should be run there
- the artifacts that should exist afterward
- the runtime guidance that should help a human or agent interpret the result

That keeps the concept grounded in the current system:

- devcontainers remain the execution substrate
- the task contract remains the primary interface
- evidence and plan artifacts remain the observable state
- runtime docs remain the explanatory surface

## Why the first scenarios use the maintenance examples

The maintenance examples are the strongest proving paths in the repository.

They already exercise:

- normalized dependency inventory artifacts
- normalized dependency planning artifacts
- compact dependency report artifacts
- validated upgrade paths

Using those examples avoids inventing artificial fixtures just to demonstrate
the concept.

It also follows Gall's Law.

The repository starts with two scenarios that are already close to real work:

- Python `uv-lock` maintenance
- Java Gradle-first maintenance

## Why this is not a parallel workflow

The scenario layer does not replace:

- `task deps:inventory`
- `task deps:plan`
- `task deps:report`
- `task upgrade`
- `task ci`

It simply packages the current proven flows into a reusable, checkable form.

That matters because the repository is explicitly trying to avoid a second
workflow system that would drift away from the task contract.

## Why the scenario manifests stay small

The manifests are intentionally modest.

They record only the information needed to:

- run the scenario
- verify the expected outputs
- point back to the runtime guidance

That keeps the maintenance burden low and makes it easier to throw the concept
away if it proves less useful than expected.

## What success looks like

The scenario concept is working if:

- humans and agents can run the same scenario from the repository root
- the output is compact enough to inspect quickly
- the scenario checks fail when a proving path drifts
- the runtime docs and the executable path reinforce each other

The concept is failing if:

- the manifests become more complex than the flows they describe
- the scenario tasks start competing with the main task contract
- the repository adds many scenario families before the first two prove useful
