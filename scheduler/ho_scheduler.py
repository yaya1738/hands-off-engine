#!/usr/bin/env python3
"""
Hands-Off Autonomous Scheduler - Batch 11

A fully autonomous Python scheduler that repeatedly executes the Batch 10 autoloop
at a user-specified interval and writes timestamped history snapshots.

Features:
- Runs ho_autoloop.run_all() at specified intervals
- Writes hands_off_summary.json and timestamped history snapshots
- Graceful error handling - never crashes, continues on errors
- SIGINT (CTRL-C) graceful shutdown
- CLI with interval parsing (Xs, Xm, Xh)
- Supports --once for single execution
- Optional verbose logging with --log

SAFETY: This scheduler is DRYRUN-only. No live trading or API calls.
"""

import os
import sys
import json
import time
import signal
import argparse
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

# Import the autoloop module
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ho_autoloop


# Global flag for graceful shutdown
shutdown_requested = False


def signal_handler(signum, frame):
    """Handle SIGINT (CTRL-C) for graceful shutdown."""
    global shutdown_requested
    print("\n[scheduler] Shutdown requested (SIGINT). Finishing current cycle...")
    shutdown_requested = True


def parse_interval(interval_str: str) -> int:
    """
    Parse interval string into seconds.

    Supported formats:
        - "Xs" - X seconds (e.g., "30s")
        - "Xm" - X minutes (e.g., "5m")
        - "Xh" - X hours (e.g., "2h")

    Args:
        interval_str: Interval string to parse

    Returns:
        Interval in seconds

    Raises:
        ValueError: If interval format is invalid
    """
    interval_str = interval_str.strip().lower()

    if not interval_str:
        raise ValueError("Interval cannot be empty")

    # Extract unit (last character) and value (everything before)
    unit = interval_str[-1]
    try:
        value = int(interval_str[:-1])
    except ValueError:
        raise ValueError(f"Invalid interval format: '{interval_str}'. Expected format: Xs, Xm, or Xh")

    if value <= 0:
        raise ValueError(f"Interval value must be positive, got: {value}")

    # Convert to seconds based on unit
    if unit == 's':
        return value
    elif unit == 'm':
        return value * 60
    elif unit == 'h':
        return value * 3600
    else:
        raise ValueError(
            f"Invalid interval unit: '{unit}'. Supported units: s (seconds), m (minutes), h (hours)"
        )


def write_summary(state_dir: str, result: dict, log: bool = False):
    """
    Write the hands_off_summary.json file.

    Args:
        state_dir: Path to state directory
        result: Result dictionary from run_all()
        log: Enable verbose logging
    """
    try:
        summary_path = os.path.join(state_dir, "hands_off_summary.json")

        with open(summary_path, 'w') as f:
            json.dump(result, f, indent=2)

        if log:
            print(f"[scheduler] Wrote summary: {summary_path}")

    except Exception as e:
        print(f"[scheduler] ERROR writing summary: {e}")


def write_history_snapshot(state_dir: str, result: dict, log: bool = False):
    """
    Write a timestamped history snapshot.

    Snapshot path format: state/history/<timestamp>.json
    Timestamp format: YYYYMMDD_HHMMSS_UTC

    Args:
        state_dir: Path to state directory
        result: Result dictionary from run_all()
        log: Enable verbose logging
    """
    try:
        history_dir = os.path.join(state_dir, "history")
        os.makedirs(history_dir, exist_ok=True)

        # Generate timestamp filename
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S_UTC")
        snapshot_path = os.path.join(history_dir, f"{timestamp}.json")

        with open(snapshot_path, 'w') as f:
            json.dump(result, f, indent=2)

        if log:
            print(f"[scheduler] Wrote history snapshot: {snapshot_path}")

    except Exception as e:
        print(f"[scheduler] ERROR writing history snapshot: {e}")


def run_cycle(state_dir: str, log: bool = False, cycle_num: Optional[int] = None):
    """
    Run a single scheduler cycle.

    Each cycle:
    1. Runs ho_autoloop.run_all()
    2. Writes hands_off_summary.json
    3. Writes timestamped history snapshot
    4. Logs cycle status

    Args:
        state_dir: Path to state directory
        log: Enable verbose logging
        cycle_num: Optional cycle number for logging

    Returns:
        Result dictionary from run_all()
    """
    cycle_label = f"cycle {cycle_num}" if cycle_num is not None else "cycle"

    if log:
        print(f"\n[scheduler] ===== Starting {cycle_label} =====")
        print(f"[scheduler] Timestamp: {datetime.now(timezone.utc).isoformat()}")

    result = None

    try:
        # Run the autoloop
        result = ho_autoloop.run_all(state_dir)

        # Write summary and history
        write_summary(state_dir, result, log=log)
        write_history_snapshot(state_dir, result, log=log)

        # Log status
        status = result.get("status", "unknown")
        exec_time = result.get("total_execution_time_sec", 0)
        summary = result.get("summary", "")

        if log:
            print(f"[scheduler] Status: {status}")
            print(f"[scheduler] Execution time: {exec_time:.3f}s")
            print(f"[scheduler] Summary: {summary}")
        else:
            # Concise output in non-verbose mode
            print(f"[scheduler] {cycle_label}: {status} ({exec_time:.3f}s) - {summary}")

    except Exception as e:
        # Critical error in cycle execution
        # Create error result and write snapshots anyway
        print(f"[scheduler] ERROR in {cycle_label}: {e}")

        result = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "status": "error",
            "error": str(e),
            "mode": "DRYRUN",
            "pipelines": {},
            "total_execution_time_sec": 0,
            "summary": f"Scheduler cycle failed: {str(e)}"
        }

        # Still try to write snapshots
        try:
            write_summary(state_dir, result, log=log)
            write_history_snapshot(state_dir, result, log=log)
        except Exception as write_error:
            print(f"[scheduler] CRITICAL: Failed to write error snapshots: {write_error}")

    if log:
        print(f"[scheduler] ===== Finished {cycle_label} =====\n")

    return result


def run_scheduler(
    state_dir: str,
    every: str = "60s",
    once: bool = False,
    log: bool = False,
    max_errors: Optional[int] = None
):
    """
    Run the autonomous scheduler.

    Args:
        state_dir: Path to state directory
        every: Interval between cycles (e.g., "60s", "5m", "1h")
        once: Run only one cycle and exit
        log: Enable verbose logging
        max_errors: Maximum consecutive errors before stopping (None = unlimited)

    Safety:
        This function runs indefinitely (unless once=True) and never crashes.
        All errors are caught and logged. The scheduler continues running
        even after pipeline failures.
    """
    global shutdown_requested

    # Parse interval
    try:
        interval_sec = parse_interval(every)
    except ValueError as e:
        print(f"[scheduler] ERROR: {e}")
        sys.exit(1)

    # Ensure state directory exists
    try:
        os.makedirs(state_dir, exist_ok=True)
    except Exception as e:
        print(f"[scheduler] ERROR: Cannot create state directory '{state_dir}': {e}")
        sys.exit(1)

    # Setup signal handler for graceful shutdown
    signal.signal(signal.SIGINT, signal_handler)

    # Print startup info
    mode_str = "single-shot" if once else f"continuous (every {every} = {interval_sec}s)"
    print(f"[scheduler] Starting Hands-Off Scheduler (Batch 11)")
    print(f"[scheduler] Mode: {mode_str}")
    print(f"[scheduler] State directory: {state_dir}")
    print(f"[scheduler] DRYRUN mode: ENABLED (no live trades)")
    print(f"[scheduler] Verbose logging: {log}")
    if max_errors:
        print(f"[scheduler] Max consecutive errors: {max_errors}")
    print(f"[scheduler] Press CTRL-C to stop gracefully\n")

    cycle_num = 0
    consecutive_errors = 0

    while not shutdown_requested:
        cycle_num += 1

        # Run cycle
        result = run_cycle(state_dir, log=log, cycle_num=cycle_num)

        # Track consecutive errors
        if result and result.get("status") == "error":
            consecutive_errors += 1
            if max_errors and consecutive_errors >= max_errors:
                print(f"[scheduler] Stopping: reached max consecutive errors ({max_errors})")
                break
        else:
            consecutive_errors = 0

        # Exit if running once
        if once:
            print("[scheduler] Single cycle completed (--once mode)")
            break

        # Wait for next cycle (unless shutdown requested)
        if not shutdown_requested and not once:
            if log:
                next_run = datetime.now(timezone.utc).timestamp() + interval_sec
                next_run_str = datetime.fromtimestamp(next_run, tz=timezone.utc).strftime("%H:%M:%S UTC")
                print(f"[scheduler] Waiting {interval_sec}s until next cycle (at {next_run_str})...")

            # Sleep in small chunks to allow responsive shutdown
            sleep_remaining = interval_sec
            while sleep_remaining > 0 and not shutdown_requested:
                sleep_chunk = min(1.0, sleep_remaining)  # Sleep 1s at a time
                time.sleep(sleep_chunk)
                sleep_remaining -= sleep_chunk

    # Shutdown
    print(f"\n[scheduler] Stopped after {cycle_num} cycle(s)")
    print("[scheduler] Shutdown complete")


def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Hands-Off Autonomous Scheduler - Batch 11 (DRYRUN only)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run every 60 seconds (default)
  python3 ho_scheduler.py state/

  # Run every 5 minutes
  python3 ho_scheduler.py --every 5m state/

  # Run every 2 hours
  python3 ho_scheduler.py --every 2h state/

  # Run once and exit
  python3 ho_scheduler.py --once state/

  # Verbose logging
  python3 ho_scheduler.py --log --every 30s state/

Interval format:
  Xs - X seconds (e.g., 30s)
  Xm - X minutes (e.g., 5m)
  Xh - X hours (e.g., 2h)

Safety:
  This scheduler runs in DRYRUN mode only.
  No live trades are executed.
  Press CTRL-C to stop gracefully.
        """
    )

    parser.add_argument(
        "state_dir",
        help="Path to state directory (e.g., state/)"
    )

    parser.add_argument(
        "--every",
        default="60s",
        help="Interval between cycles (default: 60s). Format: Xs, Xm, Xh"
    )

    parser.add_argument(
        "--once",
        action="store_true",
        help="Run a single cycle and exit"
    )

    parser.add_argument(
        "--log",
        action="store_true",
        help="Enable verbose logging"
    )

    parser.add_argument(
        "--max-errors",
        type=int,
        default=None,
        help="Maximum consecutive errors before stopping (default: unlimited)"
    )

    args = parser.parse_args()

    # Run scheduler
    run_scheduler(
        state_dir=args.state_dir,
        every=args.every,
        once=args.once,
        log=args.log,
        max_errors=args.max_errors
    )


if __name__ == "__main__":
    main()
