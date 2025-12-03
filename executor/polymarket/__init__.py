"""
Polymarket Infrastructure - Complete Trading Platform
======================================================

Comprehensive Polymarket knowledge and trading infrastructure:

MODULES:
--------
1. core (market)       - Market structure, outcomes, resolution, fees
2. clob                - Order book API, order building, fill estimation
3. orders              - Order management, all order types, batch operations
4. strategies          - Market making, arbitrage, hedging, directional
5. portfolio           - Position tracking, P&L, performance metrics
6. risk                - Risk limits, drawdown, VaR, stop losses
7. analysis            - Probability, liquidity, market efficiency
8. execution           - TWAP, VWAP, iceberg, smart routing

QUICK USAGE:
------------
```python
from executor.polymarket import market, clob, orders, strategies, portfolio, risk, analysis, execution

# Core market mechanics
market.binary_constraint(0.65, 0.35)          # Check YES+NO=1
market.kelly_criterion(0.6, 0.5)              # Optimal bet sizing
market.implied_probability(0.65)              # 65%

# Order book operations
fill = clob.estimate_fill(orderbook, 'BUY', 100)
metrics = clob.calculate_spread_metrics(orderbook)

# Order management
order = orders.create_limit_order('BUY', token_id, 0.65, 100)
orders.calculate_required_balance(0.65, 100, 'BUY')

# Trading strategies
quotes = strategies.calculate_mm_quotes(0.65, 0.02)
arb = strategies.binary_arbitrage_opportunity(0.60, 0.38)

# Portfolio management
portfolio.add_position(token_id, 100, 0.65)
summary = portfolio.get_summary()

# Risk management
risk.check_position_limit(500, current_position=200)
var = risk.calculate_var(returns, confidence=0.95)

# Market analysis
liquidity = analysis.analyze_liquidity(bids, asks)
ev = analysis.expected_value_analysis(0.65, 0.70, size=100)

# Execution algorithms
plan = execution.twap_schedule(1000, duration_minutes=60)
slices = execution.iceberg_slices(5000, max_visible=100)
```

POLYMARKET KNOWLEDGE BASE:
--------------------------
- Network: Polygon (Chain ID 137)
- Collateral: USDC (6 decimals)
- Binary markets: YES + NO = $1
- Tick size: $0.001
- Min order: $0.01
- Resolution: UMA optimistic oracle
- Fees: 0% trading, 2% on winning profits at resolution

API ENDPOINTS:
- CLOB: https://clob.polymarket.com
- Gamma: https://gamma-api.polymarket.com
"""

# Import all singleton instances
from .core import market, PolymarketCore
from .clob import clob, PolymarketCLOB, OrderBook, OrderBookLevel, Order, Trade
from .orders import orders, OrderManager, OrderParams, OrderState, OrderSide, OrderType, OrderStatus
from .strategies import strategies, TradingStrategies, Quote, ArbitrageOpportunity
from .portfolio import portfolio, PortfolioManager, Position, PortfolioSnapshot
from .risk import risk, RiskManager, RiskLimits, RiskMetrics, RiskLevel
from .analysis import analysis, MarketAnalysis, LiquidityMetrics
from .execution import execution, ExecutionEngine, ExecutionPlan, ExecutionSlice, ExecutionStrategy


class Polymarket:
    """
    Unified Polymarket trading interface.

    Access all functionality through a single entry point:
        poly = Polymarket()
        poly.market.kelly_criterion(0.6, 0.5)
        poly.clob.estimate_fill(orderbook, 'BUY', 100)
        poly.strategies.calculate_mm_quotes(0.65, 0.02)
    """

    def __init__(self):
        # Core modules
        self.market = market
        self.core = market

        self.clob = clob
        self.orderbook = clob

        self.orders = orders
        self.order_manager = orders

        self.strategies = strategies
        self.strats = strategies

        self.portfolio = portfolio
        self.positions = portfolio

        self.risk = risk
        self.risk_manager = risk

        self.analysis = analysis
        self.analytics = analysis

        self.execution = execution
        self.exec = execution

    def list_modules(self) -> dict:
        """List all available modules"""
        return {
            'market (core)': 'Market structure, outcomes, resolution, fees',
            'clob (orderbook)': 'Order book API, fill estimation, spread metrics',
            'orders (order_manager)': 'Order types, validation, batch operations',
            'strategies (strats)': 'Market making, arbitrage, hedging, directional',
            'portfolio (positions)': 'Position tracking, P&L, performance metrics',
            'risk (risk_manager)': 'Risk limits, drawdown, VaR, stop losses',
            'analysis (analytics)': 'Probability, liquidity, market efficiency',
            'execution (exec)': 'TWAP, VWAP, iceberg, smart routing'
        }

    def quick_status(self) -> dict:
        """Quick status of key parameters"""
        return {
            'network': 'Polygon (137)',
            'collateral': 'USDC',
            'clob_host': market.CLOB_HOST,
            'min_tick': market.MIN_TICK_SIZE,
            'min_order': market.MIN_ORDER_SIZE,
            'maker_fee': f"{market.MAKER_FEE * 100}%",
            'taker_fee': f"{market.TAKER_FEE * 100}%",
            'resolution_fee': f"{market.RESOLUTION_FEE * 100}%"
        }

    # ==========================================
    # CONVENIENCE METHODS
    # ==========================================

    def check_arbitrage(self, yes_price: float, no_price: float) -> dict:
        """Quick arbitrage check"""
        return market.binary_arbitrage_check(yes_price, no_price)

    def optimal_bet_size(self, win_prob: float, market_price: float,
                         bankroll: float = 1000) -> dict:
        """Calculate optimal bet size"""
        kelly = market.kelly_criterion(win_prob, market_price)
        half_kelly = market.half_kelly(win_prob, market_price)

        return {
            'kelly_fraction': kelly,
            'kelly_size': bankroll * max(0, kelly),
            'half_kelly_size': bankroll * max(0, half_kelly),
            'recommendation': 'buy' if kelly > 0 else 'sell' if kelly < 0 else 'no_edge'
        }

    def analyze_opportunity(self, yes_price: float, estimated_prob: float,
                            days_to_resolution: float = 30) -> dict:
        """Analyze a trading opportunity"""
        edge = estimated_prob - yes_price
        ev = analysis.expected_value_analysis(yes_price, estimated_prob)
        annualized = market.annualized_return(yes_price, days_to_resolution, estimated_prob)

        return {
            'price': yes_price,
            'estimated_probability': estimated_prob,
            'edge': edge,
            'edge_percent': edge * 100,
            'expected_value': ev['ev_per_share'],
            'annualized_return': annualized,
            'recommendation': ev['recommendation'],
            'kelly_fraction': market.kelly_criterion(estimated_prob, yes_price)
        }

    def create_mm_grid(self, fair_value: float, half_spread: float,
                       levels: int = 5, size_per_level: float = 100) -> list:
        """Create market making grid of orders"""
        grid = []
        for i in range(levels):
            offset = half_spread * (i + 1)

            # Bid side
            bid_price = market.probability_to_price(fair_value - offset)
            grid.append({
                'side': 'BUY',
                'price': bid_price,
                'size': size_per_level,
                'level': i + 1
            })

            # Ask side
            ask_price = market.probability_to_price(fair_value + offset)
            grid.append({
                'side': 'SELL',
                'price': ask_price,
                'size': size_per_level,
                'level': i + 1
            })

        return grid


# Singleton unified interface
poly = Polymarket()

# Export everything
__all__ = [
    # Singleton instances (primary usage)
    'market', 'clob', 'orders', 'strategies', 'portfolio',
    'risk', 'analysis', 'execution', 'poly',

    # Classes (for custom instantiation)
    'PolymarketCore', 'PolymarketCLOB', 'OrderManager',
    'TradingStrategies', 'PortfolioManager', 'RiskManager',
    'MarketAnalysis', 'ExecutionEngine', 'Polymarket',

    # Data classes
    'OrderBook', 'OrderBookLevel', 'Order', 'Trade',
    'OrderParams', 'OrderState', 'Position', 'PortfolioSnapshot',
    'Quote', 'ArbitrageOpportunity', 'RiskLimits', 'RiskMetrics',
    'LiquidityMetrics', 'ExecutionPlan', 'ExecutionSlice',

    # Enums
    'OrderSide', 'OrderType', 'OrderStatus', 'RiskLevel', 'ExecutionStrategy'
]
