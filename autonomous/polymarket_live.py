#!/usr/bin/env python3
"""
Polymarket Live Trading - Real Money Execution
Uses actual Polymarket API credentials for live trading.

Serving: Yair Siegel

LIVE TRADING - USE WITH CAUTION
"""

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional
from decimal import Decimal

PROJECT_ROOT = Path(__file__).parent.parent
STATE_DIR = PROJECT_ROOT / "state"

MASTER = "Yair Siegel"
LIVE_STATE = STATE_DIR / "polymarket_live_state.json"
TRADE_LOG = STATE_DIR / "live_trades.jsonl"

# Polymarket credentials
POLYMARKET_KEY = "0x644444ab1d39e9074b01f085a27a4bbf5a8536f411b9b2bea04eb3934f038493"
POLYMARKET_FUNDER = "0xb6781D9278c60dC3CE8c3E355Cd04142da3BF74D"
POLYMARKET_HOST = "https://clob.polymarket.com"
CHAIN_ID = 137

# Safety limits
MAX_ORDER_SIZE = 50  # Max USD per order
MAX_DAILY_TRADES = 10  # Max trades per day
MIN_CONFIDENCE = 0.7  # Minimum signal confidence


class PolymarketLive:
    """Live Polymarket trading with real money."""

    def __init__(self):
        self.state = self._load_state()
        self.client = None
        self._init_client()

    def _load_state(self) -> Dict:
        if LIVE_STATE.exists():
            with open(LIVE_STATE) as f:
                return json.load(f)
        return {
            "created_at": datetime.now(timezone.utc).isoformat(),
            "total_trades": 0,
            "total_pnl": 0.0,
            "daily_trades": 0,
            "last_trade_date": None,
            "positions": [],
            "safety_stops": 0
        }

    def _save_state(self):
        self.state["last_updated"] = datetime.now(timezone.utc).isoformat()
        with open(LIVE_STATE, 'w') as f:
            json.dump(self.state, f, indent=2)

    def _log_trade(self, trade: Dict):
        trade["timestamp"] = datetime.now(timezone.utc).isoformat()
        trade["master"] = MASTER
        with open(TRADE_LOG, 'a') as f:
            f.write(json.dumps(trade) + "\n")

    def _init_client(self):
        """Initialize Polymarket client."""
        try:
            from py_clob_client.client import ClobClient
            self.client = ClobClient(
                POLYMARKET_HOST,
                key=POLYMARKET_KEY,
                chain_id=CHAIN_ID,
                funder=POLYMARKET_FUNDER
            )
            creds = self.client.create_or_derive_api_creds()
            self.client.set_api_creds(creds)
            print("✓ Polymarket client initialized (LIVE MODE)")
        except Exception as e:
            print(f"✗ Client init failed: {e}")
            self.client = None

    def get_open_orders(self) -> List[Dict]:
        """Get all open orders."""
        if not self.client:
            return []
        try:
            orders = self.client.get_orders()
            return orders or []
        except Exception as e:
            print(f"Error getting orders: {e}")
            return []

    def get_market_price(self, token_id: str) -> Optional[Dict]:
        """Get current market price for a token."""
        if not self.client:
            return None
        try:
            book = self.client.get_order_book(token_id)
            if book:
                bids = book.get('bids', [])
                asks = book.get('asks', [])
                best_bid = float(bids[0]['price']) if bids else 0
                best_ask = float(asks[0]['price']) if asks else 1
                return {
                    "token_id": token_id,
                    "best_bid": best_bid,
                    "best_ask": best_ask,
                    "spread": best_ask - best_bid,
                    "mid": (best_bid + best_ask) / 2
                }
        except Exception as e:
            print(f"Error getting price: {e}")
        return None

    def check_safety(self) -> Dict:
        """Check if trading is safe to proceed."""
        today = datetime.now(timezone.utc).date().isoformat()

        # Reset daily counter if new day
        if self.state.get("last_trade_date") != today:
            self.state["daily_trades"] = 0
            self.state["last_trade_date"] = today

        safe = True
        reasons = []

        if self.state["daily_trades"] >= MAX_DAILY_TRADES:
            safe = False
            reasons.append(f"Daily trade limit ({MAX_DAILY_TRADES}) reached")

        return {
            "safe_to_trade": safe,
            "daily_trades": self.state["daily_trades"],
            "max_daily": MAX_DAILY_TRADES,
            "reasons": reasons
        }

    def analyze_positions(self) -> Dict:
        """Analyze current positions and orders."""
        orders = self.get_open_orders()

        analysis = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "open_orders": len(orders),
            "total_exposure": 0.0,
            "orders_by_side": {"BUY": 0, "SELL": 0},
            "orders": []
        }

        for order in orders:
            side = order.get("side", "")
            price = float(order.get("price", 0))
            size = float(order.get("original_size", order.get("size", 0)))
            exposure = price * size

            analysis["total_exposure"] += exposure
            analysis["orders_by_side"][side] = analysis["orders_by_side"].get(side, 0) + 1
            analysis["orders"].append({
                "side": side,
                "price": price,
                "size": size,
                "exposure": exposure,
                "status": order.get("status")
            })

        return analysis

    def generate_smart_signals(self) -> List[Dict]:
        """Generate trading signals based on analysis."""
        import requests

        signals = []

        try:
            # Get markets with good liquidity
            response = requests.get(
                "https://gamma-api.polymarket.com/markets",
                params={"closed": "false", "limit": 30},
                timeout=10
            )

            if response.status_code != 200:
                return signals

            markets = response.json()

            for market in markets:
                question = market.get("question", "")
                prices = json.loads(market.get("outcomePrices", "[]"))
                volume = float(market.get("volume", 0))
                liquidity = float(market.get("liquidity", 0))
                end_date = market.get("endDate", "")

                if len(prices) < 2 or liquidity < 10000:
                    continue

                yes_price = float(prices[0])
                no_price = float(prices[1])

                # Look for mispriced markets with edge
                signal = None

                # Very cheap YES with high volume = value bet
                if yes_price < 0.03 and volume > 500000:
                    signal = {
                        "market": question[:60],
                        "side": "BUY",
                        "outcome": "YES",
                        "price": yes_price,
                        "suggested_size": min(10 / yes_price, 500),  # $10 max
                        "confidence": 0.75,
                        "reason": f"Cheap YES ({yes_price:.3f}) with ${volume:,.0f} volume",
                        "token_ids": json.loads(market.get("clobTokenIds", "[]"))
                    }

                # Extreme certainty might be overconfident
                elif yes_price > 0.97 and volume > 500000:
                    signal = {
                        "market": question[:60],
                        "side": "BUY",
                        "outcome": "NO",
                        "price": no_price,
                        "suggested_size": min(10 / max(no_price, 0.01), 500),
                        "confidence": 0.6,
                        "reason": f"Overconfident YES ({yes_price:.3f}) - contrarian NO",
                        "token_ids": json.loads(market.get("clobTokenIds", "[]"))
                    }

                if signal and signal["confidence"] >= MIN_CONFIDENCE:
                    signals.append(signal)

        except Exception as e:
            print(f"Error generating signals: {e}")

        return sorted(signals, key=lambda x: x["confidence"], reverse=True)[:5]

    def run_live_cycle(self) -> Dict:
        """Run a full live trading cycle."""
        print("=" * 70)
        print("POLYMARKET LIVE TRADING")
        print(f"Master: {MASTER}")
        print(f"Time: {datetime.now(timezone.utc).isoformat()}")
        print("⚠️  LIVE MODE - REAL MONEY")
        print("=" * 70)
        print()

        results = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "mode": "LIVE"
        }

        # Safety check
        print("[SAFETY CHECK]")
        safety = self.check_safety()
        results["safety"] = safety
        print(f"  Safe to trade: {safety['safe_to_trade']}")
        print(f"  Daily trades: {safety['daily_trades']}/{safety['max_daily']}")
        if not safety["safe_to_trade"]:
            for reason in safety["reasons"]:
                print(f"  ⚠️ {reason}")
        print()

        # Analyze positions
        print("[CURRENT POSITIONS]")
        positions = self.analyze_positions()
        results["positions"] = positions
        print(f"  Open orders: {positions['open_orders']}")
        print(f"  Total exposure: ${positions['total_exposure']:.2f}")
        print(f"  BUY orders: {positions['orders_by_side'].get('BUY', 0)}")
        print(f"  SELL orders: {positions['orders_by_side'].get('SELL', 0)}")
        print()

        for order in positions["orders"][:6]:
            print(f"    {order['side']} @ ${order['price']:.3f} x {order['size']:.0f} = ${order['exposure']:.2f}")
        print()

        # Generate signals
        print("[TRADING SIGNALS]")
        signals = self.generate_smart_signals()
        results["signals"] = signals
        print(f"  Signals found: {len(signals)}")
        for signal in signals[:3]:
            print(f"    → {signal['outcome']} {signal['market'][:40]}...")
            print(f"      Price: {signal['price']:.3f} | Confidence: {signal['confidence']:.0%}")
            print(f"      Reason: {signal['reason']}")
        print()

        # Summary
        print("=" * 70)
        print("LIVE TRADING SUMMARY")
        print("=" * 70)
        print(f"  Open orders: {positions['open_orders']}")
        print(f"  Exposure: ${positions['total_exposure']:.2f}")
        print(f"  Signals: {len(signals)}")
        print()

        if signals and safety["safe_to_trade"]:
            print("READY TO EXECUTE:")
            for signal in signals[:2]:
                print(f"  → {signal['side']} {signal['outcome']} @ {signal['price']:.3f}")
                print(f"    Suggested size: {signal['suggested_size']:.0f} shares")
        else:
            print("No trades to execute this cycle")

        self._save_state()
        return results


def main():
    trader = PolymarketLive()
    return trader.run_live_cycle()


if __name__ == "__main__":
    main()
