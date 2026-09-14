"""
Polymarket Data Fetcher
=======================

Fetches prediction market data from Polymarket for arbitrage detection.
Integrates with existing hands-off-engine infrastructure.
"""

import json
import logging
import requests
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Any

from ..types import Platform, PredictionMarket

logger = logging.getLogger(__name__)


class PolymarketFetcher:
    """
    Fetches market data from Polymarket.

    Can either:
    1. Fetch live from API
    2. Read from cached polymarket-compact.json (synced by existing scripts)
    """

    BASE_URL = "https://gamma-api.polymarket.com"
    FALLBACK_URL = "https://clob.polymarket.com"

    def __init__(
        self,
        cache_path: Optional[Path] = None,
        use_cache: bool = True,
        timeout: int = 20,
    ):
        self.cache_path = cache_path
        self.use_cache = use_cache
        self.timeout = timeout
        self._session = requests.Session()
        self._session.headers.update({
            'User-Agent': 'hands-off-engine/1.0',
            'Accept': 'application/json',
        })

    def fetch_markets(
        self,
        active_only: bool = True,
        limit: int = 200,
        categories: Optional[List[str]] = None,
    ) -> List[PredictionMarket]:
        """
        Fetch markets from Polymarket.

        Args:
            active_only: Only fetch active markets
            limit: Maximum markets to fetch
            categories: Filter by categories (e.g., ['sports', 'politics'])

        Returns:
            List of PredictionMarket objects
        """
        # Try cache first if enabled
        if self.use_cache and self.cache_path and self.cache_path.exists():
            return self._load_from_cache()

        # Fetch live from API
        return self._fetch_live(active_only, limit, categories)

    def _fetch_live(
        self,
        active_only: bool,
        limit: int,
        categories: Optional[List[str]],
    ) -> List[PredictionMarket]:
        """Fetch directly from Polymarket API"""
        markets = []

        try:
            # Build URL
            url = f"{self.BASE_URL}/markets"
            params = {
                'limit': limit,
                'active': str(active_only).lower(),
            }

            response = self._session.get(url, params=params, timeout=self.timeout)
            response.raise_for_status()
            data = response.json()

            fetched_at = datetime.now(timezone.utc)

            for raw_market in data:
                market = self._parse_market(raw_market, fetched_at)
                if market:
                    # Apply category filter if specified
                    if categories:
                        tags = raw_market.get('tags', [])
                        if not any(c.lower() in [t.lower() for t in tags] for c in categories):
                            continue
                    markets.append(market)

            logger.info(f"Fetched {len(markets)} markets from Polymarket API")

        except requests.RequestException as e:
            logger.error(f"Failed to fetch from Polymarket: {e}")
            # Try fallback
            markets = self._fetch_fallback(limit)

        return markets

    def _fetch_fallback(self, limit: int) -> List[PredictionMarket]:
        """Fallback to CLOB API"""
        markets = []
        try:
            url = f"{self.FALLBACK_URL}/markets"
            response = self._session.get(url, timeout=self.timeout)
            response.raise_for_status()
            data = response.json()

            fetched_at = datetime.now(timezone.utc)

            for raw_market in data[:limit]:
                market = self._parse_market(raw_market, fetched_at)
                if market:
                    markets.append(market)

            logger.info(f"Fetched {len(markets)} markets from fallback API")

        except requests.RequestException as e:
            logger.error(f"Fallback fetch also failed: {e}")

        return markets

    def _load_from_cache(self) -> List[PredictionMarket]:
        """Load from cached polymarket-compact.json"""
        markets = []

        try:
            with open(self.cache_path, 'r') as f:
                data = json.load(f)

            # Handle both formats: list or {markets: {query: [markets]}}
            fetched_at = datetime.now(timezone.utc)

            if isinstance(data, list):
                raw_markets = data
            elif 'markets' in data:
                # Our compact format groups by query
                raw_markets = []
                for query, mlist in data['markets'].items():
                    raw_markets.extend(mlist)
            else:
                raw_markets = []

            for raw_market in raw_markets:
                market = self._parse_market(raw_market, fetched_at)
                if market:
                    markets.append(market)

            logger.info(f"Loaded {len(markets)} markets from cache")

        except Exception as e:
            logger.error(f"Failed to load from cache: {e}")

        return markets

    def _parse_market(
        self,
        raw: Dict[str, Any],
        fetched_at: datetime,
    ) -> Optional[PredictionMarket]:
        """Parse raw API response into PredictionMarket"""
        try:
            # Get market ID
            market_id = raw.get('id') or raw.get('slug') or raw.get('condition_id', '')
            if not market_id:
                return None

            # Get question
            question = raw.get('question') or raw.get('title', '')
            if not question:
                return None

            # Parse prices - try multiple formats
            yes_price, no_price = self._extract_prices(raw)
            if yes_price is None:
                return None

            # Get close time
            closes_at = None
            if 'end_date' in raw or 'endDate' in raw or 'closesAt' in raw:
                close_str = raw.get('end_date') or raw.get('endDate') or raw.get('closesAt')
                if close_str:
                    try:
                        closes_at = datetime.fromisoformat(close_str.replace('Z', '+00:00'))
                    except ValueError:
                        pass

            # Build market object
            return PredictionMarket(
                platform=Platform.POLYMARKET,
                market_id=str(market_id),
                question=question,
                yes_price=yes_price,
                no_price=no_price if no_price is not None else (1.0 - yes_price),
                volume_24h=self._safe_float(raw.get('volume24hr') or raw.get('volume')),
                liquidity=self._safe_float(raw.get('liquidity')),
                best_bid_yes=self._safe_float(raw.get('bestBid')),
                best_ask_yes=self._safe_float(raw.get('bestAsk')),
                closes_at=closes_at,
                fetched_at=fetched_at,
                raw_data=raw,
            )

        except Exception as e:
            logger.debug(f"Failed to parse market: {e}")
            return None

    def _extract_prices(self, raw: Dict) -> tuple[Optional[float], Optional[float]]:
        """Extract YES and NO prices from various API formats"""
        yes_price = None
        no_price = None

        # Format 1: outcomePrices array aligned with outcomes
        outcomes = raw.get('outcomes', [])
        prices = raw.get('outcomePrices', [])

        if outcomes and prices and len(outcomes) == len(prices):
            for i, outcome in enumerate(outcomes):
                if isinstance(outcome, str):
                    if outcome.lower() == 'yes':
                        yes_price = self._safe_float(prices[i])
                    elif outcome.lower() == 'no':
                        no_price = self._safe_float(prices[i])

        # Format 2: Direct price fields
        if yes_price is None:
            yes_price = self._safe_float(raw.get('last') or raw.get('price'))

        # Format 3: Contracts array
        if yes_price is None:
            contracts = raw.get('contracts', [])
            for c in contracts:
                name = (c.get('name') or c.get('outcome') or '').lower()
                if name == 'yes':
                    yes_price = self._safe_float(c.get('price') or c.get('lastPrice'))
                elif name == 'no':
                    no_price = self._safe_float(c.get('price') or c.get('lastPrice'))

        # Format 4: bestBuyYesCost
        if yes_price is None:
            yes_price = self._safe_float(raw.get('bestBuyYesCost'))

        return yes_price, no_price

    @staticmethod
    def _safe_float(val: Any) -> Optional[float]:
        """Safely convert to float"""
        if val is None:
            return None
        try:
            return float(val)
        except (ValueError, TypeError):
            return None

    def search_markets(self, query: str, limit: int = 50) -> List[PredictionMarket]:
        """Search markets by keyword"""
        markets = []

        try:
            url = f"{self.BASE_URL}/public-search"
            params = {'q': query, 'limit': limit}

            response = self._session.get(url, params=params, timeout=self.timeout)
            response.raise_for_status()
            data = response.json()

            fetched_at = datetime.now(timezone.utc)

            for raw_market in data:
                market = self._parse_market(raw_market, fetched_at)
                if market:
                    markets.append(market)

        except requests.RequestException as e:
            logger.error(f"Search failed: {e}")

        return markets
