# Shadow / Observation Runbook — No Live Activation

**This file is intentionally limited to non-executing review. It does not authorize trading.**

The former runbook included instructions to add Polymarket signing credentials, switch an executor mode to live, and invoke a resume command. Those instructions are withdrawn and must not be followed.

## Safe review boundary

- Treat all signal, bankroll, position-size, and performance values as simulation inputs unless independently reconciled.
- Do not add signing credentials to run a shadow test.
- Do not set a live executor mode or enable a trading-mode flag.
- Do not invoke legacy trading-resume or order-submission commands.
- Do not interpret a successful dry run as an executed trade or realized return.

## Validation

Use the repository's read-only tests and CI workflow to validate the blocked execution paths. A passing test suite demonstrates only the tested code paths; it is not approval to deploy or trade.

## Current status

The legacy pipeline, actuator order path, and direct CLOB mutation methods are blocked. The governed authority currently never grants execution-enabled status. Verified spendable balance is unknown unless a fresh, complete Polygon RPC proof is available.

Historical copies of this file may remain in Git history or external clones. This current-tree rewrite does not constitute a history scrub.
