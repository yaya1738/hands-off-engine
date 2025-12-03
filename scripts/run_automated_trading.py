#!/usr/bin/env python3
"""
Run Automated Trading: Full Pipeline Execution
===============================================

This is the main entry point for the fully automated trading system.

It wires together:
1. Alpha Integrations Hub (collects all signals)
2. Signal Router (applies vetoes, modifiers, filters)
3. Decider (converts signals to planned actions)
4. Executor (executes trades with safety gates)

The system supports:
- Batch mode: Run once and exit
- Continuous mode: Run indefinitely with configurable intervals
- Live game mode: Fast polling during active games

Usage:
    python scripts/run_automated_trading.py --mode dryrun
    python scripts/run_automated_trading.py --mode dryrun --continuous
    python scripts/run_automated_trading.py --mode live_micro --continuous

Philosophy: "Hook everything together for fully optimal wealth extraction from Polymarket"
"""

import argparse
import json
import sys
import os
from datetime import datetime, timezone
from pathlib import Path
import time

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from alpha.signal_router import UnifiedSignalRouter, ExecutionMode, RoutingDecision
from decider.ho_decider import Decider, PlannedAction

try:
    from executor.ho_executor_plan import Executor
except ImportError:
    Executor = None

try:
    from audit import AuditLogger
except ImportError:
    get_audit_logger = None

try:
    from ai_nexus.history_log import log_kernel_history_event
except ImportError:
    log_kernel_history_event = None


class AutomatedTradingPipeline:
    """
    Full automated trading pipeline that integrates all components.

    This is the "hands-off" engine - minimal human intervention required.
    """

    def __init__(
        self,
        execution_mode: ExecutionMode = ExecutionMode.DRYRUN,
        bankroll: float = 1000.0
    ):
        self.execution_mode = execution_mode
        self.bankroll = bankroll
        self.state_dir = Path(__file__).parent.parent / 'state'

        # Initialize components
        print("=" * 60)
        print("AUTOMATED TRADING PIPELINE")
        print(f"Mode: {execution_mode.value}")
        print(f"Bankroll: ${bankroll:.2f}")
        print("=" * 60)

        # 1. Signal Router (with all alpha sources)
        print("\n[1/4] Initializing Signal Router...")
        self.router = UnifiedSignalRouter(
            execution_mode=execution_mode,
            state_dir=self.state_dir
        )

        # 2. Decider
        print("[2/4] Initializing Decider...")
        self.decider = Decider(bankroll=bankroll)

        # 3. Executor
        print("[3/4] Initializing Executor...")
        if Executor:
            self.executor = Executor()
        else:
            self.executor = None
            print("  -> Executor not available, using DRYRUN logic")

        # 4. Wire the execution callback
        print("[4/4] Wiring execution callback...")
        self.router.set_execution_callback(self._execute_decisions)

        # Audit logging
        if get_audit_logger:
            self.audit = AuditLogger()
        else:
            self.audit = None

        # Output paths
        self.execution_log_path = self.state_dir / 'execution_log.jsonl'
        self.daily_summary_path = self.state_dir / 'daily_summary.json'

        print("\n[Ready] All components initialized")
        print("=" * 60)

    def _execute_decisions(self, decisions: list):
        """
        Execute routing decisions through Decider -> Executor pipeline.

        This is the callback that the router calls when signals are ready.
        """
        if not decisions:
            return 0

        print(f"\n[Execute] Processing {len(decisions)} decisions...")

        # Convert router decisions to Decider alpha signals
        alpha_signals = []
        for d in decisions:
            signal = {
                'market_id': d.signal.market_id,
                'market_name': d.signal.market_name,
                'edge': d.final_edge,
                'current_odds': d.signal.market_price,
                'side': d.signal.side,
                'model_confidence': d.final_confidence,
                'fair_price': d.signal.fair_price
            }
            alpha_signals.append(signal)

        # Run through Decider
        planned_actions = self.decider.plan_actions(alpha_signals)
        print(f"[Execute] Decider produced {len(planned_actions)} planned actions")

        # Log and execute each action
        executed = 0
        for action in planned_actions:
            success = self._execute_action(action)
            if success:
                executed += 1

        # Log to Spark Plug kernels
        if log_kernel_history_event:
            try:
                log_kernel_history_event(
                    kernel_ids=["alpha_polymarket_core", "risk_model_v2"],
                    kind="execution_batch",
                    source="automated_trading",
                    summary=f"Executed {executed}/{len(planned_actions)} actions, mode={self.execution_mode.value}",
                    details={
                        "mode": self.execution_mode.value,
                        "decisions_in": len(decisions),
                        "planned_actions": len(planned_actions),
                        "executed": executed,
                        "markets": [a.market_id for a in planned_actions]
                    },
                    importance=8,
                    tags=["execution", "automated"]
                )
            except Exception:
                pass

        return executed

    def _execute_action(self, action: PlannedAction) -> bool:
        """
        Execute a single planned action.

        Returns True if successfully executed (or logged in DRYRUN).
        """
        timestamp = datetime.now(timezone.utc).isoformat()

        # Build execution record
        record = {
            'timestamp': timestamp,
            'mode': self.execution_mode.value,
            'market_id': action.market_id,
            'market_name': action.market_name,
            'side': action.side,
            'amount': action.amount,
            'confidence': action.confidence,
            'reasoning': action.reasoning,
            'status': 'pending'
        }

        try:
            if self.execution_mode == ExecutionMode.DRYRUN:
                # Just log
                print(f"  [DRYRUN] {action.side} ${action.amount:.2f} on {action.market_id}")
                record['status'] = 'dryrun_logged'

            elif self.execution_mode == ExecutionMode.PAPER:
                # Simulate execution
                print(f"  [PAPER] {action.side} ${action.amount:.2f} on {action.market_id}")
                record['status'] = 'paper_simulated'

            elif self.execution_mode in [ExecutionMode.LIVE_MICRO, ExecutionMode.LIVE_SMALL, ExecutionMode.LIVE_NORMAL]:
                # Real execution
                if self.executor:
                    # TODO: Call actual Polymarket API via executor
                    print(f"  [LIVE] {action.side} ${action.amount:.2f} on {action.market_id}")
                    record['status'] = 'live_pending'
                    # self.executor.execute(action)
                    # record['status'] = 'live_executed'
                else:
                    print(f"  [LIVE-NOOP] No executor available")
                    record['status'] = 'no_executor'

            # Append to execution log
            with open(self.execution_log_path, 'a') as f:
                f.write(json.dumps(record) + '\n')

            # Audit log
            if self.audit:
                self.audit.log_action(
                    action_type="trade_execution",
                    action_details={
                        'market_id': action.market_id,
                        'side': action.side,
                        'amount': action.amount,
                        'mode': self.execution_mode.value,
                        'status': record['status']
                    }
                )

            return True

        except Exception as e:
            print(f"  [ERROR] Failed to execute {action.market_id}: {e}")
            record['status'] = 'error'
            record['error'] = str(e)

            with open(self.execution_log_path, 'a') as f:
                f.write(json.dumps(record) + '\n')

            return False

    def run_once(
        self,
        min_edge: float = 0.03,
        min_confidence: float = 0.5,
        max_signals: int = 20
    ):
        """
        Run a single collection and execution cycle.
        """
        print(f"\n{'='*60}")
        print(f"[Pipeline] Running single cycle")
        print(f"[Pipeline] Min edge: {min_edge:.1%}, Min confidence: {min_confidence:.1%}")
        print(f"{'='*60}")

        result = self.router.run_cycle(
            min_edge=min_edge,
            min_confidence=min_confidence,
            max_signals=max_signals,
            execute=True
        )

        # Print summary
        print(f"\n[Pipeline] Cycle Summary:")
        print(f"  - Signals collected: {result.total_signals}")
        print(f"  - Passed filters: {result.passed_filters}")
        print(f"  - Vetoed: {result.vetoed}")
        print(f"  - Executed: {result.routed_to_executor}")

        return result

    def run_continuous(
        self,
        interval_seconds: int = 60,
        live_game_interval: int = 30,
        min_edge: float = 0.03,
        min_confidence: float = 0.5,
        max_signals: int = 20
    ):
        """
        Run continuous monitoring and execution loop.

        This is the "hands-off" mode - runs until stopped.
        """
        print(f"\n{'='*60}")
        print(f"[Pipeline] Starting CONTINUOUS mode")
        print(f"[Pipeline] Regular interval: {interval_seconds}s")
        print(f"[Pipeline] Live game interval: {live_game_interval}s")
        print(f"[Pipeline] Press Ctrl+C to stop")
        print(f"{'='*60}")

        cycle_count = 0
        total_executed = 0

        try:
            while True:
                cycle_count += 1
                print(f"\n[Cycle {cycle_count}] Starting at {datetime.now().strftime('%H:%M:%S')}")

                result = self.router.run_cycle(
                    min_edge=min_edge,
                    min_confidence=min_confidence,
                    max_signals=max_signals,
                    execute=True
                )

                total_executed += result.routed_to_executor

                # Determine sleep interval
                if result.immediate_signals > 0:
                    # Live game detected - fast polling
                    print(f"[Pipeline] Live action detected! Fast polling enabled.")
                    sleep_time = live_game_interval
                else:
                    sleep_time = interval_seconds

                print(f"[Cycle {cycle_count}] Complete. Total executed: {total_executed}. Next in {sleep_time}s...")
                time.sleep(sleep_time)

        except KeyboardInterrupt:
            print(f"\n\n[Pipeline] Stopping after {cycle_count} cycles")
            print(f"[Pipeline] Total executed: {total_executed}")

    def generate_daily_summary(self):
        """
        Generate a daily summary of all executions.
        """
        today = datetime.now().strftime('%Y-%m-%d')

        # Read execution log
        executions = []
        if self.execution_log_path.exists():
            with open(self.execution_log_path, 'r') as f:
                for line in f:
                    if line.strip():
                        record = json.loads(line)
                        if record['timestamp'].startswith(today):
                            executions.append(record)

        # Calculate summary
        summary = {
            'date': today,
            'total_executions': len(executions),
            'by_mode': {},
            'by_status': {},
            'total_amount': 0,
            'markets_traded': set()
        }

        for ex in executions:
            mode = ex.get('mode', 'unknown')
            status = ex.get('status', 'unknown')
            amount = ex.get('amount', 0)
            market = ex.get('market_id', 'unknown')

            summary['by_mode'][mode] = summary['by_mode'].get(mode, 0) + 1
            summary['by_status'][status] = summary['by_status'].get(status, 0) + 1
            summary['total_amount'] += amount
            summary['markets_traded'].add(market)

        summary['markets_traded'] = list(summary['markets_traded'])
        summary['unique_markets'] = len(summary['markets_traded'])

        # Save summary
        with open(self.daily_summary_path, 'w') as f:
            json.dump(summary, f, indent=2)

        print(f"\n[Summary] Daily summary for {today}:")
        print(f"  - Total executions: {summary['total_executions']}")
        print(f"  - Total amount: ${summary['total_amount']:.2f}")
        print(f"  - Unique markets: {summary['unique_markets']}")

        return summary


def main():
    """Main entry point with CLI argument parsing"""
    parser = argparse.ArgumentParser(
        description='Run the automated trading pipeline',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Single DRYRUN cycle
  python run_automated_trading.py

  # Continuous DRYRUN mode
  python run_automated_trading.py --continuous

  # Continuous LIVE_MICRO mode (real money, tiny stakes)
  python run_automated_trading.py --mode live_micro --continuous

  # Custom intervals
  python run_automated_trading.py --continuous --interval 120 --live-interval 15
        """
    )

    parser.add_argument(
        '--mode', '-m',
        choices=['dryrun', 'paper', 'live_micro', 'live_small', 'live_normal'],
        default='dryrun',
        help='Execution mode (default: dryrun)'
    )

    parser.add_argument(
        '--continuous', '-c',
        action='store_true',
        help='Run in continuous mode'
    )

    parser.add_argument(
        '--interval', '-i',
        type=int,
        default=60,
        help='Regular polling interval in seconds (default: 60)'
    )

    parser.add_argument(
        '--live-interval', '-l',
        type=int,
        default=30,
        help='Polling interval during live games in seconds (default: 30)'
    )

    parser.add_argument(
        '--min-edge', '-e',
        type=float,
        default=0.03,
        help='Minimum edge threshold (default: 0.03 = 3%%)'
    )

    parser.add_argument(
        '--min-confidence', '-conf',
        type=float,
        default=0.5,
        help='Minimum confidence threshold (default: 0.5 = 50%%)'
    )

    parser.add_argument(
        '--max-signals', '-n',
        type=int,
        default=20,
        help='Maximum signals per cycle (default: 20)'
    )

    parser.add_argument(
        '--bankroll', '-b',
        type=float,
        default=1000.0,
        help='Bankroll for position sizing (default: $1000)'
    )

    parser.add_argument(
        '--summary',
        action='store_true',
        help='Generate daily summary and exit'
    )

    args = parser.parse_args()

    # Map mode string to enum
    mode_map = {
        'dryrun': ExecutionMode.DRYRUN,
        'paper': ExecutionMode.PAPER,
        'live_micro': ExecutionMode.LIVE_MICRO,
        'live_small': ExecutionMode.LIVE_SMALL,
        'live_normal': ExecutionMode.LIVE_NORMAL
    }
    execution_mode = mode_map[args.mode]

    # Initialize pipeline
    pipeline = AutomatedTradingPipeline(
        execution_mode=execution_mode,
        bankroll=args.bankroll
    )

    # Handle summary mode
    if args.summary:
        pipeline.generate_daily_summary()
        return

    # Run in appropriate mode
    if args.continuous:
        pipeline.run_continuous(
            interval_seconds=args.interval,
            live_game_interval=args.live_interval,
            min_edge=args.min_edge,
            min_confidence=args.min_confidence,
            max_signals=args.max_signals
        )
    else:
        pipeline.run_once(
            min_edge=args.min_edge,
            min_confidence=args.min_confidence,
            max_signals=args.max_signals
        )


if __name__ == '__main__':
    main()
