# Risk Model V1 - Hands-Off Engine

_Version: 1.0 | Locked: 2025-11-26_

## Overview

This document defines the **minimal, conservative risk model** for the Hands-Off Engine.
It is intentionally simple to establish trust before adding complexity.

## Core Philosophy

> "Prioritize trustworthiness over features. A conservative, reliable system beats a sophisticated, risky one."

## Risk Parameters

### Position Sizing

| Parameter | Value | Rationale |
|-----------|-------|-----------|
| **Max Position Size** | $100 | Hard cap per individual position |
| **Max Bankroll Fraction** | 10% | Never risk more than 10% on single position |
| **Kelly Fraction Cap** | 10% | Even if Kelly suggests more, cap at 10% |

### Entry Thresholds

| Parameter | Value | Rationale |
|-----------|-------|-----------|
| **Min Edge** | 3% | Only trade if model_edge >= 0.03 |
| **Min Confidence** | 70% | Executor rejects actions below this |
| **Price Boundaries** | 0.05 - 0.95 | Avoid near-certain markets |

### Daily Limits

| Parameter | Value | Rationale |
|-----------|-------|-----------|
| **Max Daily Risk** | $500 | Total exposure limit per day |
| **Max Positions** | 20 | Diversification requirement |
| **Circuit Breaker** | -$200 | Stop trading if daily loss exceeds |

## Position Sizing Formula

```python
# Simplified Kelly approximation
kelly_fraction = edge * confidence
size_fraction = min(kelly_fraction, 0.10)  # Cap at 10%
amount = bankroll * size_fraction
amount = min(amount, MAX_POSITION_SIZE)    # Cap at $100
```

### Example Calculations

| Edge | Confidence | Kelly | Capped | Bankroll $1000 | Final Amount |
|------|------------|-------|--------|----------------|--------------|
| 5% | 80% | 4% | 4% | $40 | $40 |
| 10% | 90% | 9% | 9% | $90 | $90 |
| 15% | 95% | 14.25% | 10% | $100 | $100 |
| 20% | 50% | 10% | 10% | $100 | $100 |

## Safety Layers

### Layer 1: Alpha Model Filtering
- Markets filtered by min edge (3%)
- Price boundaries enforced (0.05-0.95)
- Confidence scoring reduces suspicious high edges

### Layer 2: Decider Constraints
- Kelly fraction capped at 10%
- Max position size $100
- Reasoning logged for each decision

### Layer 3: Executor Validation (Reflexes)
- Confidence threshold check (70%)
- Position size validation
- Side validation (YES/NO only)
- DRYRUN/LIVE mode enforcement

### Layer 4: Circuit Breakers
- Daily loss limit: -$200 stops all trading
- Max daily positions: 20
- Max daily risk: $500 total

## DRYRUN vs LIVE

| Mode | Behavior | When to Use |
|------|----------|-------------|
| **DRYRUN** (default) | Log orders, no execution | Always, until Tier 1 complete + 2 weeks validation |
| **LIVE** | Execute real trades | Only after explicit user approval |

### LIVE Mode Checklist

Before enabling LIVE mode, verify:
- [ ] 2+ weeks of DRYRUN with positive simulated returns
- [ ] Audit logs reviewed and clean
- [ ] Circuit breakers tested
- [ ] User explicitly approves in writing
- [ ] Start with minimal capital ($100-500)

## Monitoring

Track these metrics daily:
- Win rate (target: >55%)
- Average edge of executed trades
- Position size distribution
- Daily P&L (simulated in DRYRUN)
- Rejection rate from executor

## Future Enhancements (Not V1)

These are explicitly **out of scope** for V1:
- Dynamic Kelly adjustment
- Correlation-based portfolio limits
- Market-specific risk adjustments
- Volatility-based sizing
- Machine learning risk models

## Changelog

| Date | Version | Change |
|------|---------|--------|
| 2025-11-26 | 1.0 | Initial locked version |