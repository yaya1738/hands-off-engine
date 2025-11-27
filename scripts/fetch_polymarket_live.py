#!/usr/bin/env python3
"""
Polymarket Live Data Fetcher

Fetches live market data from Polymarket's public API for specified queries/categories.
Supports rate limiting, retries, and outputs data in the compact format expected by
the alpha model.

Usage:
    python3 scripts/fetch_polymarket_live.py
    python3 scripts/fetch_polymarket_live.py --queries trump,bitcoin --output state/markets.json

Output Format:
    {
        "timestamp": "2025-11-27T12:00:00Z",
        "counts": {"trump": 12, "bitcoin": 8},
        "queries": ["trump", "bitcoin"],
        "markets": {
            "trump": [
                {
                    "query": "trump",
                    "slug": "market-slug",
                    "question": "Will Trump...?",
                    "bestBid": 0.75,
                    "last": 0.76,
                    "endDate": null
                },
                ...
            ]
        }
    }
"""

import argparse
import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Any
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError


# Default queries to fetch
DEFAULT_QUERIES = [
    "trump",
    "bitcoin",
    "ethereum",
    "fed rate",
    "inflation",
    "election",
    "israel",
    "ukraine",
    "nba",
    "nfl",
]

# API configuration
POLYMARKET_API_BASE = "https://gamma-api.polymarket.com"
CLOB_API_BASE = "https://clob.polymarket.com"
REQUEST_TIMEOUT = 30
MAX_RETRIES = 3
RETRY_DELAY = 2
RATE_LIMIT_DELAY = 0.5  # Delay between requests to avoid rate limiting


class PolymarketFetcher:
    """
    Fetches live market data from Polymarket's public APIs.
    
    Uses the Gamma API for market discovery and the CLOB API for pricing data.
    """
    
    def __init__(self, verbose: bool = False):
        """
        Initialize the fetcher.
        
        Args:
            verbose: If True, print progress messages
        """
        self.verbose = verbose
        self.session_start = time.time()
    
    def _log(self, message: str):
        """Print message if verbose mode is enabled."""
        if self.verbose:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] {message}")
    
    def _make_request(self, url: str) -> Optional[Any]:
        """
        Make HTTP request with retry logic.
        
        Args:
            url: Full URL to request
            
        Returns:
            Parsed JSON response, or None on failure
        """
        headers = {
            "Accept": "application/json",
            "User-Agent": "Hands-Off-Engine/1.0"
        }
        
        for attempt in range(MAX_RETRIES):
            try:
                req = Request(url, headers=headers)
                with urlopen(req, timeout=REQUEST_TIMEOUT) as response:
                    return json.loads(response.read().decode('utf-8'))
                    
            except HTTPError as e:
                if e.code == 429:  # Rate limited
                    wait = (2 ** attempt) * RETRY_DELAY
                    self._log(f"Rate limited, waiting {wait}s...")
                    time.sleep(wait)
                elif e.code >= 500:  # Server error
                    wait = RETRY_DELAY
                    self._log(f"Server error {e.code}, retrying in {wait}s...")
                    time.sleep(wait)
                else:
                    self._log(f"HTTP error {e.code}: {url}")
                    return None
                    
            except URLError as e:
                self._log(f"Network error: {e}")
                if attempt < MAX_RETRIES - 1:
                    time.sleep(RETRY_DELAY)
                    
            except Exception as e:
                self._log(f"Unexpected error: {e}")
                return None
        
        return None
    
    def fetch_markets_by_query(self, query: str, limit: int = 20) -> List[Dict]:
        """
        Fetch markets matching a search query.
        
        Args:
            query: Search term (e.g., "trump", "bitcoin")
            limit: Maximum number of markets to return
            
        Returns:
            List of market dictionaries
        """
        self._log(f"Fetching markets for: {query}")
        
        # Use Gamma API for market search
        url = f"{POLYMARKET_API_BASE}/markets?_limit={limit}&active=true&closed=false"
        url += f"&text_query={query}"
        
        data = self._make_request(url)
        
        if not data:
            return []
        
        markets = []
        for market in data:
            try:
                # Extract relevant fields
                outcome_prices = market.get('outcomePrices', '[]')
                if isinstance(outcome_prices, str):
                    try:
                        outcome_prices = json.loads(outcome_prices)
                    except json.JSONDecodeError:
                        outcome_prices = []
                
                # Get YES price (typically first outcome)
                yes_price = float(outcome_prices[0]) if outcome_prices else 0.5
                
                # Get best bid from order book if available
                best_bid = market.get('bestBid') or yes_price
                if isinstance(best_bid, str):
                    try:
                        best_bid = float(best_bid)
                    except ValueError:
                        best_bid = yes_price
                
                market_info = {
                    "query": query,
                    "slug": market.get('slug', market.get('conditionId', '')),
                    "question": market.get('question', ''),
                    "bestBid": round(best_bid, 4),
                    "last": round(yes_price, 4),
                    "endDate": market.get('endDateIso', market.get('endDate')),
                    "liquidity": market.get('liquidity'),
                    "volume": market.get('volume'),
                    "volume24hr": market.get('volume24hr'),
                }
                markets.append(market_info)
                
            except Exception as e:
                self._log(f"Error parsing market: {e}")
                continue
        
        # Sort by volume (descending) for most active markets first
        markets.sort(key=lambda m: float(m.get('volume24hr') or 0), reverse=True)
        
        self._log(f"  Found {len(markets)} markets for '{query}'")
        
        # Rate limit between queries
        time.sleep(RATE_LIMIT_DELAY)
        
        return markets[:limit]
    
    def fetch_all(self, queries: List[str], limit_per_query: int = 15) -> Dict:
        """
        Fetch markets for all specified queries.
        
        Args:
            queries: List of search terms
            limit_per_query: Max markets per query
            
        Returns:
            Complete data structure with all markets
        """
        timestamp = datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
        
        all_markets = {}
        counts = {}
        
        for query in queries:
            markets = self.fetch_markets_by_query(query, limit_per_query)
            all_markets[query] = markets
            counts[query] = len(markets)
        
        result = {
            "timestamp": timestamp,
            "counts": counts,
            "queries": queries,
            "markets": all_markets,
        }
        
        total_markets = sum(counts.values())
        self._log(f"Total: {total_markets} markets across {len(queries)} queries")
        
        return result


def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Fetch live Polymarket data",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Fetch default queries
  python3 scripts/fetch_polymarket_live.py
  
  # Fetch specific queries
  python3 scripts/fetch_polymarket_live.py --queries trump,bitcoin,ethereum
  
  # Custom output file
  python3 scripts/fetch_polymarket_live.py -o state/live-markets.json
  
  # Verbose mode
  python3 scripts/fetch_polymarket_live.py -v
"""
    )
    
    parser.add_argument(
        "-q", "--queries",
        type=str,
        help="Comma-separated list of queries (default: trump,bitcoin,ethereum,...)"
    )
    parser.add_argument(
        "-o", "--output",
        type=str,
        default="termux-hands-off/out/polymarket-compact.json",
        help="Output file path"
    )
    parser.add_argument(
        "-l", "--limit",
        type=int,
        default=15,
        help="Max markets per query (default: 15)"
    )
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Enable verbose output"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print to stdout instead of writing file"
    )
    
    args = parser.parse_args()
    
    # Parse queries
    if args.queries:
        queries = [q.strip() for q in args.queries.split(",")]
    else:
        queries = DEFAULT_QUERIES
    
    print(f"📊 Fetching Polymarket live data...")
    print(f"   Queries: {', '.join(queries)}")
    print()
    
    # Create fetcher and run
    fetcher = PolymarketFetcher(verbose=args.verbose)
    
    try:
        data = fetcher.fetch_all(queries, limit_per_query=args.limit)
    except KeyboardInterrupt:
        print("\n\nAborted by user")
        return 1
    except Exception as e:
        print(f"\n❌ Error: {e}")
        return 1
    
    # Output results
    total = sum(data["counts"].values())
    print(f"\n✅ Fetched {total} markets")
    
    for query, count in data["counts"].items():
        print(f"   {query}: {count}")
    
    if args.dry_run:
        print("\n--- OUTPUT ---")
        print(json.dumps(data, indent=2))
    else:
        # Write output file
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Atomic write
        tmp_path = output_path.with_suffix('.tmp')
        with open(tmp_path, 'w') as f:
            json.dump(data, f, indent=2)
        tmp_path.replace(output_path)
        
        print(f"\n📝 Written to: {output_path}")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
