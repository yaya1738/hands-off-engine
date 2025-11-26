# Portfolio Tracking System

Comprehensive portfolio tracking, P&L calculation, and position management for the Hands-Off Engine.

## Features

- **Position Management**: Track positions (open/closed) with full history
- **Portfolio Tracking**: Real-time portfolio valuation and metrics
- **P&L Calculator**: Realized and unrealized P&L by market, day, and strategy
- **Report Generation**: Daily/weekly reports, Telegram notifications, CSV/JSON exports
- **Risk Management**: Position size limits, concentration checks, health monitoring
- **Mode Separation**: Isolated DRYRUN and LIVE position tracking
- **Audit Logging**: All position changes logged for accountability

## Quick Start

```python
from portfolio import PositionManager, PortfolioTracker, PnLCalculator, ReportGenerator

# Create position manager
pm = PositionManager()

# Add a position
pos = pm.add_position(
    market_id="btc_100k_eoy",
    market_name="Will BTC hit $100k by EOY?",
    side="YES",
    entry_price=0.45,
    quantity=100.0,
    mode="DRYRUN"
)

# Update price
pm.update_position_price(pos.position_id, 0.55)

# Close position
closed = pm.close_position(pos.position_id, 0.60)
print(f"Realized P&L: ${closed.realized_pnl:.2f}")
```

## Components

### 1. Position Manager (`positions.py`)
Manages individual positions with atomic operations and audit logging.

```python
pm = PositionManager()

# Add position
pos = pm.add_position(market_id, market_name, side, entry_price, quantity, mode)

# Update price
pm.update_position_price(position_id, new_price)

# Close position
pm.close_position(position_id, exit_price)

# Query positions
open_positions = pm.get_all_positions(status="open", mode="DRYRUN")
market_positions = pm.get_positions_by_market(market_id)
```

### 2. Portfolio Tracker (`tracker.py`)
Tracks portfolio value, exposure, and risk across all positions.

```python
tracker = PortfolioTracker()

# Get portfolio metrics
value = tracker.get_portfolio_value(mode="DRYRUN")
unrealized_pnl = tracker.get_unrealized_pnl(mode="DRYRUN")
summary = tracker.get_portfolio_summary(mode="DRYRUN")

# Risk checks
allowed, reason = tracker.check_risk_limits(
    market_id="new_market",
    proposed_amount=50.0,
    mode="DRYRUN"
)

# Health check
health = tracker.get_portfolio_health_check(mode="DRYRUN")
```

### 3. P&L Calculator (`pnl.py`)
Calculates P&L across multiple dimensions with historical tracking.

```python
calc = PnLCalculator()

# Calculate P&L
realized = calc.calculate_realized_pnl(mode="DRYRUN")
unrealized = calc.calculate_unrealized_pnl(mode="DRYRUN")
total = calc.calculate_total_pnl(mode="DRYRUN")

# P&L breakdowns
by_market = calc.calculate_pnl_by_market(mode="DRYRUN")
by_day = calc.calculate_pnl_by_day(mode="DRYRUN", days=30)

# Historical snapshots
calc.save_daily_snapshot(mode="DRYRUN")
snapshots = calc.get_historical_snapshots(days=30)
```

### 4. Report Generator (`reports.py`)
Generates human-readable reports and exports.

```python
generator = ReportGenerator()

# Generate reports
daily_report = generator.generate_daily_summary(mode="DRYRUN")
weekly_report = generator.generate_weekly_summary(mode="DRYRUN")
telegram_text = generator.get_telegram_notification_text(mode="DRYRUN")

# Export data
generator.export_positions_json(Path("positions.json"), mode="DRYRUN")
generator.export_positions_csv(Path("positions.csv"), mode="DRYRUN")
generator.export_pnl_json(Path("pnl_report.json"), mode="DRYRUN")
```

### 5. Executor Integration (`executor_integration.py`)
Connects portfolio tracking with trade execution.

```python
integration = PortfolioExecutorIntegration()

# Record trade execution
position_id = integration.on_trade_executed(
    market_id="btc_100k_eoy",
    market_name="Will BTC hit $100k by EOY?",
    side="YES",
    price=0.45,
    quantity=100.0,
    mode="DRYRUN"
)

# Update prices from market data
market_prices = {"btc_100k_eoy": 0.55}
updated_count = integration.update_position_prices(market_prices)

# Close position
success = integration.on_trade_closed(position_id, exit_price=0.60)
```

## State Files

All state is persisted in `state/portfolio/`:

- **`positions.json`**: Current positions (open and closed)
- **`history.jsonl`**: Position event history (append-only log)
- **`pnl_daily.json`**: Daily P&L snapshots (rolling 90 days)

## Risk Limits

Default risk limits (configurable):

- **Per-position**: $100 max
- **Per-market**: $300 max total exposure
- **Total portfolio**: $1000 max total exposure
- **Min confidence**: 70% to execute

## Testing

Run the test suite:

```bash
python3 tests/test_portfolio.py
```

Run the example script:

```bash
python3 examples/portfolio_tracking_example.py
```

## Integration with Hands-Off Engine

The portfolio system integrates with:

1. **Executor**: Automatic position tracking when trades execute
2. **Decider**: Risk limit checks before planning actions
3. **Audit System**: All position changes logged
4. **Telegram**: Daily P&L notifications (via reports)

## Example: Full Pipeline

See `examples/portfolio_tracking_example.py` for a complete demonstration of:

- Adding and managing positions
- Calculating P&L
- Generating reports
- Executor integration

## Architecture

```
Data Flow:
  Executor → PortfolioExecutorIntegration → PositionManager → State Files
                                          ↘
                                            PortfolioTracker → Reports
                                          ↗
                                   PnLCalculator
```

## Future Enhancements

- Strategy-based P&L tracking
- Performance attribution
- Benchmark comparisons
- Advanced risk metrics (Sharpe ratio, max drawdown)
- Real-time price updates from market data feeds
