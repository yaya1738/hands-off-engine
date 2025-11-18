#!/usr/bin/env python3
"""
Hands-Off Engine - History & Performance Analytics

This module provides analytics over historical snapshots written by the scheduler.
It reads snapshots from state/history/*.json and produces:
  1. Aggregated metrics (total runs, error rates, Polymarket trends, etc.)
  2. Human-readable text report
  3. JSON summary export

SAFETY: DRYRUN-only, read-only filesystem operations (no trading, no external calls).
"""

import json
import os
import argparse
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional


def load_snapshots(state_dir: str = "state") -> List[Dict[str, Any]]:
    """
    Load all snapshot JSON files from <state_dir>/history/.

    Returns:
        List of snapshot dicts, sorted by timestamp (oldest to newest).
        Malformed or invalid files are skipped with a warning.
    """
    history_dir = Path(state_dir) / "history"

    if not history_dir.exists():
        return []

    snapshots = []
    json_files = sorted(history_dir.glob("*.json"))

    for json_file in json_files:
        try:
            with open(json_file, 'r') as f:
                data = json.load(f)

            # Basic validation: must have timestamp
            if "timestamp" not in data:
                print(f"Warning: Skipping {json_file.name} - missing 'timestamp' field")
                continue

            snapshots.append(data)

        except json.JSONDecodeError as e:
            print(f"Warning: Skipping {json_file.name} - invalid JSON: {e}")
            continue
        except Exception as e:
            print(f"Warning: Skipping {json_file.name} - error: {e}")
            continue

    # Sort by timestamp
    snapshots.sort(key=lambda x: x.get("timestamp", ""))

    return snapshots


def summarize_history(state_dir: str = "state", window_size: int = 20) -> Dict[str, Any]:
    """
    Core API: Aggregates historical snapshots into a summary dict.

    Args:
        state_dir: Path to state directory (default: "state")
        window_size: Number of recent snapshots to analyze separately (default: 20)

    Returns:
        Dict with aggregated metrics:
          - generated_at: ISO8601 timestamp
          - state_dir: path used
          - total_runs: number of valid snapshots
          - status_counts: dict of status -> count
          - error_rate: fraction of runs with status != "ok"
          - first_timestamp, last_timestamp: ISO8601 strings
          - polymarket: min/avg/max metrics for markets, orders, balance
          - recent_window_size: window size used
          - recent: metrics for last N snapshots
    """
    snapshots = load_snapshots(state_dir)

    total_runs = len(snapshots)

    # Initialize summary structure
    summary = {
        "generated_at": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
        "state_dir": state_dir,
        "total_runs": total_runs,
    }

    # Handle empty case
    if total_runs == 0:
        summary.update({
            "status_counts": {},
            "error_rate": 0.0,
            "first_timestamp": None,
            "last_timestamp": None,
            "polymarket": {},
            "recent_window_size": window_size,
            "recent": {
                "runs": 0,
                "status_counts": {},
                "error_rate": 0.0,
                "pm_balance_delta": None
            }
        })
        return summary

    # Global metrics
    status_counts = {}
    for snapshot in snapshots:
        status = snapshot.get("status", "unknown")
        status_counts[status] = status_counts.get(status, 0) + 1

    error_count = sum(count for status, count in status_counts.items() if status != "ok")
    error_rate = error_count / total_runs if total_runs > 0 else 0.0

    first_timestamp = snapshots[0].get("timestamp", "unknown")
    last_timestamp = snapshots[-1].get("timestamp", "unknown")

    # Polymarket metrics aggregation
    pm_metrics = {
        "num_markets": [],
        "num_orders": [],
        "current_pm_balance": []
    }

    for snapshot in snapshots:
        pm_data = snapshot.get("polymarket", {})

        if "num_markets" in pm_data:
            pm_metrics["num_markets"].append(pm_data["num_markets"])
        if "num_orders" in pm_data:
            pm_metrics["num_orders"].append(pm_data["num_orders"])
        if "current_pm_balance" in pm_data:
            pm_metrics["current_pm_balance"].append(pm_data["current_pm_balance"])

    # Compute min/avg/max for Polymarket metrics
    polymarket_summary = {}
    for metric_name, values in pm_metrics.items():
        if values:
            polymarket_summary[f"{metric_name}_min"] = min(values)
            polymarket_summary[f"{metric_name}_max"] = max(values)
            polymarket_summary[f"{metric_name}_avg"] = round(sum(values) / len(values), 2)

    # Recent window analysis
    recent_snapshots = snapshots[-window_size:] if total_runs > window_size else snapshots
    recent_runs = len(recent_snapshots)

    recent_status_counts = {}
    for snapshot in recent_snapshots:
        status = snapshot.get("status", "unknown")
        recent_status_counts[status] = recent_status_counts.get(status, 0) + 1

    recent_error_count = sum(count for status, count in recent_status_counts.items() if status != "ok")
    recent_error_rate = recent_error_count / recent_runs if recent_runs > 0 else 0.0

    # Balance delta in recent window
    pm_balance_delta = None
    recent_balances = [
        s.get("polymarket", {}).get("current_pm_balance")
        for s in recent_snapshots
        if s.get("polymarket", {}).get("current_pm_balance") is not None
    ]
    if len(recent_balances) >= 2:
        pm_balance_delta = round(recent_balances[-1] - recent_balances[0], 2)

    # Assemble final summary
    summary.update({
        "status_counts": status_counts,
        "error_rate": round(error_rate, 4),
        "first_timestamp": first_timestamp,
        "last_timestamp": last_timestamp,
        "polymarket": polymarket_summary,
        "recent_window_size": window_size,
        "recent": {
            "runs": recent_runs,
            "status_counts": recent_status_counts,
            "error_rate": round(recent_error_rate, 4),
            "pm_balance_delta": pm_balance_delta
        }
    })

    return summary


def render_history_report(state_dir: str = "state", window_size: int = 20) -> str:
    """
    Generate a human-readable text report from historical snapshots.

    Args:
        state_dir: Path to state directory (default: "state")
        window_size: Number of recent snapshots to analyze separately (default: 20)

    Returns:
        Formatted text report suitable for CLI/logs.
    """
    summary = summarize_history(state_dir, window_size)

    lines = []
    lines.append("=" * 70)
    lines.append("  HANDS-OFF ENGINE - HISTORY & PERFORMANCE ANALYTICS")
    lines.append("=" * 70)
    lines.append(f"Generated at:  {summary['generated_at']}")
    lines.append(f"State dir:     {summary['state_dir']}")
    lines.append("")

    # Overall runs section
    lines.append("-" * 70)
    lines.append("OVERALL RUNS")
    lines.append("-" * 70)

    if summary["total_runs"] == 0:
        lines.append("No historical snapshots found.")
        lines.append("")
        lines.append("The scheduler has not yet written any history snapshots.")
        lines.append("Run the autoloop/scheduler to generate snapshots in state/history/.")
    else:
        lines.append(f"Total runs:    {summary['total_runs']}")
        lines.append(f"Time range:    {summary['first_timestamp']} → {summary['last_timestamp']}")
        lines.append("")
        lines.append("Status breakdown:")
        for status, count in sorted(summary["status_counts"].items()):
            percentage = (count / summary["total_runs"]) * 100
            lines.append(f"  {status:12s}  {count:4d} runs  ({percentage:5.1f}%)")
        lines.append("")
        lines.append(f"Error rate:    {summary['error_rate']:.2%}")

        # Polymarket metrics section
        if summary["polymarket"]:
            lines.append("")
            lines.append("-" * 70)
            lines.append("POLYMARKET METRICS")
            lines.append("-" * 70)

            pm = summary["polymarket"]

            if "current_pm_balance_min" in pm:
                lines.append(f"Current PM balance:")
                lines.append(f"  Min:  ${pm['current_pm_balance_min']:,.2f}")
                lines.append(f"  Avg:  ${pm['current_pm_balance_avg']:,.2f}")
                lines.append(f"  Max:  ${pm['current_pm_balance_max']:,.2f}")
                lines.append("")

            if "num_markets_min" in pm:
                lines.append(f"Number of markets:")
                lines.append(f"  Min:  {pm['num_markets_min']}")
                lines.append(f"  Avg:  {pm['num_markets_avg']:.1f}")
                lines.append(f"  Max:  {pm['num_markets_max']}")
                lines.append("")

            if "num_orders_min" in pm:
                lines.append(f"Number of orders:")
                lines.append(f"  Min:  {pm['num_orders_min']}")
                lines.append(f"  Avg:  {pm['num_orders_avg']:.1f}")
                lines.append(f"  Max:  {pm['num_orders_max']}")

        # Recent window section
        lines.append("")
        lines.append("-" * 70)
        lines.append(f"RECENT {summary['recent']['runs']} RUNS (window size: {window_size})")
        lines.append("-" * 70)

        recent = summary["recent"]
        lines.append(f"Recent error rate:  {recent['error_rate']:.2%}")
        lines.append("")
        lines.append("Recent status breakdown:")
        for status, count in sorted(recent["status_counts"].items()):
            percentage = (count / recent["runs"]) * 100
            lines.append(f"  {status:12s}  {count:4d} runs  ({percentage:5.1f}%)")

        if recent["pm_balance_delta"] is not None:
            lines.append("")
            delta = recent["pm_balance_delta"]
            sign = "+" if delta >= 0 else ""
            lines.append(f"PM balance change:  {sign}${delta:,.2f}")

    lines.append("")
    lines.append("=" * 70)

    return "\n".join(lines)


def write_history_summary(state_dir: str = "state", window_size: int = 20) -> str:
    """
    Compute the history summary and write it to <state_dir>/hands_off_history_summary.json.

    Args:
        state_dir: Path to state directory (default: "state")
        window_size: Number of recent snapshots to analyze separately (default: 20)

    Returns:
        Path to the written summary file.
    """
    summary = summarize_history(state_dir, window_size)

    # Ensure state directory exists
    state_path = Path(state_dir)
    state_path.mkdir(parents=True, exist_ok=True)

    output_path = state_path / "hands_off_history_summary.json"

    # Atomic write pattern: write to temp file, then rename
    with tempfile.NamedTemporaryFile(
        mode='w',
        dir=state_path,
        delete=False,
        suffix='.tmp'
    ) as tmp_file:
        json.dump(summary, tmp_file, indent=2)
        tmp_file.write('\n')
        tmp_path = tmp_file.name

    # Atomic rename
    os.rename(tmp_path, output_path)

    return str(output_path)


def main():
    """CLI entry point for history analytics."""
    parser = argparse.ArgumentParser(
        description="Hands-Off Engine - History & Performance Analytics",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Print human-readable history report
  python3 reports/ho_history_report.py

  # Use custom state directory and window size
  python3 reports/ho_history_report.py --state-dir state --window 50

  # Write JSON summary file
  python3 reports/ho_history_report.py --write-json
        """
    )

    parser.add_argument(
        "--state-dir",
        default="state",
        help="Path to state directory (default: state)"
    )

    parser.add_argument(
        "--window",
        type=int,
        default=20,
        help="Recent window size for analysis (default: 20)"
    )

    parser.add_argument(
        "--write-json",
        action="store_true",
        help="Write JSON summary to <state-dir>/hands_off_history_summary.json"
    )

    args = parser.parse_args()

    try:
        if args.write_json:
            # Write JSON summary
            output_path = write_history_summary(args.state_dir, args.window)
            print(f"History summary written to: {output_path}")
        else:
            # Print human-readable report
            report = render_history_report(args.state_dir, args.window)
            print(report)

        return 0

    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit(main())
