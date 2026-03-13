# Architecture

The repository keeps one validated implementation at the root and extracts
reusable parts into templates and features.

This is deliberate.

- The root environment is the reference implementation.
- Templates are copies users can start from.
- Features are the reusable installation units that keep templates small.

This split keeps the system understandable while still moving toward reuse.
