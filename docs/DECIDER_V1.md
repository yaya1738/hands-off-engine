# Decider V1 - Hands-Off Engine

_Version: 1.0 | Locked: 2025-11-26_

## Overview

The **Decider** is the "brain" of the Hands-Off Engine trading pipeline. It converts alpha signals from the model into concrete `PlannedAction` objects that represent trading intentions.

The Decider's job is to take edge estimates and calculate appropriate position sizes, then package these decisions with reasoning for downstream validation and execution.

## Core Responsibility

**Transform alpha signals → PlannedActions**

- Input: Alpha signals from `state/polymarket-model.json` (edge, confidence, prices)
- Output: List of `PlannedAction` objects (market, side, amount, confidence, reasoning)
- Processing: Apply Kelly-style position sizing with conservative caps

## PlannedAction Schema

```python
@dataclass
class PlannedAction:
    """Structured representation of a planned trading action"""
    market_id: str        # Unique market identifier
    market_name: str      # Human-readable market question
    side: str             # "YES" or "NO"
    amount: float         # Dollar amount to risk
    confidence: float     # 0.0 to 1.0 (model confidence)
    reasoning: str        # Why this action makes sense
```

## Decision Rules

### 1. Accept Filtered Signals

The Decider accepts alpha signals that have already been filtered by the Alpha Model:
- Minimum edge: 3%
- Price boundaries: 0.05 - 0.95
- Valid side: YES or NO only

The Decider **does not** re-filter these signals - it trusts the upstream filtering.

### 2. Calculate Position Size (Capped Kelly)

Position sizing uses a simplified Kelly criterion with conservative caps:

```python
# Step 1: Calculate raw Kelly fraction
kelly_fraction = edge * confidence

# Step 2: Cap at maximum risk per position
max_fraction = 0.10  # Never risk more than 10% of bankroll
size_fraction = min(kelly_fraction, max_fraction)

# Step 3: Calculate dollar amount
amount = bankroll * size_fraction

# Step 4: Apply absolute cap
MAX_POSITION_SIZE = 100  # $100 max per position
amount = min(amount, MAX_POSITION_SIZE)
```

**Example calculations** (with $1000 bankroll):

| Edge | Confidence | Kelly | Capped | Amount | Final |
|------|------------|-------|--------|--------|-------|
| 5%   | 80%        | 4%    | 4%     | $40    | $40   |
| 10%  | 90%        | 9%    | 9%     | $90    | $90   |
| 15%  | 95%        | 14.25%| 10%    | $100   | $100  |
| 20%  | 50%        | 10%   | 10%    | $100   | $100  |

### 3. Generate Reasoning

Each PlannedAction includes human-readable reasoning:

```python
reasoning = (
    f"Edge: {edge:.1%}, Current odds: {current_odds:.2f}, "
    f"Confidence: {confidence:.1%}"
)
```

This reasoning is logged for audit trails and helps humans understand decisions.

### 4. Delegate Safety Validation

The Decider **does not** perform safety checks. It generates planned actions assuming:
- The Executor will validate confidence thresholds (≥70%)
- The Executor will enforce DRYRUN/LIVE mode
- The Executor will check circuit breakers and daily limits

This separation keeps the Decider focused on sizing decisions.

## Decision Flow

```
1. Load Signals
   ↓
   state/polymarket-model.json → List[dict]
   
2. For Each Signal
   ↓
   Extract: market_id, market_name, edge, side, confidence, current_odds
   
3. Calculate Size
   ↓
   kelly_fraction = edge * confidence
   size_fraction = min(kelly_fraction, 0.10)
   amount = min(bankroll * size_fraction, $100)
   
4. Generate Reasoning
   ↓
   Format: "Edge: X%, Current odds: Y, Confidence: Z%"
   
5. Create PlannedAction
   ↓
   PlannedAction(market_id, market_name, side, amount, confidence, reasoning)
   
6. Return All Actions
   ↓
   List[PlannedAction]
```

## Configuration Parameters

| Parameter | Value | Purpose |
|-----------|-------|---------|
| **Bankroll** | $1000 | Total capital for position sizing |
| **Max Fraction** | 10% | Maximum bankroll fraction per position |
| **Max Position Size** | $100 | Hard cap per individual position |

These are hardcoded in V1 for safety. Future versions may make them configurable.

## Usage Examples

### Example 1: Basic Usage

```python
from decider.ho_decider import Decider
from pathlib import Path

# Initialize with bankroll
decider = Decider(bankroll=1000.0)

# Load alpha signals from model
model_path = Path("state/polymarket-model.json")
alpha_signals = decider.load_model_signals(model_path)

# Generate planned actions
planned_actions = decider.plan_actions(alpha_signals)

# Review actions
for action in planned_actions:
    print(f"{action.market_name}: {action.side} ${action.amount:.2f}")
    print(f"  Confidence: {action.confidence:.1%}")
    print(f"  Reasoning: {action.reasoning}")
```

### Example 2: Direct Signal Processing

```python
from decider.ho_decider import Decider, PlannedAction

decider = Decider(bankroll=1000.0)

# Manually constructed signal
alpha_signals = [{
    'market_id': 'example-market-id',
    'market_name': 'Will event X happen by date Y?',
    'edge': 0.08,  # 8% edge
    'current_odds': 0.55,
    'side': 'YES',
    'model_confidence': 0.75,
    'fair_price': 0.63
}]

planned_actions = decider.plan_actions(alpha_signals)

action = planned_actions[0]
# Expected: amount = 1000 * (0.08 * 0.75) = 1000 * 0.06 = $60
print(f"Amount: ${action.amount:.2f}")  # $60.00
print(f"Confidence: {action.confidence:.1%}")  # 75.0%
```

## Example Output

### Input Signal (from polymarket-model.json)

```json
{
  "market_id": "will-trump-talk-to-macron-in-november",
  "question": "Will Trump talk to Emmanuel Macron in November?",
  "side": "NO",
  "model_edge": 0.15,
  "model_confidence": 0.49,
  "fair_price": 0.27,
  "market_price": 0.42,
  "best_bid": 0.2,
  "liquidity": 1000.0
}
```

### Output PlannedAction

```python
PlannedAction(
    market_id='will-trump-talk-to-macron-in-november',
    market_name='Will Trump talk to Emmanuel Macron in November?',
    side='NO',
    amount=73.50,  # 1000 * (0.15 * 0.49) = 1000 * 0.0735
    confidence=0.49,
    reasoning='Edge: 15.0%, Current odds: 0.42, Confidence: 49.0%'
)
```

## What the Decider Does NOT Do

The Decider is intentionally limited in scope. It **does not**:

1. **Validate safety thresholds** - Does not enforce 70% confidence minimum (Executor's job)
2. **Execute trades** - Only creates plans, never touches APIs (Executor's job)
3. **Filter markets** - Accepts pre-filtered signals from Alpha Model
4. **Check circuit breakers** - Does not verify daily limits or losses (Executor's job)
5. **Enforce DRYRUN/LIVE** - Mode selection happens downstream (Executor's job)
6. **Optimize across portfolio** - Treats each signal independently (future enhancement)
7. **Adjust for correlations** - No portfolio-level risk management yet (Tier 2+)
8. **Learn from outcomes** - No feedback loop or model updates (Tier 2+)

This separation of concerns keeps the Decider simple, testable, and focused.

## Integration Points

### Input: Alpha Model

**File:** `state/polymarket-model.json`

**Format:**
```json
{
  "generated_at": "2025-11-26T12:00:00Z",
  "total_markets_analyzed": 10,
  "markets_selected": 7,
  "markets": [
    {
      "market_id": "string",
      "question": "string",
      "side": "YES|NO",
      "model_edge": 0.05,
      "model_confidence": 0.75,
      "fair_price": 0.55,
      "market_price": 0.50,
      "best_bid": 0.49,
      "liquidity": 1000.0
    }
  ]
}
```

**Load via:** `decider.load_model_signals(Path("state/polymarket-model.json"))`

### Output: Executor

**Format:** List of `PlannedAction` dataclass instances

**Passed to:** `executor.execute_actions(planned_actions, mode='DRYRUN')`

The Executor receives planned actions and:
1. Validates confidence ≥ 70%
2. Checks circuit breakers and daily limits
3. Executes (or logs if DRYRUN)
4. Writes audit logs

## Implementation Notes

### Bankroll Management

The bankroll parameter is passed at initialization:

```python
decider = Decider(bankroll=1000.0)
```

In production, this should be dynamically set based on:
- Current account balance
- Outstanding positions
- Recent P&L

For V1, it's acceptable to hardcode or manually update this value.

### Confidence Fallback

If `model_confidence` is not provided in the signal, the Decider derives it:

```python
if model_confidence is not None:
    confidence = model_confidence
else:
    # Simple scaling: 5% edge → 0.75 confidence
    confidence = 0.5 + (edge * 5)
    confidence = max(0.0, min(1.0, confidence))
```

This fallback is conservative and should rarely be used if the Alpha Model is working correctly.

### Spark Plug Integration

The Decider logs decisions to Spark Plug kernels for historical analysis:

```python
log_kernel_history_event(
    kernel_ids=["risk_model_v2", "trading_philosophy"],
    kind="risk_decision",
    summary=f"Risk decision for {market_id}: f={kelly_fraction:.3f}, ...",
    details={...},
    importance=8
)
```

This is best-effort logging - failures never crash the Decider.

## Future Enhancements (Out of Scope for V1)

These features are **explicitly not implemented** in V1:

1. **Portfolio-level optimization** - Currently treats each position independently
2. **Correlation adjustments** - No consideration of related markets
3. **Dynamic Kelly adjustment** - Fixed 10% cap, no adaptive scaling
4. **Market-specific risk** - Same rules for all market types
5. **Time-based sizing** - No adjustment based on time to resolution
6. **Liquidity constraints** - Does not check if market can absorb size
7. **Feedback learning** - No adjustment based on past performance
8. **Multi-leg strategies** - Only single-sided positions
9. **Hedging logic** - No automatic hedge generation
10. **Configurable parameters** - Bankroll, caps, and limits are hardcoded

These will be considered in Tier 2+ roadmap items.

## Testing

### Unit Tests

Test the position sizing logic:

```python
def test_position_sizing():
    decider = Decider(bankroll=1000.0)
    
    signal = {
        'market_id': 'test',
        'market_name': 'Test Market',
        'edge': 0.10,
        'side': 'YES',
        'model_confidence': 0.80,
        'current_odds': 0.50
    }
    
    actions = decider.plan_actions([signal])
    
    # kelly = 0.10 * 0.80 = 0.08 (8%)
    # amount = 1000 * 0.08 = $80
    assert len(actions) == 1
    assert actions[0].amount == 80.0
    assert actions[0].confidence == 0.80
```

### Integration Tests

Test with real `polymarket-model.json`:

```python
def test_load_and_plan():
    decider = Decider(bankroll=1000.0)
    model_path = Path("state/polymarket-model.json")
    
    signals = decider.load_model_signals(model_path)
    actions = decider.plan_actions(signals)
    
    # Verify all actions have required fields
    for action in actions:
        assert action.market_id
        assert action.side in ['YES', 'NO']
        assert 0 < action.amount <= 100
        assert 0 <= action.confidence <= 1
        assert action.reasoning
```

## Changelog

| Date | Version | Change |
|------|---------|--------|
| 2025-11-26 | 1.0 | Initial locked version for Tier 1 |

## See Also

- [Risk Model V1](RISK_MODEL_V1.md) - Risk parameters and safety layers
- [Copilot Instructions](../.github/copilot-instructions.md) - Development guidelines
- [AI Policy](../AI_POLICY.md) - AI agent coordination rules
