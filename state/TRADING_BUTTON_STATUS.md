# Historical Trading Integration Notice — Superseded

**Status: LIVE TRADING DISABLED. This document is not an activation guide.**

This file is retained only to explain historical repository claims. Its previous statements that the trading button was ready for live use, that hourly automation could trade, and that projected profits were achievable are unverified and must not be relied upon.

The previous instructions to add Polymarket signing credentials, set `LIVE_TRADING_ENABLED=1`, increase trading limits, or start live cycles are withdrawn. **Do not follow them.** Do not add credentials or change trading-mode state based on this document.

Current reviewed safety state on the financial-integrity branch:

- `scripts/run_pipeline.py` rejects LIVE mode.
- `executor/ho_executor_plan.py` does not submit live orders.
- `autonomous/actuators.py` blocks direct order submission.
- `executor/polymarket_client.py` blocks direct market orders, limit orders, and cancellations.
- `scripts/executor.py` requires governed authority with `execution_enabled=True`; the current authority implementation never grants that capability.
- Verified spendable balance remains unknown unless a fresh, complete Polygon RPC proof is available.

No live trading, account access, order placement, cancellation, wallet movement, or deployment is authorized by this document.

Any future trading capability requires a separately reviewed design, independent tests, explicit human authorization, and a new approval decision. This notice does not grant that authorization.
