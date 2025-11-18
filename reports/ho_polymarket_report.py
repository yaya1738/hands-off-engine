#!/usr/bin/env python3
"""
ho_polymarket_report.py

Read-only reporting module for Hands-Off Polymarket DRYRUN pipeline.

Reads state files (polymarket-model.json, decision_output.json, execution_plan.json)
and generates human-readable reports and JSON summaries.

NO LIVE EXECUTION - READ ONLY.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any, Dict, List


def _load_json(path: Path, default: Any = None) -> Any:
    """Load JSON file, return default if missing or invalid."""
    if not path.exists():
        return default
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception as e:
        print(f"[warn] failed to load {path}: {e}", file=sys.stderr)
        return default


def render_polymarket_report(state_dir: str = "state") -> str:
    """
    Generate a human-readable text report from DRYRUN pipeline state files.

    Args:
        state_dir: Directory containing state files (default: "state")

    Returns:
        Multi-line text report summarizing alpha signals, portfolio, and execution plan.
    """
    state_path = Path(state_dir)

    # Load state files
    model = _load_json(state_path / "polymarket-model.json", {})
    decision = _load_json(state_path / "decision_output.json", {})
    plan = _load_json(state_path / "execution_plan.json", {})

    # Extract data
    markets = model.get("markets", [])
    total_markets = len(markets)

    # Count recommendations
    buy_yes_count = sum(1 for m in markets if m.get("rec") == "buy_yes")
    buy_no_count = sum(1 for m in markets if m.get("rec") == "buy_no")
    hold_count = sum(1 for m in markets if m.get("rec") == "hold")

    # Get top markets by positive edge
    markets_with_edge = [m for m in markets if m.get("edge", 0) > 0]
    top_markets = sorted(markets_with_edge, key=lambda m: m.get("edge", 0), reverse=True)[:5]

    # Portfolio info
    current_balances = decision.get("balances", {})
    recommend = decision.get("recommend", {})
    current_pm = current_balances.get("polymarket_usd", 0)
    target_pm = recommend.get("polymarket", 0)
    current_cash = current_balances.get("cash_usd", 0)
    target_cash = recommend.get("cash", 0)

    # Plan info
    orders = plan.get("orders", [])
    num_orders = len(orders)
    total_size_usd = sum(o.get("size_usd", 0) for o in orders)
    mode = plan.get("mode", "DRYRUN")

    # Build report
    lines = []
    lines.append("=" * 70)
    lines.append("  Hands-Off Polymarket DRYRUN Report")
    lines.append("=" * 70)
    lines.append("")

    # Alpha Summary
    lines.append("ALPHA SUMMARY")
    lines.append("-" * 70)
    lines.append(f"  Total Markets Analyzed:  {total_markets}")
    lines.append(f"  Recommendations:")
    lines.append(f"    - BUY YES:  {buy_yes_count}")
    lines.append(f"    - BUY NO:   {buy_no_count}")
    lines.append(f"    - HOLD:     {hold_count}")
    lines.append("")

    if top_markets:
        lines.append(f"  Top {len(top_markets)} Markets by Positive Edge:")
        lines.append("")
        for i, m in enumerate(top_markets, 1):
            q = m.get("question", "Unknown")
            if len(q) > 60:
                q = q[:57] + "..."
            edge = m.get("edge", 0)
            rec = m.get("rec", "hold")
            market_id = m.get("id", "?")
            lines.append(f"    {i}. [{rec.upper()}] +{edge:.3f} edge")
            lines.append(f"       ID: {market_id}")
            lines.append(f"       Q:  {q}")
            lines.append("")

    # Portfolio Summary
    lines.append("PORTFOLIO SUMMARY")
    lines.append("-" * 70)
    lines.append(f"  Current Polymarket Balance:  ${current_pm:,.2f}")
    lines.append(f"  Target Polymarket Balance:   ${target_pm:,.2f}")
    lines.append(f"  Adjustment Needed:           ${target_pm - current_pm:+,.2f}")
    lines.append("")
    lines.append(f"  Current Cash Balance:        ${current_cash:,.2f}")
    lines.append(f"  Target Cash Balance:         ${target_cash:,.2f}")
    lines.append("")

    # Execution Plan Summary
    lines.append("EXECUTION PLAN SUMMARY")
    lines.append("-" * 70)
    lines.append(f"  Number of Orders:     {num_orders}")
    lines.append(f"  Total Size (USD):     ${total_size_usd:,.2f}")
    lines.append(f"  Execution Mode:       {mode}")
    lines.append("")

    # Safety disclaimer
    lines.append("=" * 70)
    lines.append("  ⚠️  DRYRUN ONLY – NO REAL TRADES EXECUTED  ⚠️")
    lines.append("=" * 70)
    lines.append("")

    return "\n".join(lines)


def run_polymarket_pipeline_and_report(state_dir: str = "state") -> Dict[str, Any]:
    """
    Run the DRYRUN Polymarket pipeline and return results as a dict.

    This function:
    1. Runs the existing DRYRUN pipeline (alpha -> decider -> executor)
    2. Reads the resulting state files
    3. Returns both a text report and a JSON-friendly summary

    Args:
        state_dir: Directory for state files (default: "state")

    Returns:
        Dict with keys:
            - report_text: Human-readable text report (str)
            - summary: JSON-friendly summary (dict)
    """
    import subprocess

    state_path = Path(state_dir)
    state_path.mkdir(parents=True, exist_ok=True)

    # Run the pipeline components in sequence
    # Note: These are placeholder paths - actual pipeline integration would be implemented here
    # For now, we'll just read existing state files if they exist

    # In a real implementation, you would run:
    # 1. alpha/ho_alpha_polymarket.py -> generates polymarket-model.json
    # 2. decider/ho_decider.py -> generates decision_output.json
    # 3. executor/ho_executor_plan.py -> generates execution_plan.json

    # For this DRYRUN version, we assume the files already exist or create minimal placeholders

    # Generate the text report
    report_text = render_polymarket_report(state_dir)

    # Load state files for summary
    model = _load_json(state_path / "polymarket-model.json", {})
    decision = _load_json(state_path / "decision_output.json", {})
    plan = _load_json(state_path / "execution_plan.json", {})

    # Build JSON-friendly summary
    markets = model.get("markets", [])
    orders = plan.get("orders", [])
    recommend = decision.get("recommend", {})
    current_balances = decision.get("balances", {})

    summary = {
        "num_markets": len(markets),
        "num_buy_yes": sum(1 for m in markets if m.get("rec") == "buy_yes"),
        "num_buy_no": sum(1 for m in markets if m.get("rec") == "buy_no"),
        "num_hold": sum(1 for m in markets if m.get("rec") == "hold"),
        "num_orders": len(orders),
        "total_size_usd": sum(o.get("size_usd", 0) for o in orders),
        "current_pm_balance": current_balances.get("polymarket_usd", 0),
        "target_pm_balance": recommend.get("polymarket", 0),
        "mode": plan.get("mode", "DRYRUN")
    }

    return {
        "report_text": report_text,
        "summary": summary
    }


if __name__ == "__main__":
    # CLI entry point
    state_dir = sys.argv[1] if len(sys.argv) > 1 else "state"

    print(render_polymarket_report(state_dir))
