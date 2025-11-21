#!/usr/bin/env python3
"""
Hands-Off Engine: Full Pipeline Runner
======================================

This script runs the complete pipeline end-to-end:
1. Sync Polymarket model (Alpha signals)
2. Load signals and plan actions (Decider/Brain)
3. Validate and execute actions (Executor/Body)

Designed to be run via cron or manually for testing.
"""

import json
import sys
from datetime import datetime
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from alpha.sync_polymarket_model import sync_polymarket_model
from decider.ho_decider import Decider
from executor.ho_executor_plan import Executor


def print_header(text: str):
    """Print a formatted header"""
    print(f"\n{'=' * 70}")
    print(f"  {text}")
    print(f"{'=' * 70}\n")


def run_pipeline(
    bankroll: float = 1000.0,
    dryrun: bool = True,
    verbose: bool = True
) -> dict:
    """
    Run the full pipeline.
    
    Args:
        bankroll: Total bankroll for position sizing
        dryrun: If True, no real trades executed (default: True)
        verbose: If True, print detailed progress
    
    Returns:
        Dict with pipeline results and statistics
    """
    repo_root = Path(__file__).parent.parent
    
    start_time = datetime.now()
    results = {
        'start_time': start_time.isoformat(),
        'success': False,
        'error': None,
        'steps': {}
    }
    
    try:
        # Step 1: Sync Polymarket Model (Alpha)
        if verbose:
            print_header("STEP 1: Sync Alpha Signals")
        
        input_path = repo_root / 'termux-hands-off' / 'out' / 'polymarket-compact.json'
        output_path = repo_root / 'state' / 'polymarket-model.json'
        
        if not input_path.exists():
            raise FileNotFoundError(
                f"Input data not found: {input_path}\n"
                "Please ensure polymarket-compact.json exists."
            )
        
        model = sync_polymarket_model(input_path, output_path)
        
        results['steps']['sync'] = {
            'success': True,
            'markets_analyzed': model['total_markets_analyzed'],
            'markets_selected': model['markets_selected'],
            'generated_at': model['generated_at']
        }
        
        if verbose:
            print(f"✓ Synced alpha signals")
            print(f"  Markets analyzed: {model['total_markets_analyzed']}")
            print(f"  Markets selected: {model['markets_selected']}")
        
        # Step 2: Plan Actions (Decider/Brain)
        if verbose:
            print_header("STEP 2: Plan Actions (Decider)")
        
        decider = Decider(bankroll=bankroll)
        alpha_signals = decider.load_model_signals(output_path)
        planned_actions = decider.plan_actions(alpha_signals)
        
        results['steps']['decide'] = {
            'success': True,
            'signals_loaded': len(alpha_signals),
            'actions_planned': len(planned_actions)
        }
        
        if verbose:
            print(f"✓ Planned {len(planned_actions)} actions")
            print(f"  Total signals: {len(alpha_signals)}")
            if planned_actions:
                top_action = planned_actions[0]
                print(f"  Top action: {top_action.side} on {top_action.market_name[:50]}...")
                print(f"  Amount: ${top_action.amount:.2f}, Confidence: {top_action.confidence:.1%}")
        
        # Step 3: Execute Actions (Executor/Body)
        if verbose:
            print_header("STEP 3: Execute Actions (Executor)")

        executor = Executor(dryrun=dryrun)
        execution_results = executor.execute_actions(planned_actions)
        summary = executor.get_execution_summary(execution_results)

        results['steps']['execute'] = {
            'success': True,
            'mode': summary['mode'],
            'total_actions': summary['total_actions'],
            'successful': summary['successful'],
            'rejected': summary['rejected'],
            'total_amount': summary['total_amount_executed']
        }

        if verbose:
            print(f"✓ Executed actions")
            print(f"  Mode: {summary['mode']}")
            print(f"  Successful: {summary['successful']}/{summary['total_actions']}")
            print(f"  Rejected: {summary['rejected']}")
            print(f"  Total amount: ${summary['total_amount_executed']:.2f}")

        # Step 3.5: Write execution plan for notifications
        successful_actions = [
            action for action, result in zip(planned_actions, execution_results)
            if result.success
        ]

        if successful_actions:
            execution_plan_path = repo_root / 'executor' / 'execution_plan.json'
            execution_plan = {
                'timestamp': datetime.now().isoformat(),
                'dryrun': dryrun,
                'total_orders': len(successful_actions),
                'total_size_usd': sum(a.amount for a in successful_actions),
                'orders': [{
                    'market_id': action.market_id,
                    'question': action.market_name,
                    'side': action.side.lower(),
                    'size_usd': action.amount,
                    'confidence': action.confidence,
                    'edge': None,  # Extract from alpha signals if needed
                    'category': 'unknown',  # Extract from market_id if needed
                    'reason': action.reasoning,
                    'status': 'planned'
                } for action in successful_actions]
            }

            with open(execution_plan_path, 'w') as f:
                json.dump(execution_plan, f, indent=2)

            if verbose:
                print(f"✓ Execution plan written: {execution_plan_path}")
        
        # Success!
        results['success'] = True
        end_time = datetime.now()
        results['end_time'] = end_time.isoformat()
        results['duration_seconds'] = (end_time - start_time).total_seconds()
        
        if verbose:
            print_header("PIPELINE COMPLETE")
            print(f"✓ All steps completed successfully")
            print(f"  Duration: {results['duration_seconds']:.2f}s")
            print(f"  Mode: {'DRYRUN (safe)' if dryrun else 'LIVE (real money!)'}")
        
        return results
        
    except Exception as e:
        results['success'] = False
        results['error'] = str(e)
        results['end_time'] = datetime.now().isoformat()
        
        if verbose:
            print_header("PIPELINE FAILED")
            print(f"✗ Error: {e}")
            import traceback
            traceback.print_exc()
        
        return results


def save_run_log(results: dict, log_dir: Path):
    """Save pipeline run log for monitoring/debugging"""
    log_dir.mkdir(parents=True, exist_ok=True)
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    log_file = log_dir / f"pipeline_run_{timestamp}.json"
    
    with open(log_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\n📝 Run log saved: {log_file}")


def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Run the full Hands-Off Engine pipeline'
    )
    parser.add_argument(
        '--bankroll',
        type=float,
        default=1000.0,
        help='Total bankroll for position sizing (default: 1000.0)'
    )
    parser.add_argument(
        '--live',
        action='store_true',
        help='Run in LIVE mode (real money!). Default is DRYRUN.'
    )
    parser.add_argument(
        '--quiet',
        action='store_true',
        help='Minimal output (only errors)'
    )
    parser.add_argument(
        '--save-log',
        action='store_true',
        help='Save run log to state/pipeline_logs/'
    )
    
    args = parser.parse_args()
    
    # Safety check for live mode
    if args.live:
        print("\n⚠️  WARNING: You are about to run in LIVE mode with REAL MONEY!")
        print("   This will execute actual trades on Polymarket.")
        print("\n   Are you sure? Type 'YES' to continue: ", end='')
        
        confirmation = input().strip()
        if confirmation != 'YES':
            print("✗ Aborted. Use --live only when you're ready for real trading.")
            return 1
    
    # Run pipeline
    verbose = not args.quiet
    dryrun = not args.live
    
    if verbose:
        mode = 'DRYRUN (safe)' if dryrun else 'LIVE (real money!)'
        print(f"\n🚀 Starting Hands-Off Engine Pipeline")
        print(f"   Mode: {mode}")
        print(f"   Bankroll: ${args.bankroll:.2f}")
    
    results = run_pipeline(
        bankroll=args.bankroll,
        dryrun=dryrun,
        verbose=verbose
    )
    
    # Save log if requested
    if args.save_log:
        repo_root = Path(__file__).parent.parent
        log_dir = repo_root / 'state' / 'pipeline_logs'
        save_run_log(results, log_dir)
    
    # Exit code based on success
    return 0 if results['success'] else 1


if __name__ == '__main__':
    sys.exit(main())
