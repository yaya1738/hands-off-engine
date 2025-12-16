#!/usr/bin/env python3
"""
INTEGRAFIX: Distributed Trading Demo
=====================================

Demonstrates how to upgrade existing trading code to use
distributed architecture with ZERO code changes.

Serving: Yair Siegel
"""

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


def demo_before():
    """
    BEFORE: Using local-only trading components.
    This is how your existing code probably looks.
    """
    print("=" * 60)
    print("BEFORE: Local-Only Trading")
    print("=" * 60)
    print()

    # Original imports (local only)
    from autonomous.trade_executor import TradeExecutor
    # from executor.polymarket_orders import PolymarketOrders  # Would need credentials

    executor = TradeExecutor()

    print("1. Getting market data (local only)...")
    markets = executor.get_market_data(limit=5)
    print(f"   ✅ Fetched {len(markets)} markets")
    print()

    print("LIMITATIONS:")
    print("  ❌ No failover - if local fails, trading stops")
    print("  ❌ No load balancing - all trades on this machine")
    print("  ❌ No redundancy - single point of failure")
    print()


def demo_after():
    """
    AFTER: Using distributed trading with automatic failover.
    SAME CODE, just different import!
    """
    print("=" * 60)
    print("AFTER: Distributed Trading")
    print("=" * 60)
    print()

    # New imports (distributed with auto-failover)
    from integrafix.distributed_trading_wrapper import executor, orders

    print("1. Getting market data (distributed with auto-failover)...")
    markets = executor.get_market_data(limit=5)
    print(f"   ✅ Fetched {len(markets)} markets")
    print()

    print("BENEFITS:")
    print("  ✅ Automatic failover - if local fails, uses remote")
    print("  ✅ Load balancing - distributes across all nodes")
    print("  ✅ High availability - keeps working even if nodes fail")
    print("  ✅ Real-time sync - all nodes see same data")
    print()


def demo_advanced():
    """
    ADVANCED: Explicit control over execution mode.
    """
    print("=" * 60)
    print("ADVANCED: Explicit Execution Control")
    print("=" * 60)
    print()

    from integrafix.distributed_trading_integration import (
        get_distributed_trading,
        ExecutionMode
    )

    trading = get_distributed_trading()

    # Test different execution modes
    print("1. LOCAL_FIRST (default):")
    result = trading.get_market_data(limit=5, mode=ExecutionMode.LOCAL_FIRST)
    print(f"   Success: {result.success}")
    print(f"   Executed on: {result.executed_on}")
    print(f"   Latency: {result.latency_ms:.2f}ms")
    print()

    print("2. LOAD_BALANCED:")
    result = trading.get_market_data(limit=5, mode=ExecutionMode.LOAD_BALANCED)
    print(f"   Success: {result.success}")
    print(f"   Executed on: {result.executed_on}")
    print(f"   Latency: {result.latency_ms:.2f}ms")
    print()

    # Show stats
    print("3. Execution Statistics:")
    stats = trading.get_stats()
    print(f"   Total Requests: {stats['total_requests']}")
    print(f"   Local: {stats['local_executions']}, Remote: {stats['remote_executions']}")
    print(f"   Failures: {stats['failures']}")
    print(f"   Success Rate: {stats['success_rate']:.1%}")
    print(f"   Avg Latency: {stats['avg_latency_ms']:.2f}ms")
    print()


def demo_migration():
    """
    Show migration path for existing trading code.
    """
    print("=" * 60)
    print("MIGRATION GUIDE")
    print("=" * 60)
    print()

    print("""
STEP 1: Change Import (1 line)
-------------------------------
# Before:
from autonomous.trade_executor import TradeExecutor
executor = TradeExecutor()

# After:
from integrafix.distributed_trading_wrapper import executor
# That's it! executor is already initialized and distributed

STEP 2: Use Same API
--------------------
# Your existing code works unchanged:
markets = executor.get_market_data(limit=20)

# All order operations work the same:
from integrafix.distributed_trading_wrapper import orders

result = orders.limit_buy_yes('bitcoin-10k', 0.40, 10)
result = orders.market_buy_no('ethereum-5k', 5)

STEP 3: Setup Remote Nodes (Optional)
--------------------------------------
# On remote machines, register as trading service:
$ python3 integrafix/distributed_trading_integration.py --register

# Now your local code automatically uses remote nodes!

STEP 4: Monitor (Optional)
---------------------------
# Check stats:
from integrafix.distributed_trading_wrapper import get_trading_stats

stats = get_trading_stats()
print(f"Success rate: {stats['success_rate']:.1%}")

# Check services:
from integrafix.distributed_trading_wrapper import get_service_status

services = get_service_status()
for svc in services:
    print(f"{svc['service_id']}: {svc['health']}")

BENEFITS:
---------
✅ Zero code changes in your trading logic
✅ Automatic failover if local fails
✅ Load balancing across multiple machines
✅ Real-time trade data sync
✅ High availability
✅ Easy to add more capacity (just register more nodes)
    """)


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(
        description='INTEGRAFIX Distributed Trading Demo'
    )
    parser.add_argument(
        '--before',
        action='store_true',
        help='Show local-only trading (before)'
    )
    parser.add_argument(
        '--after',
        action='store_true',
        help='Show distributed trading (after)'
    )
    parser.add_argument(
        '--advanced',
        action='store_true',
        help='Show advanced features'
    )
    parser.add_argument(
        '--migration',
        action='store_true',
        help='Show migration guide'
    )
    parser.add_argument(
        '--all',
        action='store_true',
        help='Show all demos'
    )

    args = parser.parse_args()

    if args.all or (not args.before and not args.after and not args.advanced and not args.migration):
        # Run all demos
        demo_before()
        print()
        demo_after()
        print()
        demo_advanced()
        print()
        demo_migration()
    else:
        if args.before:
            demo_before()
        if args.after:
            demo_after()
        if args.advanced:
            demo_advanced()
        if args.migration:
            demo_migration()
