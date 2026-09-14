"""
Kalshi Data Fetcher
===================

Fetches prediction market data from Kalshi for arbitrage detection.

Kalshi is a CFTC-regulated prediction market exchange offering binary
event contracts on politics, economics, and current events.

API Docs: https://trading-api.readme.io/reference/
"""

import json
import logging
import requests
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Any

from ..types import Platform, PredictionMarket

logger = logging.getLogger(__name__)


class KalshiFetcher:
    """
    Fetches market data from Kalshi.

    Kalshi has both public and authenticated APIs:
    - Public: Market listings, prices (no auth required)
    - Trading: Requires API key for placing orders

    For arbitrage detection, we only need the public API.
    """

    BASE_URL = "https://trading-api.kalshi.com/trade-api/v2"
    PUBLIC_URL = "https://api.elections.kalshi.com/v1"  # Public elections API

    def __init__(
        self,
        api_key: Optional[str] = None,
        cache_path: Optional[Path] = None,
        timeout: int = 20,
    ):
        self.api_key = api_key
        self.cache_path = cache_path
        self.timeout = timeout
        self._session = requests.Session()
        self._session.headers.update({
            'User-Agent': 'hands-off-engine/1.0',
            'Accept': 'application/json',
        })

        # Add auth header if API key provided
        if self.api_key:
            self._session.headers['Authorization'] = f'Bearer {self.api_key}'

    def fetch_markets(
        self,
        status: str = "open",
        limit: int = 200,
        series_ticker: Optional[str] = None,
    ) -> List[PredictionMarket]:
        """
        Fetch markets from Kalshi.

        Args:
            status: Market status filter (open, closed, settled)
            limit: Maximum markets to fetch
            series_ticker: Filter by series (e.g., "PRES" for presidential)

        Returns:
            List of PredictionMarket objects
        """
        markets = []

        try:
            # Use the public API endpoint
            url = f"{self.BASE_URL}/markets"
            params = {
                'status': status,
                'limit': min(limit, 200),  # Kalshi max is 200 per page
            }

            if series_ticker:
                params['series_ticker'] = series_ticker

            response = self._session.get(url, params=params, timeout=self.timeout)

            if response.status_code == 401:
                logger.warning("Kalshi API requires authentication, trying public endpoints")
                return self._fetch_public_markets(limit)

            response.raise_for_status()
            data = response.json()

            fetched_at = datetime.now(timezone.utc)

            raw_markets = data.get('markets', [])
            for raw_market in raw_markets:
                market = self._parse_market(raw_market, fetched_at)
                if market:
                    markets.append(market)

            # Handle pagination if needed
            cursor = data.get('cursor')
            while cursor and len(markets) < limit:
                params['cursor'] = cursor
                response = self._session.get(url, params=params, timeout=self.timeout)
                response.raise_for_status()
                data = response.json()

                for raw_market in data.get('markets', []):
                    market = self._parse_market(raw_market, fetched_at)
                    if market:
                        markets.append(market)

                cursor = data.get('cursor')

            logger.info(f"Fetched {len(markets)} markets from Kalshi")

        except requests.RequestException as e:
            logger.error(f"Failed to fetch from Kalshi: {e}")
            # Try public fallback
            markets = self._fetch_public_markets(limit)

        return markets[:limit]

    def _fetch_public_markets(self, limit: int) -> List[PredictionMarket]:
        """Fetch from public elections API (no auth required)"""
        markets = []

        try:
            # This endpoint typically works without auth
            url = f"{self.PUBLIC_URL}/events"

            response = self._session.get(url, timeout=self.timeout)
            response.raise_for_status()
            data = response.json()

            fetched_at = datetime.now(timezone.utc)

            events = data.get('events', data) if isinstance(data, dict) else data

            for event in events[:limit]:
                # Events contain nested markets
                nested_markets = event.get('markets', [])
                for raw_market in nested_markets:
                    raw_market['event_title'] = event.get('title', '')
                    market = self._parse_market(raw_market, fetched_at)
                    if market:
                        markets.append(market)

            logger.info(f"Fetched {len(markets)} markets from Kalshi public API")

        except requests.RequestException as e:
            logger.warning(f"Public API also failed: {e}")

        return markets

    def _parse_market(
        self,
        raw: Dict[str, Any],
        fetched_at: datetime,
    ) -> Optional[PredictionMarket]:
        """Parse Kalshi API response into PredictionMarket"""
        try:
            # Get market ID (ticker)
            market_id = raw.get('ticker') or raw.get('id', '')
            if not market_id:
                return None

            # Get question/title
            question = raw.get('title') or raw.get('subtitle') or raw.get('event_title', '')
            if not question:
                return None

            # Parse prices
            # Kalshi uses 'yes_bid', 'yes_ask', 'no_bid', 'no_ask' or 'last_price'
            yes_price = self._extract_yes_price(raw)
            if yes_price is None:
                return None

            no_price = self._extract_no_price(raw)
            if no_price is None:
                # Derive from YES price for binary markets
                no_price = 1.0 - yes_price

            # Get close time
            closes_at = None
            close_str = raw.get('close_time') or raw.get('expiration_time')
            if close_str:
                try:
                    closes_at = datetime.fromisoformat(close_str.replace('Z', '+00:00'))
                except ValueError:
                    pass

            # Volume
            volume = self._safe_float(raw.get('volume')) or self._safe_float(raw.get('volume_24h'))

            # Build market object
            return PredictionMarket(
                platform=Platform.KALSHI,
                market_id=str(market_id),
                question=question,
                yes_price=yes_price,
                no_price=no_price,
                volume_24h=volume,
                liquidity=self._safe_float(raw.get('liquidity')),
                best_bid_yes=self._safe_float(raw.get('yes_bid')),
                best_ask_yes=self._safe_float(raw.get('yes_ask')),
                best_bid_no=self._safe_float(raw.get('no_bid')),
                best_ask_no=self._safe_float(raw.get('no_ask')),
                closes_at=closes_at,
                fetched_at=fetched_at,
                raw_data=raw,
            )

        except Exception as e:
            logger.debug(f"Failed to parse Kalshi market: {e}")
            return None

    def _extract_yes_price(self, raw: Dict) -> Optional[float]:
        """Extract YES price from various Kalshi formats"""
        # Format 1: Direct price fields (cents, need to divide by 100)
        if 'yes_bid' in raw and 'yes_ask' in raw:
            bid = self._safe_float(raw.get('yes_bid'))
            ask = self._safe_float(raw.get('yes_ask'))
            if bid is not None and ask is not None:
                # Kalshi prices are in cents (0-100)
                mid = (bid + ask) / 2
                return mid / 100 if mid > 1 else mid

        # Format 2: last_price
        last = self._safe_float(raw.get('last_price') or raw.get('lastPrice'))
        if last is not None:
            return last / 100 if last > 1 else last

        # Format 3: yes_price directly
        yes = self._safe_float(raw.get('yes_price'))
        if yes is not None:
            return yes / 100 if yes > 1 else yes

        # Format 4: result probabilities
        prob = self._safe_float(raw.get('probability') or raw.get('prob'))
        if prob is not None:
            return prob / 100 if prob > 1 else prob

        return None

    def _extract_no_price(self, raw: Dict) -> Optional[float]:
        """Extract NO price from Kalshi data"""
        if 'no_bid' in raw and 'no_ask' in raw:
            bid = self._safe_float(raw.get('no_bid'))
            ask = self._safe_float(raw.get('no_ask'))
            if bid is not None and ask is not None:
                mid = (bid + ask) / 2
                return mid / 100 if mid > 1 else mid

        no = self._safe_float(raw.get('no_price'))
        if no is not None:
            return no / 100 if no > 1 else no

        return None

    @staticmethod
    def _safe_float(val: Any) -> Optional[float]:
        """Safely convert to float"""
        if val is None:
            return None
        try:
            return float(val)
        except (ValueError, TypeError):
            return None

    def fetch_series(self) -> List[Dict[str, Any]]:
        """Fetch available market series (categories)"""
        series = []

        try:
            url = f"{self.BASE_URL}/series"
            response = self._session.get(url, timeout=self.timeout)
            response.raise_for_status()
            data = response.json()
            series = data.get('series', [])

        except requests.RequestException as e:
            logger.error(f"Failed to fetch Kalshi series: {e}")

        return series

    def search_markets(self, query: str, limit: int = 50) -> List[PredictionMarket]:
        """Search Kalshi markets by keyword"""
        # Kalshi doesn't have a search endpoint, so we filter locally
        all_markets = self.fetch_markets(limit=500)
        query_lower = query.lower()

        return [
            m for m in all_markets
            if query_lower in m.question.lower()
        ][:limit]
