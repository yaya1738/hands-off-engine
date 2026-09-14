#!/usr/bin/env python3
"""
SPREAD CAPTURE STRATEGY - Making Money from Wide Spreads
=========================================================

Wide spreads are PROFIT OPPORTUNITIES, not problems!

Strategy:
1. Analyze full order book depth
2. Post limit orders inside the spread to collect spread as market maker
3. Use AI to determine fair value - decide which side to post
4. When dumb money hits our orders, we profit from:
   - The spread itself
   - Being on the right side of the trade (AI edge)

Key insight: Wide spread = low competition = we ARE the market
"""

import json
import os
import sys
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field
import requests

sys.path.insert(0, str(Path(__file__).parent.parent))

LOG = logging.getLogger(__name__)

CLOB_API = "https://clob.polymarket.com"


@dataclass
class OrderBookAnalysis:
    """Deep analysis of an order book"""
    token_id: str
    question: str

    # Best prices
    best_bid: float
    best_ask: float
    mid_price: float
    spread: float
    spread_bps: float

    # Depth analysis
    bid_levels: int
    ask_levels: int
    total_bid_size: float  # Shares
    total_ask_size: float  # Shares
    total_bid_value: float  # USD
    total_ask_value: float  # USD

    # Imbalance (negative = more sell pressure, positive = more buy pressure)
    imbalance_ratio: float  # bid_value / ask_value

    # Price levels
    bids: List[Dict]  # Raw order book
    asks: List[Dict]

    # Our opportunity
    spread_capture_bid: float  # Where to post bid
    spread_capture_ask: float  # Where to post ask
    potential_profit_per_share: float


@dataclass
class SpreadCaptureSignal:
    """A signal to capture spread"""
    token_id: str
    question: str
    condition_id: str

    # Market state
    current_bid: float
    current_ask: float
    mid_price: float
    spread_bps: float

    # Our orders
    our_bid_price: float  # Post bid here
    our_ask_price: float  # Post ask here
    order_size_usd: float

    # Expected profit
    profit_per_fill_usd: float

    # AI edge - which side is undervalued?
    ai_fair_value: float
    preferred_side: str  # "BID" or "ASK" - which order is more likely to profit

    # Priority
    priority_score: float  # Higher = better opportunity


class SpreadCaptureEngine:
    """
    Engine for capturing spreads on Polymarket.

    Strategy:
    1. Find markets with wide spreads
    2. Analyze order book depth
    3. Post limit orders INSIDE the spread
    4. Use AI to lean toward the profitable side
    5. Profit when dumb money trades against us
    """

    def __init__(self, order_size_usd: float = 25.0):
        self.order_size_usd = order_size_usd
        self.session = requests.Session()
        self.session.headers.update({
            "Accept": "application/json",
            "User-Agent": "hands-off-engine/1.0"
        })

    def fetch_all_active_markets(self, limit: int = 500) -> List[Dict]:
        """Fetch all active tradeable markets"""
        LOG.info("Fetching active markets from CLOB API...")

        url = f"{CLOB_API}/sampling-markets"
        params = {"limit": limit}

        resp = self.session.get(url, params=params, timeout=30)
        resp.raise_for_status()
        data = resp.json()

        markets = data.get('data', [])
        LOG.info(f"Fetched {len(markets)} markets")

        return markets

    def get_order_book(self, token_id: str) -> Dict:
        """Fetch full order book for a token"""
        url = f"{CLOB_API}/book"
        params = {"token_id": token_id}

        resp = self.session.get(url, params=params, timeout=10)
        resp.raise_for_status()
        return resp.json()

    def analyze_order_book(self, market: Dict) -> Optional[OrderBookAnalysis]:
        """Deep analysis of market order book"""
        tokens = market.get('tokens', [])
        if not tokens:
            return None

        yes_token = tokens[0]
        token_id = yes_token.get('token_id')
        question = market.get('question', 'Unknown')

        try:
            book = self.get_order_book(token_id)
        except Exception as e:
            LOG.debug(f"Failed to get book for {token_id}: {e}")
            return None

        bids = book.get('bids', [])
        asks = book.get('asks', [])

        if not bids or not asks:
            return None

        # Parse order book
        best_bid = float(bids[0]['price'])
        best_ask = float(asks[0]['price'])

        # Skip if prices at extremes
        if best_bid < 0.01 or best_ask > 0.99:
            return None

        mid_price = (best_bid + best_ask) / 2
        spread = best_ask - best_bid
        spread_bps = (spread / mid_price) * 10000 if mid_price > 0 else 0

        # Calculate depth
        total_bid_size = sum(float(b['size']) for b in bids)
        total_ask_size = sum(float(a['size']) for a in asks)
        total_bid_value = sum(float(b['size']) * float(b['price']) for b in bids)
        total_ask_value = sum(float(a['size']) * float(a['price']) for a in asks)

        # Imbalance - > 1 means more bids (bullish), < 1 means more asks (bearish)
        imbalance_ratio = total_bid_value / total_ask_value if total_ask_value > 0 else 1.0

        # Our spread capture prices - inside the spread
        # Post bid slightly above best bid, ask slightly below best ask
        tick_size = 0.01  # Polymarket minimum tick
        our_bid = min(best_bid + tick_size, mid_price - tick_size)
        our_ask = max(best_ask - tick_size, mid_price + tick_size)

        profit_per_share = our_ask - our_bid

        return OrderBookAnalysis(
            token_id=token_id,
            question=question,
            best_bid=best_bid,
            best_ask=best_ask,
            mid_price=mid_price,
            spread=spread,
            spread_bps=spread_bps,
            bid_levels=len(bids),
            ask_levels=len(asks),
            total_bid_size=total_bid_size,
            total_ask_size=total_ask_size,
            total_bid_value=total_bid_value,
            total_ask_value=total_ask_value,
            imbalance_ratio=imbalance_ratio,
            bids=bids,
            asks=asks,
            spread_capture_bid=our_bid,
            spread_capture_ask=our_ask,
            potential_profit_per_share=profit_per_share,
        )

    def generate_spread_signals(
        self,
        min_spread_bps: float = 200,  # 2% minimum spread
        max_spread_bps: float = 5000,  # 50% maximum (avoid garbage)
        min_depth_usd: float = 100,   # Minimum book depth
        limit: int = 20
    ) -> List[SpreadCaptureSignal]:
        """
        Generate spread capture signals.

        Finds the best spread capture opportunities across all markets.
        """
        LOG.info("=" * 60)
        LOG.info("SPREAD CAPTURE ENGINE - Finding Opportunities")
        LOG.info("=" * 60)

        markets = self.fetch_all_active_markets()

        opportunities = []
        analyzed = 0

        for market in markets:
            analysis = self.analyze_order_book(market)
            if analysis is None:
                continue

            analyzed += 1

            # Filter by spread criteria
            if analysis.spread_bps < min_spread_bps:
                continue
            if analysis.spread_bps > max_spread_bps:
                continue

            # Filter by depth
            total_depth = analysis.total_bid_value + analysis.total_ask_value
            if total_depth < min_depth_usd:
                continue

            # Calculate profit opportunity
            # If we post both sides and both fill, profit = spread capture
            profit_per_fill = analysis.potential_profit_per_share * (self.order_size_usd / analysis.mid_price)

            # Determine preferred side based on order imbalance
            # If more bids than asks (imbalance > 1), prefer to post asks (sells)
            # If more asks than bids (imbalance < 1), prefer to post bids (buys)
            if analysis.imbalance_ratio > 1.2:
                preferred_side = "ASK"  # More buyers, be a seller
            elif analysis.imbalance_ratio < 0.8:
                preferred_side = "BID"  # More sellers, be a buyer
            else:
                preferred_side = "BOTH"  # Balanced, post both

            # Priority score: higher spread * depth / competition
            priority = (analysis.spread_bps / 100) * (total_depth / 1000) / (analysis.bid_levels + analysis.ask_levels + 1)

            signal = SpreadCaptureSignal(
                token_id=analysis.token_id,
                question=analysis.question,
                condition_id=market.get('condition_id', ''),
                current_bid=analysis.best_bid,
                current_ask=analysis.best_ask,
                mid_price=analysis.mid_price,
                spread_bps=analysis.spread_bps,
                our_bid_price=analysis.spread_capture_bid,
                our_ask_price=analysis.spread_capture_ask,
                order_size_usd=self.order_size_usd,
                profit_per_fill_usd=profit_per_fill,
                ai_fair_value=analysis.mid_price,  # Placeholder - AI would improve this
                preferred_side=preferred_side,
                priority_score=priority,
            )

            opportunities.append(signal)

            if len(opportunities) >= limit * 2:
                break

        LOG.info(f"Analyzed {analyzed} markets, found {len(opportunities)} opportunities")

        # Sort by priority
        opportunities.sort(key=lambda x: x.priority_score, reverse=True)

        return opportunities[:limit]

    def display_opportunities(self, signals: List[SpreadCaptureSignal]):
        """Display spread capture opportunities"""
        print("\n" + "=" * 70)
        print("SPREAD CAPTURE OPPORTUNITIES")
        print("=" * 70)

        total_potential = 0

        for i, sig in enumerate(signals, 1):
            print(f"\n{i}. {sig.question[:55]}...")
            print(f"   Current: Bid {sig.current_bid:.3f} | Ask {sig.current_ask:.3f}")
            print(f"   Spread: {sig.spread_bps:.0f} bps ({sig.current_ask - sig.current_bid:.3f})")
            print(f"   Our Orders: Bid @ {sig.our_bid_price:.3f} | Ask @ {sig.our_ask_price:.3f}")
            print(f"   Preferred Side: {sig.preferred_side}")
            print(f"   Profit if filled: ${sig.profit_per_fill_usd:.2f}")
            print(f"   Priority Score: {sig.priority_score:.2f}")

            total_potential += sig.profit_per_fill_usd

        print(f"\n{'=' * 70}")
        print(f"Total potential profit (all signals): ${total_potential:.2f}")
        print(f"Average profit per signal: ${total_potential/len(signals):.2f}" if signals else "N/A")
        print("=" * 70)

    def save_signals(self, signals: List[SpreadCaptureSignal], output_path: Path):
        """Save signals to JSON"""
        output = {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "strategy": "spread_capture",
            "order_size_usd": self.order_size_usd,
            "signal_count": len(signals),
            "total_potential_profit": sum(s.profit_per_fill_usd for s in signals),
            "signals": [
                {
                    "token_id": s.token_id,
                    "question": s.question,
                    "condition_id": s.condition_id,
                    "current_bid": s.current_bid,
                    "current_ask": s.current_ask,
                    "spread_bps": s.spread_bps,
                    "our_bid_price": s.our_bid_price,
                    "our_ask_price": s.our_ask_price,
                    "preferred_side": s.preferred_side,
                    "profit_per_fill_usd": s.profit_per_fill_usd,
                    "priority_score": s.priority_score,
                }
                for s in signals
            ]
        }

        with open(output_path, "w") as f:
            json.dump(output, f, indent=2)

        LOG.info(f"Saved {len(signals)} signals to {output_path}")


def main():
    """Main entry point"""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s"
    )

    # Initialize engine
    engine = SpreadCaptureEngine(order_size_usd=25.0)

    # Generate signals
    signals = engine.generate_spread_signals(
        min_spread_bps=300,   # 3% minimum spread to capture
        max_spread_bps=3000,  # 30% max (avoid totally illiquid)
        min_depth_usd=50,     # At least $50 on the book
        limit=20
    )

    if not signals:
        print("\nNo spread capture opportunities found.")
        return

    # Display
    engine.display_opportunities(signals)

    # Save
    output_path = Path(__file__).parent.parent / "state" / "spread_capture_signals.json"
    engine.save_signals(signals, output_path)

    print(f"\nSignals saved to: {output_path}")


if __name__ == "__main__":
    main()
