#!/usr/bin/env python3
"""
Hands-Off AI Runner - Smart Task Routing + Health-Gated Execution

This module provides a safe, file-based automation layer for executing
AI-generated tasks in DRYRUN mode only. Tasks are consumed from JSON files,
executed with health checks, and results are written back to the filesystem.

Part of Batch 15: AI-Runner Upgrade
"""

import argparse
import json
import os
import shutil
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional


def load_tasks(task_dir: str) -> List[Dict[str, Any]]:
    """
    Load all task JSON files from the task directory.

    Args:
        task_dir: Path to directory containing task JSON files

    Returns:
        List of task dictionaries, each with 'id', 'type', 'payload', and '_file_path'
        Sorted by file modification time (oldest first)
    """
    tasks = []
    task_path = Path(task_dir)

    if not task_path.exists():
        return tasks

    # Get all .json files, sorted by modification time (oldest first)
    json_files = sorted(
        task_path.glob("*.json"),
        key=lambda p: p.stat().st_mtime
    )

    for file_path in json_files:
        try:
            with open(file_path, 'r') as f:
                task_data = json.load(f)

            # Validate required fields
            if not isinstance(task_data, dict):
                print(f"Warning: Skipping {file_path.name} - not a JSON object", file=sys.stderr)
                continue

            if "id" not in task_data or "type" not in task_data:
                print(f"Warning: Skipping {file_path.name} - missing 'id' or 'type'", file=sys.stderr)
                continue

            # Add file path for later processing
            task_data["_file_path"] = str(file_path)
            tasks.append(task_data)

        except json.JSONDecodeError as e:
            print(f"Warning: Skipping {file_path.name} - invalid JSON: {e}", file=sys.stderr)
        except Exception as e:
            print(f"Warning: Skipping {file_path.name} - error: {e}", file=sys.stderr)

    return tasks


def _load_health_data(state_dir: str) -> Optional[Dict[str, Any]]:
    """Load health data from hands_off_health.json"""
    health_path = Path(state_dir) / "hands_off_health.json"

    if not health_path.exists():
        return None

    try:
        with open(health_path, 'r') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading health data: {e}", file=sys.stderr)
        return None


def _load_summary_data(state_dir: str) -> Optional[Dict[str, Any]]:
    """Load summary data from hands_off_summary.json"""
    summary_path = Path(state_dir) / "hands_off_summary.json"

    if not summary_path.exists():
        return None

    try:
        with open(summary_path, 'r') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading summary data: {e}", file=sys.stderr)
        return None


def _check_health_ok(health_data: Optional[Dict[str, Any]]) -> bool:
    """Check if health status is 'ok'"""
    if health_data is None:
        return False
    return health_data.get("status") == "ok"


def _check_polymarket_fresh(health_data: Optional[Dict[str, Any]], max_age_minutes: int = 5) -> bool:
    """
    Check if polymarket fetch data is fresh (≤ max_age_minutes old)

    Args:
        health_data: Health data dictionary
        max_age_minutes: Maximum age in minutes for data to be considered fresh

    Returns:
        True if data is fresh, False otherwise
    """
    if health_data is None:
        return False

    components = health_data.get("components", {})
    polymarket = components.get("polymarket_fetch", {})

    # Check status
    if polymarket.get("status") != "ok":
        return False

    # Check freshness
    last_update = polymarket.get("last_update")
    if not last_update:
        return False

    try:
        update_time = datetime.fromisoformat(last_update.replace('Z', '+00:00'))
        now = datetime.now(update_time.tzinfo)
        age = now - update_time

        return age <= timedelta(minutes=max_age_minutes)
    except Exception:
        return False


def _run_health_check_task(task: Dict[str, Any], state_dir: str) -> Dict[str, Any]:
    """Execute health-check task"""
    health_data = _load_health_data(state_dir)

    if health_data is None:
        return {
            "id": task["id"],
            "status": "error",
            "result": {},
            "errors": ["Health file not found: hands_off_health.json"]
        }

    return {
        "id": task["id"],
        "status": "ok",
        "result": health_data,
        "errors": []
    }


def _run_latest_summary_task(task: Dict[str, Any], state_dir: str) -> Dict[str, Any]:
    """Execute latest-summary task"""
    summary_data = _load_summary_data(state_dir)

    if summary_data is None:
        return {
            "id": task["id"],
            "status": "error",
            "result": {},
            "errors": ["Summary file not found: hands_off_summary.json"]
        }

    return {
        "id": task["id"],
        "status": "ok",
        "result": summary_data,
        "errors": []
    }


def _run_generate_history_report_task(task: Dict[str, Any], state_dir: str) -> Dict[str, Any]:
    """Execute generate-history-report task"""
    try:
        # Try to import the history report module
        from reports.ho_history_report import summarize_history

        # Call the function
        summary = summarize_history(state_dir)

        return {
            "id": task["id"],
            "status": "ok",
            "result": summary,
            "errors": []
        }
    except ImportError:
        return {
            "id": task["id"],
            "status": "error",
            "result": {},
            "errors": ["Module not found: reports.ho_history_report (Batch 13 not installed)"]
        }
    except Exception as e:
        return {
            "id": task["id"],
            "status": "error",
            "result": {},
            "errors": [f"Error generating history report: {str(e)}"]
        }


def _run_autoloop_task(task: Dict[str, Any], state_dir: str) -> Dict[str, Any]:
    """Execute run-autoloop task (DRYRUN-only, health-gated)"""
    # Load health data
    health_data = _load_health_data(state_dir)

    # Check health status
    if not _check_health_ok(health_data):
        return {
            "id": task["id"],
            "status": "skipped",
            "result": {
                "reason": "Health check failed - system not healthy"
            },
            "errors": []
        }

    # Check polymarket freshness
    if not _check_polymarket_fresh(health_data, max_age_minutes=5):
        return {
            "id": task["id"],
            "status": "skipped",
            "result": {
                "reason": "Polymarket data not fresh (> 5 minutes old)"
            },
            "errors": []
        }

    # All checks passed, try to run autoloop
    try:
        # Try to import the autoloop module
        from scheduler.ho_autoloop import run_all

        # Run autoloop
        result = run_all(state_dir=state_dir, mode="DRYRUN")

        return {
            "id": task["id"],
            "status": "ok",
            "result": result,
            "errors": []
        }
    except ImportError:
        return {
            "id": task["id"],
            "status": "error",
            "result": {},
            "errors": ["Module not found: scheduler.ho_autoloop (Batch 10 not installed)"]
        }
    except Exception as e:
        return {
            "id": task["id"],
            "status": "error",
            "result": {},
            "errors": [f"Error running autoloop: {str(e)}"]
        }


def run_task(task: Dict[str, Any], state_dir: str) -> Dict[str, Any]:
    """
    Execute ONE task.

    Must check health first for health-gated tasks.
    Must handle unknown task types.
    Must be DRYRUN-safe.

    Args:
        task: Task dictionary with 'id', 'type', and 'payload'
        state_dir: Path to state directory

    Returns:
        Result dictionary:
        {
          "id": str,
          "status": "ok" | "error" | "skipped",
          "result": {...},   # task-specific
          "errors": [...]
        }
    """
    task_type = task.get("type")

    # Dispatch to appropriate handler
    if task_type == "health-check":
        return _run_health_check_task(task, state_dir)
    elif task_type == "latest-summary":
        return _run_latest_summary_task(task, state_dir)
    elif task_type == "generate-history-report":
        return _run_generate_history_report_task(task, state_dir)
    elif task_type == "run-autoloop":
        return _run_autoloop_task(task, state_dir)
    else:
        # Unknown task type
        return {
            "id": task["id"],
            "status": "error",
            "result": {},
            "errors": [f"unknown task type: {task_type}"]
        }


def write_result(result: Dict[str, Any], results_dir: str) -> str:
    """
    Write result JSON to ai/results/<task_id>.json

    Args:
        result: Result dictionary to write
        results_dir: Path to results directory

    Returns:
        Path to written result file
    """
    results_path = Path(results_dir)
    results_path.mkdir(parents=True, exist_ok=True)

    task_id = result["id"]
    result_file = results_path / f"{task_id}.json"

    # Add timestamp
    result_with_timestamp = {
        **result,
        "timestamp": datetime.utcnow().isoformat() + "Z"
    }

    with open(result_file, 'w') as f:
        json.dump(result_with_timestamp, f, indent=2)

    return str(result_file)


def move_to_processed(task_path: str, processed_dir: str) -> str:
    """
    Archive task after execution by moving it to processed directory

    Args:
        task_path: Path to original task file
        processed_dir: Path to processed directory

    Returns:
        Path to archived task file
    """
    processed_path = Path(processed_dir)
    processed_path.mkdir(parents=True, exist_ok=True)

    source = Path(task_path)
    dest = processed_path / source.name

    # If file already exists, add timestamp
    if dest.exists():
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        stem = source.stem
        suffix = source.suffix
        dest = processed_path / f"{stem}_{timestamp}{suffix}"

    shutil.move(str(source), str(dest))
    return str(dest)


def run_ai_runner(state_dir: str = "state", ai_dir: str = "ai") -> Dict[str, Any]:
    """
    Main entrypoint for AI runner.

    - Load tasks from ai/tasks/
    - Evaluate system health (from hands_off_health.json)
    - Run oldest tasks first
    - Write results to ai/results/
    - Archive tasks to ai/processed/
    - Return summary dict

    Args:
        state_dir: Path to state directory (default: "state")
        ai_dir: Path to AI directory (default: "ai")

    Returns:
        Summary dictionary with execution statistics
    """
    # Setup paths
    task_dir = os.path.join(ai_dir, "tasks")
    results_dir = os.path.join(ai_dir, "results")
    processed_dir = os.path.join(ai_dir, "processed")

    # Load tasks
    tasks = load_tasks(task_dir)

    # Initialize counters
    stats = {
        "total_tasks": len(tasks),
        "executed": 0,
        "ok": 0,
        "skipped": 0,
        "errored": 0,
        "results": []
    }

    # Execute each task
    for task in tasks:
        try:
            # Run task
            result = run_task(task, state_dir)

            # Write result
            result_path = write_result(result, results_dir)

            # Archive task
            task_file_path = task.get("_file_path")
            if task_file_path:
                archived_path = move_to_processed(task_file_path, processed_dir)
            else:
                archived_path = None

            # Update stats
            stats["executed"] += 1
            if result["status"] == "ok":
                stats["ok"] += 1
            elif result["status"] == "skipped":
                stats["skipped"] += 1
            elif result["status"] == "error":
                stats["errored"] += 1

            # Record result info
            stats["results"].append({
                "task_id": result["id"],
                "task_type": task.get("type"),
                "status": result["status"],
                "result_path": result_path,
                "archived_path": archived_path
            })

        except Exception as e:
            # Handle unexpected errors gracefully
            print(f"Error processing task {task.get('id', 'unknown')}: {e}", file=sys.stderr)
            stats["errored"] += 1

    return stats


def main():
    """CLI entry point"""
    parser = argparse.ArgumentParser(
        description="Hands-Off AI Runner - Smart Task Routing + Health-Gated Execution"
    )
    parser.add_argument(
        "--state-dir",
        default="state",
        help="Path to state directory (default: state)"
    )
    parser.add_argument(
        "--ai-dir",
        default="ai",
        help="Path to AI directory (default: ai)"
    )

    args = parser.parse_args()

    try:
        # Run the AI runner
        stats = run_ai_runner(state_dir=args.state_dir, ai_dir=args.ai_dir)

        # Print summary
        print("\n" + "="*60)
        print("AI Runner Execution Summary")
        print("="*60)
        print(f"Total tasks found:    {stats['total_tasks']}")
        print(f"Tasks executed:       {stats['executed']}")
        print(f"  - OK:               {stats['ok']}")
        print(f"  - Skipped:          {stats['skipped']}")
        print(f"  - Errored:          {stats['errored']}")
        print("="*60)

        if stats['results']:
            print("\nTask Results:")
            for r in stats['results']:
                print(f"  [{r['status'].upper():8}] {r['task_id']} ({r['task_type']})")
                print(f"             Result: {r['result_path']}")

        print(f"\nResults written to: {os.path.join(args.ai_dir, 'results')}/")
        print(f"Tasks archived to:  {os.path.join(args.ai_dir, 'processed')}/")
        print()

        # Exit with success
        sys.exit(0)

    except Exception as e:
        print(f"\nERROR: AI Runner failed: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
