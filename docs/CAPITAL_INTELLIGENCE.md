# Integrated Capital Intelligence

Capital is a production resource, not an experimental budget. The factory treats
scarce real capital as one resource class inside the same observe → reason →
allocate → execute → verify → learn improvement loop.

## Scope

The capital-intelligence layer evaluates:

- hold-cash decisions;
- opportunity selection across authorized venues;
- risk-adjusted expected value after fees;
- liquidity and lockup costs;
- concentration and capital-preservation constraints;
- cross-venue allocation and rebalance proposals.

Polymarket and Kalshi are supported as venue identities. The decision layer does
not assume that either venue is currently connected or that an account has funds.
Current balances, market data, fees, settlement rules, and account permissions
must come from an authorized, freshness-aware adapter.

## Authority boundary

`CapitalIntelligence` is decision-only. It never stores private keys, API
credentials, transfers funds, or places orders. A real financial action must be
handed to a separately authorized financial adapter through the factory authority
path, with the resulting transaction reconciled back into shared state.

This separation lets the same intelligence compare deployment, rebalancing, and
waiting without turning scarce capital into an uncontrolled test budget.

## Default operating posture

1. Preserve runway before maximizing nominal return.
2. Compare opportunities rather than acting on the first signal.
3. Penalize downside, illiquidity, fees, lockup, and concentration.
4. Prefer holding cash when no candidate clears the value threshold.
5. Cap any individual proposed allocation as a fraction of available capital.
6. Treat execution as a separately authorized, observable side effect.
7. Feed verified outcomes back into the factory learning/improvement loop.

The objective is not maximum activity. It is maximum useful progress per unit of
scarce capital while retaining enough runway for future opportunities.
