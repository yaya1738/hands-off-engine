# System Truth — Current Financial and Execution Boundaries

This file is the current repository-level safety reference. It must not contain personal financial records, wallet addresses, signing credentials, or private contact details.

## Financial truth

- Current cash, bank, brokerage, wallet, debts, income, expenses, monthly burn, and runway are UNKNOWN until independently reconciled with current source evidence.
- A Polymarket USDC balance is verified only by a fresh, complete Polygon RPC proof bound to the configured wallet fingerprint and expected chain.
- Partial, stale, malformed, or unavailable RPC evidence is UNKNOWN, never zero and never authorization.
- Simulation state, cached snapshots, model estimates, and revenue projections are not assets, realized income, or spendable capital.
- Verified financial records require source evidence, timestamps, and idempotency.

## Execution authority

- Legacy pipeline LIVE mode is blocked.
- Legacy actuator order submission is blocked.
- Direct Polymarket CLOB order submission and cancellation methods are blocked.
- The governed executor requires execution_enabled=True; the current authority implementation never grants that capability.
- Automatic recovery, thresholds, model output, and recalibration cannot enable live trading.
- Do not add signing credentials, change live-trading flags, or execute financial operations as part of repository review.

## Persistence and privacy

- Shared finance-hub updates and ledger writes use locked, atomic operations.
- Personal financial records and wallet configuration belong only in ignored local state, never tracked repository files.
- This sanitized current-tree file does not erase previously committed Git objects, remote caches, or external clones. History remediation remains a separate security task.

No account access, wallet movement, trading, credential rotation, merge, or deployment is authorized by this file.
