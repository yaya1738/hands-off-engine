#!/usr/bin/env python3
"""
ho_autoloop.py

Hands-Off Autoloop Orchestrator for DRYRUN Polymarket pipeline.

This module provides a single entry point that:
1. Runs the DRYRUN Polymarket pipeline (alpha -> decider -> executor)
2. Generates reports and meta-summaries
3. Writes a canonical JSON summary for consumption by other systems
4. Exposes both programmatic API and CLI interface

NO LIVE EXECUTION - DRYRUN ONLY.
"""

from __future__ import annotations

import json
import sys
import traceback
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict

from reports.ho_polymarket_report import run_polymarket_pipeline_and_report


def run_all(state_dir: str = "state") -> Dict[str, Any]:
    """
    Run the full DRYRUN Polymarket pipeline and produce a meta-summary.

    This is the main orchestrator function that:
    1. Ensures state_dir exists
    2. Calls the reporting layer to run the pipeline and collect results
    3. Builds a comprehensive meta-summary structure
    4. Writes hands_off_summary.json to state_dir
    5. Returns all results for programmatic consumption

    Args:
        state_dir: Directory for state files (default: "state")

    Returns:
        Dict containing:
            - summary: The meta-summary dict written to JSON
            - report_text: Human-readable report text
            - raw: Raw pipeline/report result data

    Raises:
        Exception: Re-raises any exceptions after writing error summary to JSON
    """
    state_path = Path(state_dir)
    state_path.mkdir(parents=True, exist_ok=True)

    # Initialize meta-summary structure
    meta_summary: Dict[str, Any] = {
        "status": "ok",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "components": {
            "polymarket_alpha": "ok",
            "polymarket_decider": "ok",
            "polymarket_executor": "ok",
            "polymarket_report": "ok"
        },
        "polymarket": {
            "num_markets": 0,
            "num_orders": 0,
            "total_size_usd": 0.0,
            "current_pm_balance": 0.0,
            "target_pm_balance": 0.0,
            "mode": "DRYRUN"
        },
        "errors": []
    }

    report_text = ""
    raw_result = None

    try:
        # Run the pipeline and get results
        result = run_polymarket_pipeline_and_report(state_dir)
        raw_result = result

        # Extract report text
        report_text = result.get("report_text", "")

        # Extract summary data
        summary_data = result.get("summary", {})

        # Populate polymarket section from summary
        meta_summary["polymarket"] = {
            "num_markets": summary_data.get("num_markets", 0),
            "num_orders": summary_data.get("num_orders", 0),
            "total_size_usd": summary_data.get("total_size_usd", 0.0),
            "current_pm_balance": summary_data.get("current_pm_balance", 0.0),
            "target_pm_balance": summary_data.get("target_pm_balance", 0.0),
            "mode": summary_data.get("mode", "DRYRUN")
        }

        # All components succeeded
        meta_summary["status"] = "ok"
        meta_summary["errors"] = []

    except Exception as e:
        # Capture error and populate error summary
        error_msg = f"{type(e).__name__}: {str(e)}"
        meta_summary["status"] = "error"
        meta_summary["errors"] = [error_msg]

        # Mark all components as error (conservative approach)
        for component in meta_summary["components"]:
            meta_summary["components"][component] = "error"

        # Try to provide some context in report_text
        report_text = f"ERROR: Pipeline execution failed\n\n{error_msg}\n\n{traceback.format_exc()}"

        # Write error summary to JSON before re-raising
        summary_path = state_path / "hands_off_summary.json"
        try:
            summary_path.write_text(
                json.dumps(meta_summary, indent=2, ensure_ascii=False),
                encoding="utf-8"
            )
        except Exception as write_err:
            print(f"[ERROR] Failed to write error summary: {write_err}", file=sys.stderr)

        # Re-raise the original exception
        raise

    # Write successful summary to JSON
    summary_path = state_path / "hands_off_summary.json"
    summary_path.write_text(
        json.dumps(meta_summary, indent=2, ensure_ascii=False),
        encoding="utf-8"
    )

    # Return comprehensive result
    return {
        "summary": meta_summary,
        "report_text": report_text,
        "raw": raw_result
    }


def main():
    """
    CLI entry point for the Hands-Off Autoloop orchestrator.

    Usage:
        python3 ho_autoloop.py [state_dir]

    Example:
        python3 ho_autoloop.py state/
    """
    state_dir = sys.argv[1] if len(sys.argv) > 1 else "state"

    print("=" * 70)
    print("  Hands-Off Autoloop Orchestrator (DRYRUN)")
    print("=" * 70)
    print()

    try:
        result = run_all(state_dir)
        summary = result["summary"]

        # Print concise status summary
        print(f"Status:              {summary['status'].upper()}")
        print(f"Timestamp:           {summary['timestamp']}")
        print(f"Mode:                {summary['polymarket']['mode']}")
        print()

        # Print Polymarket metrics
        pm = summary["polymarket"]
        print("Polymarket Metrics:")
        print(f"  Markets analyzed:  {pm['num_markets']}")
        print(f"  Orders planned:    {pm['num_orders']}")
        print(f"  Total size (USD):  ${pm['total_size_usd']:,.2f}")
        print(f"  Current balance:   ${pm['current_pm_balance']:,.2f}")
        print(f"  Target balance:    ${pm['target_pm_balance']:,.2f}")
        print()

        # Print component status
        print("Components:")
        for comp, status in summary["components"].items():
            status_icon = "✓" if status == "ok" else "✗"
            print(f"  {status_icon} {comp}: {status}")
        print()

        # Print any errors
        if summary["errors"]:
            print("Errors:")
            for error in summary["errors"]:
                print(f"  - {error}")
            print()

        # Print summary JSON location
        print(f"Summary written to: {state_dir}/hands_off_summary.json")
        print()

        # Optionally print full report
        if "--full-report" in sys.argv:
            print()
            print(result["report_text"])

        print("=" * 70)
        print("  ⚠️  DRYRUN ONLY – NO REAL TRADES EXECUTED  ⚠️")
        print("=" * 70)

        sys.exit(0)

    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr)
        print(f"\nSummary file may contain error details: {state_dir}/hands_off_summary.json")
        sys.exit(1)


if __name__ == "__main__":
    main()
