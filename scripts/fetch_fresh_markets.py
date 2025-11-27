#!/usr/bin/env python3
"""
Fetch fresh active markets from Polymarket's public Gamma API
"""
import requests
import json
from datetime import datetime

def fetch_active_markets(limit=20):
    """Fetch active markets from Polymarket Gamma API"""

    # Gamma API endpoint for active markets
    url = "https://gamma-api.polymarket.com/markets"

    params = {
        "closed": "false",  # Only active markets
        "limit": limit,
        "order": "volume24hr",  # Sort by volume
        "_order": "desc"
    }

    response = requests.get(url, params=params)
    response.raise_for_status()

    markets = response.json()

    result = {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "count": len(markets),
        "markets": []
    }

    for m in markets:
        # Extract token IDs from clobTokenIds field
        clob_token_ids = m.get("clobTokenIds")
        outcomes = m.get("outcomes")

        if not clob_token_ids or not outcomes:
            continue

        # Parse JSON strings
        try:
            token_ids = json.loads(clob_token_ids)
            outcome_list = json.loads(outcomes)
        except (json.JSONDecodeError, TypeError):
            continue

        if not token_ids or not outcome_list:
            continue

        # Find the YES/Up token (usually first token)
        # For binary markets, outcomes are typically ["Yes", "No"] or ["Up", "Down"]
        yes_token_id = token_ids[0] if len(token_ids) > 0 else None
        if not yes_token_id:
            continue

        market_data = {
            "condition_id": m.get("conditionId"),
            "token_id": yes_token_id,
            "question": m.get("question"),
            "slug": m.get("slug", ""),
            "end_date": m.get("endDate"),
            "category": m.get("category", "unknown"),
            "volume_24h": m.get("volume24hr", 0),
            "liquidity": float(m.get("liquidityNum", 0)),
            "outcomes": outcome_list,
            "active": m.get("active", False),
            "closed": m.get("closed", False),
            "restricted": m.get("restricted", False)
        }

        result["markets"].append(market_data)

    return result

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
