#!/usr/bin/env python3
"""
Fetch fresh active markets from Polymarket's public Gamma API

Uses the /events endpoint which includes market prices (outcomePrices).
"""

# UNIFIED AI - All systems serve Yair Siegel
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
try:
    from ai.unified_ai import MASTER, get_master
except ImportError:
    MASTER = "Yair Siegel"

import requests
import json
from datetime import datetime

def fetch_active_markets(limit=50):
    """
    Fetch active markets with prices from Polymarket Gamma API.

    Uses the /events endpoint which includes outcomePrices, unlike /markets.
    """
    # Gamma API /events endpoint includes prices
    url = "https://gamma-api.polymarket.com/events"

    params = {
        "closed": "false",
        "limit": limit,
        "active": "true"
    }

    response = requests.get(url, params=params, timeout=30)
    response.raise_for_status()

    events = response.json()

    result = {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "count": 0,
        "markets": []
    }

    for event in events:
        markets = event.get("markets", [])

        for m in markets:
            # Skip closed markets
            if m.get("closed", False):
                continue

            # Get outcomes and prices
            outcomes = m.get("outcomes")
            outcome_prices = m.get("outcomePrices")

            if not outcomes or not outcome_prices:
                continue

            # Parse if JSON strings
            try:
                if isinstance(outcomes, str):
                    outcomes = json.loads(outcomes)
                if isinstance(outcome_prices, str):
                    outcome_prices = json.loads(outcome_prices)
            except (json.JSONDecodeError, TypeError):
                continue

            # Parse prices to floats
            try:
                prices = [float(p) for p in outcome_prices]
            except (ValueError, TypeError):
                continue

            if len(prices) < 2:
                continue

            # Get YES price (first outcome)
            yes_price = prices[0]
            no_price = prices[1] if len(prices) > 1 else 1 - yes_price

            # Extract token IDs
            clob_token_ids = m.get("clobTokenIds")
            if clob_token_ids:
                try:
                    if isinstance(clob_token_ids, str):
                        token_ids = json.loads(clob_token_ids)
                    else:
                        token_ids = clob_token_ids
                    yes_token_id = token_ids[0] if token_ids else None
                except (json.JSONDecodeError, TypeError, IndexError):
                    yes_token_id = None
            else:
                yes_token_id = None

            market_data = {
                "condition_id": m.get("conditionId"),
                "token_id": yes_token_id,
                "question": m.get("question", event.get("title", "")),
                "slug": m.get("slug", ""),
                "end_date": m.get("endDate"),
                "category": event.get("category", "unknown"),
                "volume_24h": m.get("volume24hr", 0) or 0,
                "liquidity": float(m.get("liquidityNum", 0) or 0),
                "outcomes": outcomes,
                "outcomePrices": prices,
                "yes_price": round(yes_price, 4),
                "no_price": round(no_price, 4),
                "active": m.get("active", True),
                "closed": m.get("closed", False),
                "restricted": m.get("restricted", False)
            }

            result["markets"].append(market_data)

    result["count"] = len(result["markets"])
    return result


def save_compact_format(data: dict, output_path: str):
    """
    Save fetched markets in the compact format expected by the pipeline.

    The pipeline expects termux-hands-off/out/polymarket-compact.json format.
    Now includes prices (outcomePrices, yes_price, no_price) for alpha sync.
    """
    compact = {
        "timestamp": data["timestamp"],
        "count": data["count"],
        "markets": []
    }

    for m in data["markets"]:
        compact["markets"].append({
            "token_id": m.get("token_id"),
            "condition_id": m.get("condition_id"),
            "question": m["question"],
            "slug": m.get("slug", ""),
            "category": m.get("category", "unknown"),
            "volume_24h": m.get("volume_24h", 0),
            "liquidity": m.get("liquidity", 0),
            "outcomes": m.get("outcomes", ["Yes", "No"]),
            "outcomePrices": m.get("outcomePrices", [0.5, 0.5]),
            "yes_price": m.get("yes_price", 0.5),
            "no_price": m.get("no_price", 0.5),
            "end_date": m.get("end_date"),
            "active": m.get("active", True),
            "closed": m.get("closed", False)
        })

    with open(output_path, "w") as f:
        json.dump(compact, f, indent=2)

    return compact


if __name__ == "__main__":
    print("Fetching fresh active markets from Polymarket...")

    try:
        data = fetch_active_markets(limit=50)

        # Save to file
        output_path = "state/fresh_polymarket_markets.json"
        with open(output_path, "w") as f:
            json.dump(data, f, indent=2)

        print(f"✓ Fetched {data['count']} active markets")
        print(f"✓ Saved to {output_path}")

        # Show top 5
        print("\nTop 5 markets by 24h volume:")
        for i, m in enumerate(data["markets"][:5], 1):
            print(f"{i}. {m['question'][:70]}")
            print(f"   Token ID: {m['token_id'][:20]}...")
            print(f"   Volume 24h: ${m['volume_24h']:,.0f}")
            print(f"   Liquidity: ${m['liquidity']:,.0f}")
            print(f"   Outcomes: {m['outcomes']}")
            print()

    except Exception as e:
        print(f"Error: {e}")
        exit(1)
