#!/usr/bin/env python3
"""
Hands-Off Engine Health Check Module.

Unified health monitoring for the entire Hands-Off system.
Provides both JSON and human-readable health reports.
"""

import argparse
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


def gather_health(state_dir: str = "state") -> dict:
    """
    Gather comprehensive system health information.

    Args:
        state_dir: Path to the state directory

    Returns:
        Dictionary containing health status and checks
    """
    state_path = Path(state_dir)
    errors: List[str] = []
    components: Dict[str, str] = {}
    checks: Dict[str, Any] = {}

    # Initialize checks with null values
    checks["latest_snapshot_age_sec"] = None
    checks["latest_fetch_age_sec"] = None
    checks["num_snapshots"] = 0
    checks["recent_error_rate"] = 0.0
    checks["most_recent_run_status"] = None

    # Check if state directory exists
    if not state_path.exists():
        errors.append(f"State directory '{state_dir}' does not exist")
        components["polymarket_fetch"] = "error"
        components["polymarket_pipeline"] = "error"
        components["history"] = "error"
        components["scheduler"] = "unknown"

        return {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "state_dir": state_dir,
            "status": "error",
            "components": components,
            "checks": checks,
            "errors": errors,
        }

    # Check hands_off_summary.json
    summary_status, summary_error = _check_summary_file(state_path)
    if summary_error:
        errors.append(summary_error)
    components["polymarket_pipeline"] = summary_status

    # Check polymarket-compact.json
    fetch_status, fetch_age, fetch_error = _check_polymarket_fetch(state_path)
    if fetch_error:
        errors.append(fetch_error)
    components["polymarket_fetch"] = fetch_status
    checks["latest_fetch_age_sec"] = fetch_age

    # Check snapshot history
    history_status, snapshot_info, history_errors = _check_snapshot_history(state_path)
    components["history"] = history_status
    errors.extend(history_errors)

    # Update checks from snapshot info
    if snapshot_info:
        checks["latest_snapshot_age_sec"] = snapshot_info.get("age_sec")
        checks["num_snapshots"] = snapshot_info.get("total_count", 0)
        checks["recent_error_rate"] = snapshot_info.get("error_rate", 0.0)
        checks["most_recent_run_status"] = snapshot_info.get("latest_status")

    # Scheduler is unknown (no direct way to check if it's running)
    components["scheduler"] = "unknown"

    # Determine overall status
    status = _determine_overall_status(components)

    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "state_dir": state_dir,
        "status": status,
        "components": components,
        "checks": checks,
        "errors": errors,
    }


def _check_summary_file(state_path: Path) -> Tuple[str, Optional[str]]:
    """
    Check hands_off_summary.json exists and is valid.

    Returns:
        Tuple of (status, error_message)
    """
    summary_file = state_path / "hands_off_summary.json"

    if not summary_file.exists():
        return "error", "hands_off_summary.json does not exist"

    try:
        with open(summary_file, "r") as f:
            data = json.load(f)

        # Verify it has some expected structure (flexible check)
        if not isinstance(data, dict):
            return "error", "hands_off_summary.json is not a valid JSON object"

        return "ok", None
    except json.JSONDecodeError as e:
        return "error", f"hands_off_summary.json is malformed: {e}"
    except Exception as e:
        return "error", f"Error reading hands_off_summary.json: {e}"


def _check_polymarket_fetch(state_path: Path) -> Tuple[str, Optional[int], Optional[str]]:
    """
    Check polymarket-compact.json exists, is recent, and has markets.

    Returns:
        Tuple of (status, age_in_seconds, error_message)
    """
    compact_file = state_path / "polymarket-compact.json"

    if not compact_file.exists():
        return "error", None, "polymarket-compact.json does not exist"

    try:
        # Check file age
        mtime = compact_file.stat().st_mtime
        age_sec = int((datetime.now(timezone.utc).timestamp() - mtime))

        # Read and validate content
        with open(compact_file, "r") as f:
            data = json.load(f)

        # Check if it has markets (flexible structure check)
        markets = []
        if isinstance(data, dict):
            if "markets" in data:
                markets = data.get("markets", [])
            elif "data" in data:
                markets = data.get("data", [])
        elif isinstance(data, list):
            markets = data

        if not markets or len(markets) == 0:
            return "warn", age_sec, "polymarket-compact.json contains no markets"

        # Check if data is recent (≤ 5 minutes = 300 seconds)
        if age_sec > 300:
            return "warn", age_sec, f"polymarket-compact.json is stale ({age_sec}s old)"

        return "ok", age_sec, None

    except json.JSONDecodeError as e:
        return "error", None, f"polymarket-compact.json is malformed: {e}"
    except Exception as e:
        return "error", None, f"Error reading polymarket-compact.json: {e}"


def _check_snapshot_history(state_path: Path, recent_n: int = 20) -> Tuple[str, Optional[Dict], List[str]]:
    """
    Check snapshot history for age, count, and error rates.

    Args:
        state_path: Path to state directory
        recent_n: Number of recent snapshots to analyze for error rate

    Returns:
        Tuple of (status, snapshot_info_dict, error_messages)
    """
    history_path = state_path / "history"
    errors: List[str] = []

    if not history_path.exists():
        errors.append("history/ directory does not exist")
        return "error", None, errors

    # Find all snapshot files
    try:
        snapshot_files = sorted(
            history_path.glob("snapshot_*.json"),
            key=lambda p: p.stat().st_mtime,
            reverse=True  # Most recent first
        )
    except Exception as e:
        errors.append(f"Error reading history/ directory: {e}")
        return "error", None, errors

    if not snapshot_files:
        errors.append("No snapshots found in history/ directory")
        return "warn", {"total_count": 0}, errors

    total_count = len(snapshot_files)
    latest_file = snapshot_files[0]

    # Get age of most recent snapshot
    try:
        mtime = latest_file.stat().st_mtime
        age_sec = int((datetime.now(timezone.utc).timestamp() - mtime))
    except Exception as e:
        errors.append(f"Error getting age of latest snapshot: {e}")
        age_sec = None

    # Parse latest snapshot for status
    latest_status = None
    try:
        with open(latest_file, "r") as f:
            latest_data = json.load(f)
        latest_status = _extract_status_from_snapshot(latest_data)
    except Exception as e:
        errors.append(f"Error reading latest snapshot: {e}")

    # Calculate error rate from recent N snapshots
    error_rate = _calculate_error_rate(snapshot_files[:recent_n], errors)

    # Determine status based on error rate
    status = "ok"
    if error_rate > 0.50:
        status = "error"
        errors.append(f"High error rate detected: {error_rate:.2%} of recent runs failed")
    elif error_rate > 0.25:
        status = "warn"
        errors.append(f"Elevated error rate: {error_rate:.2%} of recent runs failed")

    snapshot_info = {
        "age_sec": age_sec,
        "total_count": total_count,
        "error_rate": error_rate,
        "latest_status": latest_status,
    }

    return status, snapshot_info, errors


def _extract_status_from_snapshot(snapshot_data: dict) -> Optional[str]:
    """
    Extract status from snapshot data (flexible parsing).

    Returns:
        "ok", "error", or None if status cannot be determined
    """
    # Try various common status field names
    for key in ["status", "run_status", "pipeline_status", "result"]:
        if key in snapshot_data:
            val = snapshot_data[key]
            if isinstance(val, str):
                val_lower = val.lower()
                if val_lower in ["ok", "success", "completed"]:
                    return "ok"
                elif val_lower in ["error", "failed", "failure"]:
                    return "error"

    # Check for errors field
    if "errors" in snapshot_data:
        errors = snapshot_data["errors"]
        if isinstance(errors, list) and len(errors) > 0:
            return "error"
        elif errors:  # Non-empty string or other truthy value
            return "error"

    # Default: assume ok if no error indicators
    return "ok"


def _calculate_error_rate(snapshot_files: List[Path], errors: List[str]) -> float:
    """
    Calculate error rate from recent snapshot files.

    Returns:
        Float between 0.0 and 1.0 representing error rate
    """
    if not snapshot_files:
        return 0.0

    error_count = 0
    valid_count = 0

    for snapshot_file in snapshot_files:
        try:
            with open(snapshot_file, "r") as f:
                data = json.load(f)

            status = _extract_status_from_snapshot(data)
            valid_count += 1

            if status == "error":
                error_count += 1

        except Exception as e:
            # If we can't read a snapshot, skip it (don't count as error or success)
            pass

    if valid_count == 0:
        return 0.0

    return error_count / valid_count


def _determine_overall_status(components: Dict[str, str]) -> str:
    """
    Determine overall system status from component statuses.

    Rules:
    - If any component is "error" → "error"
    - Else if any component is "warn" → "warn"
    - Else → "ok"
    """
    has_error = any(status == "error" for status in components.values())
    has_warn = any(status == "warn" for status in components.values())

    if has_error:
        return "error"
    elif has_warn:
        return "warn"
    else:
        return "ok"


def render_health_text(health: dict) -> str:
    """
    Convert health dict to human-readable text report.

    Args:
        health: Health dictionary from gather_health()

    Returns:
        Formatted multi-line text report
    """
    lines = []

    # Header
    lines.append("=" * 58)
    lines.append("          Hands-Off System Health Report")
    lines.append("=" * 58)

    # Status
    status = health["status"].upper()
    status_symbol = "✓" if status == "OK" else ("⚠" if status == "WARN" else "✗")
    lines.append(f"Status: {status_symbol} {status}")

    # Metadata
    lines.append(f"Generated: {health['generated_at']}")
    lines.append(f"State Directory: {health['state_dir']}/")
    lines.append("")

    # Components
    lines.append("Components:")
    for component, status in health["components"].items():
        symbol = _status_symbol(status)
        lines.append(f"  {symbol} {component}: {status}")
    lines.append("")

    # Checks
    lines.append("Checks:")
    checks = health["checks"]

    if checks.get("latest_snapshot_age_sec") is not None:
        age = checks["latest_snapshot_age_sec"]
        lines.append(f"  Latest snapshot age: {_format_age(age)}")
    else:
        lines.append("  Latest snapshot age: N/A")

    if checks.get("latest_fetch_age_sec") is not None:
        age = checks["latest_fetch_age_sec"]
        lines.append(f"  Latest fetch age: {_format_age(age)}")

    lines.append(f"  Total snapshots: {checks['num_snapshots']}")

    error_rate = checks["recent_error_rate"]
    lines.append(f"  Recent error rate (20 runs): {error_rate:.2%}")

    latest_status = checks.get("most_recent_run_status")
    if latest_status:
        lines.append(f"  Latest run status: {latest_status}")

    lines.append("")

    # Errors
    errors = health.get("errors", [])
    if errors:
        lines.append("Errors:")
        for error in errors:
            lines.append(f"  • {error}")
    else:
        lines.append("No errors detected.")

    lines.append("=" * 58)

    return "\n".join(lines)


def _status_symbol(status: str) -> str:
    """Return a unicode symbol for the given status."""
    if status == "ok":
        return "✓"
    elif status == "warn":
        return "⚠"
    elif status == "error":
        return "✗"
    else:
        return "?"


def _format_age(seconds: int) -> str:
    """Format age in seconds to human-readable string."""
    if seconds < 60:
        return f"{seconds}s"
    elif seconds < 3600:
        minutes = seconds // 60
        return f"{minutes}m {seconds % 60}s"
    elif seconds < 86400:
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        return f"{hours}h {minutes}m"
    else:
        days = seconds // 86400
        hours = (seconds % 86400) // 3600
        return f"{days}d {hours}h"


def write_health_json(state_dir: str, health: dict) -> str:
    """
    Write health data to JSON file in state directory.

    Args:
        state_dir: Path to state directory
        health: Health dictionary from gather_health()

    Returns:
        Path to the written JSON file
    """
    state_path = Path(state_dir)
    state_path.mkdir(parents=True, exist_ok=True)

    output_file = state_path / "hands_off_health.json"

    with open(output_file, "w") as f:
        json.dump(health, f, indent=2)

    return str(output_file)


def main():
    """CLI entry point for health check tool."""
    parser = argparse.ArgumentParser(
        description="Hands-Off Engine Health Check Tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    parser.add_argument(
        "--state-dir",
        default="state",
        help="Path to state directory (default: state)",
    )

    parser.add_argument(
        "--write-json",
        action="store_true",
        help="Write health data to JSON file",
    )

    args = parser.parse_args()

    # Gather health information
    health = gather_health(state_dir=args.state_dir)

    # Print human-readable report
    print(render_health_text(health))

    # Write JSON if requested
    if args.write_json:
        output_path = write_health_json(args.state_dir, health)
        print(f"\nHealth data written to: {output_path}")

    # Exit with appropriate code
    status = health["status"]
    if status == "error":
        sys.exit(1)
    elif status == "warn":
        sys.exit(0)  # Warnings don't cause failure
    else:
        sys.exit(0)


if __name__ == "__main__":
    main()
