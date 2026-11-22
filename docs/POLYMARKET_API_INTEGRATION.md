# Polymarket Integration — Quarantined / Not Authorized

**Current status: live order execution is disabled. This document is not a setup or activation guide.**

This integration documentation is retained as historical context only. Its former instructions to place signing credentials in `.env.polymarket`, set `LIVE_TRADING_ENABLED=1`, run live test cycles, raise risk limits, or enable hourly trading are withdrawn. **Do not follow those instructions.**

The repository contains a Polymarket CLOB client for read operations and historical integration context, but all direct order-submission and cancellation methods are now blocked at the client boundary. The actuator and legacy pipeline are also fail-closed. The governed executor requires an execution-enabled authority decision; the current authority implementation deliberately returns `execution_enabled=False`.

Current boundaries:

- Wallet balances are unknown unless supported by a recent, complete Polygon RPC proof bound to the configured wallet fingerprint.
- Partial or failed RPC reads do not establish spendable funds.
- Local capital snapshots, signal outputs, simulated orders, and revenue projections are not real balances, realized income, or trading authority.
- No automatic recovery, recalibration, balance threshold, or model output can enable live trading.
- No trading credentials should be added or activated as part of this review.

This branch does not place or cancel orders, access financial accounts, move funds, deploy software, or authorize future live trading. A future trading implementation would require a separate reviewed architecture, independently tested authorization boundary, and explicit human approval.
