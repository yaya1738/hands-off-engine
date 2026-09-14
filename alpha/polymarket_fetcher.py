#!/usr/bin/env python3
"""
Enhanced Polymarket Data Fetcher
================================

Fetches comprehensive market data from Polymarket including:
- Volume data (for variance/volume ratio calculation)
- Creation date (for newness detection)
- Full order book when available
- Spread metrics at source

This provides the data needed for immediate profit opportunity detection.

Usage:
    from alpha.polymarket_fetcher import PolymarketFetcher

    fetcher = PolymarketFetcher()
    markets = fetcher.fetch_all()
    new_markets = fetcher.fetch_new_markets(hours=24)
"""

import json
import os
import time
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict

try:
    import requests
except ImportError:
    requests = None


@dataclass
class EnhancedMarket:
    """Enhanced market data with spread and order flow fields."""
    slug: str
    question: str
    category: str

    # Pricing
    bestBid: float
    bestAsk: float
    last: float
    mid: float

    # Volume and activity
    volume: Optional[float]
    volume_24h: Optional[float]
    trade_count: Optional[int]

    # Timing
    createdAt: Optional[str]
    endDate: Optional[str]
    age_hours: Optional[float]

    # Spread metrics (calculated at fetch time)
    spread_absolute: float
    spread_pct: float

    # Liquidity indicators
    liquidity_score: Optional[float]

    # Raw data for debugging
    raw: Dict


class PolymarketFetcher:
    """
    Fetches enhanced market data from Polymarket APIs.

    Supports multiple API endpoints:
    - Gamma API: Primary source with full market data
    - CLOB API: Order book and trade data (when available)
    """

    # API endpoints
    GAMMA_API = "https://gamma-api.polymarket.com/markets"
    CLOB_API = "https://clob.polymarket.com"

    # Default parameters
    DEFAULT_LIMIT = 500
    RETRY_COUNT = 3
    RETRY_DELAY = 2

    def __init__(self, cache_path: Optional[Path] = None):
        """
        Initialize the fetcher.

        Args:
            cache_path: Optional path to cache fetched data
        """
        if requests is None:
            raise ImportError("requests library required: pip install requests")

        self.cache_path = Path(cache_path) if cache_path else None
        self.session = requests.Session()
        self.session.headers.update({
            'Accept': 'application/json',
            'User-Agent': 'HandsOffEngine/1.0'
        })

    def _safe_float(self, value: Any) -> Optional[float]:
        """Safely convert value to float."""
        if value is None:
            return None
        try:
            return float(value)
        except (ValueError, TypeError):
            return None

    def _parse_datetime(self, value: Any) -> Optional[datetime]:
        """Parse datetime string to datetime object."""
        if not value:
            return None
        try:
            if isinstance(value, datetime):
                return value
            # Handle various formats
            for fmt in ['%Y-%m-%dT%H:%M:%S.%fZ', '%Y-%m-%dT%H:%M:%SZ', '%Y-%m-%dT%H:%M:%S']:
                try:
                    return datetime.strptime(str(value), fmt).replace(tzinfo=timezone.utc)
                except ValueError:
                    continue
            # Try ISO format as fallback
            return datetime.fromisoformat(str(value).replace('Z', '+00:00'))
        except Exception:
            return None

    def _calculate_age_hours(self, created_at: Optional[str]) -> Optional[float]:
        """Calculate market age in hours."""
        dt = self._parse_datetime(created_at)
        if not dt:
            return None
        now = datetime.now(timezone.utc)
        return (now - dt).total_seconds() / 3600

    def _extract_price(self, market: Dict, key: str, default: float = 0.0) -> float:
        """Extract a price from various possible locations in market data."""
        # Direct key
        if key in market:
            val = self._safe_float(market[key])
            if val is not None:
                return val

        # Check in outcomes
        outcomes = market.get('outcomes', [])
        outcome_prices = market.get('outcomePrices', [])

        if isinstance(outcomes, list) and isinstance(outcome_prices, list):
            for i, outcome in enumerate(outcomes):
                name = outcome if isinstance(outcome, str) else outcome.get('name', '')
                if name.lower() == 'yes' and i < len(outcome_prices):
                    val = self._safe_float(outcome_prices[i])
                    if val is not None:
                        return val

        # Check in contracts
        contracts = market.get('contracts', [])
        for contract in contracts:
            if isinstance(contract, dict):
                name = contract.get('name', '') or contract.get('outcome', '')
                if name.lower() == 'yes':
                    for price_key in [key, 'price', 'lastPrice', 'bestBuyYesCost']:
                        val = self._safe_float(contract.get(price_key))
                        if val is not None:
                            return val

        return default

    def _extract_volume(self, market: Dict) -> Optional[float]:
        """Extract volume from market data."""
        for key in ['volume', 'volume24hr', 'volumeNum', 'totalVolume']:
            val = self._safe_float(market.get(key))
            if val is not None:
                return val
        return None

    def _fetch_with_retry(self, url: str, params: Dict = None) -> Optional[Any]:
        """Fetch URL with retry logic."""
        for attempt in range(self.RETRY_COUNT):
            try:
                response = self.session.get(url, params=params, timeout=30)
                response.raise_for_status()
                return response.json()
            except Exception as e:
                if attempt < self.RETRY_COUNT - 1:
                    time.sleep(self.RETRY_DELAY * (attempt + 1))
                else:
                    print(f"Failed to fetch {url}: {e}")
                    return None
        return None

    def fetch_all(self, limit: int = None, active_only: bool = True) -> List[EnhancedMarket]:
        """
        Fetch all markets with enhanced data.

        Args:
            limit: Maximum markets to fetch
            active_only: Only fetch active markets

        Returns:
            List of EnhancedMarket objects
        """
        params = {
            'limit': limit or self.DEFAULT_LIMIT,
            'active': str(active_only).lower()
        }

        data = self._fetch_with_retry(self.GAMMA_API, params)
        if not data:
            return []

        markets = []
        for raw in data:
            market = self._parse_market(raw)
            if market:
                markets.append(market)

        return markets

    def fetch_new_markets(self, hours: int = 24) -> List[EnhancedMarket]:
        """
        Fetch markets created within the last N hours.

        New markets typically have:
        - Wider spreads (inefficient)
        - Higher variance (price discovery)
        - Immediate profit opportunities

        Args:
            hours: Fetch markets created within this many hours

        Returns:
            List of new EnhancedMarket objects sorted by age
        """
        all_markets = self.fetch_all()

        # Filter by age
        new_markets = [
            m for m in all_markets
            if m.age_hours is not None and m.age_hours <= hours
        ]

        # Sort by newest first
        new_markets.sort(key=lambda m: m.age_hours or float('inf'))

        return new_markets

    def fetch_high_spread_markets(self, min_spread_pct: float = 0.05) -> List[EnhancedMarket]:
        """
        Fetch markets with spreads above threshold.

        High spread = immediate market making profit.

        Args:
            min_spread_pct: Minimum spread percentage (0.05 = 5%)

        Returns:
            List of high-spread markets sorted by spread
        """
        all_markets = self.fetch_all()

        high_spread = [
            m for m in all_markets
            if m.spread_pct >= min_spread_pct
        ]

        # Sort by highest spread first (most profit potential)
        high_spread.sort(key=lambda m: m.spread_pct, reverse=True)

        return high_spread

    def _parse_market(self, raw: Dict) -> Optional[EnhancedMarket]:
        """Parse raw API response into EnhancedMarket."""
        slug = raw.get('slug') or raw.get('id') or ''
        if not slug:
            return None

        question = raw.get('question') or raw.get('title') or ''
        if not question:
            return None

        # Extract pricing
        best_bid = self._extract_price(raw, 'bestBid', 0.0)
        last = self._extract_price(raw, 'last', 0.5)
        best_ask = self._extract_price(raw, 'bestAsk', last)  # Default to last if no ask

        # If no explicit ask, infer from last trade
        if best_ask == 0 or best_ask == last:
            best_ask = last

        mid = (best_bid + best_ask) / 2 if best_bid > 0 else last

        # Calculate spread
        spread_abs = best_ask - best_bid if best_bid > 0 else 0
        spread_pct = spread_abs / mid if mid > 0 else 0

        # Volume
        volume = self._extract_volume(raw)
        volume_24h = self._safe_float(raw.get('volume24hr'))

        # Timing
        created_at = raw.get('createdAt') or raw.get('created_at')
        end_date = raw.get('endDate') or raw.get('end_date')
        age_hours = self._calculate_age_hours(created_at)

        # Category inference
        category = raw.get('category') or raw.get('query') or self._infer_category(question)

        return EnhancedMarket(
            slug=slug,
            question=question,
            category=category,
            bestBid=best_bid,
            bestAsk=best_ask,
            last=last,
            mid=mid,
            volume=volume,
            volume_24h=volume_24h,
            trade_count=raw.get('tradeCount'),
            createdAt=created_at,
            endDate=end_date,
            age_hours=round(age_hours, 2) if age_hours else None,
            spread_absolute=round(spread_abs, 4),
            spread_pct=round(spread_pct, 4),
            liquidity_score=raw.get('liquidityNum'),
            raw=raw
        )

    def _infer_category(self, question: str) -> str:
        """Infer category from question text."""
        q_lower = question.lower()

        categories = {
            'crypto': ['bitcoin', 'btc', 'ethereum', 'eth', 'crypto', 'token', 'coin'],
            'politics': ['trump', 'biden', 'election', 'president', 'congress', 'senate', 'vote'],
            'sports': ['nba', 'nfl', 'mlb', 'nhl', 'soccer', 'football', 'basketball', 'championship'],
            'economics': ['fed', 'inflation', 'gdp', 'unemployment', 'rate', 'economy'],
        }

        for cat, keywords in categories.items():
            if any(kw in q_lower for kw in keywords):
                return cat

        return 'other'

    def to_compact_format(self, markets: List[EnhancedMarket]) -> Dict:
        """
        Convert to compact format compatible with existing pipeline.

        Adds enhanced fields for spread analysis.
        """
        by_category: Dict[str, List[Dict]] = {}

        for market in markets:
            cat = market.category
            if cat not in by_category:
                by_category[cat] = []

            by_category[cat].append({
                'slug': market.slug,
                'question': market.question,
                'query': cat,
                'bestBid': market.bestBid,
                'bestAsk': market.bestAsk,
                'last': market.last,
                'endDate': market.endDate,
                # Enhanced fields
                'volume': market.volume,
                'createdAt': market.createdAt,
                'age_hours': market.age_hours,
                'spread_pct': market.spread_pct,
            })

        return {
            'timestamp': datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ'),
            'counts': {cat: len(mkts) for cat, mkts in by_category.items()},
            'queries': list(by_category.keys()),
            'markets': by_category
        }

    def save_enhanced_snapshot(self, output_path: Path, markets: List[EnhancedMarket] = None):
        """
        Save enhanced market snapshot for spread analysis.

        Args:
            output_path: Path to save JSON
            markets: Markets to save (fetches if None)
        """
        if markets is None:
            markets = self.fetch_all()

        data = self.to_compact_format(markets)

        output_path.parent.mkdir(parents=True, exist_ok=True)

        tmp_path = output_path.with_suffix('.tmp')
        with open(tmp_path, 'w') as f:
            json.dump(data, f, indent=2)
        tmp_path.replace(output_path)


def main():
    """CLI entry point for testing."""
    import sys

    repo_root = Path(__file__).parent.parent
    output_path = repo_root / 'state' / 'polymarket-enhanced.json'

    print("Fetching enhanced Polymarket data...")
    print()

    fetcher = PolymarketFetcher()

    # Fetch all markets
    markets = fetcher.fetch_all()
    print(f"Fetched {len(markets)} markets")

    # Find new markets (last 24 hours)
    new_markets = [m for m in markets if m.age_hours is not None and m.age_hours <= 24]
    print(f"New markets (< 24h): {len(new_markets)}")

    # Find high-spread markets
    high_spread = [m for m in markets if m.spread_pct >= 0.05]
    print(f"High spread (>= 5%): {len(high_spread)}")

    print()
    print("=" * 70)
    print("TOP IMMEDIATE PROFIT OPPORTUNITIES (High Spread + New)")
    print("=" * 70)
    print()

    # Score by combined opportunity
    def opportunity_score(m):
        spread_score = min(1.0, m.spread_pct / 0.1)  # 10% = max
        newness_score = 1.0 if m.age_hours and m.age_hours < 2 else (
            0.5 if m.age_hours and m.age_hours < 24 else 0.1
        )
        return 0.6 * spread_score + 0.4 * newness_score

    markets.sort(key=opportunity_score, reverse=True)

    for i, m in enumerate(markets[:15], 1):
        score = opportunity_score(m)
        age_str = f"{m.age_hours:.1f}h" if m.age_hours else "?"
        print(f"{i:2d}. [Score: {score:.2f}] Spread: {m.spread_pct:.1%} | Age: {age_str}")
        print(f"    {m.question[:60]}...")
        print(f"    Bid: {m.bestBid:.3f} | Ask: {m.bestAsk:.3f} | Mid: {m.mid:.3f}")
        if m.volume:
            print(f"    Volume: ${m.volume:,.0f}")
        print()

    # Save enhanced snapshot
    fetcher.save_enhanced_snapshot(output_path, markets)
    print(f"\nSaved enhanced data to: {output_path}")

    return 0


if __name__ == '__main__':
    import sys
    sys.exit(main())
