#!/usr/bin/env python3
"""
Hands-Off Brain Summary - Top-Level View

Consolidates all key state files into a unified "brain" view:
  - hands_off_health.json
  - hands_off_summary.json
  - hands_off_history_summary.json
  - hands_off_ai_loop.json

Produces:
  - hands_off_brain.json - unified JSON view
  - hands_off_brain.txt - human-readable text report

STATUS DERIVATION RULES:
  1. If health.status == "error" → overall status = "error"
  2. Else if recent error rate > 0.25 → status = "warn"
  3. Else → status = "ok"

  Fallback: If health file is missing, derive from history/ai_loop status.

DRYRUN-ONLY: Read-mostly plus local file writes. No trading, no network.
"""

import json
import os
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List


def _safe_read_json(file_path: str) -> tuple[Optional[Dict[str, Any]], Optional[str]]:
    """
    Safely read a JSON file, returning (data, error_message).

    Returns:
        (dict, None) if successful
        (None, error_str) if file missing or malformed
    """
    if not os.path.exists(file_path):
        return None, f"File not found: {file_path}"

    try:
        with open(file_path, 'r') as f:
            data = json.load(f)
        return data, None
    except json.JSONDecodeError as e:
        return None, f"Malformed JSON in {file_path}: {e}"
    except Exception as e:
        return None, f"Error reading {file_path}: {e}"


def _determine_overall_status(
    health_status: Optional[str],
    error_rate: Optional[float]
) -> str:
    """
    Determine overall system status based on health and error rate.

    Rules:
      1. If health_status == "error" → "error"
      2. Else if error_rate > 0.25 → "warn"
      3. Else → "ok"
    """
    if health_status == "error":
        return "error"

    if error_rate is not None and error_rate > 0.25:
        return "warn"

    return "ok"


def _extract_health_section(
    health_data: Optional[Dict[str, Any]],
    errors: List[str]
) -> Dict[str, Any]:
    """Extract health information from hands_off_health.json"""
    if health_data is None:
        return {
            "status": None,
            "recent_error_rate": None,
            "latest_snapshot_age_sec": None
        }

    try:
        status = health_data.get("overall_status", "unknown")
        error_rate = health_data.get("error_rate", 0.0)

        # Try to calculate snapshot age
        last_check = health_data.get("last_check_ts")
        age_sec = None
        if last_check:
            try:
                last_dt = datetime.fromisoformat(last_check.replace('Z', '+00:00'))
                now_dt = datetime.now(timezone.utc)
                age_sec = int((now_dt - last_dt).total_seconds())
            except:
                pass

        return {
            "status": status,
            "recent_error_rate": error_rate,
            "latest_snapshot_age_sec": age_sec
        }
    except Exception as e:
        errors.append(f"Error parsing health data: {e}")
        return {
            "status": None,
            "recent_error_rate": None,
            "latest_snapshot_age_sec": None
        }


def _extract_polymarket_section(
    summary_data: Optional[Dict[str, Any]],
    errors: List[str]
) -> Dict[str, Any]:
    """Extract Polymarket information from hands_off_summary.json"""
    if summary_data is None:
        return {
            "num_markets": None,
            "num_orders": None,
            "current_pm_balance": None,
            "target_pm_balance": None,
            "mode": "DRYRUN"
        }

    try:
        # Summary file structure may vary; extract what we can
        execution = summary_data.get("execution", {})
        decision = summary_data.get("decision", {})

        num_markets = len(summary_data.get("markets", []))
        num_orders = len(execution.get("orders", []))

        current_balance = summary_data.get("current_pm_balance")
        target_balance = summary_data.get("target_pm_balance")

        # If balances are in decision or execution sections
        if current_balance is None:
            current_balance = decision.get("current_pm_balance") or execution.get("current_pm_balance")
        if target_balance is None:
            target_balance = decision.get("target_pm_balance") or execution.get("target_pm_balance")

        mode = summary_data.get("mode", "DRYRUN")

        return {
            "num_markets": num_markets if num_markets > 0 else None,
            "num_orders": num_orders if num_orders > 0 else None,
            "current_pm_balance": current_balance,
            "target_pm_balance": target_balance,
            "mode": mode
        }
    except Exception as e:
        errors.append(f"Error parsing summary data: {e}")
        return {
            "num_markets": None,
            "num_orders": None,
            "current_pm_balance": None,
            "target_pm_balance": None,
            "mode": "DRYRUN"
        }


def _extract_loop_section(
    loop_data: Optional[Dict[str, Any]],
    errors: List[str]
) -> Dict[str, Any]:
    """Extract AI loop information from hands_off_ai_loop.json"""
    if loop_data is None:
        return {
            "last_cycle_status": None,
            "last_cycle_ts": None,
            "recent_cycles": None
        }

    try:
        status = loop_data.get("status", "unknown")
        timestamp = loop_data.get("timestamp") or loop_data.get("last_run_ts")

        # Try to get cycle count from loop metadata
        cycles = loop_data.get("total_cycles") or loop_data.get("cycle_count")

        return {
            "last_cycle_status": status,
            "last_cycle_ts": timestamp,
            "recent_cycles": cycles
        }
    except Exception as e:
        errors.append(f"Error parsing AI loop data: {e}")
        return {
            "last_cycle_status": None,
            "last_cycle_ts": None,
            "recent_cycles": None
        }


def _extract_history_section(
    history_data: Optional[Dict[str, Any]],
    errors: List[str]
) -> Dict[str, Any]:
    """Extract history/trend information from hands_off_history_summary.json"""
    if history_data is None:
        return {
            "total_runs": None,
            "error_rate": None,
            "pm_balance_delta_recent": None
        }

    try:
        total_runs = history_data.get("total_runs", 0)
        error_rate = history_data.get("error_rate", 0.0)

        # Extract recent balance delta if available
        balance_delta = history_data.get("pm_balance_delta") or history_data.get("recent_balance_change")

        return {
            "total_runs": total_runs,
            "error_rate": error_rate,
            "pm_balance_delta_recent": balance_delta
        }
    except Exception as e:
        errors.append(f"Error parsing history data: {e}")
        return {
            "total_runs": None,
            "error_rate": None,
            "pm_balance_delta_recent": None
        }


def _generate_notes(
    health: Dict[str, Any],
    polymarket: Dict[str, Any],
    loop: Dict[str, Any],
    history: Dict[str, Any],
    overall_status: str
) -> List[str]:
    """Generate human-readable notes based on current state"""
    notes = []

    # Health notes
    if health.get("status") == "error":
        notes.append("Health check reporting errors - investigation needed")
    elif health.get("status") == "warn":
        notes.append("Health check reporting warnings")

    # Error rate notes
    error_rate = history.get("error_rate") or health.get("recent_error_rate")
    if error_rate is not None:
        if error_rate > 0.25:
            notes.append(f"High error rate: {error_rate*100:.1f}%")
        elif error_rate > 0.10:
            notes.append(f"Moderate error rate: {error_rate*100:.1f}%")

    # Balance notes
    current_bal = polymarket.get("current_pm_balance")
    target_bal = polymarket.get("target_pm_balance")
    if current_bal is not None and target_bal is not None:
        diff = current_bal - target_bal
        if abs(diff) > target_bal * 0.1:  # More than 10% off target
            notes.append(f"PM balance off target by ${abs(diff):.2f}")

    # Loop notes
    if loop.get("last_cycle_status") == "error":
        notes.append("Last AI loop cycle failed")

    # Default healthy note
    if not notes and overall_status == "ok":
        notes.append("System healthy; error rate within normal bounds")

    return notes


def build_brain_summary(state_dir: str = "state") -> Dict[str, Any]:
    """
    Read top-level state files from <state_dir> and build a unified
    'brain summary' dict. Never raises on missing/malformed files;
    instead records problems in an 'errors' list inside the result.

    Returns a dict suitable for JSON serialization.
    """
    errors: List[str] = []

    # Define file paths
    health_path = os.path.join(state_dir, "hands_off_health.json")
    summary_path = os.path.join(state_dir, "hands_off_summary.json")
    history_path = os.path.join(state_dir, "hands_off_history_summary.json")
    loop_path = os.path.join(state_dir, "hands_off_ai_loop.json")

    # Read all files safely
    health_data, health_err = _safe_read_json(health_path)
    summary_data, summary_err = _safe_read_json(summary_path)
    history_data, history_err = _safe_read_json(history_path)
    loop_data, loop_err = _safe_read_json(loop_path)

    # Track source statuses
    sources = {
        "summary": "ok" if summary_err is None else ("missing" if "not found" in summary_err else "error"),
        "history": "ok" if history_err is None else ("missing" if "not found" in history_err else "error"),
        "health": "ok" if health_err is None else ("missing" if "not found" in health_err else "error"),
        "ai_loop": "ok" if loop_err is None else ("missing" if "not found" in loop_err else "error")
    }

    # Collect errors
    for err in [health_err, summary_err, history_err, loop_err]:
        if err:
            errors.append(err)

    # Extract sections
    health = _extract_health_section(health_data, errors)
    polymarket = _extract_polymarket_section(summary_data, errors)
    loop = _extract_loop_section(loop_data, errors)
    history = _extract_history_section(history_data, errors)

    # Determine overall status
    health_status = health.get("status")
    error_rate = history.get("error_rate") or health.get("recent_error_rate")
    overall_status = _determine_overall_status(health_status, error_rate)

    # Generate notes
    notes = _generate_notes(health, polymarket, loop, history, overall_status)

    # Build final summary
    summary = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "state_dir": state_dir,
        "status": overall_status,
        "sources": sources,
        "health": health,
        "polymarket": polymarket,
        "loop": loop,
        "history": history,
        "notes": notes,
        "errors": errors
    }

    return summary


def _format_text_report(summary: Dict[str, Any]) -> str:
    """Format brain summary as human-readable text"""
    lines = []
    lines.append("=" * 60)
    lines.append("Hands-Off Brain Summary")
    lines.append("=" * 60)
    lines.append(f"Generated: {summary['generated_at']}")
    lines.append(f"State dir: {summary['state_dir']}")
    lines.append("")
    lines.append(f"Overall Status: {summary['status'].upper()}")
    lines.append("")

    # Health section
    health = summary['health']
    lines.append("Health:")
    lines.append(f"  Status: {health['status'] or 'unknown'}")
    if health['recent_error_rate'] is not None:
        lines.append(f"  Recent error rate: {health['recent_error_rate']*100:.1f}%")
    if health['latest_snapshot_age_sec'] is not None:
        lines.append(f"  Latest snapshot age: {health['latest_snapshot_age_sec']}s")
    lines.append("")

    # Polymarket section
    pm = summary['polymarket']
    lines.append("Polymarket:")
    lines.append(f"  Mode: {pm['mode']}")
    if pm['num_markets'] is not None:
        lines.append(f"  Markets: {pm['num_markets']}")
    if pm['num_orders'] is not None:
        lines.append(f"  Orders: {pm['num_orders']}")
    if pm['current_pm_balance'] is not None:
        lines.append(f"  Current PM balance: ${pm['current_pm_balance']:.2f}")
    if pm['target_pm_balance'] is not None:
        lines.append(f"  Target PM balance:  ${pm['target_pm_balance']:.2f}")
    lines.append("")

    # Loop section
    loop = summary['loop']
    lines.append("Loop:")
    if loop['last_cycle_status']:
        lines.append(f"  Last cycle: {loop['last_cycle_status']} at {loop['last_cycle_ts'] or 'unknown time'}")
    if loop['recent_cycles'] is not None:
        lines.append(f"  Recent cycles counted: {loop['recent_cycles']}")
    if loop['last_cycle_status'] is None:
        lines.append("  No loop data available")
    lines.append("")

    # History section
    hist = summary['history']
    lines.append("History:")
    if hist['total_runs'] is not None:
        lines.append(f"  Total runs: {hist['total_runs']}")
    if hist['error_rate'] is not None:
        lines.append(f"  Error rate: {hist['error_rate']*100:.1f}%")
    if hist['pm_balance_delta_recent'] is not None:
        delta = hist['pm_balance_delta_recent']
        sign = "+" if delta >= 0 else ""
        lines.append(f"  PM balance delta (recent): {sign}${delta:.2f}")
    if hist['total_runs'] is None:
        lines.append("  No history data available")
    lines.append("")

    # Notes
    lines.append("Notes:")
    if summary['notes']:
        for note in summary['notes']:
            lines.append(f"  - {note}")
    else:
        lines.append("  (none)")
    lines.append("")

    # Errors
    lines.append("Errors:")
    if summary['errors']:
        for error in summary['errors']:
            lines.append(f"  - {error}")
    else:
        lines.append("  (none)")

    lines.append("=" * 60)

    return "\n".join(lines)


def write_brain_summary(state_dir: str = "state") -> Dict[str, Any]:
    """
    High-level helper:
      - Calls build_brain_summary(...)
      - Writes JSON to <state_dir>/hands_off_brain.json
      - Writes a text report to <state_dir>/hands_off_brain.txt
      - Returns the summary dict
    """
    # Build summary
    summary = build_brain_summary(state_dir)

    # Ensure state directory exists
    os.makedirs(state_dir, exist_ok=True)

    # Write JSON
    json_path = os.path.join(state_dir, "hands_off_brain.json")
    with open(json_path, 'w') as f:
        json.dump(summary, f, indent=2)

    # Write text report
    txt_path = os.path.join(state_dir, "hands_off_brain.txt")
    text_report = _format_text_report(summary)
    with open(txt_path, 'w') as f:
        f.write(text_report)

    return summary


def main():
    """CLI entrypoint"""
    import argparse

    parser = argparse.ArgumentParser(
        description="Generate unified brain summary from state files"
    )
    parser.add_argument(
        "--state-dir",
        default="state",
        help="State directory to read from and write to (default: state)"
    )

    args = parser.parse_args()

    try:
        summary = write_brain_summary(args.state_dir)
        status = summary['status']
        print(f"Brain summary written to {args.state_dir}/hands_off_brain.json (status={status})")
        return 0
    except Exception as e:
        print(f"ERROR: Failed to generate brain summary: {e}")
        return 1


if __name__ == "__main__":
    import sys
    sys.exit(main())
