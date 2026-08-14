# Polymarket Current-Rules Gate

**Status:** Mandatory pre-trade safety contract
**Effective:** 2026-08-14
**Authority:** Current Polymarket documentation, not historical repository knowledge

## Purpose

Polymarket rules, fees, rewards, order behavior, and market-specific constraints change over time. Historical strategy documents and code must never be treated as authoritative for a live financial action.

The system MUST perform a fresh rules check immediately before any action could become a live trade. If the check cannot establish current rules, the action remains blocked.

## Current facts that materially affect strategy

- Polymarket currently has fee-enabled market categories and a Maker Rebates program funded by taker fees. Makers pay 0% maker fee; eligible filled maker liquidity can receive daily rebates. The rebate percentage can change over time.
- The current fee schedule is market/category dependent. The market object exposes `feesEnabled`, and fee calculation should use the market's current `feeSchedule` rather than a hard-coded historical rate.
- Liquidity Rewards are distinct from Maker Rebates. Resting competitive limit orders can earn liquidity rewards, with eligibility depending on current market-specific reward parameters such as maximum spread, minimum size, and other rules.
- Limit orders can partially fill and may qualify for maker-side economics/rewards depending on how they execute and the current market configuration.
- Immediately executable/taking orders can incur taker fees in fee-enabled markets. Therefore market-order/taker economics must be included in expected value and execution-cost calculations.
- Sports markets have additional order timing behavior documented by Polymarket, including automatic cancellation of outstanding limit orders at game start and delays on marketable orders. These are market-specific constraints and must not be generalized to every market.
- Trading size is constrained economically by available order-book depth and price impact even where the orderbook itself has no fixed universal size limit.

## Required pre-trade gate

Before any live financial execution becomes eligible, the system MUST establish all of the following from current authoritative data:

1. Current market metadata and `feesEnabled` state.
2. Current `feeSchedule` / fee parameters for the specific market.
3. Current maker-rebate eligibility and parameters, if relevant.
4. Current liquidity-reward eligibility and parameters, if relevant.
5. Current order-type behavior and whether the proposed order is maker/resting or taker/immediately executable.
6. Current order-book depth, spread, and expected price impact.
7. Current market-specific restrictions/timing rules.
8. Timestamp/source provenance for the rules snapshot.
9. A successful safety decision explicitly permitting the *class of financial action*.
10. The global live-trading ban must also be lifted explicitly; current rules alone never authorize live trading.

If any item is missing, stale, contradictory, or unavailable: **DENY**.

## Strategy / probability integration

The current rules snapshot must flow into probability, EV, and execution-cost calculations. In particular, expected value must account for:

`gross_edge - taker_fee - spread_cost - expected_slippage - gas/transaction_cost + expected_maker_rebate + expected_liquidity_reward`

where applicable and where each term is supported by a current rules snapshot.

A reward must never be treated as guaranteed alpha. Rewards and rebates are contingent on current eligibility, competition, fills, market parameters, and program rules.

## Staleness policy

A cached rules snapshot may be used for research and simulation, but it MUST NOT authorize live execution after its freshness window expires. Live execution requires a fresh rules check immediately before the final green-light.

The system should retain the source URL, retrieval timestamp, relevant market identifier, and normalized rules version used for every future financial decision.

## Historical knowledge quarantine

Documents or code that state historical conditions such as "0% trading fees" as a universal Polymarket rule are **historical references only** unless revalidated against current authoritative sources.

The same quarantine applies to any hard-coded fee, reward, rebate, order-type, market-limit, timing, or platform-rule assumption.

## Authoritative sources

- Polymarket Documentation changelog: https://docs.polymarket.com/changelog
- Polymarket Liquidity Rewards documentation: https://docs.polymarket.com/market-makers/liquidity-rewards
- Polymarket Trading Help Center: https://help.polymarket.com/en/collections/17859610-trading
- Polymarket Liquidity Rewards Help Center: https://help.polymarket.com/en/articles/13364466-liquidity-rewards
- Polymarket Maker Rebates Help Center: https://help.polymarket.com/en/articles/13364471-maker-rebates-program
- Polymarket Limit Orders Help Center: https://help.polymarket.com/en/articles/13364444-limit-orders

## Non-negotiable safety rule

**This document does not enable trading.**

The live-trading hard block remains independent and authoritative. This gate exists so that, if live trading is ever explicitly unbanned, obsolete financial assumptions cannot silently authorize execution.
