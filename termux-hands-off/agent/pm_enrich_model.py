#!/usr/bin/env python3
"""
pm_enrich_model.py

Enriches polymarket-model.json with live prices and computed edges.

Flow:
1. Read polymarket-compact.json (scanner output with live market data)
2. Read polymarket-model.json (manually curated markets with fair_yes values)
3. For each event in model:
   - Look up current market price from compact
   - For YES: use best_ask
   - For NO: use (1 - best_bid) or no_price
   - Compute edge_pct_points = 100 * (fair_yes - price)
4. Write enriched polymarket-model.json back

This makes the model output interpretable for the decider.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional


STATE_DIR = Path.home() / "hands-off-out" / "state"
COMPACT_FILE = STATE_DIR / "polymarket-compact.json"
MODEL_FILE = STATE_DIR / "polymarket-model.json"


def load_compact() -> Dict[str, Any]:
    """Load polymarket-compact.json and index by market ID."""
    if not COMPACT_FILE.exists():
        print(f"[pm_enrich] warning: {COMPACT_FILE} not found")
        return {}

    try:
        data = json.loads(COMPACT_FILE.read_text(encoding="utf-8"))
    except Exception as e:
        print(f"[pm_enrich] error reading compact: {e}")
        return {}

    # Compact file is a dict mapping market_id -> market data
    if isinstance(data, dict):
        return data

    # If it's a list, convert to dict
    if isinstance(data, list):
        return {m.get("id", m.get("slug", str(i))): m for i, m in enumerate(data)}

    print(f"[pm_enrich] unexpected compact format")
    return {}


def load_model() -> Dict[str, Any]:
    """Load polymarket-model.json."""
    if not MODEL_FILE.exists():
        print(f"[pm_enrich] error: {MODEL_FILE} not found")
        return {}

    try:
        return json.loads(MODEL_FILE.read_text(encoding="utf-8"))
    except Exception as e:
        print(f"[pm_enrich] error reading model: {e}")
        return {}


def get_trade_price(market: Dict[str, Any], side: str) -> float:
    """
    Extract the trading price for a given side.

    For YES: use best_ask (the price to BUY yes)
    For NO: use (1 - best_bid) or no_price (the price to BUY no)
    """
    if side.upper() == "YES":
        # Price to buy YES
        return float(market.get("best_ask", market.get("yes_price", 0.0)))
    else:
        # Price to buy NO
        best_bid = market.get("best_bid")
        if best_bid is not None:
            return 1.0 - float(best_bid)
        return float(market.get("no_price", market.get("best_no", 0.0)))


def enrich_event(event: Dict[str, Any], compact: Dict[str, Any]) -> Dict[str, Any]:
    """
    Enrich a single event with live price and computed edge.

    Returns the enriched event dict.
    """
    event_id = event.get("id")
    if not event_id:
        print(f"[pm_enrich] warning: event missing id, skipping")
        return event

    # Look up market in compact
    market = compact.get(event_id)
    if not market:
        print(f"[pm_enrich] warning: market {event_id} not in compact, keeping old values")
        # Set defaults if not present
        if "price" not in event:
            event["price"] = 0.0
        if "edge_pct_points" not in event:
            event["edge_pct_points"] = None
        return event

    # Get side (default to YES if not specified)
    side = event.get("side", "YES")

    # Extract trading price
    price = get_trade_price(market, side)
    event["price"] = price

    # Get or compute fair_yes
    fair_yes = event.get("fair_yes")
    if fair_yes is None:
        # If no fair value set, use market price as placeholder
        # (In production, this should come from a real model)
        fair_yes = price
        event["fair_yes"] = fair_yes
        print(f"[pm_enrich] warning: {event_id} has no fair_yes, using market price {price:.3f}")

    # Compute edge
    fair = float(fair_yes)
    # For YES positions: edge = fair - price_to_buy_yes
    # For NO positions: if fair_yes represents the model's YES belief,
    #   then for a NO bet, effective_fair = (1 - fair_yes)
    #   and edge = effective_fair - price_to_buy_no
    # To keep it simple: if side is NO, adjust the edge calculation
    if side.upper() == "YES":
        edge_pct = 100.0 * (fair - price)
    else:
        # For NO bets: edge = (1 - fair_yes) - price_to_buy_no
        edge_pct = 100.0 * ((1.0 - fair) - price)

    event["edge_pct_points"] = round(edge_pct, 2)

    # Also enrich with latest market metadata if useful
    event.setdefault("question", market.get("question", ""))
    event.setdefault("category", market.get("category", ""))

    return event


def main() -> None:
    """Main enrichment pipeline."""
    print("[pm_enrich] starting enrichment...")

    # Load data
    compact = load_compact()
    model = load_model()

    if not model:
        print("[pm_enrich] error: no model to enrich")
        return

    events = model.get("events", [])
    if not events:
        print("[pm_enrich] warning: no events in model")
        return

    print(f"[pm_enrich] enriching {len(events)} events...")

    # Enrich each event
    enriched_count = 0
    for event in events:
        original_price = event.get("price")
        enrich_event(event, compact)
        if event.get("price") != original_price:
            enriched_count += 1

    # Update timestamp
    model["as_of"] = datetime.now(timezone.utc).isoformat()

    # Write back
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    MODEL_FILE.write_text(json.dumps(model, indent=2, sort_keys=True), encoding="utf-8")

    print(f"[pm_enrich] enriched {enriched_count}/{len(events)} events")
    print(f"[pm_enrich] wrote {MODEL_FILE}")

    # Print summary
    print("\n[pm_enrich] summary:")
    for ev in events:
        edge = ev.get("edge_pct_points")
        edge_str = f"{edge:+.1f}pp" if edge is not None else "N/A"
        print(f"  {ev.get('id')}: price={ev.get('price'):.3f} edge={edge_str}")


if __name__ == "__main__":
    main()
