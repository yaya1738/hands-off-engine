#!/usr/bin/env python3
"""
Polymarket live data fetcher for Hands-Off Engine (Batch 12).

Fetches live market data from Polymarket's public Gamma API and transforms
it into the compact format expected by the Alpha pipeline.

DRYRUN ONLY - Read-only public data access, no trading or authentication.
"""

import json
import os
import sys
import time
import urllib.request
import urllib.error
from datetime import datetime
from typing import Dict, List, Any, Optional


# Constants
POLYMARKET_API_URL = "https://gamma-api.polymarket.com/events"
REQUEST_TIMEOUT = 15
USER_AGENT = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36"


def fetch_markets_raw() -> dict:
    """
    Fetch raw markets JSON from Polymarket's public Gamma API.

    Returns:
        dict: The raw decoded JSON as a Python dict.

    Raises:
        urllib.error.URLError: If network request fails.
        json.JSONDecodeError: If response is not valid JSON.
        TimeoutError: If request times out.
    """
    headers = {
        "User-Agent": USER_AGENT,
        "Accept": "application/json",
        "Accept-Language": "en-US,en;q=0.9",
    }

    req = urllib.request.Request(POLYMARKET_API_URL, headers=headers)

    try:
        with urllib.request.urlopen(req, timeout=REQUEST_TIMEOUT) as response:
            data = response.read().decode('utf-8')
            return json.loads(data)
    except urllib.error.HTTPError as e:
        raise RuntimeError(f"HTTP error {e.code}: {e.reason}") from e
    except urllib.error.URLError as e:
        raise RuntimeError(f"Network error: {e.reason}") from e
    except json.JSONDecodeError as e:
        raise RuntimeError(f"Invalid JSON response: {e}") from e


def _normalize_market_prices(market: dict) -> tuple:
    """
    Extract and normalize price data from a market.

    Args:
        market: Raw market data from API.

    Returns:
        tuple: (bestBid, last) prices as floats, or (None, None) if unavailable.
    """
    outcome_prices = market.get("outcomePrices")
    if not outcome_prices:
        return None, None

    try:
        prices = [float(p) for p in outcome_prices]
    except (ValueError, TypeError):
        return None, None

    if not prices:
        return None, None

    # For binary markets, use the "Yes" outcome or first price
    # Use max price as primary signal (bestBid approximation)
    best_bid = max(prices)

    # Use first price as "last" (most recent traded)
    last = prices[0] if prices else None

    return best_bid, last


def _infer_category(title: str, question: str, tags: List[dict]) -> str:
    """
    Infer a category/group key for a market based on title, question, and tags.

    Args:
        title: Event title.
        question: Market question.
        tags: List of tag objects with 'label' field.

    Returns:
        str: Category key (e.g., "crypto", "sports", "politics", "other").
    """
    text = f"{title} {question}".lower()

    # Check tags first
    for tag in tags:
        label = tag.get("label", "").lower()
        if "crypto" in label or "bitcoin" in label or "ethereum" in label:
            return "crypto"
        if "sports" in label or "nba" in label or "nfl" in label:
            return "sports"
        if "politics" in label or "election" in label:
            return "politics"

    # Fallback to text matching
    if any(kw in text for kw in ["bitcoin", "ethereum", "crypto", "btc", "eth"]):
        return "crypto"
    if any(kw in text for kw in ["nba", "nfl", "sports", "lakers", "celtics"]):
        return "sports"
    if any(kw in text for kw in ["election", "trump", "biden", "politics"]):
        return "politics"
    if any(kw in text for kw in ["inflation", "fed", "rate", "economy"]):
        return "economy"

    return "other"


def build_compact_from_raw(raw: dict) -> dict:
    """
    Transform the raw Polymarket API format into the compact format used
    by the Alpha pipeline.

    Expected compact format:
    {
      "timestamp": "<ISO8601>",
      "markets": {
        "<category>": [
          {
            "id": "...",
            "slug": "...",
            "question": "...",
            "bestBid": 0.12,
            "last": 0.13,
            "endDate": "...",
            "title": "...",
            "outcomes": [...],
            "outcomePrices": [...]
          },
          ...
        ]
      }
    }

    Args:
        raw: Raw API response (should be a list of events).

    Returns:
        dict: Compact market data structure.
    """
    timestamp = datetime.utcnow().isoformat() + "Z"
    markets_by_category = {}

    # Handle both list and dict responses
    events = raw if isinstance(raw, list) else []

    for event in events:
        if not isinstance(event, dict):
            continue

        title = event.get("title") or event.get("ticker") or event.get("slug") or ""
        if not title:
            continue

        tags = event.get("tags") or []
        event_markets = event.get("markets") or []

        for market in event_markets:
            question = market.get("question") or title
            slug = market.get("slug") or ""
            market_id = market.get("id") or market.get("clob_token_ids", [""])[0]

            # Extract price data
            best_bid, last = _normalize_market_prices(market)
            if best_bid is None:
                # Skip markets without valid price data
                continue

            # Infer category
            category = _infer_category(title, question, tags)

            # Build compact market entry
            compact_market = {
                "id": market_id,
                "slug": slug,
                "question": question,
                "title": title,
                "bestBid": round(best_bid, 4) if best_bid else None,
                "last": round(last, 4) if last else None,
                "endDate": market.get("end_date_iso") or market.get("endDate") or "",
                "outcomes": market.get("outcomes") or [],
                "outcomePrices": market.get("outcomePrices") or [],
            }

            # Add to category
            if category not in markets_by_category:
                markets_by_category[category] = []
            markets_by_category[category].append(compact_market)

    return {
        "timestamp": timestamp,
        "markets": markets_by_category
    }


def write_compact(state_dir: str, compact: dict) -> str:
    """
    Write the compact JSON to <state_dir>/polymarket-compact.json.
    Uses atomic write (write to temp file, then rename) for safety.

    Args:
        state_dir: Directory to write the file to.
        compact: Compact market data structure.

    Returns:
        str: Full path to the written file.
    """
    # Ensure state directory exists
    os.makedirs(state_dir, exist_ok=True)

    output_path = os.path.join(state_dir, "polymarket-compact.json")
    temp_path = output_path + ".tmp"

    # Write to temp file first
    with open(temp_path, 'w') as f:
        json.dump(compact, f, indent=2)

    # Atomic rename
    os.replace(temp_path, output_path)

    return output_path


def fetch_and_write(state_dir: str = "state") -> str:
    """
    High-level convenience function:
    - Fetch raw markets from Polymarket
    - Build compact representation
    - Write to <state_dir>/polymarket-compact.json

    Args:
        state_dir: Directory to write the file to (default: "state").

    Returns:
        str: Path to the written file.

    Raises:
        RuntimeError: If fetch or write fails.
    """
    # Fetch raw data
    raw = fetch_markets_raw()

    # Transform to compact format
    compact = build_compact_from_raw(raw)

    # Write to file
    output_path = write_compact(state_dir, compact)

    return output_path


def main():
    """CLI entry point."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Fetch live Polymarket data and write to compact JSON format"
    )
    parser.add_argument(
        "state_dir",
        nargs="?",
        default="state",
        help="Directory to write polymarket-compact.json (default: state)"
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Print raw API response for debugging"
    )

    args = parser.parse_args()

    try:
        if args.debug:
            print("Fetching raw Polymarket data...", file=sys.stderr)
            raw = fetch_markets_raw()
            print(json.dumps(raw, indent=2))
            sys.exit(0)

        # Normal operation
        print(f"Fetching Polymarket markets...", file=sys.stderr)
        output_path = fetch_and_write(args.state_dir)

        # Print summary
        with open(output_path, 'r') as f:
            compact = json.load(f)

        total_markets = sum(len(markets) for markets in compact.get("markets", {}).values())
        categories = list(compact.get("markets", {}).keys())

        print(f"✓ Fetched {total_markets} markets across {len(categories)} categories")
        print(f"  Categories: {', '.join(categories)}")
        print(f"  Timestamp: {compact.get('timestamp')}")
        print(f"  Output: {output_path}")

        sys.exit(0)

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
