#!/usr/bin/env python3
"""
Signal Generator - Real Trading Signal Generation
Serving: Yair Siegel

Actually fetches Polymarket data and generates actionable signals.
This feeds the power plant turbine.
"""

import json
import requests
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Dict, List, Optional
from dataclasses import dataclass

BASE_DIR = Path("/root/hands-off-engine")
STATE_DIR = BASE_DIR / "state"
SIGNAL_FILE = STATE_DIR / "trading_signals.json"
SIGNAL_LOG = STATE_DIR / "signal_history.jsonl"

GAMMA_API = "https://gamma-api.polymarket.com"
CLOB_API = "https://clob.polymarket.com"


@dataclass
class TradingSignal:
    """A trading signal ready for execution."""
    market_id: str
    question: str
    token_id: str
    side: str  # BUY or SELL
    price: float
    confidence: float
    reason: str
    volume_24h: float
    liquidity: float
    generated_at: str

    def to_dict(self) -> Dict:
        return {
            "market_id": self.market_id,
            "question": self.question,
            "token_id": self.token_id,
            "side": self.side,
            "price": self.price,
            "confidence": self.confidence,
            "reason": self.reason,
            "volume_24h": self.volume_24h,
            "liquidity": self.liquidity,
            "generated_at": self.generated_at,
        }


class SignalGenerator:
    """
    Generates trading signals from Polymarket market data.
    """

    def __init__(self):
        self.signals: List[TradingSignal] = []
        self.last_scan = None

    def fetch_markets(self, limit: int = 100) -> List[Dict]:
        """Fetch active markets from Polymarket."""
        try:
            resp = requests.get(
                f"{GAMMA_API}/markets",
                params={"closed": "false", "limit": limit, "order": "volume24hr", "ascending": "false"},
                timeout=30
            )
            if resp.status_code == 200:
                return resp.json()
        except Exception as e:
            print(f"Error fetching markets: {e}")
        return []

    def analyze_market(self, market: Dict) -> Optional[TradingSignal]:
        """
        Analyze a market for trading opportunity.

        SIGNAL CRITERIA:
        1. High volume (active market)
        2. Price away from 0.5 but not extreme (potential profit)
        3. Good liquidity (can execute trade)
        4. Event resolving soon (time value)
        """
        try:
            question = market.get("question", "")[:100]
            market_id = market.get("conditionId", "")
            volume = float(market.get("volume", 0) or 0)
            liquidity = float(market.get("liquidity", 0) or 0)

            # Parse outcomes and prices from JSON strings
            outcomes_str = market.get("outcomes", "[]")
            prices_str = market.get("outcomePrices", "[]")

            try:
                outcomes = json.loads(outcomes_str) if isinstance(outcomes_str, str) else outcomes_str
                prices = json.loads(prices_str) if isinstance(prices_str, str) else prices_str
            except:
                return None

            if len(outcomes) < 2 or len(prices) < 2:
                return None

            # Find YES and NO indices
            yes_idx = outcomes.index("Yes") if "Yes" in outcomes else 0
            no_idx = outcomes.index("No") if "No" in outcomes else 1

            yes_price = float(prices[yes_idx])
            no_price = float(prices[no_idx])

            # SIGNAL LOGIC
            signal = None
            confidence = 0.0
            reason = ""

            # 1. Volume filter - need active markets
            if volume < 1000:
                return None

            # 2. Liquidity filter - need to be able to execute
            if liquidity < 500:
                return None

            # 3. Price-based signals

            # Get clob token IDs if available
            clob_token_ids = market.get("clobTokenIds", "[]")
            try:
                token_ids = json.loads(clob_token_ids) if isinstance(clob_token_ids, str) else clob_token_ids
                yes_token_id = token_ids[yes_idx] if len(token_ids) > yes_idx else market_id
                no_token_id = token_ids[no_idx] if len(token_ids) > no_idx else market_id
            except:
                yes_token_id = market_id
                no_token_id = market_id

            # Strong YES signal: price very low, could be mispriced
            if yes_price < 0.20 and volume > 10000:
                signal = TradingSignal(
                    market_id=market_id,
                    question=question,
                    token_id=yes_token_id,
                    side="BUY",
                    price=yes_price,
                    confidence=0.6 + (0.20 - yes_price),  # More confident at lower prices
                    reason=f"Low YES price ${yes_price:.2f} with high volume ${volume:,.0f}",
                    volume_24h=volume,
                    liquidity=liquidity,
                    generated_at=datetime.now(timezone.utc).isoformat(),
                )

            # Strong NO signal: NO price very low
            elif no_price < 0.20 and volume > 10000:
                signal = TradingSignal(
                    market_id=market_id,
                    question=question,
                    token_id=no_token_id,
                    side="BUY",
                    price=no_price,
                    confidence=0.6 + (0.20 - no_price),
                    reason=f"Low NO price ${no_price:.2f} with high volume ${volume:,.0f}",
                    volume_24h=volume,
                    liquidity=liquidity,
                    generated_at=datetime.now(timezone.utc).isoformat(),
                )

            # Moderate signals: price in tradeable range
            elif 0.20 <= yes_price <= 0.45 and volume > 50000:
                signal = TradingSignal(
                    market_id=market_id,
                    question=question,
                    token_id=yes_token_id,
                    side="BUY",
                    price=yes_price,
                    confidence=0.55,
                    reason=f"YES at ${yes_price:.2f}, good risk/reward with ${volume:,.0f} volume",
                    volume_24h=volume,
                    liquidity=liquidity,
                    generated_at=datetime.now(timezone.utc).isoformat(),
                )

            elif 0.20 <= no_price <= 0.45 and volume > 50000:
                signal = TradingSignal(
                    market_id=market_id,
                    question=question,
                    token_id=no_token_id,
                    side="BUY",
                    price=no_price,
                    confidence=0.55,
                    reason=f"NO at ${no_price:.2f}, good risk/reward with ${volume:,.0f} volume",
                    volume_24h=volume,
                    liquidity=liquidity,
                    generated_at=datetime.now(timezone.utc).isoformat(),
                )

            return signal

        except Exception as e:
            return None

    def scan_opportunities(self, min_confidence: float = 0.5) -> List[Dict]:
        """
        Scan all markets and generate signals.
        Returns list of signal dicts sorted by confidence.
        """
        self.signals = []
        markets = self.fetch_markets(limit=200)

        for market in markets:
            signal = self.analyze_market(market)
            if signal and signal.confidence >= min_confidence:
                self.signals.append(signal)

        # Sort by confidence
        self.signals.sort(key=lambda x: x.confidence, reverse=True)
        self.last_scan = datetime.now(timezone.utc)

        # Save to file
        self.save_signals()

        return [s.to_dict() for s in self.signals]

    def save_signals(self):
        """Save signals to state file."""
        data = {
            "last_scan": self.last_scan.isoformat() if self.last_scan else None,
            "count": len(self.signals),
            "signals": [s.to_dict() for s in self.signals],
        }
        SIGNAL_FILE.write_text(json.dumps(data, indent=2))

        # Also log to history
        for signal in self.signals:
            entry = signal.to_dict()
            entry["logged_at"] = datetime.now(timezone.utc).isoformat()
            with open(SIGNAL_LOG, "a") as f:
                f.write(json.dumps(entry) + "\n")

    def get_best_signal(self) -> Optional[Dict]:
        """Get the single best signal available."""
        if self.signals:
            return self.signals[0].to_dict()

        # Check saved signals
        if SIGNAL_FILE.exists():
            try:
                data = json.loads(SIGNAL_FILE.read_text())
                signals = data.get("signals", [])
                if signals:
                    return signals[0]
            except:
                pass

        return None

    def display(self):
        """Display current signals."""
        print("\n📊 TRADING SIGNALS")
        print("=" * 70)

        if not self.signals:
            if SIGNAL_FILE.exists():
                data = json.loads(SIGNAL_FILE.read_text())
                print(f"Last scan: {data.get('last_scan', 'Never')}")
                signals = data.get("signals", [])
            else:
                print("No signals generated yet. Run 'scan' first.")
                return
        else:
            signals = [s.to_dict() for s in self.signals]
            print(f"Last scan: {self.last_scan}")

        print(f"Total signals: {len(signals)}")

        for i, sig in enumerate(signals[:10], 1):
            print(f"\n{i}. {sig['question'][:60]}...")
            print(f"   {sig['side']} at ${sig['price']:.3f}")
            print(f"   Confidence: {sig['confidence']*100:.0f}%")
            print(f"   Reason: {sig['reason']}")
            print(f"   Volume: ${sig['volume_24h']:,.0f}")


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Signal Generator")
    parser.add_argument("command", choices=["scan", "show", "best"], nargs="?", default="scan")
    parser.add_argument("--min-confidence", type=float, default=0.5)
    args = parser.parse_args()

    gen = SignalGenerator()

    if args.command == "scan":
        print("🔍 Scanning markets for opportunities...")
        signals = gen.scan_opportunities(min_confidence=args.min_confidence)
        print(f"✅ Found {len(signals)} signals")
        gen.display()
    elif args.command == "show":
        gen.display()
    elif args.command == "best":
        best = gen.get_best_signal()
        if best:
            print(f"\n🎯 BEST SIGNAL:")
            print(f"   {best['question'][:60]}...")
            print(f"   {best['side']} at ${best['price']:.3f}")
            print(f"   Confidence: {best['confidence']*100:.0f}%")
        else:
            print("No signals available")


if __name__ == "__main__":
    main()
