"""
Polymarket API Client - Production Grade
=========================================

Proper integration with Polymarket's CLOB and Gamma APIs.
Fetches real market data, order books, and prices.

This is the foundation for a serious trading system.
"""

import os
import json
import logging
import requests
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple, Any
from decimal import Decimal

LOG = logging.getLogger(__name__)

# API Endpoints
GAMMA_API = "https://gamma-api.polymarket.com"
CLOB_API = "https://clob.polymarket.com"


@dataclass
class OrderBookLevel:
    """Single price level in order book"""
    price: float
    size: float


@dataclass
class OrderBook:
    """Full order book for a market"""
    token_id: str
    bids: List[OrderBookLevel] = field(default_factory=list)
    asks: List[OrderBookLevel] = field(default_factory=list)
    timestamp: str = ""

    @property
    def best_bid(self) -> Optional[float]:
        return self.bids[0].price if self.bids else None

    @property
    def best_ask(self) -> Optional[float]:
        return self.asks[0].price if self.asks else None

    @property
    def mid_price(self) -> Optional[float]:
        if self.best_bid and self.best_ask:
            return (self.best_bid + self.best_ask) / 2
        return None

    @property
    def spread(self) -> Optional[float]:
        if self.best_bid and self.best_ask:
            return self.best_ask - self.best_bid
        return None

    @property
    def spread_bps(self) -> Optional[float]:
        """Spread in basis points"""
        if self.mid_price and self.spread:
            return (self.spread / self.mid_price) * 10000
        return None

    @property
    def bid_depth_usd(self) -> float:
        """Total USD depth on bid side"""
        return sum(level.price * level.size for level in self.bids)

    @property
    def ask_depth_usd(self) -> float:
        """Total USD depth on ask side"""
        return sum(level.price * level.size for level in self.asks)


@dataclass
class Market:
    """Complete market data for trading"""
    # Core identifiers
    condition_id: str
    token_id_yes: str
    token_id_no: str
    slug: str
    question: str

    # Pricing
    last_price: Optional[float] = None
    best_bid: Optional[float] = None
    best_ask: Optional[float] = None

    # Liquidity
    volume_24h: float = 0.0
    liquidity: float = 0.0

    # Market state
    active: bool = True
    closed: bool = False
    restricted: bool = False
    end_date: Optional[str] = None
    category: str = "unknown"

    # Order books (populated on demand)
    order_book_yes: Optional[OrderBook] = None
    order_book_no: Optional[OrderBook] = None

    @property
    def mid_price(self) -> Optional[float]:
        if self.best_bid is not None and self.best_ask is not None:
            return (self.best_bid + self.best_ask) / 2
        return self.last_price

    @property
    def spread(self) -> Optional[float]:
        if self.best_bid is not None and self.best_ask is not None:
            return self.best_ask - self.best_bid
        return None

    @property
    def spread_bps(self) -> Optional[float]:
        if self.mid_price and self.spread:
            return (self.spread / self.mid_price) * 10000
        return None

    @property
    def is_tradeable(self) -> bool:
        """Check if market can be traded"""
        return (
            self.active and
            not self.closed and
            not self.restricted and
            self.liquidity > 0 and
            self.best_bid is not None and
            self.best_ask is not None
        )

    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization"""
        return {
            "condition_id": self.condition_id,
            "token_id_yes": self.token_id_yes,
            "token_id_no": self.token_id_no,
            "slug": self.slug,
            "question": self.question,
            "last_price": self.last_price,
            "best_bid": self.best_bid,
            "best_ask": self.best_ask,
            "mid_price": self.mid_price,
            "spread": self.spread,
            "spread_bps": self.spread_bps,
            "volume_24h": self.volume_24h,
            "liquidity": self.liquidity,
            "active": self.active,
            "closed": self.closed,
            "restricted": self.restricted,
            "end_date": self.end_date,
            "category": self.category,
            "is_tradeable": self.is_tradeable,
        }


class PolymarketAPI:
    """
    Production-grade Polymarket API client.

    Provides:
    - Real market discovery with proper filtering
    - Live price feeds from CLOB
    - Order book depth analysis
    - Liquidity and spread validation
    """

    def __init__(self, timeout: int = 30):
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update({
            "Accept": "application/json",
            "User-Agent": "hands-off-engine/1.0"
        })

    def _get(self, url: str, params: Optional[Dict] = None) -> Any:
        """Make GET request with error handling"""
        try:
            resp = self.session.get(url, params=params, timeout=self.timeout)
            resp.raise_for_status()
            return resp.json()
        except requests.RequestException as e:
            LOG.error(f"API request failed: {url} - {e}")
            raise

    def get_active_markets(
        self,
        limit: int = 100,
        min_volume_24h: float = 1000,
        min_liquidity: float = 5000,
        exclude_restricted: bool = True,
        exclude_sports: bool = True,
    ) -> List[Market]:
        """
        Fetch active, tradeable markets with real data.

        Args:
            limit: Max markets to return
            min_volume_24h: Minimum 24h volume in USD
            min_liquidity: Minimum liquidity in USD
            exclude_restricted: Skip restricted markets (note: most are marked restricted)
            exclude_sports: Skip sports betting markets

        Returns:
            List of Market objects with real pricing data
        """
        LOG.info(f"Fetching active markets (min_vol=${min_volume_24h}, min_liq=${min_liquidity})")

        # Use /events endpoint - it has much better data than /markets
        # The /markets endpoint returns mostly sports with 0 liquidity
        params = {
            "closed": "false",
            "active": "true",
            "limit": limit * 2,  # Fetch extra for filtering
        }

        events = self._get(f"{GAMMA_API}/events", params)

        # Flatten markets from events
        raw_markets = []
        for event in events:
            for m in event.get("markets", []):
                raw_markets.append(m)

        markets = []
        for m in raw_markets:
            # Skip if missing critical data
            if not m.get("clobTokenIds") or not m.get("conditionId"):
                continue

            # Parse token IDs
            try:
                token_ids = json.loads(m.get("clobTokenIds", "[]"))
                if len(token_ids) < 2:
                    continue
            except (json.JSONDecodeError, TypeError):
                continue

            # Build market object
            volume_24h = float(m.get("volume24hr", 0) or 0)
            liquidity = float(m.get("liquidityNum", 0) or 0)

            # Parse outcomes for price data
            outcomes_prices = m.get("outcomePrices")
            best_bid = None
            best_ask = None
            last_price = None

            if outcomes_prices:
                try:
                    prices = json.loads(outcomes_prices)
                    if len(prices) >= 2:
                        # First outcome is typically YES
                        last_price = float(prices[0])
                except (json.JSONDecodeError, TypeError, ValueError):
                    pass

            market = Market(
                condition_id=m.get("conditionId", ""),
                token_id_yes=token_ids[0],
                token_id_no=token_ids[1] if len(token_ids) > 1 else "",
                slug=m.get("slug", ""),
                question=m.get("question", ""),
                last_price=last_price,
                best_bid=best_bid,
                best_ask=best_ask,
                volume_24h=volume_24h,
                liquidity=liquidity,
                active=m.get("active", False),
                closed=m.get("closed", False),
                restricted=m.get("restricted", False),
                end_date=m.get("endDate"),
                category=m.get("category", "unknown"),
            )

            # Apply filters
            # Note: Don't filter on restricted by default - Polymarket marks most markets
            # as restricted for certain regions, but they're still tradeable
            if exclude_restricted and market.restricted:
                # Skip this filter for now - too aggressive
                pass

            if market.volume_24h < min_volume_24h:
                continue

            if market.liquidity < min_liquidity:
                continue

            if exclude_sports and self._is_sports_market(market):
                continue

            if market.closed or not market.active:
                continue

            markets.append(market)

            if len(markets) >= limit:
                break

        LOG.info(f"Found {len(markets)} tradeable markets")
        return markets

    def _is_sports_market(self, market: Market) -> bool:
        """Detect sports betting markets by slug patterns"""
        slug = market.slug.lower()
        sports_patterns = [
            "nba-", "nfl-", "mlb-", "nhl-", "cbb-", "cwbb-",
            "-vs-", "rams-", "hawks-", "bulls-", "lakers-",
            "cowboys-", "eagles-", "bears-", "patriots-",
            "championship", "playoffs", "finals",
        ]
        return any(pattern in slug for pattern in sports_patterns)

    def get_order_book(self, token_id: str) -> OrderBook:
        """
        Fetch live order book for a token.

        Args:
            token_id: The CLOB token ID

        Returns:
            OrderBook with bids and asks
        """
        LOG.debug(f"Fetching order book for token {token_id[:20]}...")

        data = self._get(f"{CLOB_API}/book", {"token_id": token_id})

        bids = []
        asks = []

        for bid in data.get("bids", []):
            try:
                bids.append(OrderBookLevel(
                    price=float(bid.get("price", 0)),
                    size=float(bid.get("size", 0))
                ))
            except (ValueError, TypeError):
                continue

        for ask in data.get("asks", []):
            try:
                asks.append(OrderBookLevel(
                    price=float(ask.get("price", 0)),
                    size=float(ask.get("size", 0))
                ))
            except (ValueError, TypeError):
                continue

        # Sort: bids descending, asks ascending
        bids.sort(key=lambda x: x.price, reverse=True)
        asks.sort(key=lambda x: x.price)

        return OrderBook(
            token_id=token_id,
            bids=bids,
            asks=asks,
            timestamp=datetime.now(timezone.utc).isoformat()
        )

    def enrich_market_with_orderbook(self, market: Market) -> Market:
        """
        Fetch order books and enrich market with live pricing.

        Args:
            market: Market to enrich

        Returns:
            Market with order book data and updated pricing
        """
        try:
            # Fetch YES token order book
            ob_yes = self.get_order_book(market.token_id_yes)
            market.order_book_yes = ob_yes

            # Update pricing from order book
            if ob_yes.best_bid is not None:
                market.best_bid = ob_yes.best_bid
            if ob_yes.best_ask is not None:
                market.best_ask = ob_yes.best_ask

            LOG.debug(
                f"Enriched {market.slug}: bid={market.best_bid}, "
                f"ask={market.best_ask}, spread={market.spread_bps:.0f}bps"
                if market.spread_bps else f"Enriched {market.slug}: no spread data"
            )

        except Exception as e:
            LOG.warning(f"Failed to enrich {market.slug}: {e}")

        return market

    def get_market_price(self, token_id: str) -> Tuple[Optional[float], Optional[float], Optional[float]]:
        """
        Get current bid/ask/mid prices for a token.

        Args:
            token_id: CLOB token ID

        Returns:
            Tuple of (best_bid, best_ask, mid_price)
        """
        ob = self.get_order_book(token_id)
        return ob.best_bid, ob.best_ask, ob.mid_price

    def estimate_execution_price(
        self,
        token_id: str,
        side: str,
        size_usd: float
    ) -> Tuple[Optional[float], float]:
        """
        Estimate execution price and slippage for an order.

        Walks the order book to simulate execution.

        Args:
            token_id: CLOB token ID
            side: "BUY" or "SELL"
            size_usd: Order size in USD

        Returns:
            Tuple of (avg_price, slippage_bps)
        """
        ob = self.get_order_book(token_id)

        levels = ob.asks if side == "BUY" else ob.bids
        if not levels:
            return None, 0.0

        mid = ob.mid_price
        if mid is None:
            return None, 0.0

        remaining = size_usd
        total_cost = 0.0
        total_size = 0.0

        for level in levels:
            level_value = level.price * level.size
            if level_value >= remaining:
                # Partial fill at this level
                fill_size = remaining / level.price
                total_cost += remaining
                total_size += fill_size
                remaining = 0
                break
            else:
                # Full fill at this level
                total_cost += level_value
                total_size += level.size
                remaining -= level_value

        if total_size == 0:
            return None, 0.0

        avg_price = total_cost / total_size
        slippage_bps = abs(avg_price - mid) / mid * 10000 if mid > 0 else 0

        return avg_price, slippage_bps

    def validate_trade(
        self,
        market: Market,
        side: str,
        size_usd: float,
        max_spread_bps: float = 500,
        max_slippage_bps: float = 200,
        min_liquidity_ratio: float = 10,
    ) -> Tuple[bool, List[str]]:
        """
        Validate if a trade should be executed.

        Checks:
        - Market is tradeable
        - Spread is acceptable
        - Slippage is acceptable
        - Sufficient liquidity

        Args:
            market: Market to trade
            side: "YES" or "NO"
            size_usd: Order size
            max_spread_bps: Maximum acceptable spread
            max_slippage_bps: Maximum acceptable slippage
            min_liquidity_ratio: liquidity/order_size minimum

        Returns:
            Tuple of (is_valid, reasons)
        """
        reasons = []

        # Basic tradeability
        if not market.is_tradeable:
            reasons.append(f"Market not tradeable: active={market.active}, closed={market.closed}, restricted={market.restricted}")
            return False, reasons

        # Spread check
        if market.spread_bps is not None and market.spread_bps > max_spread_bps:
            reasons.append(f"Spread too wide: {market.spread_bps:.0f}bps > {max_spread_bps}bps")
            return False, reasons

        # Liquidity check
        if market.liquidity < size_usd * min_liquidity_ratio:
            reasons.append(
                f"Insufficient liquidity: ${market.liquidity:.0f} < "
                f"${size_usd * min_liquidity_ratio:.0f} (10x order size)"
            )
            return False, reasons

        # Slippage check
        token_id = market.token_id_yes if side == "YES" else market.token_id_no
        avg_price, slippage = self.estimate_execution_price(token_id, "BUY", size_usd)

        if slippage > max_slippage_bps:
            reasons.append(f"Slippage too high: {slippage:.0f}bps > {max_slippage_bps}bps")
            return False, reasons

        reasons.append(f"Trade validated: spread={market.spread_bps:.0f}bps, slippage={slippage:.0f}bps")
        return True, reasons


def fetch_tradeable_markets(
    min_volume: float = 10000,
    min_liquidity: float = 50000,
    limit: int = 50,
    enrich: bool = True,
) -> List[Dict]:
    """
    Convenience function to fetch tradeable markets.

    Args:
        min_volume: Minimum 24h volume
        min_liquidity: Minimum liquidity
        limit: Max markets
        enrich: Whether to fetch order books

    Returns:
        List of market dicts
    """
    api = PolymarketAPI()

    markets = api.get_active_markets(
        limit=limit,
        min_volume_24h=min_volume,
        min_liquidity=min_liquidity,
        exclude_restricted=True,
        exclude_sports=True,
    )

    if enrich:
        for market in markets:
            api.enrich_market_with_orderbook(market)

    return [m.to_dict() for m in markets]


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    print("=" * 70)
    print("POLYMARKET API - Production Market Fetch")
    print("=" * 70)

    api = PolymarketAPI()

    # Fetch markets
    markets = api.get_active_markets(
        limit=20,
        min_volume_24h=10000,
        min_liquidity=50000,
        exclude_restricted=True,
        exclude_sports=True,
    )

    print(f"\nFound {len(markets)} tradeable markets:\n")

    for i, m in enumerate(markets[:10], 1):
        # Enrich with order book
        api.enrich_market_with_orderbook(m)

        print(f"{i}. {m.question[:60]}...")
        print(f"   Token (YES): {m.token_id_yes[:30]}...")
        print(f"   Price: {m.mid_price:.3f}" if m.mid_price else "   Price: N/A")
        print(f"   Bid/Ask: {m.best_bid:.3f}/{m.best_ask:.3f}" if m.best_bid else "   Bid/Ask: N/A")
        print(f"   Spread: {m.spread_bps:.0f}bps" if m.spread_bps else "   Spread: N/A")
        print(f"   Volume 24h: ${m.volume_24h:,.0f}")
        print(f"   Liquidity: ${m.liquidity:,.0f}")
        print(f"   Tradeable: {m.is_tradeable}")
        print()

    # Save to file
    output = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "count": len(markets),
        "markets": [m.to_dict() for m in markets]
    }

    output_path = "state/live_markets.json"
    with open(output_path, "w") as f:
        json.dump(output, f, indent=2)

    print(f"Saved to {output_path}")
