# Simulator Module

The simulator module provides comprehensive backtesting capabilities for the Hands-Off Engine trading strategies.

## Components

### 1. Market Simulator (`market.py`)
Simulates market price movements for backtesting:
- **Replay historical odds data** - Load and replay actual market data
- **Generate synthetic scenarios** - Create realistic market data using random walks
- **Multiple markets support** - Simulate many markets simultaneously
- **Time-series queries** - Query market state at any point in time

### 2. Execution Simulator (`executor.py`)
Simulates realistic order execution:
- **Order fills** - Simulates market and limit orders
- **Slippage modeling** - Price impact based on order size
- **Fee tracking** - Configurable trading fees
- **Position tracking** - Tracks all open positions
- **P&L calculation** - Real-time and final P&L

### 3. Backtest Engine (`backtest.py`)
Orchestrates the backtesting process:
- **Strategy execution** - Runs strategies over historical/synthetic data
- **Step-by-step simulation** - Time-based simulation with configurable intervals
- **Performance tracking** - Records all metrics throughout backtest
- **Multiple strategies** - Compare different approaches

### 4. Performance Metrics (`metrics.py`)
Calculates comprehensive trading metrics:
- **Sharpe ratio** - Risk-adjusted returns
- **Maximum drawdown** - Worst peak-to-trough decline
- **Win rate** - Percentage of profitable trades
- **Profit factor** - Ratio of gross profit to gross loss
- **Edge decay analysis** - Track strategy performance over time
- **CAGR** - Compound annual growth rate

### 5. Report Generator (`reports.py`)
Creates professional reports:
- **HTML reports** - Interactive styled reports
- **Markdown reports** - Simple text-based reports
- **Comparison tables** - Compare multiple strategies
- **Trade analysis** - Detailed trade-by-trade breakdowns

## Usage

### Command Line

Run a backtest from the command line:

```bash
# Basic usage with synthetic data
python -m simulator.backtest --start 2024-01-01 --end 2024-12-31 --strategy buy_and_hold --synthetic

# Custom configuration
python -m simulator.backtest \
  --start 2024-01-01 \
  --end 2024-12-31 \
  --strategy threshold \
  --capital 5000 \
  --fee-rate 0.02 \
  --slippage-rate 0.005 \
  --interval-hours 1 \
  --report-format both \
  --synthetic
```

### Python API

Use the simulator programmatically:

```python
from datetime import datetime, timezone
from simulator.market import MarketSimulator, Market
from simulator.backtest import BacktestEngine, BacktestConfig
from simulator.reports import ReportGenerator

# Create synthetic market data
market_sim = MarketSimulator()
market = Market(
    market_id="btc_100k",
    market_name="BTC $100k by EOY?",
    initial_yes_price=0.40,
    volatility=0.05,
    drift=0.01
)

start = datetime(2024, 1, 1, tzinfo=timezone.utc)
end = datetime(2024, 12, 31, tzinfo=timezone.utc)
market_sim.generate_synthetic_data(market, start, end, interval_hours=1)

# Run backtest
engine = BacktestEngine(market_simulator=market_sim)
config = BacktestConfig(
    strategy_name="my_strategy",
    start_date=start,
    end_date=end,
    initial_capital=1000.0
)

def my_strategy(timestamp, market_snapshots, executor):
    """Your custom strategy logic"""
    actions = []
    # ... strategy implementation
    return actions

result = engine.run_backtest(config, my_strategy)

# Generate reports
report_gen = ReportGenerator()
report_gen.generate_html_report(result)
report_gen.generate_markdown_report(result)
```

## Built-in Strategies

### Buy and Hold
Simple strategy that buys YES on all markets at the start.

```bash
python -m simulator.backtest --start 2024-01-01 --end 2024-12-31 --strategy buy_and_hold --synthetic
```

### Threshold Strategy
Buys YES when price < 0.3, buys NO when price > 0.7.

```bash
python -m simulator.backtest --start 2024-01-01 --end 2024-12-31 --strategy threshold --synthetic
```

## Creating Custom Strategies

A strategy is a function with this signature:

```python
def my_strategy(
    timestamp: datetime,
    market_snapshots: Dict[str, MarketSnapshot],
    executor: ExecutionSimulator
) -> List[Dict]:
    """
    Args:
        timestamp: Current simulation time
        market_snapshots: Dict of market_id -> MarketSnapshot
        executor: ExecutionSimulator with current portfolio state
    
    Returns:
        List of action dicts with keys:
        - market_id: str
        - side: "YES" or "NO"
        - size: float (dollar amount)
        - limit_price: Optional[float]
    """
    actions = []
    
    for market_id, snapshot in market_snapshots.items():
        # Your strategy logic here
        if some_condition:
            actions.append({
                'market_id': market_id,
                'side': 'YES',
                'size': 100.0
            })
    
    return actions
```

Register your strategy in `__main__.py`:

```python
STRATEGIES = {
    'buy_and_hold': buy_and_hold_strategy,
    'threshold': simple_threshold_strategy,
    'my_strategy': my_strategy,  # Add your strategy
}
```

## Data Directories

- `data/historical/` - Historical market data files (JSON format)
- `data/simulations/` - Backtest results (JSON format)
- `data/simulations/reports/` - Generated reports (HTML/Markdown)

## Output Files

### Backtest Results (JSON)
```json
{
  "strategy": "my_strategy",
  "start_date": "2024-01-01T00:00:00+00:00",
  "end_date": "2024-12-31T00:00:00+00:00",
  "initial_capital": 1000.0,
  "final_value": 1150.0,
  "total_return_pct": 15.0,
  "num_trades": 42,
  "metrics": {
    "sharpe_ratio": 1.25,
    "max_drawdown_pct": 8.5,
    "win_rate": 65.0,
    "profit_factor": 1.8
  }
}
```

### Reports
- **HTML**: Interactive report with styling and formatting
- **Markdown**: Plain text report for easy viewing
- **Comparison tables**: Side-by-side strategy comparison

## Performance Metrics Explained

- **Total Return**: Overall percentage gain/loss
- **Sharpe Ratio**: Risk-adjusted return (higher is better, >1 is good)
- **Max Drawdown**: Largest peak-to-trough decline (lower is better)
- **Win Rate**: Percentage of profitable trades
- **Profit Factor**: Gross profit / gross loss (>1 means profitable)
- **Average Win/Loss**: Average P&L per winning/losing trade

## Integration with Main Engine

The simulator is designed to work with the main Hands-Off Engine components:

- Uses same `audit` logging system
- Compatible with `decider` module's PlannedAction format
- Can test strategies that use `alpha` module signals
- Respects `executor` safety constraints (max position size, confidence thresholds)

## Best Practices

1. **Start with synthetic data** - Use `--synthetic` flag to test strategies quickly
2. **Use realistic parameters** - Set fee_rate and slippage_rate to match real markets
3. **Test multiple time periods** - Ensure strategy works across different market conditions
4. **Compare strategies** - Run multiple strategies and compare results
5. **Analyze edge decay** - Check if strategy performance degrades over time
6. **Review individual trades** - Use trade analysis reports to understand behavior

## Future Enhancements

Potential additions to the simulator:

- Real-time data fetching from Polymarket API
- Advanced slippage models (order book depth)
- Multi-asset portfolio optimization
- Walk-forward optimization
- Monte Carlo simulation
- Risk parity strategies
- Machine learning integration

## Examples

See the `__main__.py` file for complete examples of running backtests from the command line.

Each module (`market.py`, `executor.py`, `metrics.py`, etc.) also includes example usage in its `if __name__ == "__main__"` section.
