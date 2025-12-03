#!/usr/bin/env python3
"""
Trade Executor - Polymarket Trading Capability
Executes trades on Polymarket when enabled.

Serving: Yair Siegel
"""

import json
import os
import requests
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional
from decimal import Decimal

PROJECT_ROOT = Path(__file__).parent.parent
STATE_DIR = PROJECT_ROOT / "state"

MASTER = "Yair Siegel"
TRADE_STATE = STATE_DIR / "trade_executor_state.json"
TRADE_LOG = STATE_DIR / "trade_history.jsonl"


class TradeExecutor:
    """Execute trades on Polymarket."""

    def __init__(self):
        self.state = self._load_state()
        self.mode = os.environ.get("TRADING_MODE", "DRYRUN")

    def _load_state(self) -> Dict:
        if TRADE_STATE.exists():
            with open(TRADE_STATE) as f:
                return json.load(f)
        return {
            "created_at": datetime.now(timezone.utc).isoformat(),
            "mode": "DRYRUN",
            "total_trades": 0,
            "winning_trades": 0,
            "losing_trades": 0,
            "total_pnl": 0.0,
            "best_trade": None,
            "worst_trade": None
        }

    def _save_state(self):
        self.state["last_updated"] = datetime.now(timezone.utc).isoformat()
        with open(TRADE_STATE, 'w') as f:
            json.dump(self.state, f, indent=2)

    def _log_trade(self, trade: Dict):
        """Log trade to history."""
        trade["timestamp"] = datetime.now(timezone.utc).isoformat()
        trade["master"] = MASTER
        with open(TRADE_LOG, 'a') as f:
            f.write(json.dumps(trade) + "\n")

    def get_market_data(self, limit: int = 20) -> List[Dict]:
        """Fetch current market data from Polymarket."""
        try:
            response = requests.get(
                "https://gamma-api.polymarket.com/markets",
                params={"closed": "false", "limit": limit},
                timeout=10
            )
            if response.status_code == 200:
                return response.json()
        except Exception as e:
            print(f"Error fetching markets: {e}")
        return []

    def analyze_opportunity(self, market: Dict) -> Optional[Dict]:
        """Analyze a market for trading opportunity."""
        try:
            question = market.get("question", "")
            prices = json.loads(market.get("outcomePrices", "[]"))
            volume = float(market.get("volume", 0))
            liquidity = float(market.get("liquidity", 0))

            if len(prices) < 2:
                return None

            yes_price = float(prices[0])
            no_price = float(prices[1])

            # Look for mispriced markets
            signal = None

            # Very low YES price with high volume = potential value
            if yes_price < 0.05 and volume > 100000:
                signal = {
                    "market": question[:80],
                    "side": "YES",
                    "price": yes_price,
                    "confidence": 0.6,
                    "reason": f"Low YES ({yes_price:.3f}) with ${volume:,.0f} volume"
                }

            # Very high YES price might be overconfident
            elif yes_price > 0.95 and volume > 100000:
                signal = {
                    "market": question[:80],
                    "side": "NO",
                    "price": no_price,
                    "confidence": 0.5,
                    "reason": f"High YES ({yes_price:.3f}) may be overconfident"
                }

            # Liquidity opportunity - large spread
            spread = abs(yes_price - (1 - no_price))
            if spread > 0.02 and liquidity > 10000:
                if not signal:
                    signal = {
                        "market": question[:80],
                        "side": "SPREAD",
                        "spread": spread,
                        "confidence": 0.4,
                        "reason": f"Wide spread ({spread:.3f}) arbitrage potential"
                    }

            return signal

        except Exception as e:
            return None

    def generate_signals(self) -> List[Dict]:
        """Generate trading signals from current markets."""
        print("[GENERATING SIGNALS]")
        markets = self.get_market_data(50)
        signals = []

        for market in markets:
            signal = self.analyze_opportunity(market)
            if signal:
                signals.append(signal)

        # Sort by confidence
        signals.sort(key=lambda x: x.get("confidence", 0), reverse=True)
        return signals[:10]

    def execute_trade(self, signal: Dict, amount: float = 1.0) -> Dict:
        """Execute a trade (DRYRUN or LIVE)."""
        result = {
            "signal": signal,
            "amount": amount,
            "mode": self.mode,
            "executed_at": datetime.now(timezone.utc).isoformat()
        }

        if self.mode == "DRYRUN":
            result["status"] = "simulated"
            result["message"] = "Trade simulated (DRYRUN mode)"
            result["simulated_fill"] = {
                "price": signal.get("price", 0),
                "shares": amount / max(signal.get("price", 0.01), 0.01),
                "cost": amount
            }
            print(f"  [DRYRUN] {signal['side']} {signal['market'][:40]}... @ {signal.get('price', 'N/A')}")

        elif self.mode == "LIVE":
            # Check for API credentials
            private_key = os.environ.get("POLYMARKET_PRIVATE_KEY")
            if not private_key:
                result["status"] = "failed"
                result["error"] = "No POLYMARKET_PRIVATE_KEY configured"
                return result

            # Would execute real trade here
            result["status"] = "live_disabled"
            result["message"] = "Live trading requires additional setup"

        self._log_trade(result)
        self.state["total_trades"] += 1
        return result

    def check_positions(self) -> Dict:
        """Check current positions."""
        try:
            with open(STATE_DIR / "financial_state.json") as f:
                financial = json.load(f)
                return {
                    "balance": financial.get("balance", 0),
                    "positions_value": financial.get("positions_value", 0),
                    "positions": financial.get("positions", []),
                    "mode": financial.get("system_mode", "DRYRUN")
                }
        except:
            return {"error": "Could not load financial state"}

    def run_trading_cycle(self) -> Dict:
        """Run a full trading cycle."""
        print("=" * 70)
        print("TRADE EXECUTOR - POLYMARKET TRADING")
        print(f"Master: {MASTER}")
        print(f"Mode: {self.mode}")
        print(f"Time: {datetime.now(timezone.utc).isoformat()}")
        print("=" * 70)
        print()

        results = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "mode": self.mode
        }

        # Check positions
        print("[CURRENT POSITIONS]")
        positions = self.check_positions()
        results["positions"] = positions
        print(f"  Balance: ${positions.get('balance', 'unknown')}")
        print(f"  Positions: ${positions.get('positions_value', 'unknown')}")
        print(f"  Mode: {positions.get('mode', 'unknown')}")
        print()

        # Generate signals
        signals = self.generate_signals()
        results["signals_generated"] = len(signals)
        print(f"  Signals found: {len(signals)}")
        print()

        # Show top signals
        print("[TOP SIGNALS]")
        for i, signal in enumerate(signals[:5], 1):
            print(f"  {i}. {signal['side']}: {signal['market'][:50]}...")
            print(f"     Price: {signal.get('price', 'N/A')} | Confidence: {signal.get('confidence', 0):.0%}")
            print(f"     Reason: {signal.get('reason', 'N/A')}")
            print()

        # Execute trades (in DRYRUN mode)
        print("[TRADE EXECUTION]")
        trades_executed = []
        if signals and self.mode == "DRYRUN":
            # Execute top 3 signals in simulation
            for signal in signals[:3]:
                trade = self.execute_trade(signal, amount=1.0)
                trades_executed.append(trade)

        results["trades_executed"] = len(trades_executed)
        print()

        # Summary
        print("=" * 70)
        print("CYCLE COMPLETE")
        print("=" * 70)
        print(f"  Signals: {len(signals)}")
        print(f"  Trades: {len(trades_executed)} ({self.mode})")
        print()

        if self.mode == "DRYRUN":
            print("To enable LIVE trading:")
            print("  1. Set TRADING_MODE=LIVE")
            print("  2. Ensure POLYMARKET_PRIVATE_KEY is set")
            print("  3. Run: python3 autonomous/trade_executor.py")

        self._save_state()
        return results


def main():
    executor = TradeExecutor()
    return executor.run_trading_cycle()


if __name__ == "__main__":
    main()
