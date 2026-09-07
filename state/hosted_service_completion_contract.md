# Hosted autonomous service completion contract

A hosted autonomous service cycle is considered successful only when its persisted liveness evidence reports all of:

- `execution_observed == true`
- `verification_observed == true`
- `execution_succeeded == true`
- `live_system_active == true`

The GitHub Actions workflow asserts these conditions after the governed supervisor executes. A green workflow alone is not treated as proof of successful autonomous execution.

The service remains fail-closed for external production authority and live mutation; this contract does not grant additional mutation authority.
