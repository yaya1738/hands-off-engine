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


def _safe_read_json(path: Path) -> Optional[Dict]:
    """Safely read JSON file, returning None if not found or invalid."""
    if not path.exists():
        return None

    try:
        with open(path, 'r') as f:
            return json.load(f)
    except (json.JSONDecodeError, Exception):
        return None


def _determine_overall_status(
    health_data: Optional[Dict],
    loop_data: Optional[Dict],
    summary_data: Optional[Dict]
) -> str:
    """Determine overall system status from components."""
    # Check health status
    if health_data:
        health_status = health_data.get("status", "unknown")
        if health_status in ["critical", "error"]:
            return "critical"
        elif health_status in ["warning", "degraded"]:
            return "warning"

    # Check loop status
    if loop_data:
        loop_status = loop_data.get("status", "unknown")
        if loop_status in ["error", "failed"]:
            return "warning"

    # Check summary status
    if summary_data:
        summary_status = summary_data.get("status", "unknown")
        if summary_status in ["error"]:
            return "warning"

    # If we have no data, status is unknown
    if not health_data and not loop_data and not summary_data:
        return "unknown"

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
        "loop": state_path / "hands_off_ai_loop.json"
    }

    # Read all source files
    summary_data = _safe_read_json(sources["summary"])
    history_data = _safe_read_json(sources["history"])
    health_data = _safe_read_json(sources["health"])
    loop_data = _safe_read_json(sources["loop"])

    # Track which sources were found
    source_status = {}
    for name, path in sources.items():
        if path.exists():
            source_status[name] = "found"
        else:
            source_status[name] = "missing"
            errors.append(f"Missing source file: {path.name}")

    # Determine overall status
    overall_status = _determine_overall_status(health_data, loop_data, summary_data)

    # Build health section
    if health_data:
        health_section = {
            "status": health_data.get("status", "unknown"),
            "components": health_data.get("components", {}),
            "last_check": health_data.get("generated_at")
        }
    else:
        health_section = {
            "status": "unknown",
            "components": {},
            "last_check": None
        }

    # Build polymarket section from summary
    if summary_data:
        polymarket_section = {
            "mode": summary_data.get("mode", "DRYRUN"),
            "positions": summary_data.get("positions", []),
            "orders": summary_data.get("orders", []),
            "balance": summary_data.get("balance", 0)
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
            "cycles": loop_data.get("cycles", 0)
        }
    else:
        loop_section = {
            "status": "unknown",
            "last_run": None,
            "cycles": 0
        }

    # Build history section
    if history_data:
        history_section = {
            "events": history_data.get("events", []),
            "trends": history_data.get("trends", {}),
            "last_update": history_data.get("generated_at")
        }
    else:
        history_section = {
            "events": [],
            "trends": {},
            "last_update": None
        }

    # Add notes
    notes.append(f"Brain summary generated from {sum(1 for s in source_status.values() if s == 'found')} sources")

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
        f.write("HANDS-OFF ENGINE BRAIN SUMMARY\n")
        f.write("=" * 60 + "\n")
        f.write(f"Generated: {brain_data['generated_at']}\n")
        f.write(f"Status: {brain_data['status']}\n")
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

    print(f"Brain summary generated: {result['output_files']}")
