#!/usr/bin/env python3
"""
Hands-Off Engine - Batch 17: Continuous Autonomous AI Loop (DRYRUN-Only)

This module implements a continuous autonomous AI loop that orchestrates:
- Task Generator (Batch 16)
- AI Runner (Batch 15)
- Health Monitor (Batch 14)

It runs indefinitely, monitoring health, writing summaries, and never crashing.
This is an AI-native closed-loop orchestrator, not a scheduler replacement.

Safety: ALWAYS DRYRUN. Never executes real trading operations.
"""

import argparse
import json
import os
import signal
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional


# Global flag for graceful shutdown
_shutdown_requested = False


def _signal_handler(signum, frame):
    """Handle SIGINT (Ctrl+C) gracefully."""
    global _shutdown_requested
    _shutdown_requested = True
    print("\n[AI_LOOP] Shutdown requested. Completing current cycle and exiting gracefully...")


def parse_interval(interval: str) -> int:
    """
    Parse interval string to seconds.

    Supported formats:
    - "10s" -> 10 seconds
    - "2m" -> 120 seconds
    - "1h" -> 3600 seconds

    Args:
        interval: Interval string (e.g., "30s", "5m", "1h")

    Returns:
        Number of seconds

    Raises:
        ValueError: If interval format is invalid
    """
    if not interval:
        raise ValueError("Interval cannot be empty")

    interval = interval.strip().lower()

    # Extract numeric part and unit
    if interval[-1] == 's':
        return int(interval[:-1])
    elif interval[-1] == 'm':
        return int(interval[:-1]) * 60
    elif interval[-1] == 'h':
        return int(interval[:-1]) * 3600
    else:
        raise ValueError(f"Invalid interval format: {interval}. Use format like '30s', '5m', or '1h'")


def sleep_interruptible(seconds: int, verbose: bool = False) -> bool:
    """
    Sleep for specified seconds, checking for shutdown signal every second.

    Args:
        seconds: Number of seconds to sleep
        verbose: If True, print progress

    Returns:
        True if shutdown was requested during sleep, False otherwise
    """
    global _shutdown_requested

    for i in range(seconds):
        if _shutdown_requested:
            return True
        if verbose and (i + 1) % 10 == 0:
            remaining = seconds - (i + 1)
            print(f"[AI_LOOP] Sleeping... {remaining}s remaining")
        time.sleep(1)

    return _shutdown_requested


def load_health(state_dir: str) -> Dict[str, Any]:
    """
    Load health status from state/hands_off_health.json.

    Args:
        state_dir: State directory path

    Returns:
        Health data dictionary, or {"status": "unknown"} if not available
    """
    health_path = Path(state_dir) / "hands_off_health.json"

    try:
        if not health_path.exists():
            return {"status": "unknown", "reason": "health file not found"}

        with open(health_path, 'r') as f:
            health = json.load(f)

        # Ensure it has a status field
        if "status" not in health:
            health["status"] = "unknown"

        return health

    except json.JSONDecodeError:
        return {"status": "unknown", "reason": "health file malformed"}
    except Exception as e:
        return {"status": "unknown", "reason": f"error reading health: {str(e)}"}


def invoke_task_generator(state_dir: str, ai_dir: str, verbose: bool = False) -> Dict[str, Any]:
    """
    Invoke Task Generator (Batch 16).

    Args:
        state_dir: State directory path
        ai_dir: AI directory path
        verbose: Enable verbose output

    Returns:
        Result dictionary with status and details
    """
    try:
        # Import here to allow graceful fallback if not available
        from ai.ho_task_generator import TaskGenerator

        tg = TaskGenerator(state_dir, ai_dir)
        result = tg.run(verbose=verbose)

        return {
            "status": "success",
            "result": result,
            "error": None
        }

    except ImportError:
        return {
            "status": "error",
            "result": None,
            "error": "TaskGenerator not available (Batch 16 not implemented)"
        }
    except Exception as e:
        return {
            "status": "error",
            "result": None,
            "error": f"TaskGenerator failed: {str(e)}"
        }


def invoke_ai_runner(state_dir: str, ai_dir: str, verbose: bool = False) -> Dict[str, Any]:
    """
    Invoke AI Runner (Batch 15).

    Args:
        state_dir: State directory path
        ai_dir: AI directory path
        verbose: Enable verbose output

    Returns:
        Result dictionary with status and details
    """
    try:
        # Import here to allow graceful fallback if not available
        from ai.ho_ai_runner import run_ai_runner

        result = run_ai_runner(state_dir, ai_dir, verbose=verbose)

        return {
            "status": "success",
            "result": result,
            "error": None
        }

    except ImportError:
        return {
            "status": "error",
            "result": None,
            "error": "AI Runner not available (Batch 15 not implemented)"
        }
    except Exception as e:
        return {
            "status": "error",
            "result": None,
            "error": f"AI Runner failed: {str(e)}"
        }


def write_loop_summary(
    state_dir: str,
    cycle: int,
    interval: str,
    health: Dict[str, Any],
    task_generator_result: Dict[str, Any],
    ai_runner_result: Dict[str, Any],
    errors: list,
    verbose: bool = False
) -> None:
    """
    Write loop summary to state files.

    Writes two files:
    1. state/hands_off_ai_loop.json (latest summary)
    2. state/history/ai_loop_<timestamp>.json (per-cycle history)

    Args:
        state_dir: State directory path
        cycle: Current cycle number
        interval: Configured interval string
        health: Health status dictionary
        task_generator_result: Task generator result
        ai_runner_result: AI runner result
        errors: List of errors in this cycle
        verbose: Enable verbose output
    """
    timestamp = datetime.utcnow().isoformat() + "Z"

    # Determine overall status
    tg_failed = task_generator_result.get("status") != "success"
    runner_failed = ai_runner_result.get("status") != "success"

    if tg_failed or runner_failed:
        status = "error"
    elif errors:
        status = "partial"
    else:
        status = "ok"

    summary = {
        "timestamp": timestamp,
        "cycle": cycle,
        "interval": interval,
        "health": health.get("status", "unknown"),
        "task_generator": task_generator_result,
        "ai_runner": ai_runner_result,
        "errors": errors,
        "status": status
    }

    # Write latest summary
    state_path = Path(state_dir)
    state_path.mkdir(parents=True, exist_ok=True)

    latest_path = state_path / "hands_off_ai_loop.json"
    with open(latest_path, 'w') as f:
        json.dump(summary, f, indent=2)

    if verbose:
        print(f"[AI_LOOP] Wrote latest summary to {latest_path}")

    # Write history entry
    history_dir = state_path / "history"
    history_dir.mkdir(parents=True, exist_ok=True)

    # Use timestamp for filename
    ts_str = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    history_path = history_dir / f"ai_loop_{ts_str}.json"

    with open(history_path, 'w') as f:
        json.dump(summary, f, indent=2)

    if verbose:
        print(f"[AI_LOOP] Wrote history entry to {history_path}")


def run_single_cycle(
    state_dir: str,
    ai_dir: str,
    cycle: int,
    interval: str,
    verbose: bool = False
) -> Dict[str, Any]:
    """
    Run a single AI loop cycle.

    Args:
        state_dir: State directory path
        ai_dir: AI directory path
        cycle: Current cycle number
        interval: Configured interval string
        verbose: Enable verbose output

    Returns:
        Cycle result dictionary with status and errors
    """
    if verbose:
        print(f"\n[AI_LOOP] ===== Cycle {cycle} starting =====")

    errors = []

    # Step 1: Invoke Task Generator
    if verbose:
        print("[AI_LOOP] Step 1: Invoking Task Generator...")

    tg_result = invoke_task_generator(state_dir, ai_dir, verbose)

    if tg_result["status"] != "success":
        errors.append({
            "component": "task_generator",
            "error": tg_result["error"]
        })
        if verbose:
            print(f"[AI_LOOP] Task Generator failed: {tg_result['error']}")
    elif verbose:
        print("[AI_LOOP] Task Generator completed successfully")

    # Step 2: Invoke AI Runner
    if verbose:
        print("[AI_LOOP] Step 2: Invoking AI Runner...")

    runner_result = invoke_ai_runner(state_dir, ai_dir, verbose)

    if runner_result["status"] != "success":
        errors.append({
            "component": "ai_runner",
            "error": runner_result["error"]
        })
        if verbose:
            print(f"[AI_LOOP] AI Runner failed: {runner_result['error']}")
    elif verbose:
        print("[AI_LOOP] AI Runner completed successfully")

    # Step 3: Read Health
    if verbose:
        print("[AI_LOOP] Step 3: Reading health status...")

    health = load_health(state_dir)

    if verbose:
        print(f"[AI_LOOP] Health status: {health.get('status', 'unknown')}")

    # Step 4: Write Loop Summary
    if verbose:
        print("[AI_LOOP] Step 4: Writing loop summary...")

    write_loop_summary(
        state_dir=state_dir,
        cycle=cycle,
        interval=interval,
        health=health,
        task_generator_result=tg_result,
        ai_runner_result=runner_result,
        errors=errors,
        verbose=verbose
    )

    if verbose:
        print(f"[AI_LOOP] ===== Cycle {cycle} completed =====")

    return {
        "cycle": cycle,
        "status": "error" if errors else "ok",
        "errors": errors
    }


def run_ai_loop(
    state_dir: str = "state",
    ai_dir: str = "ai",
    interval: str = "30s",
    max_errors: int = 50,
    verbose: bool = False,
    once: bool = False
) -> int:
    """
    Run the continuous autonomous AI loop.

    This is the main entry point. It runs forever (or once if --once is set),
    orchestrating Task Generator, AI Runner, and health monitoring.

    The loop:
    1. Generates tasks (Batch 16)
    2. Executes tasks (Batch 15)
    3. Monitors health (Batch 14)
    4. Writes loop summary
    5. Sleeps for configured interval
    6. Repeats indefinitely (unless --once is set)

    Error handling:
    - Tracks consecutive errors
    - If consecutive_errors > max_errors, stops safely
    - Never crashes, always writes final summary

    SIGINT handling:
    - Catches Ctrl+C
    - Completes current cycle
    - Writes final summary
    - Exits gracefully

    Args:
        state_dir: State directory path (default: "state")
        ai_dir: AI directory path (default: "ai")
        interval: Sleep interval between cycles (default: "30s")
        max_errors: Maximum consecutive errors before stopping (default: 50)
        verbose: Enable verbose output (default: False)
        once: Run exactly one cycle and exit (default: False)

    Returns:
        Exit code (0 = success, 1 = fatal error)
    """
    # Register signal handler
    signal.signal(signal.SIGINT, _signal_handler)

    # Parse interval
    try:
        interval_seconds = parse_interval(interval)
    except ValueError as e:
        print(f"[AI_LOOP] ERROR: {e}", file=sys.stderr)
        return 1

    if verbose:
        print(f"[AI_LOOP] Starting continuous autonomous AI loop")
        print(f"[AI_LOOP] State directory: {state_dir}")
        print(f"[AI_LOOP] AI directory: {ai_dir}")
        print(f"[AI_LOOP] Interval: {interval} ({interval_seconds}s)")
        print(f"[AI_LOOP] Max errors: {max_errors}")
        print(f"[AI_LOOP] Once mode: {once}")
        print(f"[AI_LOOP] Press Ctrl+C to stop gracefully")

    # Ensure directories exist
    Path(state_dir).mkdir(parents=True, exist_ok=True)
    Path(ai_dir).mkdir(parents=True, exist_ok=True)

    cycle = 0
    consecutive_errors = 0

    global _shutdown_requested

    try:
        while not _shutdown_requested:
            cycle += 1

            # Run single cycle
            cycle_result = run_single_cycle(
                state_dir=state_dir,
                ai_dir=ai_dir,
                cycle=cycle,
                interval=interval,
                verbose=verbose
            )

            # Check for errors
            if cycle_result["status"] == "error":
                consecutive_errors += 1
                if verbose:
                    print(f"[AI_LOOP] Consecutive errors: {consecutive_errors}/{max_errors}")

                if consecutive_errors > max_errors:
                    print(f"[AI_LOOP] FATAL: Exceeded max consecutive errors ({max_errors})", file=sys.stderr)

                    # Write final fatal summary
                    write_loop_summary(
                        state_dir=state_dir,
                        cycle=cycle,
                        interval=interval,
                        health={"status": "fatal"},
                        task_generator_result={"status": "stopped", "error": "max errors exceeded"},
                        ai_runner_result={"status": "stopped", "error": "max errors exceeded"},
                        errors=[{"fatal": f"Exceeded max consecutive errors: {max_errors}"}],
                        verbose=verbose
                    )

                    return 1
            else:
                # Reset error counter on success
                consecutive_errors = 0

            # If --once mode, exit after first cycle
            if once:
                if verbose:
                    print("[AI_LOOP] Once mode: exiting after single cycle")
                break

            # Sleep
            if not _shutdown_requested and not once:
                if verbose:
                    print(f"[AI_LOOP] Sleeping for {interval}...")

                shutdown_during_sleep = sleep_interruptible(interval_seconds, verbose)

                if shutdown_during_sleep:
                    break

        # Graceful shutdown
        if _shutdown_requested:
            print("[AI_LOOP] Graceful shutdown completed")

        return 0

    except Exception as e:
        print(f"[AI_LOOP] FATAL ERROR: {e}", file=sys.stderr)

        # Write final error summary
        try:
            write_loop_summary(
                state_dir=state_dir,
                cycle=cycle,
                interval=interval,
                health={"status": "fatal"},
                task_generator_result={"status": "crashed", "error": str(e)},
                ai_runner_result={"status": "crashed", "error": str(e)},
                errors=[{"fatal": str(e)}],
                verbose=verbose
            )
        except Exception as write_error:
            print(f"[AI_LOOP] Failed to write final summary: {write_error}", file=sys.stderr)

        return 1


def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Hands-Off Engine - Continuous Autonomous AI Loop (Batch 17)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python3 ai/ho_ai_loop.py
  python3 ai/ho_ai_loop.py --interval 1m --verbose
  python3 ai/ho_ai_loop.py --once
  python3 ai/ho_ai_loop.py --state-dir /tmp/state --ai-dir /tmp/ai
        """
    )

    parser.add_argument(
        "--state-dir",
        default="state",
        help="State directory path (default: state)"
    )

    parser.add_argument(
        "--ai-dir",
        default="ai",
        help="AI directory path (default: ai)"
    )

    parser.add_argument(
        "--interval",
        default="30s",
        help="Sleep interval between cycles (e.g., 10s, 2m, 1h) (default: 30s)"
    )

    parser.add_argument(
        "--max-errors",
        type=int,
        default=50,
        help="Maximum consecutive errors before stopping (default: 50)"
    )

    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose output"
    )

    parser.add_argument(
        "--once",
        action="store_true",
        help="Run exactly one cycle and exit (useful for testing)"
    )

    args = parser.parse_args()

    # Run the loop
    exit_code = run_ai_loop(
        state_dir=args.state_dir,
        ai_dir=args.ai_dir,
        interval=args.interval,
        max_errors=args.max_errors,
        verbose=args.verbose,
        once=args.once
    )

    sys.exit(exit_code)


if __name__ == "__main__":
    main()
