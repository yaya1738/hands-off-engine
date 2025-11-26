#!/usr/bin/env python3
"""
Complete example demonstrating all simulator features.
"""

import sys
import os
from datetime import datetime, timezone

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from simulator.market import MarketSimulator, Market
from simulator.backtest import BacktestEngine, BacktestConfig
from simulator.reports import ReportGenerator


def momentum_strategy(timestamp, market_snapshots, executor):
    """Momentum strategy"""
    actions = []
    for market_id, snapshot in market_snapshots.items():
        if market_id in executor.positions:
            continue
        if 0.40 <= snapshot.yes_price <= 0.60:
            actions.append({'market_id': market_id, 'side': 'YES', 'size': 75.0})
    return actions


def mean_reversion_strategy(timestamp, market_snapshots, executor):
    """Mean reversion strategy"""
    actions = []
    for market_id, snapshot in market_snapshots.items():
        if market_id in executor.positions:
            continue
        if snapshot.yes_price < 0.35:
            actions.append({'market_id': market_id, 'side': 'YES', 'size': 80.0})
        elif snapshot.yes_price > 0.65:
            actions.append({'market_id': market_id, 'side': 'NO', 'size': 80.0})
    return actions


def main():
    print("=" * 70)
    print("Simulator Complete Example")
    print("=" * 70)
    
    market_sim = MarketSimulator()
    markets = [
        Market("volatile_market", "Volatile market", 0.50, 0.10, 0.0),
        Market("trending_up", "Upward trending", 0.30, 0.03, 0.015),
    ]
    
    start = datetime(2024, 1, 1, tzinfo=timezone.utc)
    end = datetime(2024, 2, 1, tzinfo=timezone.utc)
    
    for market in markets:
        market_sim.generate_synthetic_data(market, start, end, interval_hours=1)
    
    engine = BacktestEngine(market_simulator=market_sim)
    strategies = {'momentum': momentum_strategy, 'mean_reversion': mean_reversion_strategy}
    results = []
    
    for name, func in strategies.items():
        config = BacktestConfig(name, start, end, 1000.0)
        result = engine.run_backtest(config, func)
        results.append(result)
        print(f"{name}: {result.total_return_pct:+.2f}%")
    
    report_gen = ReportGenerator()
    report_gen.generate_comparison_table(results, format="html")
    print("\nReports generated in data/simulations/reports/")


if __name__ == "__main__":
    main()
