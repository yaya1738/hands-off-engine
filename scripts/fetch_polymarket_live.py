#!/usr/bin/env python3
"""
Fetch Polymarket Live: Pull current market data from Polymarket API
===================================================================

This script fetches fresh market data from Polymarket's public Gamma API
and outputs it in the compact format expected by sync_polymarket_model.py.

Target markets (high volume Nov 27, 2025):
1. Fed Rate Decision Dec 2025 - $159M volume
2. Russia/Ukraine Ceasefire - $37M volume
3. NFL/NBA Games - $1-4M per game
4. Chile Presidential Election - $79M volume

Usage:
    python scripts/fetch_polymarket_live.py [--output FILE] [--queries QUERY,QUERY,...]

Output: JSON in polymarket-compact.json format:
{
    "timestamp": "2025-11-27T...",
    "counts": {"fed": 5, "russia": 3, ...},
    "queries": ["fed", "russia", ...],
    "markets": {
        "fed": [{"slug": "...", "question": "...", "bestBid": 0.5, ...}, ...],
        ...
    }
}
"""

import argparse
import json
import sys
import urllib.request
import urllib.error
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional


# Default queries targeting high-volume markets
DEFAULT_QUERIES = [
    "fed rate",
    "russia ukraine ceasefire",
    "nfl",
    "nba",
    "chile election",
    "bitcoin",
    "ethereum",
]

# Polymarket Gamma API base URL
API_BASE = "https://gamma-api.polymarket.com"


def get_json(url: str, params: Optional[dict] = None, timeout: int = 30) -> Any:
    """
    Make a GET request and return parsed JSON.
    
    Args:
        url: The URL to fetch
        params: Optional query parameters
        timeout: Request timeout in seconds
    
    Returns:
        Parsed JSON response
        
    Raises:
        Exception on network or parsing errors
    """
    if params:
        query = "&".join(f"{k}={urllib.parse.quote(str(v))}" for k, v in params.items())
        url = f"{url}?{query}"
    
    req = urllib.request.Request(url, headers={
        "User-Agent": "hands-off-engine/1.0",
        "Accept": "application/json",
    })
    
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8"))


def fetch_markets_by_query(query: str, limit: int = 20) -> list[dict]:
    """
    Fetch markets matching a search query.
    
    Uses the public-search endpoint which returns events containing markets.
    
    Args:
        query: Search term
        limit: Maximum results per type
    
    Returns:
        List of market dicts with normalized fields
    """
    markets = []
    
    try:
        # Try public-search endpoint first (best coverage)
        url = f"{API_BASE}/public-search"
        data = get_json(url, params={
            "q": query,
            "limit_per_type": limit,
            "optimized": "true"
        })
        
        # Extract markets from events
        events = data.get("events") or []
        for event in events:
            event_markets = event.get("markets") or []
            for m in event_markets:
                markets.append(normalize_market(m, query))
    except Exception as e:
        print(f"  Warning: public-search failed for '{query}': {e}", file=sys.stderr)
    
    # If public-search returned nothing, try events endpoint
    if not markets:
        try:
            url = f"{API_BASE}/events"
            events = get_json(url)
            
            # Filter by keyword match
            query_lower = query.lower()
            for event in (events if isinstance(events, list) else []):
                title = (event.get("title") or event.get("ticker") or "").lower()
                if query_lower in title:
                    for m in (event.get("markets") or []):
                        markets.append(normalize_market(m, query))
        except Exception as e:
            print(f"  Warning: events endpoint failed for '{query}': {e}", file=sys.stderr)
    
    return markets


def normalize_market(market: dict, query: str) -> dict:
    """
    Normalize market data to the compact format.
    
    Args:
        market: Raw market dict from API
        query: The query that found this market
    
    Returns:
        Normalized market dict
    """
    # Extract price (prefer bestBid, fall back to lastTradePrice)
    best_bid = market.get("bestBid")
    if best_bid is not None:
        try:
            best_bid = float(best_bid)
        except (ValueError, TypeError):
            best_bid = None
    
    last_price = market.get("lastTradePrice") or market.get("lastPrice") or market.get("last")
    if last_price is not None:
        try:
            last_price = float(last_price)
        except (ValueError, TypeError):
            last_price = None
    
    return {
        "query": query,
        "slug": market.get("slug") or "",
        "question": market.get("question") or market.get("title") or market.get("name") or "",
        "bestBid": best_bid,
        "last": last_price,
        "endDate": market.get("endDate") or market.get("closeTime") or market.get("close_time"),
    }


def fetch_all_markets(queries: list[str], limit_per_query: int = 15) -> dict:
    """
    Fetch markets for all queries and build compact output.
    
    Args:
        queries: List of search queries
        limit_per_query: Maximum markets per query
    
    Returns:
        Dict in polymarket-compact.json format
    """
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    
    result = {
        "timestamp": timestamp,
        "counts": {},
        "queries": queries,
        "markets": {},
    }
    
    for query in queries:
        # Use simplified key for the query
        key = query.split()[0].lower() if query else "unknown"
        
        print(f"  Fetching: {query}...", file=sys.stderr)
        markets = fetch_markets_by_query(query, limit=limit_per_query)
        
        # Filter to valid markets (have slug and some price data)
        valid_markets = [
            m for m in markets
            if m.get("slug") and (m.get("bestBid") is not None or m.get("last") is not None)
        ]
        
        # Sort by best bid descending to get most active markets
        valid_markets.sort(key=lambda m: m.get("bestBid") or 0, reverse=True)
        
        # Take top N
        top_markets = valid_markets[:limit_per_query]
        
        result["markets"][key] = top_markets
        result["counts"][key] = len(top_markets)
        print(f"    → Found {len(top_markets)} markets", file=sys.stderr)
    
    return result


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="Fetch live Polymarket data for the trading pipeline"
    )
    parser.add_argument(
        "--output", "-o",
        type=str,
        default=None,
        help="Output file path (default: termux-hands-off/out/polymarket-compact.json)"
    )
    parser.add_argument(
        "--queries", "-q",
        type=str,
        default=None,
        help="Comma-separated list of search queries (default: fed rate,russia ukraine ceasefire,...)"
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=15,
        help="Maximum markets per query (default: 15)"
    )
    
    args = parser.parse_args()
    
    # Determine output path
    if args.output:
        output_path = Path(args.output)
    else:
        repo_root = Path(__file__).parent.parent
        output_path = repo_root / "termux-hands-off" / "out" / "polymarket-compact.json"
    
    # Determine queries
    if args.queries:
        queries = [q.strip() for q in args.queries.split(",") if q.strip()]
    else:
        queries = DEFAULT_QUERIES
    
    print(f"📊 Fetching Polymarket live data...", file=sys.stderr)
    print(f"   Queries: {queries}", file=sys.stderr)
    print(f"   Output:  {output_path}", file=sys.stderr)
    print(file=sys.stderr)
    
    try:
        # Fetch all markets
        data = fetch_all_markets(queries, limit_per_query=args.limit)
        
        # Calculate totals
        total_markets = sum(data["counts"].values())
        
        # Ensure output directory exists
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Write atomically (tmp file then rename)
        tmp_path = output_path.with_suffix(".tmp")
        with open(tmp_path, "w") as f:
            json.dump(data, f, indent=2)
        tmp_path.replace(output_path)
        
        print(file=sys.stderr)
        print(f"✓ Success!", file=sys.stderr)
        print(f"  Timestamp: {data['timestamp']}", file=sys.stderr)
        print(f"  Total markets: {total_markets}", file=sys.stderr)
        print(f"  Breakdown: {data['counts']}", file=sys.stderr)
        print(f"  Output: {output_path}", file=sys.stderr)
        
        # Also print JSON to stdout for piping
        print(json.dumps(data, indent=2))
        
        return 0
        
    except Exception as e:
        print(f"✗ Error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
