# Security Policy Scenario Set

This scenario set exercises the repository's policy-aware security review path.

It keeps the scope narrow:

- one Python audit-policy scenario
- one repo-owned proving workspace
- artifact checks that stay stable as upstream advisory data changes

This scenario does not replace `task scan`.

It packages the current Python package-audit policy overlay into a repeatable,
observable run for humans and agents inside the maintainer container.
