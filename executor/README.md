# Execution Pipeline Documentation

## Overview

The Live Execution Pipeline is the "Body + Reflexes" of the Hands-Off Engine. It transforms planned actions from the Decider into executed trades with comprehensive safety checks and monitoring.

## Architecture

```
Decider → ExecutorCore → [PreTrade → Engine → PostTrade] → Monitor
                              ↓         ↓         ↓
                          Safety    Execute   Confirm
                          Checks    Orders    + Update
```

## Components

### 1. ExecutorCore (`executor/core.py`)

**Purpose:** Main coordinator that orchestrates the complete execution pipeline.

**Key Features:**
- Receives PlannedActions from Decider
- Coordinates all execution components
- Manages kill switch and circuit breaker
- Provides unified status interface

**Safety Mechanisms:**
- Kill switch (manual emergency stop)
- Circuit breaker integration
- DRYRUN enforced by default
- Explicit flag required for LIVE mode

**Usage:**
```python
from executor.core import ExecutorCore

# Initialize (DRYRUN by default)
executor = ExecutorCore(dryrun=True, bankroll=1000.0)

# Execute signals
summary = executor.execute_signals(planned_actions)

# Check status
status = executor.get_status()

# Emergency stop
executor.enable_kill_switch("Market volatility too high")
```

### 2. PreTradeValidator (`executor/pretrade.py`)

**Purpose:** Validates all trades against safety rules before execution.

**Safety Checks:**
- **Position Limit:** Max $100 per position
- **Daily Loss Limit:** Max $500 daily loss
- **Concentration:** Max 20% of portfolio in one position
- **Liquidity:** Min $100 liquidity required
- **Confidence:** Min 70% confidence threshold
- **Circuit Breaker:** Stops all trading when triggered

**Usage:**
```python
from executor.pretrade import PreTradeValidator

validator = PreTradeValidator()

# Validate trade
is_valid, results = validator.validate_trade(action, bankroll=1000.0)

# Trigger circuit breaker
validator.trigger_circuit_breaker("Emergency stop")
```

### 3. ExecutionEngine (`executor/engine.py`)

**Purpose:** Handles order submission and execution.

**Modes:**
- **DRYRUN:** Logs orders but doesn't execute (default)
- **LIVE:** Executes via Polymarket API (not yet implemented)

**Features:**
- Order submission and tracking
- Smart order routing (planned)
- Slippage control (50 bps max)
- Partial fill handling
- State management (pending orders, history, metrics)

**Usage:**
```python
from executor.engine import ExecutionEngine

engine = ExecutionEngine(dryrun=True)

# Submit order
order = engine.submit_order(action)

# Execute order
result = engine.execute_order(order)

# Get metrics
metrics = engine.get_metrics()
```

### 4. PostTradeProcessor (`executor/posttrade.py`)

**Purpose:** Handles tasks after order execution.

**Features:**
- Fill confirmation
- Position tracking and updates
- Audit logging
- Notifications (Telegram/Slack)

**Position Tracking:**
- Tracks quantity, cost basis, average price
- Calculates realized P&L
- Maintains trade history

**Usage:**
```python
from executor.posttrade import PostTradeProcessor

processor = PostTradeProcessor()

# Process execution
processor.process_execution(order, result)

# Get positions
positions = processor.get_positions()

# Get summary
summary = processor.get_position_summary()
```

### 5. ExecutionMonitor (`executor/monitor.py`)

**Purpose:** Monitors execution quality and handles issues.

**Monitoring:**
- Pending order timeouts
- Execution quality metrics
- Failure rate alerts
- Slippage alerts
- Slow execution alerts

**Usage:**
```python
from executor.monitor import ExecutionMonitor

monitor = ExecutionMonitor()

# Check timeouts
timeouts = monitor.check_timeouts()

# Check quality
quality = monitor.check_execution_quality()

# Get pending summary
pending = monitor.get_pending_summary()
```

## State Files

### `state/execution/pending.json`
Tracks orders that are pending execution.

```json
{
  "orders": [
    {
      "order_id": "order_20251126_123456_1234",
      "market_id": "market_id",
      "market_name": "Market Name",
      "side": "YES",
      "amount": 50.0,
      "status": "pending",
      "created_at": "2025-11-26T12:34:56Z"
    }
  ],
  "last_updated": "2025-11-26T12:34:56Z"
}
```

### `state/execution/history.jsonl`
JSONL log of all executions (one entry per line).

```json
{"timestamp": "2025-11-26T12:34:56Z", "order": {...}, "result": {...}}
```

### `state/execution/metrics.json`
Execution quality metrics.

```json
{
  "total_orders": 100,
  "successful_fills": 95,
  "failed_orders": 5,
  "total_slippage_bps": 12.5,
  "avg_execution_time_ms": 150.0,
  "last_reset": "2025-11-26T00:00:00Z"
}
```

### `state/positions.json`
Current position tracking.

```json
{
  "positions": {
    "market_id": {
      "market_id": "market_id",
      "market_name": "Market Name",
      "side": "YES",
      "quantity": 100.0,
      "total_cost": 60.0,
      "avg_price": 0.6,
      "realized_pnl": 5.0,
      "trades": [...]
    }
  },
  "last_updated": "2025-11-26T12:34:56Z"
}
```

### `state/circuit_breaker.json`
Circuit breaker state.

```json
{
  "triggered": false,
  "triggered_at": null,
  "reason": null
}
```

### `state/kill_switch.json`
Kill switch state.

```json
{
  "enabled": false,
  "reason": null,
  "timestamp": null
}
```

## Safety Features

### DRYRUN Mode (Default)

All execution starts in DRYRUN mode by default. This mode:
- Logs all orders to audit trail
- Simulates fills with no slippage
- Updates metrics and state
- Does NOT execute real trades

To enable LIVE mode, you must:
1. Pass `dryrun=False` to ExecutorCore
2. Pass `enable_live=True` to explicitly confirm

```python
# This will still be DRYRUN (safe)
executor = ExecutorCore(dryrun=False)

# This enables LIVE (dangerous)
executor = ExecutorCore(dryrun=False, enable_live=True)
```

### Kill Switch

Manual emergency stop that blocks all trading.

**When to use:**
- Market conditions change dramatically
- System issues detected
- Manual intervention needed

**How to use:**
```python
# Stop all trading
executor.enable_kill_switch("Market volatility spike")

# Resume trading (requires manual action)
executor.disable_kill_switch()
```

### Circuit Breaker

Automatic safety mechanism triggered by:
- Excessive losses
- High failure rate
- System errors

Once triggered, all trading stops until manually reset.

### Pre-Trade Validation

Every trade goes through comprehensive checks:

1. **Kill Switch Check:** Is trading allowed?
2. **Circuit Breaker Check:** Is the circuit breaker triggered?
3. **Position Limit Check:** Is position size within limits?
4. **Daily Loss Check:** Have we exceeded daily loss limit?
5. **Concentration Check:** Will this create excessive concentration?
6. **Confidence Check:** Is confidence above minimum threshold?
7. **Liquidity Check:** Is there sufficient market liquidity?

If ANY check fails, the trade is rejected.

## Risk Limits

| Parameter | Limit | Rationale |
|-----------|-------|-----------|
| Max Position Size | $100 | Limit single-position risk |
| Max Daily Loss | $500 | Limit daily downside |
| Max Portfolio Concentration | 20% | Prevent over-concentration |
| Min Liquidity | $100 | Ensure tradeable markets |
| Min Confidence | 70% | Filter low-quality signals |
| Max Slippage | 50 bps | Control execution costs |
| Order Timeout | 60 seconds | Prevent stuck orders |

## Execution Flow

```
1. Receive PlannedAction from Decider
   ↓
2. Check Kill Switch
   ↓
3. Validate with PreTradeValidator
   ↓ (if valid)
4. Submit Order to ExecutionEngine
   ↓
5. Execute Order (DRYRUN or LIVE)
   ↓
6. Confirm Fill (PostTradeProcessor)
   ↓
7. Update Positions
   ↓
8. Log to Audit Trail
   ↓
9. Send Notification
   ↓
10. Monitor Quality (ExecutionMonitor)
```

## Monitoring & Alerts

### Execution Quality Metrics

- **Success Rate:** % of orders filled successfully
- **Average Slippage:** Avg slippage in basis points
- **Average Execution Time:** Avg time to fill in milliseconds
- **Failure Rate:** % of orders that fail

### Alerts

Alerts are generated when:
- Failure rate > 20%
- Average slippage > 50 bps
- Average execution time > 5 seconds

## Testing

Run comprehensive tests:

```bash
# Test execution pipeline
python3 tests/test_execution_pipeline.py

# Test alpha pipeline (compatibility check)
python3 tests/test_alpha_pipeline.py

# Run demo
python3 scripts/demo_execution_pipeline.py
```

## Integration with Decider

The execution pipeline integrates seamlessly with the Decider:

```python
from decider.ho_decider import Decider
from executor.core import ExecutorCore

# Load signals
decider = Decider(bankroll=1000.0)
signals = decider.load_model_signals(model_path)

# Plan actions
planned_actions = decider.plan_actions(signals)

# Execute
executor = ExecutorCore(dryrun=True, bankroll=1000.0)
summary = executor.execute_signals(planned_actions)
```

## Future Enhancements

### Planned Features

1. **Polymarket API Integration**
   - Real order submission
   - Real-time fill monitoring
   - Position sync with exchange

2. **Smart Order Routing**
   - TWAP (Time-Weighted Average Price)
   - VWAP (Volume-Weighted Average Price)
   - Iceberg orders

3. **Advanced Risk Management**
   - Dynamic position sizing
   - Correlation-based limits
   - Volatility-adjusted sizing

4. **Enhanced Monitoring**
   - Real-time dashboards
   - Performance analytics
   - Risk attribution

5. **Notifications**
   - Telegram bot integration
   - Slack webhooks
   - Email alerts

## Security & Audit

### Audit Logging

All critical operations are logged to:
- `logs/audit/audit_YYYY-MM-DD.jsonl`

Every log entry includes:
- Timestamp
- Event type
- Component
- Data payload
- Session ID (if applicable)

### State File Safety

State files use atomic writes:
1. Write to `.tmp` file
2. Move to actual file (atomic operation)
3. Prevents corruption from partial writes

## Troubleshooting

### Orders Not Executing

Check:
1. Is DRYRUN mode enabled? (default: yes)
2. Is kill switch enabled?
3. Is circuit breaker triggered?
4. Are pre-trade checks passing?

### High Rejection Rate

Check:
1. Position sizes within limits?
2. Confidence scores above 70%?
3. Sufficient liquidity?
4. Daily loss limit not exceeded?

### Monitor Alerts

Check:
1. Execution quality metrics
2. Recent failure rate
3. Average slippage
4. System health

## Support

For issues or questions:
1. Check audit logs: `logs/audit/`
2. Review execution history: `state/execution/history.jsonl`
3. Check system status: `executor.get_status()`
4. Review test output: `python3 tests/test_execution_pipeline.py`
