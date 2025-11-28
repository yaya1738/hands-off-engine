# Decider V1 - Hands-Off Engine

_Version: 1.0 | Created: 2025-11-28_

## Overview

The **Decider** is the "brain" of the Hands-Off Engine pipeline. It converts alpha signals into structured `PlannedAction` objects that represent trading intentions, which are then validated and executed by the Executor (body).

## Core Philosophy

> "Simple, conservative decision-making. Each signal gets a proportional bet size based on edge and confidence, capped to protect capital."

The Decider does NOT make complex multi-position optimizations. It simply:
1. Takes each alpha signal
2. Calculates appropriate position size using Kelly criterion
3. Applies conservative caps
4. Produces a PlannedAction

## Input: Alpha Signals

The Decider reads from `state/polymarket-model.json` which contains:

```json
{
  "markets": [
    {
      "market_id": "market-slug",
      "token_id": "clob-token-id",
      "question": "Market question?",
      "model_edge": 0.05,
      "market_price": 0.45,
      "fair_price": 0.50,
      "side": "YES",
      "model_confidence": 0.80
    }
  ]
}
```

### Required Fields

| Field | Type | Description |
|-------|------|-------------|
| `market_id` | string | Slug for display/logging |
| `question` | string | Market question (becomes `market_name`) |
| `model_edge` | float | Expected edge (e.g., 0.05 for 5%) |
| `side` | string | "YES" or "NO" |

### Optional Fields

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `token_id` | string | null | CLOB token ID for actual trading |
| `model_confidence` | float | derived | Model's confidence in the prediction |
| `market_price` | float | 0 | Current market odds |
| `fair_price` | float | null | Model's fair price estimate |

## Output: PlannedAction

```python
@dataclass
class PlannedAction:
    market_id: str      # Slug for display/logging
    market_name: str    # Market question
    side: str           # "YES" or "NO"
    amount: float       # Dollar amount to risk
    confidence: float   # 0.0 to 1.0
    reasoning: str      # Why this action makes sense
    token_id: str       # Optional: CLOB token for trading
```

## Position Sizing Algorithm

### Step 1: Determine Confidence

```python
if model_confidence is provided:
    confidence = model_confidence
else:
    # Fallback heuristic when model doesn't provide confidence
    # 5 is a scaling factor that maps typical edges (2-10%) to reasonable confidence levels
    # This is a conservative linear approximation, not derived from betting theory
    confidence = 0.5 + (edge * 5)
    confidence = clamp(confidence, 0.0, 1.0)
```

### Step 2: Calculate Size Fraction

```python
# This is a simplified position sizing heuristic, NOT the true Kelly criterion
# True Kelly: f = (bp - q) / b where b=odds, p=win prob, q=loss prob
# We use this approximation because:
# 1. It's conservative (typically undersizes vs true Kelly)
# 2. It's intuitive (higher edge + higher confidence = larger bet)
# 3. The 10% cap dominates in practice anyway
kelly_fraction = edge * confidence
```

### Step 3: Apply Caps

```python
max_fraction = 0.10  # Never risk more than 10% of bankroll
size_fraction = min(kelly_fraction, max_fraction)
```

### Step 4: Calculate Amount

```python
amount = bankroll * size_fraction
amount = min(amount, max_position_usd)  # From risk profile
```

## Configuration

### Risk Profile Integration

The Decider reads `state/risk_profile.json` for:

| Parameter | Default | Description |
|-----------|---------|-------------|
| `max_position_usd` | $50 | Maximum dollar amount per position |

### Bankroll

Default bankroll is `$5000`. Can be overridden when instantiating:

```python
decider = Decider(bankroll=10000.0)
```

## Example Calculations

Calculation flow: kelly_fraction = edge × confidence → capped_fraction = min(kelly, 10%) → raw_amount = bankroll × capped_fraction → final = min(raw_amount, $50)

| Edge | Confidence | Kelly (edge×conf) | Capped | Raw ($5000×capped) | Final (max $50) |
|------|------------|-------------------|--------|---------------------|-----------------|
| 3% | 70% | 2.1% | 2.1% | $105 | **$50** |
| 5% | 80% | 4.0% | 4.0% | $200 | **$50** |
| 10% | 90% | 9.0% | 9.0% | $450 | **$50** |
| 15% | 95% | 14.25% | 10% | $500 | **$50** |
| 2% | 60% | 1.2% | 1.2% | $60 | **$50** |
| 1% | 50% | 0.5% | 0.5% | $25 | **$25** |

Note: With current defaults ($50 max position), most calculated amounts get capped. This is intentional for safety during shadow mode.

## Integration with Pipeline

```
Alpha Model → Decider → Executor → Audit
     ↓           ↓          ↓
  signals   PlannedActions  trades
```

### Usage

```python
from decider.ho_decider import Decider
from pathlib import Path

decider = Decider(bankroll=5000.0)

# Load signals from model file
model_path = Path("state/polymarket-model.json")
signals = decider.load_model_signals(model_path)

# Generate planned actions
actions = decider.plan_actions(signals)

# Pass to executor
for action in actions:
    executor.execute(action)
```

## Audit Integration

Every decision is logged via the audit system:

1. **Risk decisions** - Logged per-market with edge, confidence, Kelly fraction
2. **Decider outcomes** - Aggregate summary of all actions produced

History events are also logged for Spark Plug kernels (when available):
- `risk_decision` events for each market
- `decider_outcome` events for aggregate summaries

## Safety Features

1. **Kelly fraction cap at 10%** - Never risk more than 10% of bankroll per position
2. **Max position from risk profile** - Aligns with executor validation
3. **Conservative defaults** - $50 max, $5000 bankroll
4. **No leverage** - Amount is always positive, bounded
5. **Graceful degradation** - History logging failures don't crash the decider

## Future Enhancements (Not V1)

These are explicitly **out of scope** for V1:

- Portfolio optimization (correlation-aware)
- Dynamic bankroll adjustment
- Multi-timeframe position building
- Market-specific sizing adjustments
- Volatility-based sizing
- Order book depth consideration

## Related Documents

- `docs/RISK_MODEL_V1.md` - Risk parameters and constraints
- `executor/ho_executor.py` - Validation and execution
- `alpha/ho_alpha.py` - Signal generation
- `docs/AUDIT_SYSTEM.md` - Logging and accountability

## Changelog

| Date | Version | Change |
|------|---------|--------|
| 2025-11-28 | 1.0 | Initial locked version |
