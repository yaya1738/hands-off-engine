#!/usr/bin/env python3
"""
Portfolio Tracking System Example

Demonstrates the full portfolio tracking pipeline.
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from portfolio.positions import PositionManager
from portfolio.tracker import PortfolioTracker
from portfolio.executor_integration import PortfolioExecutorIntegration


def example_basic_usage():
    """Example: Basic position management"""
    print("=" * 70)
    print("EXAMPLE 1: Basic Position Management")
    print("=" * 70 + "\n")
    
    pm = PositionManager()
    
    print("Adding position...")
    pos = pm.add_position(
        market_id="btc_100k_eoy",
        market_name="Will BTC hit $100k by EOY?",
        side="YES",
        entry_price=0.45,
        quantity=100.0,
        mode="DRYRUN"
    )
    print(f"✓ Position created: {pos.position_id}")
    print(f"  Entry amount: ${pos.entry_amount:.2f}")
    
    print("\nUpdating price to $0.55...")
    pm.update_position_price(pos.position_id, 0.55)
    updated = pm.get_position(pos.position_id)
    print(f"✓ Price updated")
    print(f"  Unrealized P&L: ${updated.unrealized_pnl:.2f}")
    
    print("\nClosing position at $0.60...")
    closed = pm.close_position(pos.position_id, 0.60)
    print(f"✓ Position closed")
    print(f"  Realized P&L: ${closed.realized_pnl:.2f}\n")


def example_executor_integration():
    """Example: Integration with executor"""
    print("=" * 70)
    print("EXAMPLE 2: Executor Integration")
    print("=" * 70 + "\n")
    
    integration = PortfolioExecutorIntegration()
    
    print("Simulating trade executions...")
    pos_id = integration.on_trade_executed(
        market_id="market_1",
        market_name="Will BTC hit $100k?",
        side="YES",
        price=0.45,
        quantity=100.0,
        mode="DRYRUN"
    )
    print(f"  ✓ Trade executed")
    
    print("\nUpdating market prices...")
    integration.update_position_prices({"market_1": 0.55})
    print(f"  ✓ Prices updated")
    
    summary = integration.get_portfolio_summary(mode="DRYRUN")
    print(f"\nPortfolio Summary:")
    print(f"  Unrealized P&L: ${summary['open_positions']['unrealized_pnl']:.2f}\n")


if __name__ == '__main__':
    print("\nPORTFOLIO TRACKING SYSTEM EXAMPLES\n")
    example_basic_usage()
    print("-" * 70 + "\n")
    example_executor_integration()
    print("State files: ./state/portfolio/")
