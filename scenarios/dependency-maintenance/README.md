# Dependency Maintenance Scenario Set

This scenario set is the first executable Phase 10 proving slice.

It keeps the scope narrow:

- one Python dependency-maintenance scenario
- one Java dependency-maintenance scenario
- both backed by repo-owned maintenance examples
- both executed through the existing task contract

These scenarios are intentionally thin.

They do not introduce a new workflow model.

They package the current `evidence -> plan -> execution` shape into repeatable,
observable runs that agents and humans can exercise inside the maintainer
container.

Current scenarios:

- `python-uv-lock-maintenance.json`
- `java-gradle-maintenance.json`
