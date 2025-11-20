#!/usr/bin/env python3
"""
Integration Demo: Hands-Off Engine Pipeline
============================================

This script demonstrates the full pipeline:
Alpha → Decider (Brain) → Executor (Body + Reflexes)

It shows:
1. Mock alpha signals with edge estimates
2. Decider converting signals to planned actions
3. Executor validating and executing with safety checks
4. Clear separation between brain, body, and reflexes
"""

import sys
from pathlib import Path

# Add parent directory to path to import modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from decider.ho_decider import Decider, PlannedAction
from executor.ho_executor_plan import Executor, ExecutionResult


def generate_mock_alpha_signals():
    """
    Generate mock alpha signals for demo purposes.
    In production, these would come from the alpha module.
    """
    return [
        {
            'market_id': 'pm_001',
            'market_name': 'Will team X win the championship?',
            'edge': 0.08,  # 8% edge
            'current_odds': 0.65,
            'side': 'YES'
        },
        {
            'market_id': 'pm_002',
            'market_name': 'Will event Y happen this month?',
            'edge': 0.12,  # 12% edge
            'current_odds': 0.45,
            'side': 'NO'
        },
        {
            'market_id': 'pm_003',
            'market_name': 'Will candidate Z win election?',
            'edge': 0.03,  # 3% edge (low)
            'current_odds': 0.55,
            'side': 'YES'
        }
    ]


def print_section(title: str):
    """Print a formatted section header"""
    print(f"\n{'=' * 70}")
    print(f"  {title}")
    print(f"{'=' * 70}\n")


def print_alpha_signals(signals):
    """Print alpha signals in a readable format"""
    print_section("1. ALPHA SIGNALS")
    for i, signal in enumerate(signals, 1):
        print(f"Signal {i}:")
        print(f"  Market: {signal['market_name']}")
        print(f"  Market ID: {signal['market_id']}")
        print(f"  Edge: {signal['edge']:.1%}")
        print(f"  Current Odds: {signal['current_odds']:.2f}")
        print(f"  Side: {signal['side']}")
        print()


def print_planned_actions(actions):
    """Print planned actions in a readable format"""
    print_section("2. PLANNED ACTIONS (Brain/Decider Output)")
    for i, action in enumerate(actions, 1):
        print(f"Action {i}:")
        print(f"  Market: {action.market_name}")
        print(f"  Market ID: {action.market_id}")
        print(f"  Side: {action.side}")
        print(f"  Amount: ${action.amount:.2f}")
        print(f"  Confidence: {action.confidence:.1%}")
        print(f"  Reasoning: {action.reasoning}")
        print()


def print_execution_results(results):
    """Print execution results in a readable format"""
    print_section("3. EXECUTION RESULTS (Body + Reflexes)")
    for i, result in enumerate(results, 1):
        status_icon = "✓" if result.success else "✗"
        print(f"{status_icon} Result {i}:")
        print(f"  Market: {result.market_name}")
        print(f"  Market ID: {result.market_id}")
        print(f"  Success: {result.success}")
        print(f"  Message: {result.message}")
        print(f"  Executed Amount: ${result.executed_amount:.2f}")
        print()


def print_summary(summary):
    """Print execution summary"""
    print_section("4. EXECUTION SUMMARY")
    print(f"Mode: {summary['mode']}")
    print(f"Total Actions: {summary['total_actions']}")
    print(f"Successful: {summary['successful']}")
    print(f"Rejected: {summary['rejected']}")
    print(f"Total Amount Executed: ${summary['total_amount_executed']:.2f}")
    print()


def main():
    """Run the integration demo"""
    print("\n" + "=" * 70)
    print("  HANDS-OFF ENGINE INTEGRATION DEMO")
    print("  Demonstrating: Alpha → Brain → Body → Reflexes")
    print("=" * 70)

    # Step 1: Generate alpha signals
    alpha_signals = generate_mock_alpha_signals()
    print_alpha_signals(alpha_signals)

    # Step 2: Decider converts signals to planned actions (Brain)
    decider = Decider()
    planned_actions = decider.plan_actions(alpha_signals)
    print_planned_actions(planned_actions)

    # Step 3: Executor validates and executes actions (Body + Reflexes)
    executor = Executor(dryrun=True)  # Always DRYRUN in demo
    execution_results = executor.execute_actions(planned_actions)
    print_execution_results(execution_results)

    # Step 4: Generate and print summary
    summary = executor.get_execution_summary(execution_results)
    print_summary(summary)

    # Final notes
    print_section("NOTES")
    print("✓ All trades executed in DRYRUN mode (safe)")
    print("✓ Safety reflexes active (position size, confidence checks)")
    print("✓ Brain-Body-Reflex separation demonstrated")
    print("✓ Structured action flow: Alpha → Decider → Executor")
    print("\nFor production use:")
    print("  - Set executor dryrun=False after safety review")
    print("  - Implement real alpha signals from ho_alpha_polymarket.py")
    print("  - Add risk model for position sizing")
    print("  - Implement actual trading API calls in executor")
    print()


if __name__ == "__main__":
    main()
