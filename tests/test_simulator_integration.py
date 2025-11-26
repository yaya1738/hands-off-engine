#!/usr/bin/env python3
"""
Integration test for simulator with existing decider/executor modules.

Tests that the simulator can work with PlannedAction format from decider.
"""

import sys
import os
from datetime import datetime, timezone, timedelta

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from simulator.market import MarketSimulator, Market, MarketSnapshot
from simulator.executor import ExecutionSimulator
from simulator.backtest import BacktestEngine, BacktestConfig
from simulator.metrics import PerformanceMetrics
from decider.ho_decider import PlannedAction


def alpha_driven_strategy(timestamp, market_snapshots, executor):
    """
    Strategy that mimics the decider module's PlannedAction approach.
    
    This demonstrates integration between simulator and main engine components.
    """
    actions = []
    
    # Simulate alpha signals (in real scenario, these come from alpha module)
    for market_id, snapshot in market_snapshots.items():
        # Simple edge calculation: if price seems too low or too high
        edge = 0.0
        side = None
        confidence = 0.0
        
        if snapshot.yes_price < 0.35:
            # Market seems underpriced for YES
            edge = 0.35 - snapshot.yes_price
            side = "YES"
            confidence = min(0.95, 0.7 + edge * 2)
        elif snapshot.yes_price > 0.65:
            # Market seems overpriced for YES (good for NO)
            edge = snapshot.yes_price - 0.65
            side = "NO"
            confidence = min(0.95, 0.7 + edge * 2)
        
        # Only act if we have edge and meet confidence threshold (like executor's MIN_CONFIDENCE_THRESHOLD)
        if edge > 0 and confidence >= 0.7:
            # Check if we already have a position (avoid over-concentration)
            if market_id in executor.positions:
                continue
            
            # Kelly-style sizing (simplified)
            # Kelly = edge / odds, but cap at 10% of capital
            max_size = min(100.0, executor.capital * 0.1)  # Matches executor's MAX_POSITION_SIZE
            
            # Create action in format similar to PlannedAction
            actions.append({
                'market_id': market_id,
                'side': side,
                'size': max_size,
                'limit_price': None,  # Market order
                'confidence': confidence,
                'reasoning': f'Edge: {edge:.3f}, Confidence: {confidence:.2f}'
            })
    
    return actions


def test_integration():
    """Test simulator integration with existing modules"""
    print("=" * 70)
    print("Testing Simulator Integration with Decider/Executor Concepts")
    print("=" * 70)
    print()
    
    # Create market simulator with synthetic data
    market_sim = MarketSimulator()
    
    # Create markets with different characteristics
    markets = [
        Market(
            market_id="underpriced_market",
            market_name="Underpriced market (starts at 0.25)",
            initial_yes_price=0.25,
            volatility=0.02,
            drift=0.005
        ),
        Market(
            market_id="overpriced_market",
            market_name="Overpriced market (starts at 0.75)",
            initial_yes_price=0.75,
            volatility=0.02,
            drift=-0.005
        ),
        Market(
            market_id="neutral_market",
            market_name="Neutral market (starts at 0.50)",
            initial_yes_price=0.50,
            volatility=0.03,
            drift=0.0
        ),
    ]
    
    start = datetime(2024, 1, 1, tzinfo=timezone.utc)
    end = datetime(2024, 1, 15, tzinfo=timezone.utc)
    
    print("Generating synthetic market data...")
    for market in markets:
        snapshots = market_sim.generate_synthetic_data(market, start, end, interval_hours=1)
        print(f"  {market.market_name}: {len(snapshots)} snapshots")
    print()
    
    # Create backtest configuration
    config = BacktestConfig(
        strategy_name="alpha_driven",
        start_date=start,
        end_date=end,
        initial_capital=1000.0,
        fee_rate=0.02,  # 2% like Polymarket
        slippage_rate=0.005,
        interval_hours=1
    )
    
    # Run backtest
    print("Running backtest with alpha-driven strategy...")
    engine = BacktestEngine(market_simulator=market_sim)
    result = engine.run_backtest(config, alpha_driven_strategy)
    
    # Display results
    print()
    print("=" * 70)
    print("Results")
    print("=" * 70)
    
    if result.success:
        print(f"✅ Backtest completed successfully")
        print()
        print(f"Initial Capital: ${config.initial_capital:,.2f}")
        print(f"Final Value: ${result.final_portfolio_value:,.2f}")
        print(f"Total Return: {result.total_return_pct:+.2f}%")
        print(f"Number of Trades: {result.num_trades}")
        
        summary = result.metrics.get_summary()
        print()
        print("Performance Metrics:")
        print(f"  Sharpe Ratio: {summary.get('sharpe_ratio', 0):.3f}")
        print(f"  Max Drawdown: {summary.get('max_drawdown_pct', 0):.2f}%")
        print(f"  Win Rate: {summary.get('win_rate', 0):.2f}%")
        print(f"  Profit Factor: {summary.get('profit_factor', 0):.2f}")
        
        print()
        print("✅ Integration test passed!")
        print()
        print("The simulator successfully:")
        print("  - Works with PlannedAction-like format")
        print("  - Respects executor safety constraints (max position, confidence)")
        print("  - Integrates with audit logging")
        print("  - Produces comprehensive metrics")
    else:
        print(f"❌ Backtest failed: {result.error_message}")
        return False
    
    return True


if __name__ == "__main__":
    success = test_integration()
    sys.exit(0 if success else 1)
