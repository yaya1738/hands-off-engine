"""
AI-Runner v0.4 - Task Processor with Spark Plug Integration

Watches ai/tasks/ for JSON task files and executes them.

Task types supported:
    - sparkplug_autokernel_refresh: Auto-refresh memory kernels from history

Results are written to ai/results/

Example task files:
    - ai/tasks/sparkplug_nightly.json (config-driven mode)
    - ai/tasks/sparkplug_manual.json (explicit kernel list)

CLI:
    python ai_runner.py process-all          # Process all tasks in ai/tasks/
    python ai_runner.py process-one <file>   # Process specific task file
    python ai_runner.py watch                # Watch and process continuously (future)

Safety:
    - design_only mode (no trading/risk/decider/executor imports)
    - All results written to ai/results/ for auditing
    - Task files moved to ai/tasks/processed/ after completion
"""

import sys
import json
import argparse
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional

# Add repo root to path
REPO_ROOT = Path(__file__).parent
sys.path.insert(0, str(REPO_ROOT))

# Import Spark Plug auto-kernel
from ai_nexus.spark_plug_autokernel import run_autokernel_refresh
from ai_nexus.history_log import log_kernel_history_event

# Paths
TASKS_DIR = REPO_ROOT / "ai" / "tasks"
RESULTS_DIR = REPO_ROOT / "ai" / "results"
PROCESSED_DIR = TASKS_DIR / "processed"
CONFIG_DIR = REPO_ROOT / "ai" / "config"
SPARKPLUG_CONFIG = CONFIG_DIR / "sparkplug_kernels.json"

# Ensure directories exist
TASKS_DIR.mkdir(parents=True, exist_ok=True)
RESULTS_DIR.mkdir(parents=True, exist_ok=True)
PROCESSED_DIR.mkdir(parents=True, exist_ok=True)


# =============================================================================
# Task Processors
# =============================================================================

def process_sparkplug_autokernel_refresh(task: Dict) -> Dict:
    """
    Process a Spark Plug auto-kernel refresh task

    Args:
        task: Task dict with structure:
        {
            "task_type": "sparkplug_autokernel_refresh",
            "task_id": "sparkplug_nightly_2025-11-26",
            "mode": "config" | "explicit",
            "kernels": [...],  # only if mode == "explicit"
            "dry_run": bool    # optional, default False
        }

    Returns:
        Result dict with structure:
        {
            "task_type": "sparkplug_autokernel_refresh",
            "task_id": "...",
            "run_at": "2025-11-26T10:32:00Z",
            "kernels": [
                {
                    "kernel_id": "risk_model_v2",
                    "result": { ... }
                },
                ...
            ],
            "summary": {
                "total_kernels": int,
                "success": int,
                "no_history": int,
                "kernel_not_found": int,
                "errors": int
            }
        }
    """
    task_id = task.get("task_id", "unknown")
    mode = task.get("mode", "config")
    dry_run = task.get("dry_run", False)

    print(f"Processing Spark Plug auto-kernel refresh task: {task_id}")
    print(f"  Mode: {mode}")
    print(f"  Dry run: {dry_run}")

    # Determine which kernels to refresh
    kernels_to_refresh = []

    if mode == "config":
        # Load config file
        print(f"  Loading config from: {SPARKPLUG_CONFIG}")

        if not SPARKPLUG_CONFIG.exists():
            return {
                "status": "error",
                "task_type": "sparkplug_autokernel_refresh",
                "task_id": task_id,
                "run_at": datetime.utcnow().isoformat() + "Z",
                "error": {
                    "type": "ConfigNotFound",
                    "message": f"Config file not found: {SPARKPLUG_CONFIG}",
                    "stage": "load_config"
                }
            }

        try:
            with open(SPARKPLUG_CONFIG) as f:
                config = json.load(f)

            # Filter enabled kernels
            for kernel_entry in config.get("kernels", []):
                if kernel_entry.get("enabled", False):
                    kernels_to_refresh.append({
                        "kernel_id": kernel_entry["kernel_id"],
                        "mode": kernel_entry.get("mode", "cpu")
                    })

            print(f"  Found {len(kernels_to_refresh)} enabled kernels in config")

        except Exception as e:
            return {
                "status": "error",
                "task_type": "sparkplug_autokernel_refresh",
                "task_id": task_id,
                "run_at": datetime.utcnow().isoformat() + "Z",
                "error": {
                    "type": type(e).__name__,
                    "message": str(e),
                    "stage": "load_config"
                }
            }

    elif mode == "explicit":
        # Use explicitly provided kernel list
        kernels_to_refresh = task.get("kernels", [])
        print(f"  Using explicit kernel list: {len(kernels_to_refresh)} kernels")

    else:
        return {
            "status": "error",
            "task_type": "sparkplug_autokernel_refresh",
            "task_id": task_id,
            "run_at": datetime.utcnow().isoformat() + "Z",
            "error": {
                "type": "InvalidMode",
                "message": f"Invalid mode '{mode}'. Must be 'config' or 'explicit'.",
                "stage": "validate_task"
            }
        }

    if not kernels_to_refresh:
        return {
            "status": "success",
            "task_type": "sparkplug_autokernel_refresh",
            "task_id": task_id,
            "run_at": datetime.utcnow().isoformat() + "Z",
            "kernels": [],
            "summary": {
                "total_kernels": 0,
                "success": 0,
                "no_history": 0,
                "kernel_not_found": 0,
                "errors": 0
            }
        }

    # Process each kernel
    results = []
    summary = {
        "total_kernels": len(kernels_to_refresh),
        "success": 0,
        "no_history": 0,
        "kernel_not_found": 0,
        "errors": 0
    }

    for i, kernel_entry in enumerate(kernels_to_refresh, 1):
        kernel_id = kernel_entry["kernel_id"]
        kernel_mode = kernel_entry.get("mode", "cpu")

        print(f"\n  [{i}/{len(kernels_to_refresh)}] Processing kernel: {kernel_id}")

        try:
            result = run_autokernel_refresh(
                kernel_id=kernel_id,
                mode=kernel_mode,
                dry_run=dry_run
            )

            # Update summary counts
            status = result.get("status", "unknown")
            if status == "success":
                summary["success"] += 1
            elif status == "no_history":
                summary["no_history"] += 1
            elif status == "kernel_not_found":
                summary["kernel_not_found"] += 1
            elif status == "error":
                summary["errors"] += 1

            results.append({
                "kernel_id": kernel_id,
                "result": result
            })

            print(f"      Status: {status}")

        except Exception as e:
            # Catch any unexpected exceptions
            print(f"      Status: error (exception: {type(e).__name__})")
            summary["errors"] += 1

            results.append({
                "kernel_id": kernel_id,
                "result": {
                    "status": "error",
                    "kernel_id": kernel_id,
                    "error": {
                        "type": type(e).__name__,
                        "message": str(e),
                        "stage": "run_autokernel_refresh"
                    }
                }
            })

    # Log AI coordination event for Spark Plug kernels
    try:
        results_by_kernel = {r["kernel_id"]: r["result"] for r in results}
        log_kernel_history_event(
            kernel_ids=["ai_coordination", "system_health"],
            kind="ai_coordination",
            source="ai_runner.sparkplug",
            summary=f"Spark Plug refresh task {task_id} processed {len(results_by_kernel)} kernels: success={summary['success']}, errors={summary['errors']}",
            details={
                "task_id": task_id,
                "mode": mode,
                "dry_run": dry_run,
                "kernel_ids": list(results_by_kernel.keys()),
                "statuses": {k: v.get("status", "unknown") for k, v in results_by_kernel.items()},
                "summary": summary,
            },
            importance=6,
            tags=["spark_plug", "ai_runner"],
        )
    except Exception as e:
        # Best-effort logging - never crash the task processor
        print(f"[history_log] Warning: Failed to log AI coordination event: {e}")

    # Build final result
    return {
        "status": "success",
        "task_type": "sparkplug_autokernel_refresh",
        "task_id": task_id,
        "run_at": datetime.utcnow().isoformat() + "Z",
        "kernels": results,
        "summary": summary
    }


# =============================================================================
# Task Dispatcher
# =============================================================================

def process_task(task_file: Path) -> Dict:
    """
    Process a single task file

    Args:
        task_file: Path to task JSON file

    Returns:
        Result dict
    """
    print(f"\n{'='*70}")
    print(f"Processing task: {task_file.name}")
    print(f"{'='*70}")

    # Load task
    try:
        with open(task_file) as f:
            task = json.load(f)
    except Exception as e:
        return {
            "status": "error",
            "task_file": str(task_file),
            "error": {
                "type": "InvalidTaskFile",
                "message": f"Failed to load task file: {e}",
                "stage": "load_task"
            }
        }

    # Dispatch based on task_type
    task_type = task.get("task_type")

    if task_type == "sparkplug_autokernel_refresh":
        result = process_sparkplug_autokernel_refresh(task)

    else:
        result = {
            "status": "error",
            "task_type": task_type,
            "task_id": task.get("task_id", "unknown"),
            "error": {
                "type": "UnsupportedTaskType",
                "message": f"Task type '{task_type}' is not supported",
                "stage": "dispatch"
            }
        }

    return result


def write_result(result: Dict, task_file: Path) -> Path:
    """
    Write task result to ai/results/

    Args:
        result: Result dict
        task_file: Original task file

    Returns:
        Path to result file
    """
    # Generate result filename
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    task_type = result.get("task_type", "unknown")
    task_id = result.get("task_id", "unknown")

    result_filename = f"{task_type}_{task_id}_{timestamp}.json"
    result_path = RESULTS_DIR / result_filename

    # Write result
    with open(result_path, 'w') as f:
        json.dump(result, f, indent=2)

    print(f"\nResult written to: {result_path}")
    return result_path


def move_task_to_processed(task_file: Path) -> Path:
    """
    Move task file to processed directory

    Args:
        task_file: Task file to move

    Returns:
        New path to task file
    """
    new_path = PROCESSED_DIR / task_file.name

    # If file already exists, add timestamp
    if new_path.exists():
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        stem = task_file.stem
        suffix = task_file.suffix
        new_path = PROCESSED_DIR / f"{stem}_{timestamp}{suffix}"

    task_file.rename(new_path)
    print(f"Task moved to: {new_path}")
    return new_path


# =============================================================================
# CLI Commands
# =============================================================================

def cmd_process_all(args):
    """Process all tasks in ai/tasks/"""
    print(f"Scanning for tasks in: {TASKS_DIR}")

    # Find all .json files in tasks directory (exclude processed subdirectory)
    task_files = [
        f for f in TASKS_DIR.glob("*.json")
        if f.is_file() and not f.name.startswith(".")
    ]

    if not task_files:
        print("No task files found.")
        return

    print(f"Found {len(task_files)} task file(s)")

    # Process each task
    for task_file in task_files:
        try:
            result = process_task(task_file)
            write_result(result, task_file)

            # Move task to processed directory
            if not args.keep:
                move_task_to_processed(task_file)

        except Exception as e:
            print(f"Error processing {task_file}: {e}")
            if args.continue_on_error:
                continue
            else:
                raise

    print(f"\n{'='*70}")
    print("All tasks processed.")
    print(f"{'='*70}\n")


def cmd_process_one(args):
    """Process a specific task file"""
    task_file = Path(args.task_file)

    if not task_file.exists():
        print(f"Error: Task file not found: {task_file}")
        sys.exit(1)

    result = process_task(task_file)
    write_result(result, task_file)

    # Move task to processed directory
    if not args.keep:
        move_task_to_processed(task_file)

    print(f"\n{'='*70}")
    print("Task processed.")
    print(f"{'='*70}\n")


# =============================================================================
# Main CLI
# =============================================================================

def main():
    parser = argparse.ArgumentParser(
        description="AI-Runner v0.4 - Task Processor with Spark Plug Integration",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Process all tasks in ai/tasks/
  python ai_runner.py process-all

  # Process specific task file
  python ai_runner.py process-one ai/tasks/sparkplug_nightly.json

  # Process all tasks but keep originals (don't move to processed/)
  python ai_runner.py process-all --keep
        """
    )

    subparsers = parser.add_subparsers(dest="command", required=True)

    # process-all command
    parser_all = subparsers.add_parser(
        "process-all",
        help="Process all tasks in ai/tasks/"
    )
    parser_all.add_argument(
        "--keep",
        action="store_true",
        help="Keep original task files (don't move to processed/)"
    )
    parser_all.add_argument(
        "--continue-on-error",
        action="store_true",
        help="Continue processing remaining tasks if one fails"
    )
    parser_all.set_defaults(func=cmd_process_all)

    # process-one command
    parser_one = subparsers.add_parser(
        "process-one",
        help="Process a specific task file"
    )
    parser_one.add_argument(
        "task_file",
        help="Path to task file"
    )
    parser_one.add_argument(
        "--keep",
        action="store_true",
        help="Keep original task file (don't move to processed/)"
    )
    parser_one.set_defaults(func=cmd_process_one)

    args = parser.parse_args()

    # Execute command
    args.func(args)


if __name__ == "__main__":
    main()
