#!/usr/bin/env python3
"""
ABCFC LIVE - Real Order Book + Order Flow Integration

Connects ABCFC to:
1. Real Polymarket order book (L2 data)
2. Order flow analysis
3. Live position valuation

Created by: Yair Siegel
"""

import math
import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Callable, Tuple
from datetime import datetime, timedelta

# Import pure math and unified system
from executor.math.abcfc_pure import ABCFC2D, DensityFunc
from executor.math.abcfc_unified import (
    PositionABCFC,
    UnifiedABCFCHierarchy,
    create_binary_market_density,
    create_flow_adjusted_density
)


# ============================================================================
# ORDER BOOK UTILITIES
# ============================================================================

@dataclass
class OrderBookLevel:
    """Single price level in order book."""
    price: float
    size: float


@dataclass
class OrderBook:
    """Order book with bids and asks."""
    bids: List[OrderBookLevel] = field(default_factory=list)  # Sorted high to low
    asks: List[OrderBookLevel] = field(default_factory=list)  # Sorted low to high
    timestamp: float = 0.0

    @property
    def best_bid(self) -> float:
        return self.bids[0].price if self.bids else 0.0

    @property
    def best_ask(self) -> float:
        return self.asks[0].price if self.asks else 1.0

    @property
    def mid_price(self) -> float:
        return (self.best_bid + self.best_ask) / 2

    @property
    def spread(self) -> float:
        return self.best_ask - self.best_bid

    def walk_book_sell(self, shares: float) -> float:
        """
        Calculate proceeds from selling shares by walking the book.

        Returns total proceeds (walking down bids).
        """
        remaining = shares
        proceeds = 0.0

        for level in self.bids:
            if remaining <= 0:
                break
            fill = min(remaining, level.size)
            proceeds += fill * level.price
            remaining -= fill

        # If we couldn't fill everything, remaining shares are worth 0
        # (or we could assume worst price)
        if remaining > 0:
            # Assume we'd have to sell at 0 for remaining
            pass

        return proceeds

    def walk_book_buy(self, shares: float) -> float:
        """
        Calculate cost to buy shares by walking the book.

        Returns total cost (walking up asks).
        """
        remaining = shares
        cost = 0.0

        for level in self.asks:
            if remaining <= 0:
                break
            fill = min(remaining, level.size)
            cost += fill * level.price
            remaining -= fill

        # If we couldn't fill, remaining would cost $1 each (worst case binary)
        if remaining > 0:
            cost += remaining * 1.0

        return cost

    def liquidation_value(self, shares: float, side: str) -> float:
        """
        Get liquidation value for a position.

        side: "YES" (we hold YES shares, need to sell) or "NO" (we hold NO shares, need to buy YES to close)
        """
        if side == "YES":
            return self.walk_book_sell(shares)
        else:
            # For NO: we need to buy back YES
            return -self.walk_book_buy(shares)


def parse_polymarket_book(book_data) -> OrderBook:
    """Parse Polymarket API order book response (handles both dict and object)."""
    bids = []
    asks = []

    # Handle both dict and object (OrderBookSummary from py_clob_client)
    bids_raw = getattr(book_data, 'bids', None) or book_data.get("bids", []) if isinstance(book_data, dict) else []
    asks_raw = getattr(book_data, 'asks', None) or book_data.get("asks", []) if isinstance(book_data, dict) else []

    # If book_data is an object with .bids/.asks attributes
    if bids_raw is None:
        bids_raw = getattr(book_data, 'bids', []) or []
    if asks_raw is None:
        asks_raw = getattr(book_data, 'asks', []) or []

    for bid in bids_raw:
        # Handle both dict and OrderSummary object
        if hasattr(bid, 'price'):
            bids.append(OrderBookLevel(float(bid.price), float(bid.size)))
        elif isinstance(bid, dict):
            bids.append(OrderBookLevel(
                price=float(bid.get("price", 0)),
                size=float(bid.get("size", 0))
            ))

    for ask in asks_raw:
        if hasattr(ask, 'price'):
            asks.append(OrderBookLevel(float(ask.price), float(ask.size)))
        elif isinstance(ask, dict):
            asks.append(OrderBookLevel(
                price=float(ask.get("price", 0)),
                size=float(ask.get("size", 0))
            ))

    # Sort: bids high to low, asks low to high
    bids.sort(key=lambda x: x.price, reverse=True)
    asks.sort(key=lambda x: x.price)

    return OrderBook(bids=bids, asks=asks, timestamp=time.time())


# ============================================================================
# ORDER FLOW ANALYSIS
# ============================================================================

@dataclass
class OrderFlowStats:
    """Statistics about order flow."""
    order_rate: float = 0.0          # Orders per minute
    buy_sell_ratio: float = 1.0      # >1 = more buys
    avg_order_size: float = 0.0
    volatility: float = 0.0          # Price volatility
    regularity: float = 0.5          # 0=chaotic, 1=regular
    confidence: float = 0.5          # How much we trust these stats


def analyze_order_flow(trades: List[Dict], window_minutes: int = 60) -> OrderFlowStats:
    """
    Analyze recent trades to get order flow statistics.

    Args:
        trades: List of trade dicts with 'timestamp', 'side', 'size', 'price'
        window_minutes: How far back to look
    """
    if not trades:
        return OrderFlowStats()

    now = time.time()
    cutoff = now - (window_minutes * 60)

    # Filter to window
    recent = [t for t in trades if t.get("timestamp", 0) > cutoff]

    if not recent:
        return OrderFlowStats(confidence=0.2)

    # Calculate stats
    n_trades = len(recent)
    duration_minutes = (now - min(t.get("timestamp", now) for t in recent)) / 60
    order_rate = n_trades / max(duration_minutes, 1)

    buys = sum(1 for t in recent if t.get("side") == "BUY")
    sells = n_trades - buys
    buy_sell_ratio = buys / max(sells, 1)

    sizes = [float(t.get("size", 0)) for t in recent]
    avg_size = sum(sizes) / len(sizes) if sizes else 0

    prices = [float(t.get("price", 0)) for t in recent]
    if len(prices) > 1:
        mean_price = sum(prices) / len(prices)
        volatility = math.sqrt(sum((p - mean_price) ** 2 for p in prices) / len(prices))
    else:
        volatility = 0

    # Calculate regularity from inter-arrival times
    timestamps = sorted([t.get("timestamp", 0) for t in recent])
    if len(timestamps) > 1:
        gaps = [timestamps[i+1] - timestamps[i] for i in range(len(timestamps)-1)]
        mean_gap = sum(gaps) / len(gaps)
        if mean_gap > 0:
            var_gap = sum((g - mean_gap) ** 2 for g in gaps) / len(gaps)
            cv = math.sqrt(var_gap) / mean_gap  # Coefficient of variation
            regularity = max(0, min(1, 1 - (cv - 1) / 2))  # CV=1 is Poisson
        else:
            regularity = 0.5
    else:
        regularity = 0.5

    confidence = min(1.0, n_trades / 20) * regularity

    return OrderFlowStats(
        order_rate=order_rate,
        buy_sell_ratio=buy_sell_ratio,
        avg_order_size=avg_size,
        volatility=volatility,
        regularity=regularity,
        confidence=confidence
    )


# ============================================================================
# FLOW-ADJUSTED DENSITY
# ============================================================================

def create_flow_density(
    base_prob_yes: float,
    entry_price: float,
    shares: float,
    flow_stats: OrderFlowStats
) -> DensityFunc:
    """
    Create density function adjusted by order flow.

    - Higher order rate → faster evolution
    - Lower confidence → wider spread
    - Buy/sell imbalance → shifts expected
    """
    # Base outcomes
    win_pnl = shares * (1 - entry_price)
    lose_pnl = shares * (-entry_price)

    # Adjust probability based on buy/sell imbalance
    # More buys = slightly higher prob of YES
    imbalance_factor = (flow_stats.buy_sell_ratio - 1) * 0.05
    adjusted_prob = max(0.05, min(0.95, base_prob_yes + imbalance_factor))

    # Spread factor based on confidence (lower confidence = wider spread)
    spread_mult = 1.5 - flow_stats.confidence * 0.5  # 1.0 to 1.5

    # Speed factor based on order rate (higher rate = faster evolution)
    speed_mult = 1 + min(flow_stats.order_rate / 10, 1)  # 1.0 to 2.0

    def density(x: float, t: float, a: float, b: float, T: float) -> float:
        if T <= 0:
            return 0.0

        # Adjust time progression by speed
        effective_t = t * speed_mult
        progress = min(effective_t / T, 1.0)

        # Base sigma adjusted by spread factor
        base_sigma = (b - a) * 0.1 * spread_mult

        if progress < 0.1:
            # Early: concentrated near 0
            sigma = base_sigma * 0.5
            z = x / (sigma + 0.001)
            return math.exp(-0.5 * z * z)

        elif progress > 0.9:
            # Near resolution: bimodal
            sigma = base_sigma * 0.3 * (1.1 - progress)

            z_win = (x - win_pnl) / (sigma + 0.001)
            z_lose = (x - lose_pnl) / (sigma + 0.001)

            p_win = adjusted_prob * math.exp(-0.5 * z_win * z_win)
            p_lose = (1 - adjusted_prob) * math.exp(-0.5 * z_lose * z_lose)

            return p_win + p_lose

        else:
            # Middle: transitioning
            split_factor = (progress - 0.1) / 0.8

            expected = adjusted_prob * win_pnl + (1 - adjusted_prob) * lose_pnl
            sigma_uni = base_sigma * (1 - split_factor * 0.3)
            z_uni = (x - expected * progress) / (sigma_uni + 0.001)
            p_uni = math.exp(-0.5 * z_uni * z_uni)

            sigma_bi = base_sigma * 0.8
            z_win = (x - win_pnl * progress) / (sigma_bi + 0.001)
            z_lose = (x - lose_pnl * progress) / (sigma_bi + 0.001)
            p_bi = adjusted_prob * math.exp(-0.5 * z_win * z_win) + \
                   (1 - adjusted_prob) * math.exp(-0.5 * z_lose * z_lose)

            return (1 - split_factor) * p_uni + split_factor * p_bi

    return density


# ============================================================================
# LIVE POSITION ABCFC
# ============================================================================

@dataclass
class LivePosition:
    """A live trading position with order book context."""
    token_id: str
    market_name: str
    shares: float
    entry_price: float
    side: str  # "YES" or "NO"
    market_prob: float = 0.5
    order_book: OrderBook = None
    flow_stats: OrderFlowStats = None
    resolution_time: datetime = None

    @property
    def worst_liquidation(self) -> float:
        """Worst case: liquidate now at L2 prices."""
        if not self.order_book:
            # Fallback: assume total loss
            return -self.shares * self.entry_price

        if self.side == "YES":
            proceeds = self.order_book.walk_book_sell(self.shares)
            return proceeds - (self.shares * self.entry_price)
        else:
            cost = self.order_book.walk_book_buy(self.shares)
            # For NO, we paid (1 - entry) and need to buy back YES
            return (self.shares * (1 - self.entry_price)) - cost

    @property
    def best_resolution(self) -> float:
        """Best case: market resolves in our favor."""
        if self.side == "YES":
            return self.shares * (1 - self.entry_price)
        else:
            return self.shares * self.entry_price

    @property
    def worst_resolution(self) -> float:
        """Worst case: market resolves against us."""
        if self.side == "YES":
            return -self.shares * self.entry_price
        else:
            return -self.shares * (1 - self.entry_price)

    @property
    def expected_pnl(self) -> float:
        """Expected P&L based on current market probability."""
        if self.side == "YES":
            return self.shares * (self.market_prob - self.entry_price)
        else:
            return self.shares * ((1 - self.market_prob) - (1 - self.entry_price))

    @property
    def duration_days(self) -> float:
        """Days until resolution (or 30 if unknown)."""
        if self.resolution_time:
            delta = self.resolution_time - datetime.now()
            return max(0.1, delta.total_seconds() / 86400)
        return 30.0

    def to_abcfc(self) -> PositionABCFC:
        """Convert to proper ABCFC with flow-adjusted density."""

        # Bounds
        worst = min(self.worst_liquidation, self.worst_resolution)
        best = self.best_resolution

        # Create density
        if self.flow_stats:
            density = create_flow_density(
                base_prob_yes=self.market_prob if self.side == "YES" else (1 - self.market_prob),
                entry_price=self.entry_price,
                shares=self.shares,
                flow_stats=self.flow_stats
            )
        else:
            density = create_binary_market_density(
                prob_yes=self.market_prob if self.side == "YES" else (1 - self.market_prob),
                entry_price=self.entry_price,
                shares=self.shares
            )

        abcfc = ABCFC2D(
            bounds=(worst, best),
            duration=self.duration_days,
            density=density
        )

        return PositionABCFC(
            name=self.market_name,
            abcfc=abcfc,
            position_type="binary_live",
            shares=self.shares,
            entry_price=self.entry_price,
            prob_win=self.market_prob
        )


# ============================================================================
# LIVE HIERARCHY BUILDER
# ============================================================================

class LiveABCFCBuilder:
    """
    Builds ABCFC hierarchy from live Polymarket data.
    """

    def __init__(self, name: str = "Yair Siegel"):
        self.name = name
        self.positions: List[LivePosition] = []

    def add_position(
        self,
        token_id: str,
        market_name: str,
        shares: float,
        entry_price: float,
        side: str = "YES",
        market_prob: float = None,
        order_book: OrderBook = None,
        trades: List[Dict] = None,
        resolution_time: datetime = None
    ):
        """Add a live position. side is 'YES' or 'NO'."""

        # Infer market prob from order book if not given
        if market_prob is None and order_book:
            market_prob = order_book.mid_price
        elif market_prob is None:
            market_prob = 0.5

        # Analyze order flow
        flow_stats = None
        if trades:
            flow_stats = analyze_order_flow(trades)

        position = LivePosition(
            token_id=token_id,
            market_name=market_name,
            shares=shares,
            entry_price=entry_price,
            side=side,
            market_prob=market_prob,
            order_book=order_book,
            flow_stats=flow_stats,
            resolution_time=resolution_time
        )

        self.positions.append(position)

    def build_hierarchy(self) -> UnifiedABCFCHierarchy:
        """Build complete hierarchy from positions."""

        hierarchy = UnifiedABCFCHierarchy(self.name)

        # Add Trading category
        hierarchy.add_category("Trading", worst=0, best=0, expected=0)

        # Add Polymarket subcategory
        hierarchy.add_subcategory("Trading", "Polymarket", worst=0, best=0, expected=0)

        # Add each position
        for pos in self.positions:
            pos_abcfc = pos.to_abcfc()

            # Add to hierarchy
            hierarchy.all_nodes[pos.market_name] = pos_abcfc
            parent = hierarchy.get_node("Polymarket")
            parent.add_child(pos_abcfc)

        return hierarchy

    def get_summary(self) -> Dict:
        """Get summary of all positions."""
        total_worst = sum(p.worst_resolution for p in self.positions)
        total_best = sum(p.best_resolution for p in self.positions)
        total_expected = sum(p.expected_pnl for p in self.positions)

        return {
            "n_positions": len(self.positions),
            "total_worst": total_worst,
            "total_best": total_best,
            "total_expected": total_expected,
            "positions": [
                {
                    "name": p.market_name,
                    "shares": p.shares,
                    "entry": p.entry_price,
                    "prob": p.market_prob,
                    "worst": p.worst_resolution,
                    "best": p.best_resolution,
                    "expected": p.expected_pnl
                }
                for p in self.positions
            ]
        }


# ============================================================================
# POLYMARKET INTEGRATION
# ============================================================================

def fetch_polymarket_book(client, token_id: str) -> OrderBook:
    """Fetch order book from Polymarket."""
    try:
        book = client.get_order_book(token_id)
        return parse_polymarket_book(book)
    except Exception as e:
        print(f"Error fetching book for {token_id}: {e}")
        return OrderBook()


def fetch_polymarket_trades(client, token_id: str) -> List[Dict]:
    """Fetch recent trades from Polymarket."""
    try:
        # This would use the actual API method
        trades = client.get_trades(asset_id=token_id)
        return trades or []
    except Exception as e:
        print(f"Error fetching trades for {token_id}: {e}")
        return []


def build_live_hierarchy_from_polymarket(client, positions: List[Dict]) -> UnifiedABCFCHierarchy:
    """
    Build hierarchy from real Polymarket positions.

    Args:
        client: Polymarket CLOB client
        positions: List of position dicts with token_id, shares, entry_price, side
    """
    builder = LiveABCFCBuilder("Yair Siegel")

    for pos in positions:
        token_id = pos.get("token_id")
        if not token_id:
            continue

        # Fetch live data
        order_book = fetch_polymarket_book(client, token_id)
        trades = fetch_polymarket_trades(client, token_id)

        builder.add_position(
            token_id=token_id,
            market_name=pos.get("market_name", f"Market {token_id[:8]}"),
            shares=pos.get("shares", 0),
            entry_price=pos.get("entry_price", 0.5),
            side=pos.get("side", "YES"),
            order_book=order_book,
            trades=trades
        )

    return builder.build_hierarchy()


# ============================================================================
# DEMO
# ============================================================================

if __name__ == "__main__":
    print("=" * 70)
    print("ABCFC LIVE - Order Book + Flow Integration")
    print("=" * 70)

    # Create mock order book
    mock_book = OrderBook(
        bids=[
            OrderBookLevel(0.55, 500),
            OrderBookLevel(0.53, 1000),
            OrderBookLevel(0.50, 2000),
            OrderBookLevel(0.45, 5000),
        ],
        asks=[
            OrderBookLevel(0.57, 500),
            OrderBookLevel(0.60, 1000),
            OrderBookLevel(0.65, 2000),
            OrderBookLevel(0.70, 5000),
        ]
    )

    print("\n1. Order Book Analysis...")
    print(f"   Best bid: ${mock_book.best_bid:.2f}")
    print(f"   Best ask: ${mock_book.best_ask:.2f}")
    print(f"   Mid: ${mock_book.mid_price:.2f}")
    print(f"   Spread: ${mock_book.spread:.2f}")

    # Walk the book
    sell_100 = mock_book.walk_book_sell(100)
    print(f"\n   Sell 100 shares: ${sell_100:.2f} ({sell_100/100:.4f}/share)")

    sell_1000 = mock_book.walk_book_sell(1000)
    print(f"   Sell 1000 shares: ${sell_1000:.2f} ({sell_1000/1000:.4f}/share)")

    # Mock trades for flow analysis
    now = time.time()
    mock_trades = [
        {"timestamp": now - 60*i, "side": "BUY" if i % 3 != 0 else "SELL", "size": 50 + i*10, "price": 0.55 + 0.01*(i%5)}
        for i in range(30)
    ]

    print("\n2. Order Flow Analysis...")
    flow = analyze_order_flow(mock_trades)
    print(f"   Order rate: {flow.order_rate:.1f} orders/min")
    print(f"   Buy/sell ratio: {flow.buy_sell_ratio:.2f}")
    print(f"   Avg order size: {flow.avg_order_size:.0f}")
    print(f"   Regularity: {flow.regularity:.2f}")
    print(f"   Confidence: {flow.confidence:.2f}")

    # Create live position
    print("\n3. Live Position ABCFC...")

    position = LivePosition(
        token_id="abc123",
        market_name="Election 2024 YES",
        shares=100,
        entry_price=0.40,
        side="YES",
        market_prob=mock_book.mid_price,
        order_book=mock_book,
        flow_stats=flow
    )

    print(f"\n   Position: {position.shares} {position.side} @ ${position.entry_price:.2f}")
    print(f"   Market prob: {position.market_prob:.1%}")
    print(f"   Worst liquidation: ${position.worst_liquidation:.2f}")
    print(f"   Best resolution: ${position.best_resolution:.2f}")
    print(f"   Expected P&L: ${position.expected_pnl:.2f}")

    # Convert to ABCFC
    abcfc = position.to_abcfc()
    print(f"\n   ABCFC: {abcfc}")
    print(f"   E[profit | t=0]: {abcfc.expected(0):.2f}")
    print(f"   E[profit | t=15]: {abcfc.expected(15):.2f}")
    print(f"   E[profit | t=30]: {abcfc.expected(30):.2f}")

    # Plot
    print("\n4. Generating Flow-Adjusted Visualization...")
    result = abcfc.plot(save_path="/tmp/abcfc_live_position.png")
    print(f"   Chart: {result.get('chart_path')}")

    # Build full hierarchy
    print("\n5. Building Live Hierarchy...")

    builder = LiveABCFCBuilder("Yair Siegel")

    # Add multiple positions
    builder.add_position(
        token_id="abc123",
        market_name="Election YES",
        shares=100,
        entry_price=0.40,
        side="YES",
        market_prob=0.56,
        order_book=mock_book,
        trades=mock_trades
    )

    builder.add_position(
        token_id="def456",
        market_name="Fed Rate NO",
        shares=50,
        entry_price=0.30,
        side="NO",  # Holding NO shares
        market_prob=0.70,
        order_book=mock_book  # Using same mock book for demo
    )

    builder.add_position(
        token_id="ghi789",
        market_name="BTC 100k",
        shares=80,
        entry_price=0.45,
        side="YES",
        market_prob=0.35,
        order_book=mock_book
    )

    hierarchy = builder.build_hierarchy()

    print("\nHierarchy:")
    hierarchy.print_tree()

    summary = builder.get_summary()
    print(f"\nTotal Expected: ${summary['total_expected']:.2f}")
    print(f"Bounds: [${summary['total_worst']:.2f}, ${summary['total_best']:.2f}]")

    # Plot hierarchy
    result = hierarchy.plot_hierarchy_2d(save_path="/tmp/abcfc_live_hierarchy.png")
    print(f"\nHierarchy chart: {result.get('chart_path')}")

    print("\n" + "=" * 70)
    print("DONE - ABCFCs now use real order book + flow data!")
    print("=" * 70)
