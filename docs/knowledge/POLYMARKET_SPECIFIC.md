# Polymarket-Specific Knowledge — Current-State Authority

> **Status: dynamic / freshness-required.** This document is not a permanent source of truth for fees, rewards, collateral, API behavior, eligibility, or market rules. Current protocol state must be queried from authoritative Polymarket APIs/docs before making trading decisions.

## Current trading economics

- Polymarket now charges **taker fees on fee-enabled markets**. Makers are not charged platform trading fees.
- Fees are determined **per market at match time**. Do not hard-code a universal fee rate.
- Query the market's current fee configuration (`feesEnabled` / `feeSchedule` or the current CLOB market-info endpoint) before calculating expected value.
- Current documented fee model: `fee = C × feeRate × p × (1 - p)`.
- Fee categories and rates can change; treat published tables as snapshots, not constants.
- **Market/taker execution is more expensive than passive maker execution** on fee-enabled markets. Expected-value calculations must include the current taker fee.

## Maker / limit-order economics

- Resting limit orders that add liquidity can qualify for **maker rebates and/or liquidity rewards**, depending on the market/program.
- Maker rebates are funded from taker fees and are distributed according to the active program rules.
- Liquidity rewards depend on factors such as order size, competitiveness relative to midpoint/other liquidity, time active, and the specific market's reward program.
- Rewards are not guaranteed and program parameters can change. Query current market/program data before assigning reward value.
- Strategy evaluation must therefore compare:
  - expected alpha,
  - taker fee,
  - expected maker rebate,
  - liquidity reward,
  - fill probability,
  - adverse selection,
  - spread/price impact,
  - inventory risk,
  - opportunity cost and capital constraints.

## Order-selection rule

Prefer a resting/post-only limit order when its expected fill economics dominate immediate execution. Use a market/taker order only when the value of immediacy exceeds the current all-in taker cost and execution risk.

Never assume "limit = free" or "market = cheap". Compute from current market parameters and expected execution outcomes.

## Market-specific rules

- Read the resolution rules before entry.
- Re-check rules for open positions when the platform/market exposes updated rule information.
- Treat ambiguous or changing rules as additional risk.
- Resolution criteria, eligibility, fee status, reward eligibility, tick size, minimum order size, and order semantics are **market-specific** and must not be inferred from an old example.

## API / protocol freshness

Polymarket's CLOB V2 changed important execution semantics, including dynamic match-time fee handling and order structure. Current integrations must follow the current V2 API/SDK behavior rather than legacy order fields or fee calculations.

The system must monitor authoritative Polymarket documentation/changelog and current API responses for:

1. fee-model changes;
2. maker-rebate changes;
3. liquidity-reward changes;
4. order-type/post-only behavior;
5. tick sizes and minimum order sizes;
6. collateral/token changes;
7. API/SDK breaking changes;
8. geographic/eligibility restrictions;
9. market-category activation dates;
10. market-specific resolution-rule changes.

## Legacy information policy

Older repository material claiming **zero trading fees**, universal fee-free execution, static reward assumptions, obsolete collateral, or legacy API semantics is historical context only. It must not be used as live trading logic without current-source validation.

This applies to all Polymarket-related code, documentation, strategy notes, reports, fetchers, executors, and the Yair/master strategy. A future refresh must update the underlying source-of-truth layer rather than merely editing one document.

## Reality / freshness contract

Any Polymarket economic assumption used by an automated strategy should carry:

- `source`
- `observed_at`
- `effective_at` when known
- `market_id` / `condition_id` when applicable
- `freshness_deadline`
- `confidence`
- `assumption_version`

If a required fact is stale, unavailable, or contradictory, the strategy should **stop treating the fact as valid** and either refresh it or conservatively avoid the affected action.

## Authoritative references

- Polymarket trading fees: https://docs.polymarket.com/trading/fees
- Maker rebates: https://docs.polymarket.com/market-makers/maker-rebates
- Liquidity rewards: https://docs.polymarket.com/market-makers/liquidity-rewards
- CLOB V2 migration: https://docs.polymarket.com/v2-migration
- Polymarket changelog: https://docs.polymarket.com/changelog

## Core principle

**Polymarket knowledge is a live dependency, not static documentation.** The Factory must continuously reconcile repository assumptions against authoritative external state and propagate validated changes into strategy, execution, risk, and reporting layers before those layers act on them.
