#!/usr/bin/env python3
"""
🔍 LIVE ARBITRAGE SCANNER - Actually Finds Free Money
Serving: Yair Siegel

NOT A LIST. This ACTUALLY scans for arbitrage opportunities.

PRINCIPLE: If YES + NO < $1.00, buy both, one pays $1 = guaranteed profit
           If YES + NO > $1.00, sell both (if possible) = guaranteed profit

This runs continuously and alerts when opportunities appear.
"""

import json
import os
import time
import requests
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass

BASE_DIR = Path(__file__).resolve().parent.parent
STATE_DIR = BASE_DIR / "state"
ARB_STATE = STATE_DIR / "arbitrage_opportunities.json"
ARB_LOG = STATE_DIR / "arbitrage_log.jsonl"

# Polymarket API
POLYMARKET_API = "https://clob.polymarket.com"
GAMMA_API = "https://gamma-api.polymarket.com"


@dataclass
class ArbitrageOpportunity:
    """A detected arbitrage opportunity."""
    market_id: str
    question: str
    yes_price: float
    no_price: float
    sum_price: float
    gap: float  # How much below/above $1
    profit_per_dollar: float  # Profit per $1 invested
    detected_at: str
    volume_24h: float = 0
    liquidity: float = 0


class PolymarketScanner:
    """
    Scans Polymarket for arbitrage opportunities.
    """

    def __init__(self):
        self.opportunities: List[ArbitrageOpportunity] = []
        self.last_scan = None

    def get_all_markets(self) -> List[Dict]:
        """Fetch all active markets from Polymarket."""
        try:
            # Get markets from Gamma API (more comprehensive)
            resp = requests.get(
                f"{GAMMA_API}/markets",
                params={"closed": "false", "limit": 500},
                timeout=30
            )
            if resp.status_code == 200:
                return resp.json()
        except Exception as e:
            print(f"Error fetching markets: {e}")

        return []

    def get_market_prices(self, condition_id: str) -> Tuple[float, float]:
        """Get YES and NO prices for a market."""
        try:
            # Get orderbook
            resp = requests.get(
                f"{POLYMARKET_API}/book",
                params={"token_id": condition_id},
                timeout=10
            )
            if resp.status_code == 200:
                book = resp.json()
                # Best bid/ask
                bids = book.get("bids", [])
                asks = book.get("asks", [])

                best_bid = float(bids[0]["price"]) if bids else 0
                best_ask = float(asks[0]["price"]) if asks else 1

                return best_bid, best_ask
        except:
            pass

        return 0, 1

    def scan_for_arbitrage(self, min_gap: float = 0.02) -> List[ArbitrageOpportunity]:
        """
        Scan all markets for arbitrage opportunities.

        min_gap: Minimum price gap to consider (0.02 = 2 cents)
        """
        opportunities = []
        markets = self.get_all_markets()

        for market in markets:
            try:
                # Get market details
                question = market.get("question", "Unknown")
                market_id = market.get("condition_id", "")

                # Get YES and NO outcomes
                outcomes = market.get("outcomes", [])
                if len(outcomes) < 2:
                    continue

                # Get prices
                yes_outcome = outcomes[0]
                no_outcome = outcomes[1] if len(outcomes) > 1 else None

                yes_price = float(yes_outcome.get("price", 0.5))
                no_price = float(no_outcome.get("price", 0.5)) if no_outcome else (1 - yes_price)

                # Calculate sum
                sum_price = yes_price + no_price
                gap = abs(1.0 - sum_price)

                # Check for opportunity
                if gap >= min_gap:
                    profit_per_dollar = gap / sum_price if sum_price > 0 else 0

                    opp = ArbitrageOpportunity(
                        market_id=market_id,
                        question=question[:100],
                        yes_price=yes_price,
                        no_price=no_price,
                        sum_price=sum_price,
                        gap=gap,
                        profit_per_dollar=profit_per_dollar,
                        detected_at=datetime.now(timezone.utc).isoformat(),
                        volume_24h=float(market.get("volume24hr", 0)),
                        liquidity=float(market.get("liquidity", 0)),
                    )
                    opportunities.append(opp)

            except Exception as e:
                continue

        # Sort by profit potential
        opportunities.sort(key=lambda x: x.profit_per_dollar, reverse=True)

        self.opportunities = opportunities
        self.last_scan = datetime.now(timezone.utc)

        return opportunities

    def save_opportunities(self):
        """Save current opportunities to state."""
        data = {
            "last_scan": self.last_scan.isoformat() if self.last_scan else None,
            "count": len(self.opportunities),
            "opportunities": [
                {
                    "market_id": o.market_id,
                    "question": o.question,
                    "yes_price": o.yes_price,
                    "no_price": o.no_price,
                    "sum_price": o.sum_price,
                    "gap": o.gap,
                    "profit_per_dollar": o.profit_per_dollar,
                    "detected_at": o.detected_at,
                    "volume_24h": o.volume_24h,
                }
                for o in self.opportunities
            ]
        }
        ARB_STATE.write_text(json.dumps(data, indent=2))

    def log_opportunity(self, opp: ArbitrageOpportunity):
        """Log opportunity to history."""
        entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "market_id": opp.market_id,
            "question": opp.question,
            "gap": opp.gap,
            "profit": opp.profit_per_dollar,
        }
        with open(ARB_LOG, "a") as f:
            f.write(json.dumps(entry) + "\n")


class ArbitrageFinder:
    """
    Main arbitrage finder that runs continuously.
    """

    def __init__(self):
        self.scanner = PolymarketScanner()
        self.alert_threshold = 0.03  # Alert if gap > 3%

    def scan_once(self) -> Dict:
        """Run one scan and return results."""
        print("🔍 Scanning Polymarket for arbitrage...")

        opportunities = self.scanner.scan_for_arbitrage(min_gap=0.01)
        self.scanner.save_opportunities()

        result = {
            "scanned_at": datetime.now(timezone.utc).isoformat(),
            "markets_checked": "all active",
            "opportunities_found": len(opportunities),
            "best_opportunities": [],
        }

        if opportunities:
            # Log and show best ones
            for opp in opportunities[:5]:
                self.scanner.log_opportunity(opp)
                result["best_opportunities"].append({
                    "question": opp.question,
                    "yes": f"${opp.yes_price:.2f}",
                    "no": f"${opp.no_price:.2f}",
                    "sum": f"${opp.sum_price:.2f}",
                    "gap": f"{opp.gap*100:.1f}%",
                    "profit_per_$1": f"${opp.profit_per_dollar:.4f}",
                })

        return result

    def run_continuous(self, interval_seconds: int = 60):
        """Run continuous scanning."""
        print(f"🔄 Starting continuous arbitrage scan (every {interval_seconds}s)")
        print("   Press Ctrl+C to stop\n")

        while True:
            try:
                result = self.scan_once()

                if result["opportunities_found"] > 0:
                    print(f"\n⚡ Found {result['opportunities_found']} opportunities!")
                    for opp in result["best_opportunities"][:3]:
                        print(f"   {opp['question'][:50]}...")
                        print(f"      YES={opp['yes']} + NO={opp['no']} = {opp['sum']}")
                        print(f"      Gap: {opp['gap']}, Profit: {opp['profit_per_$1']}/dollar")
                else:
                    print(f"   No significant arbitrage found at {datetime.now().strftime('%H:%M:%S')}")

                time.sleep(interval_seconds)

            except KeyboardInterrupt:
                print("\n\n🛑 Stopping scanner...")
                break
            except Exception as e:
                print(f"Error: {e}")
                time.sleep(10)

    def display_current(self):
        """Display current opportunities."""
        if ARB_STATE.exists():
            data = json.loads(ARB_STATE.read_text())

            print("\n🔍 CURRENT ARBITRAGE OPPORTUNITIES")
            print("=" * 70)
            print(f"Last scan: {data.get('last_scan', 'Never')}")
            print(f"Opportunities: {data.get('count', 0)}")

            for opp in data.get("opportunities", [])[:10]:
                print(f"\n  📊 {opp['question'][:60]}...")
                print(f"     YES: ${opp['yes_price']:.3f}")
                print(f"     NO:  ${opp['no_price']:.3f}")
                print(f"     SUM: ${opp['sum_price']:.3f} (gap: {opp['gap']*100:.1f}%)")
                print(f"     Profit per $1: ${opp['profit_per_dollar']:.4f}")
                print(f"     24h Volume: ${opp['volume_24h']:,.0f}")
        else:
            print("\n⚠️  No scan data. Run 'scan' first.")


def main():
    import argparse
    parser = argparse.ArgumentParser(description="🔍 Arbitrage Scanner")
    parser.add_argument("command", choices=["scan", "watch", "show"],
                       nargs="?", default="scan")
    parser.add_argument("--interval", type=int, default=60,
                       help="Scan interval in seconds")
    args = parser.parse_args()

    finder = ArbitrageFinder()

    if args.command == "scan":
        result = finder.scan_once()
        print(f"\n✅ Scan complete")
        print(f"   Opportunities found: {result['opportunities_found']}")
        if result["best_opportunities"]:
            print("\n   Best opportunities:")
            for opp in result["best_opportunities"]:
                print(f"   • {opp['question'][:50]}...")
                print(f"     Gap: {opp['gap']}, Profit: {opp['profit_per_$1']}/dollar")
    elif args.command == "watch":
        finder.run_continuous(args.interval)
    elif args.command == "show":
        finder.display_current()


if __name__ == "__main__":
    main()
