#!/usr/bin/env python3
"""
ho_executor_plan.py - Generate execution plan from decisions (DRYRUN-safe)

Reads decider/decisions.json and creates executor/execution_plan.json with
orders ready for execution.
"""
import json
import sys
from pathlib import Path
from datetime import datetime, timezone
from typing import List, Dict, Any

DECIDER_DIR = Path(__file__).parent.parent / "decider"
INPUT_FILE = DECIDER_DIR / "decisions.json"
OUTPUT_FILE = Path(__file__).parent / "execution_plan.json"

DEFAULT_POSITION_SIZE = 25  # Default position size in USD (small for DRYRUN testing)


def load_decisions() -> Dict[str, Any]:
    """Load decisions from decider"""
    if not INPUT_FILE.exists():
        print(f"[executor] Decisions file not found: {INPUT_FILE}")
        return {'decisions': [], 'dryrun': True}

    try:
        return json.loads(INPUT_FILE.read_text())
    except Exception as e:
        print(f"[executor] Failed to load decisions: {e}")
        return {'decisions': [], 'dryrun': True}


def create_execution_plan(decisions_data: Dict[str, Any]) -> Dict[str, Any]:
    """Create execution plan from decisions"""
    decisions = decisions_data.get('decisions', [])
    dryrun = decisions_data.get('dryrun', True)

    orders = []

    for decision in decisions:
        if decision['action'] in ('buy_yes', 'buy_no'):
            order = {
                'candidate_id': decision['candidate_id'],
                'question': decision['question'],
                'side': decision['action'],
                'size_usd': DEFAULT_POSITION_SIZE,
                'score': decision['score'],
                'edge': decision['edge'],
                'category': decision['category'],
                'reason': decision['reason'],
                'status': 'planned' if dryrun else 'pending'
            }
            orders.append(order)

    plan = {
        'timestamp': datetime.now(timezone.utc).isoformat(),
        'dryrun': dryrun,
        'total_orders': len(orders),
        'total_size_usd': len(orders) * DEFAULT_POSITION_SIZE,
        'orders': orders
    }

    return plan


def main():
    # Default to DRYRUN unless explicitly disabled
    dryrun = '--live' not in sys.argv

    print(f"[executor] Running in {'DRYRUN' if dryrun else 'LIVE'} mode")

    decisions_data = load_decisions()
    if not decisions_data.get('decisions'):
        print("[executor] No decisions to execute")
        return

    print(f"[executor] Creating execution plan...")
    plan = create_execution_plan(decisions_data)

    print(f"[executor] Plan: {plan['total_orders']} orders, ${plan['total_size_usd']} total")

    # Write output
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_FILE.write_text(json.dumps(plan, indent=2))

    print(f"[executor] Wrote {OUTPUT_FILE}")

    # Print summary
    if plan['orders']:
        print(f"\n[executor] Execution Plan Summary:")
        for i, order in enumerate(plan['orders'][:10], 1):
            side = order['side']
            size = order['size_usd']
            score = order['score']
            question = order['question'][:60]
            print(f"  {i}. {side:10} ${size:3} | score={score:.4f} | {question}")

        if len(plan['orders']) > 10:
            print(f"  ... and {len(plan['orders']) - 10} more orders")


if __name__ == "__main__":
    main()
