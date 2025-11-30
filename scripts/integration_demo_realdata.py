#!/usr/bin/env python3
"""
Integration Demo: Real Alpha Signals Pipeline
=============================================

This script demonstrates the full pipeline using REAL market data:
Sync → Alpha → Decider (Brain) → Executor (Body + Reflexes)

It shows:
1. Loading real alpha signals from state/polymarket-model.json
2. Decider converting signals to planned actions with Kelly sizing
3. Executor validating and executing with safety checks
4. Clear separation between brain, body, and reflexes

This is the production-ready version that uses actual market data
instead of mocks.
"""

# UNIFIED AI - All systems serve Yair Siegel
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))
try:
    from ai.unified_ai import MASTER, get_master
except ImportError:
    MASTER = "Yair Siegel"


import sys
from pathlib import Path

# Add parent directory to path to import modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from decider.ho_decider import Decider, PlannedAction
from executor.ho_executor_plan import Executor, ExecutionResult


def print_section(title: str):
    """Print a formatted section header"""
    print(f"\n{'=' * 70}")
    print(f"  {title}")
    print(f"{'=' * 70}\n")


def print_model_info(model_path: Path):
    """Print information about the loaded model"""
    import json
    
    with open(model_path, 'r') as f:
        model = json.load(f)
    
    print_section("1. ALPHA MODEL INFO")
    print(f"Generated at: {model['generated_at']}")
    print(f"Source timestamp: {model['source_timestamp']}")
    print(f"Markets analyzed: {model['total_markets_analyzed']}")
    print(f"Markets selected: {model['markets_selected']}")
    print()


def print_alpha_signals(signals):
    """Print alpha signals in a readable format"""
    print_section("2. TOP ALPHA SIGNALS (from Real Data)")
    for i, signal in enumerate(signals[:5], 1):  # Show top 5
        print(f"Signal {i}:")
        print(f"  Market: {signal['market_name'][:60]}...")
        print(f"  Market ID: {signal['market_id']}")
        print(f"  Edge: {signal['edge']:.1%}")
        print(f"  Model Confidence: {signal.get('model_confidence', 0):.1%}")
        print(f"  Current Price: {signal['current_odds']:.2f}")
        print(f"  Fair Price: {signal.get('fair_price', 0):.2f}")
        print(f"  Side: {signal['side']}")
        print()


def print_planned_actions(actions):
    """Print planned actions in a readable format"""
    print_section("3. PLANNED ACTIONS (Brain/Decider Output)")
    for i, action in enumerate(actions[:5], 1):  # Show top 5
        print(f"Action {i}:")
        print(f"  Market: {action.market_name[:60]}...")
        print(f"  Market ID: {action.market_id}")
        print(f"  Side: {action.side}")
        print(f"  Amount: ${action.amount:.2f}")
        print(f"  Confidence: {action.confidence:.1%}")
        print(f"  Reasoning: {action.reasoning}")
        print()


def print_execution_results(results):
    """Print execution results in a readable format"""
    print_section("4. EXECUTION RESULTS (Body + Reflexes)")
    for i, result in enumerate(results[:10], 1):  # Show top 10
        status_icon = "✓" if result.success else "✗"
        print(f"{status_icon} Result {i}:")
        print(f"  Market: {result.market_name[:60]}...")
        print(f"  Success: {result.success}")
        print(f"  Message: {result.message}")
        if result.success:
            print(f"  Executed Amount: ${result.executed_amount:.2f}")
        print()


def print_summary(summary):
    """Print execution summary"""
    print_section("5. EXECUTION SUMMARY")
    print(f"Mode: {summary['mode']}")
    print(f"Total Actions: {summary['total_actions']}")
    print(f"Successful: {summary['successful']}")
    print(f"Rejected: {summary['rejected']}")
    print(f"Total Amount Executed: ${summary['total_amount_executed']:.2f}")
    print()


def main():
    """Run the integration demo with real data"""
    print("\n" + "=" * 70)
    print("  HANDS-OFF ENGINE: REAL DATA INTEGRATION DEMO")
    print("  Pipeline: Sync → Alpha → Brain → Body → Reflexes")
    print("=" * 70)
    
    # Set up paths
    repo_root = Path(__file__).parent.parent
    model_path = repo_root / 'state' / 'polymarket-model.json'
    
    # Check if model file exists
    if not model_path.exists():
        print(f"\n✗ Error: Model file not found at {model_path}")
        print(f"\nPlease run the sync script first:")
        print(f"  python3 alpha/sync_polymarket_model.py")
        return 1
    
    try:
        # Step 1: Load model info
        print_model_info(model_path)
        
        # Step 2: Load alpha signals from real data
        decider = Decider(bankroll=1000.0)  # $1000 bankroll
        alpha_signals = decider.load_model_signals(model_path)
        print_alpha_signals(alpha_signals)
        
        # Step 3: Decider converts signals to planned actions (Brain)
        planned_actions = decider.plan_actions(alpha_signals)
        print_planned_actions(planned_actions)
        
        # Step 4: Executor validates and executes actions (Body + Reflexes)
        executor = Executor(dryrun=True)  # Always DRYRUN in demo
        execution_results = executor.execute_actions(planned_actions)
        print_execution_results(execution_results)
        
        # Step 5: Generate and print summary
        summary = executor.get_execution_summary(execution_results)
        print_summary(summary)
        
        # Final notes
        print_section("NOTES")
        print("✓ All trades executed in DRYRUN mode (safe)")
        print("✓ Using REAL market data from polymarket-model.json")
        print("✓ Safety reflexes active (position size, confidence checks)")
        print("✓ Brain-Body-Reflex separation demonstrated")
        print("✓ Kelly-style position sizing based on edge and confidence")
        print("\nData Pipeline:")
        print("  1. termux-hands-off/out/polymarket-compact.json (raw data)")
        print("  2. alpha/sync_polymarket_model.py (transform)")
        print("  3. state/polymarket-model.json (alpha signals)")
        print("  4. decider/ho_decider.py (planned actions)")
        print("  5. executor/ho_executor_plan.py (execution)")
        print("\nFor production use:")
        print("  - Set executor dryrun=False after safety review")
        print("  - Implement actual trading API calls in executor")
        print("  - Add cron job to run sync_polymarket_model.py regularly")
        print("  - Add monitoring and alerting for failed runs")
        print()
        
        return 0
        
    except Exception as e:
        print(f"\n✗ Error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
