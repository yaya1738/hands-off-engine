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

# UNIFIED AI - All systems serve Yair Siegel
from ai.unified_ai import announce_agent, get_master, log_action, MASTER

from alpha.sync_polymarket_model import sync_polymarket_model
from decider.ho_decider import Decider
from executor.ho_executor_plan import Executor

# Optional intelligent alpha engine
try:
    from alpha.intelligent_alpha_engine import IntelligentAlphaEngine
    HAS_INTELLIGENT_ALPHA = True
except ImportError:
    HAS_INTELLIGENT_ALPHA = False


def run_intelligent_alpha(output_path: Path, bankroll: float, verbose: bool = True) -> dict:
    """
    Run intelligent alpha engine and save in canonical format.

    Returns dict compatible with sync_polymarket_model output.
    """
    from datetime import timezone

    engine = IntelligentAlphaEngine(
        bankroll=bankroll,
        use_chatgpt=False,  # Only Claude for now
        use_claude=True,
        min_edge=0.03,  # 3% minimum edge
        min_confidence="low"  # Accept all confidence levels
    )

    # Generate signals - limit to 5 for faster runtime (each takes ~20s API call)
    signals = engine.generate_signals(limit=5)

    if verbose:
        print(f"  Generated {len(signals)} intelligent signals")

    # Convert confidence string to float
    conf_map = {"low": 0.3, "medium": 0.6, "high": 0.9}

    # Convert to canonical format expected by Decider
    markets = []
    for sig in signals:
        markets.append({
            "market_id": sig.market_id,
            "token_id": sig.token_id,  # Critical for actual trading!
            "question": sig.question,
            "query_category": "intelligent",
            "side": sig.side,
            "model_edge": round(sig.edge, 4),
            "model_confidence": conf_map.get(sig.confidence, 0.5),
            "fair_price": round(sig.fair_probability, 4),
            "market_price": round(sig.market_price, 4),
            "best_bid": round(sig.market_price, 4),
            "liquidity": sig.liquidity,
            # Extra fields from intelligent engine
            "reasoning": sig.reasoning,
            "reasoning_quality": sig.reasoning_quality,
            "order_type": sig.order_type,
            "recommended_size_usd": sig.recommended_size_usd
        })

    # Build output
    output = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "source_timestamp": datetime.now(timezone.utc).isoformat(),
        "total_markets_analyzed": len(signals),
        "markets_selected": len(signals),
        "engine": "intelligent_alpha_v1",
        "markets": markets
    }

    # Save to file
    with open(output_path, 'w') as f:
        json.dump(output, f, indent=2)

    return output


def print_header(text: str):
    """Print a formatted header"""
    print(f"\n{'=' * 70}")
    print(f"  {text}")
    print(f"{'=' * 70}\n")


def run_pipeline(
    bankroll: float = 5000.0,
    dryrun: bool = True,
    verbose: bool = True,
    intelligent: bool = False
) -> dict:
    """
    Run the full pipeline.

    Args:
        bankroll: Total bankroll for position sizing
        dryrun: If True, no real trades executed (default: True)
        verbose: If True, print detailed progress
        intelligent: If True, use LLM-based intelligent alpha engine

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
        # Step 0: Early balance check to avoid wasting LLM API calls
        from executor.trading_safeguards import TradingSafeguards
        MIN_TRADING_BALANCE = 1.0  # Enable micro-trading with any balance

        try:
            safeguards = TradingSafeguards()
            ok, msg = safeguards.check_wallet_balance(MIN_TRADING_BALANCE)
            # Parse balance from message like "Wallet: $8.99"
            import re
            match = re.search(r'\$(\d+\.?\d*)', msg)
            if match:
                balance = float(match.group(1))
                if balance < MIN_TRADING_BALANCE:
                    if verbose:
                        print(f"⏸️  SKIPPING PIPELINE: Balance ${balance:.2f} < ${MIN_TRADING_BALANCE} minimum")
                        print(f"   No point generating signals we can't trade.")
                        print(f"   Position monitor still running for exit opportunities.")
                    results['success'] = True
                    results['skipped'] = f"Low balance: ${balance:.2f}"
                    return results
        except Exception as e:
            # If balance check fails, continue anyway
            if verbose:
                print(f"⚠️  Balance check failed ({e}), continuing...")

        # Step 1: Sync Polymarket Model (Alpha)
        if verbose:
            engine_type = "Intelligent (LLM)" if intelligent else "Simple (hash)"
            print_header(f"STEP 1: Generate Alpha Signals [{engine_type}]")

        output_path = repo_root / 'state' / 'polymarket-model.json'

        if intelligent and HAS_INTELLIGENT_ALPHA:
            # Use LLM-based intelligent alpha engine
            if verbose:
                print("  Using intelligent alpha engine (Claude)...")
            model = run_intelligent_alpha(output_path, bankroll, verbose)
        else:
            # Use simple hash-based model (backward compatible)
            input_path = repo_root / 'termux-hands-off' / 'out' / 'polymarket-compact.json'

            # Auto-fetch if data is missing or stale (>2 hours old)
            should_fetch = False
            if not input_path.exists():
                should_fetch = True
                if verbose:
                    print("⚠ Input data missing, auto-fetching...")
            else:
                # Check staleness
                import os
                file_age_hours = (datetime.now().timestamp() - os.path.getmtime(input_path)) / 3600
                if file_age_hours > 2:
                    should_fetch = True
                    if verbose:
                        print(f"⚠ Input data stale ({file_age_hours:.1f}h old), auto-fetching...")

            if should_fetch:
                try:
                    # Import and run fetch
                    sys.path.insert(0, str(repo_root / 'scripts'))
                    from fetch_fresh_markets import fetch_active_markets, save_compact_format
                    markets = fetch_active_markets(limit=50)
                    save_compact_format(markets, str(input_path))
                    if verbose:
                        print(f"✓ Fetched {markets['count']} fresh markets")
                except Exception as fetch_err:
                    if not input_path.exists():
                        raise FileNotFoundError(
                            f"Input data not found and fetch failed: {fetch_err}\n"
                            "Please ensure Polymarket API is accessible."
                        )
                    else:
                        if verbose:
                            print(f"⚠ Fetch failed ({fetch_err}), using stale data")

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

        # Step 3.5: Write execution plan for notifications (always write if we have planned actions)
        # This ensures shadow mode tracking and healthcheck see fresh plans
        if planned_actions:
            execution_plan_path = repo_root / 'executor' / 'execution_plan.json'

            # Track execution status for each action
            orders = []
            for action, result in zip(planned_actions, execution_results):
                orders.append({
                    'market_id': action.market_id,
                    'token_id': getattr(action, 'token_id', None),  # Critical for CLOB trading
                    'question': action.market_name,
                    'side': action.side.lower(),
                    'size_usd': action.amount,
                    'confidence': action.confidence,
                    'edge': None,  # Extract from alpha signals if needed
                    'category': 'unknown',  # Extract from market_id if needed
                    'reason': action.reasoning,
                    'status': 'executed' if result.success else 'planned',
                    'execution_error': result.message if not result.success else None
                })

            execution_plan = {
                'timestamp': datetime.now().isoformat(),
                'dryrun': dryrun,
                'total_orders': len(planned_actions),
                'total_size_usd': sum(a.amount for a in planned_actions),
                'successful_orders': summary['successful'],
                'orders': orders
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


def get_actual_bankroll() -> float:
    """
    Get actual available bankroll from financial state.
    
    Returns:
        float: Actual balance, or 0 if unable to determine
    """
    try:
        repo_root = Path(__file__).parent.parent
        financial_state = repo_root / 'state' / 'financial_state.json'
        
        if financial_state.exists():
            with open(financial_state) as f:
                state = json.load(f)
            balance = state.get('balance', 0)
            print(f"  Detected actual balance: ${balance:.2f}")
            return float(balance)
    except (FileNotFoundError, json.JSONDecodeError, ValueError) as e:
        print(f"  Warning: Could not read actual balance ({type(e).__name__}: {e})")
    return 0.0


def main():
    """Main entry point"""
    announce_agent("trading-pipeline")  # UNIFIED AI
    import argparse
    
    # Default minimum bankroll for micro-trading when actual balance unavailable
    MIN_DEFAULT_BANKROLL = 10.0
    
    # Get actual balance for intelligent default
    actual_balance = get_actual_bankroll()
    default_bankroll = actual_balance if actual_balance > 0 else MIN_DEFAULT_BANKROLL
    
    parser = argparse.ArgumentParser(
        description='Run the full Hands-Off Engine pipeline'
    )
    parser.add_argument(
        '--bankroll',
        type=float,
        default=default_bankroll,
        help=f'Total bankroll for position sizing (default: {"actual balance" if actual_balance > 0 else f"${MIN_DEFAULT_BANKROLL:.2f}"} = ${default_bankroll:.2f})'
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
    parser.add_argument(
        '--intelligent',
        action='store_true',
        help='Use LLM-based intelligent alpha engine instead of simple hash model'
    )
    
    args = parser.parse_args()

    # Safety check for live mode - only prompt if running interactively
    if args.live:
        # Check if running in autonomous mode (cron, systemd, etc.)
        import os
        is_autonomous = (
            not sys.stdin.isatty() or  # No terminal attached
            os.getenv("HANDS_OFF_AUTONOMOUS", "0") == "1" or  # Explicit flag
            os.getenv("CRON_JOB", "") != ""  # Running from cron
        )

        if is_autonomous:
            # Autonomous mode - validate state file instead of prompting
            state_file = Path(__file__).parent.parent / 'state' / 'trading_mode.json'
            if state_file.exists():
                import json
                with open(state_file) as f:
                    trading_mode = json.load(f)
                if not trading_mode.get('live_trading_enabled', False):
                    print("✗ Live trading disabled in state file. Aborting.")
                    return 1
                print(f"✓ Autonomous live mode confirmed via state file (reason: {trading_mode.get('reason', 'unknown')})")
            else:
                print("✗ No trading_mode.json found. Cannot run live autonomously.")
                return 1
        else:
            # Interactive mode - prompt for confirmation
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
        alpha_type = "Intelligent (LLM)" if args.intelligent else "Simple"
        print(f"\n🚀 Starting Hands-Off Engine Pipeline")
        print(f"   Mode: {mode}")
        print(f"   Alpha: {alpha_type}")
        print(f"   Bankroll: ${args.bankroll:.2f}")

    results = run_pipeline(
        bankroll=args.bankroll,
        dryrun=dryrun,
        verbose=verbose,
        intelligent=args.intelligent
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
