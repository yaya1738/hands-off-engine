#!/usr/bin/env python3
"""
Spark Plug Nightly Task Generator

Generates a task file for nightly auto-kernel refresh and optionally
runs the ai_runner to process it.

Usage:
    # Generate task file only
    python scripts/sparkplug_nightly.py generate

    # Generate and run task
    python scripts/sparkplug_nightly.py run

    # Generate and run with dry_run
    python scripts/sparkplug_nightly.py run --dry-run

This script is designed to be called from cron or systemd timer:

    # Example cron entry (runs at 2am daily)
    0 2 * * * cd /path/to/hands-off-engine && python scripts/sparkplug_nightly.py run

    # Example systemd timer (see docs/SPARK_PLUG_v0.4_AI_RUNNER_INTEGRATION.md)
"""

import sys
import json
import argparse
from pathlib import Path
from datetime import datetime, timezone

# Add repo root to path
REPO_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(REPO_ROOT))

TASKS_DIR = REPO_ROOT / "ai" / "tasks"


def generate_task_file(dry_run: bool = False) -> Path:
    """
    Generate a nightly spark plug task file.
    
    Args:
        dry_run: If True, generate task with dry_run=True.
                 Default is False (LIVE mode) for production use.
        
    Returns:
        Path to generated task file
    """
    # Generate date-based task ID
    date_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    task_id = f"sparkplug_nightly_{date_str}"
    
    # Generate task - default is LIVE mode (dry_run=False)
    task = {
        "task_type": "sparkplug_autokernel_refresh",
        "task_id": task_id,
        "mode": "config",
        "dry_run": dry_run  # False = LIVE, True = dry-run testing
    }
    
    # Ensure tasks directory exists
    TASKS_DIR.mkdir(parents=True, exist_ok=True)
    
    # Write task file
    task_file = TASKS_DIR / f"{task_id}.json"
    with open(task_file, 'w') as f:
        json.dump(task, f, indent=2)
    
    print(f"✅ Generated task file: {task_file}")
    return task_file


def run_task(task_file: Path, keep: bool = False) -> int:
    """
    Run the generated task using ai_runner.
    
    Args:
        task_file: Path to task file
        keep: If True, keep task file (don't move to processed/)
        
    Returns:
        Exit code (0 for success, 1 for error)
    """
    import ai_runner
    
    print(f"\n🚀 Processing task: {task_file.name}")
    
    try:
        # Process task
        result = ai_runner.process_task(task_file)
        
        # Write result
        result_path = ai_runner.write_result(result, task_file)
        
        # Move task to processed (unless --keep)
        if not keep:
            ai_runner.move_task_to_processed(task_file)
        
        # Print summary
        print(f"\n{'='*70}")
        print(f"Spark Plug Nightly Complete")
        print(f"{'='*70}")
        print(f"Status: {result['status']}")
        
        if 'summary' in result:
            summary = result['summary']
            print(f"\nSummary:")
            print(f"  Total kernels: {summary.get('total_kernels', 0)}")
            print(f"  Success: {summary.get('success', 0)}")
            print(f"  No history: {summary.get('no_history', 0)}")
            print(f"  Errors: {summary.get('errors', 0)}")
        
        print(f"\nResult file: {result_path}")
        print(f"{'='*70}\n")
        
        return 0 if result['status'] == 'success' else 1
        
    except Exception as e:
        print(f"\n❌ Error processing task: {e}")
        return 1


def main():
    parser = argparse.ArgumentParser(
        description="Spark Plug Nightly Task Generator",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Generate task file only
  python scripts/sparkplug_nightly.py generate

  # Generate and run task
  python scripts/sparkplug_nightly.py run

  # Generate and run with dry_run
  python scripts/sparkplug_nightly.py run --dry-run

  # Generate and run, keep task file
  python scripts/sparkplug_nightly.py run --keep
        """
    )
    
    subparsers = parser.add_subparsers(dest="command", required=True)
    
    # generate command
    parser_gen = subparsers.add_parser(
        "generate",
        help="Generate a nightly task file"
    )
    parser_gen.add_argument(
        "--dry-run",
        action="store_true",
        help="Generate task with dry_run=True"
    )
    
    # run command
    parser_run = subparsers.add_parser(
        "run",
        help="Generate and run nightly task"
    )
    parser_run.add_argument(
        "--dry-run",
        action="store_true",
        help="Run with dry_run=True (no actual CPU execution)"
    )
    parser_run.add_argument(
        "--keep",
        action="store_true",
        help="Keep task file (don't move to processed/)"
    )
    
    args = parser.parse_args()
    
    if args.command == "generate":
        generate_task_file(dry_run=args.dry_run)
        
    elif args.command == "run":
        task_file = generate_task_file(dry_run=args.dry_run)
        exit_code = run_task(task_file, keep=args.keep)
        sys.exit(exit_code)


if __name__ == "__main__":
    main()
