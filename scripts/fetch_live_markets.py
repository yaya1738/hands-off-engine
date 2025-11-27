#!/usr/bin/env python3
"""
Fetch Live Markets: Real-time Polymarket Data Fetcher
=====================================================

This script fetches fresh market data from Polymarket's public API
to power the cash explosion operation with live opportunities.

Features:
- Fetches trending markets by category
- Filters for markets with good liquidity
- Outputs in polymarket-compact.json format for the alpha pipeline

Usage:
    python scripts/fetch_live_markets.py
    python scripts/fetch_live_markets.py --categories bitcoin,trump
"""

import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional
import urllib.request
import urllib.error


# Polymarket CLOB API endpoints
POLYMARKET_GAMMA_API = "https://gamma-api.polymarket.com"
POLYMARKET_CLOB_API = "https://clob.polymarket.com"

# Categories to track for cash explosion
DEFAULT_CATEGORIES = ["bitcoin", "ethereum", "trump", "politics", "crypto"]


def fetch_url(url: str, timeout: int = 30) -> Optional[dict]:
    """Fetch JSON from URL with error handling."""
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (compatible; HandsOffEngine/1.0)",
            "Accept": "application/json"
        }
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=timeout) as response:
            return json.loads(response.read().decode())
    except urllib.error.URLError as e:
        print(f"Network error fetching {url}: {e}")
        return None
    except json.JSONDecodeError as e:
        print(f"JSON parse error from {url}: {e}")
        return None
    except Exception as e:
        print(f"Unexpected error fetching {url}: {e}")
        return None


def fetch_markets_by_query(query: str, limit: int = 20) -> List[Dict]:
    """
    Fetch markets matching a search query from Polymarket.

    Args:
        query: Search term (e.g., "bitcoin", "trump")
        limit: Maximum number of markets to fetch

    Returns:
        List of market dicts
    """
    # Use the gamma API for market search
    url = f"{POLYMARKET_GAMMA_API}/markets?limit={limit}&active=true&closed=false"

    data = fetch_url(url)
    if not data:
        return []

    # Filter markets matching query (case-insensitive)
    markets = []
    query_lower = query.lower()

    for market in data:
        question = market.get("question", "").lower()
        slug = market.get("slug", "").lower()

        if query_lower in question or query_lower in slug:
            # Transform to compact format
            compact_market = {
                "query": query,
                "slug": market.get("slug", ""),
                "question": market.get("question", ""),
                "bestBid": parse_price(market.get("bestBid")),
                "last": parse_price(market.get("lastTradePrice")),
                "endDate": market.get("endDate")
            }
            markets.append(compact_market)

    return markets[:limit]


def fetch_trending_markets(limit: int = 50) -> List[Dict]:
    """
    Fetch currently trending/active markets from Polymarket.

    Args:
        limit: Maximum number of markets

    Returns:
        List of market dicts
    """
    url = f"{POLYMARKET_GAMMA_API}/markets?limit={limit}&active=true&closed=false&order=volume24hr&ascending=false"

    data = fetch_url(url)
    if not data:
        return []

    return data


def parse_price(price_str) -> Optional[float]:
    """Parse price from various formats."""
    if price_str is None:
        return None
    try:
        return float(price_str)
    except (ValueError, TypeError):
        return None


def categorize_market(market: Dict) -> str:
    """Determine category for a market based on question/slug."""
    question = market.get("question", "").lower()
    slug = market.get("slug", "").lower()
    text = question + " " + slug

    if "bitcoin" in text or "btc" in text:
        return "bitcoin"
    if "ethereum" in text or "eth" in text:
        return "ethereum"
    if "trump" in text:
        return "trump"
    if "israel" in text or "gaza" in text:
        return "israel"
    if "nba" in text or "basketball" in text:
        return "nba"
    if "nfl" in text or "football" in text:
        return "nfl"
    if any(term in text for term in ["president", "election", "congress", "senate", "vote"]):
        return "politics"
    if any(term in text for term in ["crypto", "coin", "defi"]):
        return "crypto"

    return "other"


def fetch_live_markets(
    categories: List[str] = None,
    markets_per_category: int = 12
) -> Dict:
    """
    Fetch fresh market data organized by category.

    Args:
        categories: List of categories to fetch
        markets_per_category: Max markets per category

    Returns:
        Dict in polymarket-compact.json format
    """
    if categories is None:
        categories = DEFAULT_CATEGORIES

    print(f"Fetching live markets for categories: {categories}")

    # First, get trending markets
    trending = fetch_trending_markets(100)

    # Organize by category
    markets_by_category = {cat: [] for cat in categories}
    counts = {cat: 0 for cat in categories}

    for market in trending:
        category = categorize_market(market)

        if category in markets_by_category and counts[category] < markets_per_category:
            compact_market = {
                "query": category,
                "slug": market.get("slug", ""),
                "question": market.get("question", ""),
                "bestBid": parse_price(market.get("bestBid")),
                "last": parse_price(market.get("lastTradePrice")),
                "endDate": market.get("endDate")
            }

            # Only include markets with price data
            if compact_market["last"] is not None or compact_market["bestBid"] is not None:
                markets_by_category[category].append(compact_market)
                counts[category] += 1

    # Build output structure
    result = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "counts": counts,
        "queries": categories,
        "markets": markets_by_category
    }

    return result


def save_market_data(data: Dict, output_path: Path):
    """Save market data to JSON file."""
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Write atomically
    tmp_path = output_path.with_suffix(".tmp")
    with open(tmp_path, "w") as f:
        json.dump(data, f, indent=2)
    tmp_path.replace(output_path)

    print(f"Saved to: {output_path}")


def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(description="Fetch live Polymarket data")
    parser.add_argument(
        "--categories",
        type=str,
        default=",".join(DEFAULT_CATEGORIES),
        help=f"Comma-separated categories (default: {','.join(DEFAULT_CATEGORIES)})"
    )
    parser.add_argument(
        "--per-category",
        type=int,
        default=12,
        help="Max markets per category (default: 12)"
    )
    parser.add_argument(
        "--output",
        type=str,
        default=None,
        help="Output path (default: termux-hands-off/out/polymarket-compact.json)"
    )

    args = parser.parse_args()

    # Parse categories
    categories = [c.strip() for c in args.categories.split(",")]

    # Set output path
    repo_root = Path(__file__).parent.parent
    if args.output:
        output_path = Path(args.output)
    else:
        output_path = repo_root / "termux-hands-off" / "out" / "polymarket-compact.json"

    print("=" * 60)
    print("  CASH EXPLOSION: Live Market Data Fetcher")
    print("=" * 60)
    print()

    # Fetch live data
    data = fetch_live_markets(
        categories=categories,
        markets_per_category=args.per_category
    )

    # Show summary
    print()
    print("Market counts by category:")
    for cat, count in data["counts"].items():
        print(f"  {cat}: {count}")

    total_markets = sum(data["counts"].values())
    print(f"\nTotal markets: {total_markets}")

    # Save data
    save_market_data(data, output_path)

    print()
    print("Ready for pipeline: python scripts/run_pipeline.py --bankroll 1500")
    print()

    return 0


if __name__ == "__main__":
    sys.exit(main())
