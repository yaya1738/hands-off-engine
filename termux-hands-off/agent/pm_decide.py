#!/usr/bin/env python3
"""
pm_decide.py

Simple decider that:
1. Reads polymarket-model.json (enriched with prices and edges)
2. Filters events by min_edge_to_bet_pct_points
3. Sizes positions based on allocation caps and default stake
4. Generates DRYRUN orders in decision_report.json

This is the "decider" layer that converts model output → actionable orders.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional


STATE_DIR = Path.home() / "hands-off-out" / "state"
MODEL_FILE = STATE_DIR / "polymarket-model.json"
DECISION_FILE = STATE_DIR / "decision_report.json"


def load_model() -> Dict[str, Any]:
    """Load polymarket-model.json."""
    if not MODEL_FILE.exists():
        print(f"[pm_decide] error: {MODEL_FILE} not found")
        return {}

    try:
        return json.loads(MODEL_FILE.read_text(encoding="utf-8"))
    except Exception as e:
        print(f"[pm_decide] error reading model: {e}")
        return {}


def decide_event(event: Dict[str, Any], globals_cfg: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Decide whether to generate an order for this event.

    Returns an order dict if edge is sufficient, else None.
    """
    event_id = event.get("id", "unknown")
    side = event.get("side", "YES").upper()
    price = event.get("price", 0.0)
    edge_pct = event.get("edge_pct_points")
    fair_yes = event.get("fair_yes")
    question = event.get("question", "")
    alloc = event.get("alloc", {})

    # Check edge threshold
    min_edge = globals_cfg.get("min_edge_to_bet_pct_points", 3.0)
    if edge_pct is None or edge_pct < min_edge:
        return None

    # Determine stake
    max_usd = alloc.get("max_usd", 0.0)
    default_stake = globals_cfg.get("default_stake_usd", 5.0)

    # Use smaller of default_stake and max_usd
    stake_usd = min(default_stake, max_usd) if max_usd > 0 else default_stake

    # Skip if stake is too small
    if stake_usd < 0.01:
        return None

    # Generate order
    order = {
        "market_id": event_id,
        "side": side,
        "limit_price": price,
        "stake_usd": stake_usd,
        "edge_pct_points": edge_pct,
        "fair_yes": fair_yes,
        "question": question,
        "reason": f"{side} edge of {edge_pct:+.1f}pp (fair={fair_yes:.3f}, price={price:.3f})",
    }

    return order


def main() -> None:
    """Main decision pipeline."""
    print("[pm_decide] starting decision process...")

    # Load model
    model = load_model()
    if not model:
        print("[pm_decide] error: no model to decide on")
        return

    globals_cfg = model.get("globals", {})
    events = model.get("events", [])

    if not events:
        print("[pm_decide] warning: no events in model")
        return

    print(f"[pm_decide] evaluating {len(events)} events...")
    print(f"[pm_decide] min_edge_to_bet: {globals_cfg.get('min_edge_to_bet_pct_points', 3.0)}pp")

    # Generate orders
    orders: List[Dict[str, Any]] = []
    for event in events:
        order = decide_event(event, globals_cfg)
        if order:
            orders.append(order)
            print(f"[pm_decide]   ✓ {order['side']} on {order['market_id']}: "
                  f"edge={order['edge_pct_points']:+.1f}pp, stake=${order['stake_usd']:.2f}")
        else:
            edge = event.get("edge_pct_points")
            edge_str = f"{edge:+.1f}pp" if edge is not None else "N/A"
            print(f"[pm_decide]   ✗ {event.get('id')}: edge={edge_str} (below threshold)")

    # Compute total
    total_live_usd = sum(o["stake_usd"] for o in orders)

    # Build decision report
    report = {
        "as_of": datetime.now(timezone.utc).isoformat(),
        "mode": "DRYRUN",
        "infra_allow_trades": False,
        "gate_blocked": False,
        "polymarket": {
            "orders": orders,
            "total_live_usd": total_live_usd,
        },
    }

    # Write decision report
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    DECISION_FILE.write_text(json.dumps(report, indent=2), encoding="utf-8")

    print(f"\n[pm_decide] generated {len(orders)} orders (total: ${total_live_usd:.2f})")
    print(f"[pm_decide] wrote {DECISION_FILE}")


if __name__ == "__main__":
    main()
