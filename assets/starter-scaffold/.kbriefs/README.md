# Knowledge Briefs

This project treats Knowledge-Based Product Development (KBPD) as a
first-class part of delivery.

`.kbriefs/` is where reusable project knowledge lives.

Use it to capture:

- decisions that materially shaped the project
- experiments and the evidence they produced
- failures and the preventive lessons from them
- limits and performance or compatibility boundaries
- trade-offs between competing design choices
- source evaluations that affect trust or adoption decisions

## Starter Workflow

1. Search existing K-Briefs before making a durable decision.
2. Use the closest template from `.kbriefs/templates/`.
3. Keep the brief focused on reusable knowledge, not task logistics.
4. Update the brief when the evidence changes.

## Suggested IDs

Use simple project-local identifiers until the team defines a stronger scheme.

Examples:

- `KB-0001-my-first-tradeoff.md`
- `KB-0002-api-timeout-boundary.md`
- `KB-0003-database-source-profile.md`

## Templates Included

- `design-space.md`
- `failure-mode.md`
- `limit.md`
- `source-profile.md`
- `standard.md`
- `tradeoff.md`

## Notes

- K-Briefs are living documents.
- A short, high-signal brief is better than a long vague one.
- If a lesson changes how agents or humans should work, link it from
  `AGENTS.md` or the relevant `docs/` page.
