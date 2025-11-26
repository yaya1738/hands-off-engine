#!/usr/bin/env python3
"""
Live Execution Pipeline Demo

This script demonstrates the complete execution pipeline from
signal to trade, including all safety checks and monitoring.
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from decider.ho_decider import Decider, PlannedAction
from executor.core import ExecutorCore


def demo_basic_execution():
    """Demonstrate basic execution flow"""
    print("\n" + "=" * 70)
    print("  DEMO 1: Basic Execution Flow")
    print("=" * 70 + "\n")
    
    # Initialize executor in DRYRUN mode (default)
    executor = ExecutorCore(dryrun=True, bankroll=1000.0)
    
    # Check initial status
    status = executor.get_status()
    print(f"Initial Status:")
    print(f"  Mode: {status['mode']}")
    print(f"  Kill Switch: {'ENABLED' if status['kill_switch']['enabled'] else 'disabled'}")
    print(f"  Pending Orders: {status['pending_orders']['total_pending']}")
    
    # Create test actions
    actions = [
        PlannedAction(
            market_id="demo_market_1",
            market_name="Will BTC reach $100k by EOY?",
            side="YES",
            amount=50.0,
            confidence=0.85,
            reasoning="Strong bullish signals, high confidence"
        ),
        PlannedAction(
            market_id="demo_market_2",
            market_name="Will ETH reach $5k by EOY?",
            side="NO",
            amount=30.0,
            confidence=0.75,
            reasoning="Moderate bearish signals"
        ),
    ]
    
    print(f"\nPlanned Actions: {len(actions)}")
    for i, action in enumerate(actions, 1):
        print(f"  {i}. {action.market_name}")
        print(f"     Side: {action.side}, Amount: ${action.amount:.2f}, Confidence: {action.confidence:.1%}")
    
    # Execute signals
    print("\nExecuting signals...")
    summary = executor.execute_signals(actions)
    
    print(f"\nExecution Summary:")
    print(f"  Status: {summary['status']}")
    print(f"  Total Actions: {summary['total_actions']}")
    print(f"  Executed: {summary['executed_count']}")
    print(f"  Rejected: {summary['rejected_count']}")
    
    if summary['executed']:
        print(f"\nExecuted Orders:")
        for item in summary['executed']:
            result = item['result']
            print(f"  - {item['order'].market_name}")
            print(f"    Status: {result.status}")
            print(f"    Filled: ${result.filled_amount:.2f} @ {result.filled_price:.4f}")
            print(f"    Slippage: {result.slippage_bps:.2f} bps")
            print(f"    Time: {result.execution_time_ms:.0f} ms")


def demo_safety_checks():
    """Demonstrate safety checks and rejections"""
    print("\n" + "=" * 70)
    print("  DEMO 2: Safety Checks and Rejections")
    print("=" * 70 + "\n")
    
    executor = ExecutorCore(dryrun=True, bankroll=1000.0)
    
    # Create actions that will trigger various safety checks
    actions = [
        PlannedAction(
            market_id="safe_market",
            market_name="Safe Market (will pass)",
            side="YES",
            amount=50.0,
            confidence=0.85,
            reasoning="Valid action"
        ),
        PlannedAction(
            market_id="low_conf_market",
            market_name="Low Confidence Market (will fail)",
            side="YES",
            amount=50.0,
            confidence=0.5,  # Below 0.7 threshold
            reasoning="Low confidence - should be rejected"
        ),
        PlannedAction(
            market_id="large_position",
            market_name="Large Position (will fail)",
            side="YES",
            amount=150.0,  # Above $100 limit
            confidence=0.9,
            reasoning="Too large - should be rejected"
        ),
    ]
    
    print(f"Testing {len(actions)} actions with various risk profiles...")
    
    summary = executor.execute_signals(actions)
    
    print(f"\nResults:")
    print(f"  Executed: {summary['executed_count']}")
    print(f"  Rejected: {summary['rejected_count']}")
    
    if summary['rejected']:
        print(f"\nRejected Orders:")
        for item in summary['rejected']:
            action = item['action']
            print(f"  - {action.market_name}")
            print(f"    Reason: {item['reason']}")
            if 'details' in item:
                for detail in item['details']:
                    print(f"      • {detail}")


def demo_kill_switch():
    """Demonstrate kill switch functionality"""
    print("\n" + "=" * 70)
    print("  DEMO 3: Kill Switch (Emergency Stop)")
    print("=" * 70 + "\n")
    
    executor = ExecutorCore(dryrun=True, bankroll=1000.0)
    
    action = PlannedAction(
        market_id="test_market",
        market_name="Test Market",
        side="YES",
        amount=50.0,
        confidence=0.85,
        reasoning="Test action"
    )
    
    # Normal execution
    print("1. Normal execution:")
    summary = executor.execute_signals([action])
    print(f"   Status: {summary['status']}")
    print(f"   Executed: {summary['executed_count']}")
    
    # Enable kill switch
    print("\n2. Enabling kill switch...")
    executor.enable_kill_switch("Emergency: Market volatility too high")
    print("   Kill switch ENABLED")
    
    # Try to execute with kill switch
    print("\n3. Attempting execution with kill switch:")
    summary = executor.execute_signals([action])
    print(f"   Status: {summary['status']}")
    print(f"   Message: {summary.get('message', 'N/A')}")
    
    # Disable kill switch
    print("\n4. Disabling kill switch...")
    executor.disable_kill_switch()
    print("   Kill switch disabled")
    
    # Normal execution again
    print("\n5. Normal execution after reset:")
    summary = executor.execute_signals([action])
    print(f"   Status: {summary['status']}")
    print(f"   Executed: {summary['executed_count']}")


def demo_with_decider():
    """Demonstrate integration with Decider"""
    print("\n" + "=" * 70)
    print("  DEMO 4: Complete Pipeline (Decider → Executor)")
    print("=" * 70 + "\n")
    
    # Check if model file exists
    repo_root = Path(__file__).parent.parent
    model_path = repo_root / 'state' / 'polymarket-model.json'
    
    if not model_path.exists():
        print("⊘ Skipping: Model file not found")
        print(f"   Expected at: {model_path}")
        return
    
    print("Loading signals from Decider...")
    decider = Decider(bankroll=1000.0)
    signals = decider.load_model_signals(model_path)
    
    # Limit to first 3 for demo
    signals = signals[:3]
    print(f"Loaded {len(signals)} signals")
    
    # Plan actions
    print("\nPlanning actions...")
    planned_actions = decider.plan_actions(signals)
    print(f"Planned {len(planned_actions)} actions")
    
    for i, action in enumerate(planned_actions, 1):
        print(f"  {i}. {action.market_name}")
        print(f"     Side: {action.side}, Amount: ${action.amount:.2f}, Confidence: {action.confidence:.1%}")
    
    # Execute through pipeline
    print("\nExecuting through pipeline...")
    executor = ExecutorCore(dryrun=True, bankroll=1000.0)
    summary = executor.execute_signals(planned_actions)
    
    print(f"\nExecution Summary:")
    print(f"  Status: {summary['status']}")
    print(f"  Mode: {summary['mode']}")
    print(f"  Total: {summary['total_actions']}")
    print(f"  Executed: {summary['executed_count']}")
    print(f"  Rejected: {summary['rejected_count']}")
    
    # Show final status
    status = executor.get_status()
    print(f"\nFinal Status:")
    print(f"  Positions: {status['positions']['total_positions']}")
    print(f"  Total Exposure: ${status['positions']['total_exposure']:.2f}")
    print(f"  Execution Quality: {status['execution_quality']['status']}")


def demo_monitoring():
    """Demonstrate execution monitoring"""
    print("\n" + "=" * 70)
    print("  DEMO 5: Execution Monitoring")
    print("=" * 70 + "\n")
    
    executor = ExecutorCore(dryrun=True, bankroll=1000.0)
    
    # Execute some orders
    actions = [
        PlannedAction(
            market_id=f"monitor_test_{i}",
            market_name=f"Monitor Test {i}",
            side="YES" if i % 2 == 0 else "NO",
            amount=40.0,
            confidence=0.8,
            reasoning=f"Test {i}"
        )
        for i in range(5)
    ]
    
    print(f"Executing {len(actions)} test orders...")
    summary = executor.execute_signals(actions)
    print(f"Executed: {summary['executed_count']}")
    
    # Get status with monitoring info
    status = executor.get_status()
    
    print(f"\nExecution Quality:")
    quality = status['execution_quality']
    metrics = quality['metrics']
    print(f"  Total Orders: {metrics['total_orders']}")
    print(f"  Successful: {metrics['successful_fills']}")
    print(f"  Failed: {metrics['failed_orders']}")
    if metrics['total_orders'] > 0:
        success_rate = metrics['successful_fills'] / metrics['total_orders']
        print(f"  Success Rate: {success_rate:.1%}")
    print(f"  Avg Slippage: {metrics['total_slippage_bps']:.2f} bps")
    print(f"  Avg Execution Time: {metrics['avg_execution_time_ms']:.0f} ms")
    
    if quality['alerts']:
        print(f"\nAlerts: {len(quality['alerts'])}")
        for alert in quality['alerts']:
            print(f"  - [{alert['severity']}] {alert['type']}: {alert['message']}")
    else:
        print(f"\nAlerts: None (all systems nominal)")


def main():
    """Run all demos"""
    print("\n" + "=" * 80)
    print("  LIVE EXECUTION PIPELINE DEMONSTRATION")
    print("  " + "=" * 76)
    print("  All executions in DRYRUN mode - no real trades placed")
    print("=" * 80)
    
    demos = [
        demo_basic_execution,
        demo_safety_checks,
        demo_kill_switch,
        demo_with_decider,
        demo_monitoring,
    ]
    
    for demo in demos:
        try:
            demo()
        except Exception as e:
            print(f"\n✗ Demo failed: {e}")
            import traceback
            traceback.print_exc()
    
    print("\n" + "=" * 80)
    print("  DEMONSTRATION COMPLETE")
    print("=" * 80 + "\n")


if __name__ == '__main__':
    main()
