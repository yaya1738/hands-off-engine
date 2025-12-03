# MATH ENGINE - CORE TRADING MATHEMATICS

## KNOWLEDGE BASE FOR: Mathematical Calculation Infrastructure

**File**: `executor/math_engine.py`
**Purpose**: Robust mathematical infrastructure for quantitative trading
**Serving**: Yair Siegel

---

## CORE MODULES

### 1. KELLY CRITERION (`kelly`)

The Kelly Criterion maximizes long-term growth rate for position sizing.

**Formula**: `f* = (bp - q) / b`

Where:
- `b` = odds received on the bet (net odds)
- `p` = probability of winning
- `q` = probability of losing (1 - p)
- `f*` = fraction of bankroll to bet

**Methods**:

```python
from executor.math_engine import kelly

# Optimal fraction
kelly.optimal_fraction(win_prob=0.6, odds=2.0)  # Returns: 0.2

# Optimal dollar size
kelly.optimal_size(win_prob=0.6, odds=2.0, bankroll=10000, fraction=0.5)  # Half Kelly

# From market price (Polymarket)
kelly.from_market_price(
    market_price=0.40,    # Current YES price
    true_prob=0.55,       # Your estimated probability
    bankroll=10000,
    fraction=0.5          # Half Kelly (safer)
)
# Returns: {"side": "BUY", "size": 150.00, "edge": 0.15, "kelly_f": 0.25}

# Multiple positions
kelly.multi_position(
    opportunities=[
        {"market": "A", "true_prob": 0.6, "market_price": 0.45},
        {"market": "B", "true_prob": 0.7, "market_price": 0.55}
    ],
    bankroll=10000,
    max_total_exposure=0.8
)
```

**Key Insights**:
- Always use fractional Kelly (0.5 = half) for real trading
- Maximum position capped at 25% of bankroll
- Negative Kelly = don't bet
- Scales down when total exposure exceeds limit

---

### 2. GRID CALCULATOR (`grid`)

Market-making grid generation for spread capture.

**Methods**:

```python
from executor.math_engine import grid

# Standard grid
grid.generate(
    center=0.5,           # Center price
    spread_bps=100,       # 100 bps = 1%
    levels=5,             # 5 levels each side
    size_per_level=10     # $10 per order
)
# Returns: {"bids": [...], "asks": [...], "total_orders": 10}

# Logarithmic grid (tighter near center)
grid.logarithmic_grid(
    center=0.5,
    spread_pct=5,
    levels=10,
    size_curve="exponential"  # "flat", "linear", "exponential"
)

# Optimal spread (Avellaneda-Stoikov)
grid.optimal_spread(
    volatility=0.02,      # Price volatility
    inventory=100,        # Current position
    risk_aversion=0.1     # Higher = wider spreads
)

# Price levels
grid.price_levels(start=0.40, end=0.60, count=10)
```

**Grid Types**:
- **Linear**: Equal spacing between levels
- **Logarithmic**: Tighter near center, wider at edges
- **Exponential sizing**: Larger orders at better prices

---

### 3. RISK CALCULATOR (`risk`)

Risk metrics and portfolio analysis.

**Methods**:

```python
from executor.math_engine import risk

# Value at Risk
risk.value_at_risk(
    returns=[-0.02, 0.01, -0.03, 0.02, -0.01],
    confidence=0.95,
    position_size=10000
)

# Expected Shortfall (CVaR)
risk.expected_shortfall(returns, confidence=0.95)

# Maximum Drawdown
risk.max_drawdown(equity_curve=[10000, 10500, 10200, 9800, 10100])
# Returns: {"max_drawdown": 0.067, "peak_idx": 1, "trough_idx": 3}

# Position Risk
risk.position_risk(
    entry_price=0.40,
    current_price=0.45,
    size=100,
    side="BUY"
)
# Returns: {"pnl": 5.00, "pnl_pct": 12.5, "max_loss": 40.00}

# Portfolio Exposure
risk.portfolio_exposure(positions=[
    {"side": "BUY", "size": 100, "price": 0.40},
    {"side": "SELL", "size": 50, "price": 0.60}
])
# Returns: {"long_exposure": 40, "short_exposure": 20, "net": 20, "gross": 60}

# Sharpe Ratio
risk.sharpe_ratio(returns, risk_free=0.02)
```

---

### 4. STATISTICAL CALCULATOR (`stats`)

Statistical analysis for market data.

**Methods**:

```python
from executor.math_engine import stats

# Volatility
stats.volatility(prices=[0.50, 0.51, 0.49, 0.52], window=20)

# EWMA Volatility (RiskMetrics)
stats.ewma_volatility(returns, decay=0.94)

# Correlation
stats.correlation(series1, series2)

# Mean Reversion Half-Life
stats.mean_reversion_half_life(prices)  # Ornstein-Uhlenbeck

# Z-Score
stats.zscore(value=0.55, mean=0.50, std=0.02)

# Percentile
stats.percentile(values, pct=0.95)
```

---

### 5. HFT CALCULATOR (`hft`)

High-frequency trading capacity calculations.

**Methods**:

```python
from executor.math_engine import hft

# Throughput Capacity
hft.throughput(
    wallets=63,           # Number of wallets
    rate_per_wallet=1000, # Orders/sec each
    processes=4,          # Parallel processes
    efficiency=0.8        # Overhead factor
)
# Returns: {"single_process_max": 63000, "multi_process_max": 201600}

# Latency Percentiles
hft.latency_percentiles(latencies=[10, 15, 12, 20, 8])
# Returns: {"p50": 12, "p95": 20, "p99": 20}

# Optimal Batch Size
hft.optimal_batch_size(
    network_latency_ms=50,
    processing_time_per_order_ms=2,
    max_latency_ms=100
)

# Capital Efficiency
hft.capital_efficiency(
    working_capital=5000,
    total_capital=10000,
    orders_per_sec=100
)
```

---

### 6. PRICE CALCULATOR (`price`)

Price manipulation utilities for Polymarket.

**Methods**:

```python
from executor.math_engine import price

# Implied Probability
price.implied_probability(0.45)  # 45%

# Price from Probability
price.price_from_probability(0.55)  # 0.55 (clamped to 0.001-0.999)

# Mid Price
price.mid_price(bid=0.44, ask=0.46)  # 0.45

# Spread Analysis
price.spread(bid=0.44, ask=0.46)
# Returns: {"absolute": 0.02, "relative": 0.044, "bps": 44.4}

# Round to Tick
price.round_to_tick(0.4567, tick_size=0.001)  # 0.457

# Binary Expected Value
price.binary_ev(price=0.40, true_prob=0.55, side="BUY")
# Returns: expected value per dollar risked
```

---

## UNIFIED INTERFACE

```python
from executor.math_engine import math

# All modules accessible
math.kelly.optimal_size(...)
math.grid.generate(...)
math.risk.value_at_risk(...)
math.stats.volatility(...)
math.hft.throughput(...)
math.price.binary_ev(...)

# Quick access methods
math.optimal_size(win_prob=0.6, odds=2.0, bankroll=10000)
math.generate_grid(center=0.5, spread_bps=100, levels=5)
math.calculate_var(returns, confidence=0.95)
math.throughput_capacity(wallets=100)
```

---

## POLYMARKET CONSTANTS

```python
POLYMARKET_MIN_PRICE = 0.001   # $0.001
POLYMARKET_MAX_PRICE = 0.999   # $0.999
POLYMARKET_TICK_SIZE = 0.001   # $0.001
POLYMARKET_MIN_SIZE = 0.01     # $0.01
MAX_POSITION_PCT = 0.25        # 25% max per position
```

---

## CLI USAGE

```bash
# Kelly calculation
python math_engine.py kelly 0.6 2.0 10000

# Grid generation
python math_engine.py grid 0.5 100 5

# Throughput calculation
python math_engine.py throughput 100
```

---

## INTEGRATION WITH TRADING

The math engine integrates with:
- `executor/yair_auto_trader.py` - Position sizing
- `executor/unlimited_hft.py` - Throughput calculations
- `autonomous/hft_execution_bridge.py` - Risk management
- `trading/` modules - Strategy calculations

---

## SPECIALIZED MATH MODULES

Additional mathematical libraries in `executor/math/`:

| Module | Purpose | Key Functions |
|--------|---------|---------------|
| `abstract_algebra.py` | Groups, rings, fields | Algebraic structures |
| `analysis.py` | Real/complex analysis | Limits, continuity |
| `discrete.py` | Discrete math | Combinatorics, graphs |
| `financial.py` | Financial math | Options, bonds, rates |
| `geometry.py` | Computational geometry | Vectors, transforms |
| `ml_math.py` | ML foundations | Gradients, loss functions |
| `number_theory.py` | Number theory | Primes, modular arithmetic |
| `statistics.py` | Statistical methods | Distributions, tests |

See `KNOWLEDGE_ADVANCED.md` for theoretical mathematics documentation.

---

## SUMMARY

**Core Capabilities**:
- Kelly Criterion position sizing with market price integration
- Grid generation for market making (linear & logarithmic)
- Full risk suite (VaR, CVaR, drawdown, Sharpe)
- HFT capacity planning (63 wallets × 1000 = 63K orders/sec)
- Polymarket-specific price utilities

**Key Design Principles**:
- All calculations pure Python (no heavy dependencies)
- Decimal precision for financial calculations
- Conservative defaults (half Kelly, 25% max position)
- Unified interface through `math` singleton
