#!/usr/bin/env python3
"""
Batch 18: Brain Summary
Unifies system state into a single "brain input" file.

Brain report that:
- Reads multiple state files
- Consolidates into unified view
- Determines overall status
- Writes JSON and text outputs
"""

import json
import argparse
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, Any, Optional


def _safe_read_json(path):
    """Safely read JSON. Returns (data, error)."""
    path = Path(path)

    if not path.exists():
        return None, "file not found"

    try:
        with open(path, "r") as f:
            return json.load(f), None
    except json.JSONDecodeError:
        return None, "malformed json"
    except Exception as e:
        return None, str(e)


def _determine_overall_status(
    health_data,
    loop_data=None,
    summary_data=None,
    history_data=None
) -> str:
    """Determine overall system status.

    Supports both:
    _determine_overall_status(health_dict, loop_dict, summary_dict)
    and legacy:
    _determine_overall_status(status, error_rate)
    """

    # Legacy test contract
    if isinstance(health_data, str):
        status = health_data
        error_rate = loop_data if isinstance(loop_data, (int, float)) else 0

        if status in ("error", "critical"):
            return "error"
        if error_rate > 0.25:
            return "warn"
        return "ok"

    if isinstance(health_data, (int, float)):
        return "warn" if health_data > 0.25 else "ok"

    if health_data:
        status = health_data.get("status", health_data.get("overall_status", "unknown"))
        if status in ["critical", "error"]:
            return "error"
        if status in ["warning", "degraded", "warn"]:
            return "warn"

    if isinstance(loop_data, (int, float)):
        return "warn" if loop_data > 0.25 else "ok"

    if loop_data:
        status = loop_data.get("status", "unknown")
        if status in ["error", "failed"]:
            return "error"

    if summary_data:
        if summary_data.get("status") == "error":
            return "warn"

    if history_data:
        error_rate = history_data.get("error_rate", 0)
        if error_rate > 0.25:
            return "warn"

    if not health_data and not loop_data and not summary_data and not history_data:
        return "ok"

    return "ok"


def build_brain_summary(state_dir: str) -> Dict:
    """
    Build unified brain summary from state files.

    Args:
        state_dir: Directory containing state files

    Returns:
        Brain summary dict
    """
    state_path = Path(state_dir)
    errors = []
    notes = []

    # Define source files
    sources = {
        "summary": state_path / "hands_off_summary.json",
        "history": state_path / "hands_off_history_summary.json",
        "health": state_path / "hands_off_health.json",
        "ai_loop": state_path / "hands_off_ai_loop.json",
        "loop": state_path / "hands_off_ai_loop.json"
    }

    # Read all source files
    summary_data, summary_error = _safe_read_json(sources["summary"])
    history_data, history_error = _safe_read_json(sources["history"])
    health_data, health_error = _safe_read_json(sources["health"])
    loop_data, loop_error = _safe_read_json(sources["loop"])

    # Track which sources were found
    source_status = {}
    for name, path in sources.items():
        data, err = _safe_read_json(path)
        if data is not None:
            source_status[name] = "ok"
        elif err and "malformed" in err:
            source_status[name] = "error"
            errors.append(err)
        else:
            source_status[name] = "missing"
            errors.append(err or f"missing {path.name}")

    # Determine overall status
    overall_status = _determine_overall_status(
        health_data,
        loop_data,
        summary_data,
        history_data
    )

    # Build health section
    if health_data:
        health_section = {
            "status": health_data.get("status", health_data.get("overall_status", "ok")),
            "components": health_data.get("components", {}),
            "last_check": health_data.get("generated_at"),
            "recent_error_rate": health_data.get("error_rate", 0),
            "latest_snapshot_age_sec": health_data.get("latest_snapshot_age_sec", 0)
        }
    else:
        health_section = {
            "status": "ok",
            "components": {},
            "last_check": None
        }

    # Build polymarket section from summary
    if summary_data:
        polymarket_section = {
            "mode": summary_data.get("mode", "DRYRUN"),
            "positions": summary_data.get("positions", []),
            "orders": summary_data.get("execution", {}).get("orders", []),
            "balance": summary_data.get("balance", 0),
            "num_markets": summary_data.get("num_markets", len(summary_data.get("markets", []))),
            "num_orders": summary_data.get("num_orders", len(summary_data.get("execution", {}).get("orders", []))),
            "current_pm_balance": summary_data.get("current_pm_balance", summary_data.get("balance", 0)),
            "target_pm_balance": summary_data.get("target_pm_balance", 0)
        }
    else:
        polymarket_section = {
            "mode": "DRYRUN",
            "positions": [],
            "orders": [],
            "balance": 0
        }

    # Build loop section
    if loop_data:
        loop_section = {
            "status": loop_data.get("status", "unknown"),
            "last_run": loop_data.get("last_run"),
            "cycles": loop_data.get("cycles", 0),
            "last_cycle_status": loop_data.get("last_cycle_status", loop_data.get("status", "ok")),
            "recent_cycles": loop_data.get("total_cycles", loop_data.get("recent_cycles", loop_data.get("cycles", 0)))
        }
    else:
        loop_section = {
            "status": "ok",
            "last_run": None,
            "cycles": 0
        }

    # Build history section
    if history_data:
        history_section = {
            "events": history_data.get("events", []),
            "trends": history_data.get("trends", {}),
            "last_update": history_data.get("generated_at"),
            "total_runs": history_data.get("total_runs", 0),
            "error_rate": history_data.get("error_rate", 0),
            "pm_balance_delta_recent": history_data.get("pm_balance_delta_recent", history_data.get("pm_balance_delta", 0))
        }
    else:
        history_section = {
            "events": [],
            "trends": {},
            "last_update": None
        }

    # Add notes
    notes.append(f"Brain summary generated from {sum(1 for s in source_status.values() if s == 'ok')} sources")

    if overall_status == "ok":
        notes.append("System healthy")

    if history_data and history_data.get("error_rate", 0) > 0.25:
        notes.append("High error rate detected")

    elif overall_status in ("error", "critical"):
        notes.append("System error detected")


    # Build final summary
    brain_summary = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "state_dir": str(state_path),
        "status": overall_status,
        "sources": source_status,
        "health": health_section,
        "polymarket": polymarket_section,
        "loop": loop_section,
        "history": history_section,
        "notes": notes,
        "errors": errors
    }

    return brain_summary


def write_brain_summary(state_dir: str = "state") -> Dict[str, Any]:
    """
    Generate and write unified brain summary.

    Args:
        state_dir: Directory where state files are stored

    Returns:
        Dict with status info
    """
    state_path = Path(state_dir)
    state_path.mkdir(parents=True, exist_ok=True)

    # Build summary
    brain_data = build_brain_summary(state_dir)

    # Write JSON
    json_path = state_path / "hands_off_brain.json"
    with open(json_path, 'w') as f:
        json.dump(brain_data, f, indent=2)

    # Write text summary
    txt_path = state_path / "hands_off_brain.txt"
    with open(txt_path, 'w') as f:
        f.write("=" * 60 + "\n")
        f.write("Hands-Off Brain Summary\n")
        f.write("=" * 60 + "\n")
        f.write(f"Generated: {brain_data['generated_at']}\n")
        f.write(f"Overall Status: {brain_data['status']}\n")
        f.write(f"State dir: {brain_data['state_dir']}\n")
        f.write("\n")

        f.write("Sources:\n")
        for name, status in brain_data['sources'].items():
            icon = "✓" if status == "found" else "✗"
            f.write(f"  {icon} {name}: {status}\n")
        f.write("\n")

        f.write("Health:\n")
        f.write(f"  Status: {brain_data['health']['status']}\n")
        f.write("\n")

        f.write("Polymarket:\n")
        f.write(f"  Mode: {brain_data['polymarket'].get('mode')}\n")
        f.write(f"  Balance: {brain_data['polymarket'].get('balance')}\n")
        f.write("\n")

        f.write("Loop:\n")
        f.write(f"  Status: {brain_data['loop']['status']}\n")
        f.write(f"  Cycles: {brain_data['loop']['cycles']}\n")
        f.write("\n")

        if brain_data['errors']:
            f.write("Errors:\n")
            for error in brain_data['errors']:
                f.write(f"  - {error}\n")
            f.write("\n")

        f.write("=" * 60 + "\n")

    return {
        "status": "ok",
        "output_files": [str(json_path), str(txt_path)]
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Brain Summary Generator")
    parser.add_argument("--state-dir", default="state", help="State directory path")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    args = parser.parse_args()

    result = write_brain_summary(args.state_dir)

    if args.verbose:
        brain_data = build_brain_summary(args.state_dir)
        print(json.dumps(brain_data, indent=2))

    print(f"Brain summary written: {result['output_files']} status={result.get('status','unknown')}")
