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

# INTEGRAFIX: Import ABCFC bridge for proper decision scoring
try:
    from integrafix.claude_abcfc_bridge import get_bridge
    ABCFC_AVAILABLE = True
except ImportError:
    ABCFC_AVAILABLE = False

MASTER = "Yair Siegel"
TRADE_STATE = STATE_DIR / "trade_executor_state.json"
TRADE_LOG = STATE_DIR / "trade_history.jsonl"


class TradeExecutor:
    """Execute trades on Polymarket."""

    def __init__(self):
        self.state = self._load_state()
        self.mode = self._get_trading_mode()

    def _get_trading_mode(self) -> str:
        """INTEGRAFIX: Get trading mode from config file first, then env, then state."""
        # 1. Check config file (highest priority)
        config_file = PROJECT_ROOT / "config" / "trading_config.json"
        if config_file.exists():
            try:
                with open(config_file) as f:
                    config = json.load(f)
                if config.get("live_trading_enabled") and not config.get("dry_run"):
                    return "LIVE"
            except Exception as e:
                # INTEGRAFIX: Log config load failures
                import logging
                logging.warning(f"Failed to load trading config: {e}")
        # 2. Check environment variable
        env_mode = os.environ.get("TRADING_MODE")
        if env_mode:
            return env_mode
        # 3. Check state file
        return self.state.get("mode", "DRYRUN")

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
        """Analyze a market for trading opportunity using ABCFC evaluation."""
        try:
            question = market.get("question", "")
            prices = json.loads(market.get("outcomePrices", "[]"))
            volume = float(market.get("volume", 0))
            liquidity = float(market.get("liquidity", 0))

            if len(prices) < 2:
                return None

            yes_price = float(prices[0])
            no_price = float(prices[1])

            # INTEGRAFIX: Use ABCFC bridge for proper evaluation
            if ABCFC_AVAILABLE:
                return self._analyze_with_abcfc(market, question, yes_price, no_price, volume, liquidity)

            # Fallback: original heuristics (deprecated)
            return self._analyze_heuristic(question, yes_price, no_price, volume, liquidity)

        except Exception as e:
            return None

    def _analyze_with_abcfc(self, market: Dict, question: str, yes_price: float,
                            no_price: float, volume: float, liquidity: float) -> Optional[Dict]:
        """INTEGRAFIX: Analyze using ABCFC bridge for proper scoring."""
        bridge = get_bridge()

        # Potential actions: buy YES, buy NO, or skip
        trade_size = 1.0  # $1 base position for evaluation

        actions = [
            {
                "name": "buy_yes",
                "action_type": "buy",
                "side": "YES",
                "price": yes_price,
                "size": trade_size,
                "market": question[:80],
                "volume": volume,
                "liquidity": liquidity
            },
            {
                "name": "buy_no",
                "action_type": "buy",
                "side": "NO",
                "price": no_price,
                "size": trade_size,
                "market": question[:80],
                "volume": volume,
                "liquidity": liquidity
            },
            {
                "name": "skip",
                "action_type": "hold",
                "side": "NONE",
                "market": question[:80]
            }
        ]

        # Evaluate using trading decision method
        result = bridge.evaluate_trading_decision(
            decision=f"Trade on: {question[:50]}",
            actions=actions
        )

        recommended = result.get("recommended", {})
        action_name = recommended.get("action", "skip")
        score = recommended.get("score", 0)

        # Only signal if score is positive and not skip
        if action_name == "skip" or score <= 0:
            return None

        # Find the action details
        for a in actions:
            if a["name"] == action_name:
                return {
                    "market": question[:80],
                    "side": a["side"],
                    "price": a.get("price", 0),
                    "confidence": min(score / 10, 1.0),  # Normalize score to confidence
                    "abcfc_score": score,
                    "reason": f"ABCFC score: {score:.2f}",
                    "using_abcfc": True
                }

        return None

    def _analyze_heuristic(self, question: str, yes_price: float, no_price: float,
                          volume: float, liquidity: float) -> Optional[Dict]:
        """Fallback heuristic analysis (deprecated - prefer ABCFC)."""
        signal = None

        # Very low YES price with high volume = potential value
        if yes_price < 0.05 and volume > 100000:
            signal = {
                "market": question[:80],
                "side": "YES",
                "price": yes_price,
                "confidence": 0.6,
                "reason": f"Low YES ({yes_price:.3f}) with ${volume:,.0f} volume",
                "using_abcfc": False
            }

        # Very high YES price might be overconfident
        elif yes_price > 0.95 and volume > 100000:
            signal = {
                "market": question[:80],
                "side": "NO",
                "price": no_price,
                "confidence": 0.5,
                "reason": f"High YES ({yes_price:.3f}) may be overconfident",
                "using_abcfc": False
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
                    "reason": f"Wide spread ({spread:.3f}) arbitrage potential",
                    "using_abcfc": False
                }

        return signal

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
            # INTEGRAFIX: Use credential_loader for unified key access
            from integrafix.credential_loader import load_polymarket_key
            private_key = load_polymarket_key()
            if not private_key:
                result["status"] = "failed"
                result["error"] = "No API key - check credential_loader"
                return result

            # INTEGRAFIX: Execute real trade via py_clob_client
            from py_clob_client.client import ClobClient
            from py_clob_client.clob_types import OrderArgs
            from py_clob_client.order_builder.constants import BUY, SELL

            client = ClobClient(
                host="https://clob.polymarket.com",
                key=private_key,
                chain_id=137
            )
            creds = client.create_or_derive_api_creds()
            client.set_api_creds(creds)

            # Get token_id from signal
            token_id = signal.get("token_id") or signal.get("market_id")
            side_const = BUY if signal.get("side") == "BUY" else SELL
            price = signal.get("price", 0.5)

            order_args = OrderArgs(
                token_id=token_id,
                price=price,
                size=amount,
                side=side_const
            )

            signed_order = client.create_order(order_args)
            api_result = client.post_order(signed_order)

            if api_result and (api_result.get("orderID") or api_result.get("success")):
                result["status"] = "executed"
                result["order_id"] = api_result.get("orderID") or str(api_result)[:50]
            else:
                result["status"] = "failed"
                result["error"] = f"API error: {api_result}"

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
