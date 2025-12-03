#!/usr/bin/env python3
"""
UNIFIED TRADING BRAIN - All Trading Capabilities in One Place
==============================================================

This module unifies ALL trading and Polymarket capabilities scattered
across the repo into a single, coherent trading arm.

Master: Yair Siegel

CAPABILITIES:
- Market data fetching (Polymarket, arbitrage sources)
- Signal generation and analysis
- Trade execution with safeguards
- Position tracking
- Alpha strategies (spread capture, arbitrage)
- Risk management

INTEGRATED MODULES:
- executor/polymarket_api.py - Low-level Polymarket API
- executor/trading_safeguards.py - Safety checks
- autonomous/actuators.py - Execution layer
- trading/signal_generator.py - Signal generation
- alpha/* - Alpha strategies
- arbitrage/* - Cross-platform arbitrage
"""

import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass

BASE_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(BASE_DIR))

STATE_DIR = BASE_DIR / "state"


@dataclass
class TradingState:
    """Current state of the trading system."""
    balance: float
    positions: List[Dict]
    pending_orders: List[Dict]
    daily_pnl: float
    trade_count_today: int
    last_trade_time: Optional[str]
    mode: str  # "live", "shadow", "disabled"


@dataclass
class TradeDecision:
    """A decision to trade or not."""
    should_trade: bool
    reason: str
    signal: Optional[Dict]
    size_usd: float
    confidence: float


class TradingBrain:
    """
    The unified trading brain that coordinates all trading activities.

    This is the SINGLE POINT for all trading decisions and execution.
    All other trading code should go through this brain.
    """

    def __init__(self):
        self.state_file = STATE_DIR / "trading_brain_state.json"
        self._load_state()
        self._init_components()

    def _load_state(self):
        """Load trading brain state."""
        if self.state_file.exists():
            with open(self.state_file) as f:
                self._state = json.load(f)
        else:
            self._state = {
                "mode": "shadow",  # Default to shadow (paper) trading
                "balance": 0,
                "daily_loss_limit": 10.0,
                "max_position_size": 5.0,
                "min_confidence": 0.7,
                "last_sync": None
            }

    def _save_state(self):
        """Save trading brain state."""
        self._state["last_sync"] = datetime.now(timezone.utc).isoformat()
        STATE_DIR.mkdir(exist_ok=True)
        with open(self.state_file, 'w') as f:
            json.dump(self._state, f, indent=2)

    def _init_components(self):
        """Initialize all trading components."""
        # Safeguards
        try:
            from executor.trading_safeguards import TradingSafeguards
            self.safeguards = TradingSafeguards()
        except ImportError:
            self.safeguards = None

        # Actuator (execution)
        try:
            from autonomous.actuators import ActuatorHub
            self.actuator_hub = ActuatorHub()
            self.polymarket = self.actuator_hub.polymarket
        except ImportError:
            self.actuator_hub = None
            self.polymarket = None

        # Signal generator
        try:
            from trading.signal_generator import SignalGenerator
            self.signal_gen = SignalGenerator()
        except ImportError:
            self.signal_gen = None

        # Alpha strategies
        self.strategies = self._load_strategies()

    def _load_strategies(self) -> Dict:
        """Load available alpha strategies."""
        strategies = {}

        # SpreadCaptureEngine - uses generate_spread_signals()
        try:
            from alpha.spread_capture_strategy import SpreadCaptureEngine
            strategies["spread_capture"] = SpreadCaptureEngine
        except Exception as e:
            print(f"[TradingBrain] SpreadCaptureEngine load error: {e}")

        # IntelligentAlphaEngine
        try:
            from alpha.intelligent_alpha_engine import IntelligentAlphaEngine
            strategies["intelligent_alpha"] = IntelligentAlphaEngine
        except Exception as e:
            print(f"[TradingBrain] IntelligentAlphaEngine load error: {e}")

        # ArbitrageDetector - uses detect_opportunities()
        try:
            from arbitrage.opportunity_detector import ArbitrageDetector
            strategies["arbitrage"] = ArbitrageDetector
        except Exception as e:
            print(f"[TradingBrain] ArbitrageDetector load error: {e}")

        # SpreadAnalyzer - has find_opportunities()
        try:
            from alpha.spread_analyzer import SpreadAnalyzer
            strategies["spread_analyzer"] = SpreadAnalyzer
        except Exception as e:
            print(f"[TradingBrain] SpreadAnalyzer load error: {e}")

        return strategies

    # =========================================================================
    # MARKET DATA
    # =========================================================================

    def get_markets(self, limit: int = 50) -> List[Dict]:
        """Fetch active Polymarket markets."""
        if self.signal_gen:
            return self.signal_gen.fetch_markets(limit)

        # Fallback to direct API
        import requests
        try:
            resp = requests.get(
                "https://gamma-api.polymarket.com/markets",
                params={"closed": "false", "limit": limit},
                timeout=30
            )
            if resp.status_code == 200:
                return resp.json()
        except:
            pass
        return []

    def get_market(self, market_id: str) -> Optional[Dict]:
        """Get specific market details."""
        import requests
        try:
            resp = requests.get(
                f"https://gamma-api.polymarket.com/markets/{market_id}",
                timeout=30
            )
            if resp.status_code == 200:
                return resp.json()
        except:
            pass
        return None

    def get_balance(self) -> float:
        """Get current USDC balance."""
        if self.safeguards:
            ok, msg = self.safeguards.check_wallet_balance(0)
            if "balance: $" in msg:
                try:
                    return float(msg.split("balance: $")[1].split()[0])
                except:
                    pass
        return self._state.get("balance", 0)

    def get_positions(self) -> List[Dict]:
        """Get current positions."""
        positions_file = STATE_DIR / "positions.json"
        if positions_file.exists():
            try:
                with open(positions_file) as f:
                    data = json.load(f)
                return data.get("positions", [])
            except:
                pass
        return []

    # =========================================================================
    # SIGNAL GENERATION
    # =========================================================================

    def generate_signals(self, min_confidence: float = None) -> List[Dict]:
        """Generate trading signals from ALL sources - full power integration."""
        if min_confidence is None:
            min_confidence = self._state.get("min_confidence", 0.7)

        all_signals = []

        # From signal generator
        if self.signal_gen:
            try:
                signals = self.signal_gen.scan_opportunities()
                for s in signals:
                    if isinstance(s, dict) and s.get("confidence", 0) >= min_confidence:
                        s["source"] = "signal_generator"
                        all_signals.append(s)
            except Exception as e:
                print(f"[TradingBrain] Signal generator error: {e}")

        # From alpha strategies - UNIFIED INTERFACE for each strategy type
        for name, strategy_class in self.strategies.items():
            try:
                strategy = strategy_class()

                # SpreadCaptureEngine - uses generate_spread_signals()
                if name == "spread_capture" and hasattr(strategy, "generate_spread_signals"):
                    signals = strategy.generate_spread_signals()
                    for sig in (signals or []):
                        opp = self._convert_signal_to_dict(sig, name)
                        if opp and opp.get("confidence", 0) >= min_confidence:
                            all_signals.append(opp)

                # IntelligentAlphaEngine - uses generate_signals()
                elif name == "intelligent_alpha" and hasattr(strategy, "generate_signals"):
                    signals = strategy.generate_signals()
                    for sig in (signals or []):
                        opp = self._convert_signal_to_dict(sig, name)
                        if opp and opp.get("confidence", 0) >= min_confidence:
                            all_signals.append(opp)

                # ArbitrageDetector - uses scan_all()
                elif name == "arbitrage" and hasattr(strategy, "scan_all"):
                    result = strategy.scan_all()
                    # scan_all returns dict with 'prediction' and 'crypto' keys
                    for key, opps in result.items():
                        for opp in (opps or []):
                            d = self._convert_signal_to_dict(opp, f"{name}_{key}")
                            if d and d.get("confidence", 0) >= min_confidence:
                                all_signals.append(d)

                # SpreadAnalyzer - uses find_opportunities()
                elif name == "spread_analyzer" and hasattr(strategy, "find_opportunities"):
                    markets = self.get_markets(50)  # Provide markets
                    opps = strategy.find_opportunities(markets, min_score=min_confidence)
                    for opp in (opps or []):
                        d = self._convert_signal_to_dict(opp, name)
                        if d:
                            all_signals.append(d)

                # Generic fallback for any strategy with find_opportunities
                elif hasattr(strategy, "find_opportunities"):
                    opps = strategy.find_opportunities()
                    for opp in (opps or []):
                        d = self._convert_signal_to_dict(opp, name)
                        if d and d.get("confidence", 0) >= min_confidence:
                            all_signals.append(d)

            except Exception as e:
                print(f"[TradingBrain] Strategy {name} error: {e}")

        # Sort by confidence
        all_signals.sort(key=lambda x: x.get("confidence", 0), reverse=True)

        return all_signals

    def _convert_signal_to_dict(self, signal, source: str) -> Optional[Dict]:
        """Convert any signal type to dict format."""
        try:
            if isinstance(signal, dict):
                signal["source"] = source
                return signal
            elif hasattr(signal, "__dict__"):
                d = signal.__dict__.copy() if hasattr(signal, "__dict__") else {}
                d["source"] = source
                # Handle dataclass fields
                if hasattr(signal, "question"):
                    d["question"] = signal.question
                if hasattr(signal, "confidence"):
                    d["confidence"] = signal.confidence
                if hasattr(signal, "side"):
                    d["side"] = signal.side
                if hasattr(signal, "edge"):
                    d["confidence"] = signal.edge  # Use edge as confidence
                if hasattr(signal, "token_id"):
                    d["token_id"] = signal.token_id
                if hasattr(signal, "market_slug"):
                    d["market_slug"] = signal.market_slug
                return d
            elif hasattr(signal, "to_dict"):
                d = signal.to_dict()
                d["source"] = source
                return d
            else:
                return {"raw": str(signal), "source": source, "confidence": 0.5}
        except Exception as e:
            print(f"[TradingBrain] Signal conversion error: {e}")
            return None

    def get_best_signal(self, min_confidence: float = None) -> Optional[Dict]:
        """Get the single best trading signal."""
        signals = self.generate_signals(min_confidence)
        return signals[0] if signals else None

    # =========================================================================
    # TRADING DECISIONS
    # =========================================================================

    def should_trade(self, signal: Dict = None) -> TradeDecision:
        """
        Unified decision: Should we trade right now?

        Checks:
        1. Mode (live/shadow/disabled)
        2. Balance sufficient
        3. Safeguards pass
        4. Signal quality
        5. unified_ai approval
        """
        # Get signal if not provided
        if signal is None:
            signal = self.get_best_signal()

        if signal is None:
            return TradeDecision(
                should_trade=False,
                reason="No valid signal",
                signal=None,
                size_usd=0,
                confidence=0
            )

        confidence = signal.get("confidence", 0)

        # Check mode
        mode = self._state.get("mode", "shadow")
        if mode == "disabled":
            return TradeDecision(
                should_trade=False,
                reason="Trading disabled",
                signal=signal,
                size_usd=0,
                confidence=confidence
            )

        # Check balance
        balance = self.get_balance()
        if balance < 1:
            return TradeDecision(
                should_trade=False,
                reason=f"Balance too low: ${balance:.2f}",
                signal=signal,
                size_usd=0,
                confidence=confidence
            )

        # Calculate position size (25% of balance max)
        max_size = min(balance * 0.25, self._state.get("max_position_size", 5.0))
        size_usd = min(max_size, 1.50)  # Start with micro-trades

        # Check safeguards
        if self.safeguards:
            ok, msg = self.safeguards.check_position_size(size_usd)
            if not ok:
                return TradeDecision(
                    should_trade=False,
                    reason=f"Safeguard: {msg}",
                    signal=signal,
                    size_usd=0,
                    confidence=confidence
                )

            ok, msg = self.safeguards.check_daily_loss_limit()
            if not ok:
                return TradeDecision(
                    should_trade=False,
                    reason=f"Safeguard: {msg}",
                    signal=signal,
                    size_usd=0,
                    confidence=confidence
                )

        # Check unified_ai
        try:
            from ai.unified_ai import should_execute, check_trading_allowed

            ok, msg = check_trading_allowed(size_usd)
            if not ok:
                return TradeDecision(
                    should_trade=False,
                    reason=f"Brain: {msg}",
                    signal=signal,
                    size_usd=0,
                    confidence=confidence
                )

            action = f"trade {signal.get('side', 'BUY')} ${size_usd:.2f} on {signal.get('question', 'market')[:30]}"
            if not should_execute(action, roi_estimate=confidence - 0.5):
                return TradeDecision(
                    should_trade=False,
                    reason="Brain rejected action",
                    signal=signal,
                    size_usd=0,
                    confidence=confidence
                )
        except ImportError:
            pass

        # All checks passed
        return TradeDecision(
            should_trade=True,
            reason="All checks passed",
            signal=signal,
            size_usd=size_usd,
            confidence=confidence
        )

    # =========================================================================
    # TRADE EXECUTION
    # =========================================================================

    def execute_trade(self, decision: TradeDecision = None) -> Dict:
        """
        Execute a trade based on decision.

        Returns result with status, order_id, etc.
        """
        if decision is None:
            decision = self.should_trade()

        if not decision.should_trade:
            return {
                "success": False,
                "reason": decision.reason,
                "mode": self._state.get("mode", "shadow")
            }

        signal = decision.signal
        size_usd = decision.size_usd
        mode = self._state.get("mode", "shadow")

        result = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "mode": mode,
            "signal": signal,
            "size_usd": size_usd,
            "success": False,
            "reason": None
        }

        if mode == "shadow":
            # Shadow trade - just log it
            self._log_shadow_trade(signal, size_usd)
            result["success"] = True
            result["reason"] = "Shadow trade logged"
            return result

        if mode == "live":
            # Live trade through UNIFIED TRADING HUB (single execution path)
            try:
                from trading.unified_trading_hub import get_trading_hub, TradeRequest

                hub = get_trading_hub()
                request = TradeRequest(
                    market_slug=signal.get("market_slug", signal.get("slug", "")),
                    side=signal.get("side", "YES"),
                    amount_usd=size_usd,
                    token_id=signal.get("token_id"),
                    confidence=signal.get("confidence", 0.7),
                    reason=f"TradingBrain: {signal.get('question', 'auto')[:50]}",
                    source="trading_brain"
                )
                trade_result = hub.execute_trade(request)
                result["success"] = trade_result.success
                result["order_id"] = trade_result.order_id
                result["reason"] = trade_result.message
            except Exception as e:
                result["reason"] = str(e)

        # Log result
        self._log_trade_result(result)

        return result

    def _log_shadow_trade(self, signal: Dict, size_usd: float):
        """Log a shadow (paper) trade."""
        shadow_file = STATE_DIR / "shadow_trades.jsonl"
        entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "type": "shadow",
            "signal": signal,
            "size_usd": size_usd
        }
        with open(shadow_file, 'a') as f:
            f.write(json.dumps(entry) + '\n')

    def _log_trade_result(self, result: Dict):
        """Log trade result."""
        log_file = STATE_DIR / "trade_log.jsonl"
        with open(log_file, 'a') as f:
            f.write(json.dumps(result) + '\n')

    # =========================================================================
    # AUTONOMOUS OPERATION
    # =========================================================================

    def run_cycle(self) -> Dict:
        """
        Run one trading cycle autonomously.

        Called by coordination_agent or cron.
        """
        cycle_result = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "balance": self.get_balance(),
            "signals_found": 0,
            "trade_decision": None,
            "trade_result": None
        }

        # Generate signals
        signals = self.generate_signals()
        cycle_result["signals_found"] = len(signals)

        if not signals:
            cycle_result["trade_decision"] = "No signals"
            return cycle_result

        # Make decision
        decision = self.should_trade(signals[0])
        cycle_result["trade_decision"] = decision.reason

        if decision.should_trade:
            # Execute
            result = self.execute_trade(decision)
            cycle_result["trade_result"] = result

        return cycle_result

    # =========================================================================
    # STATUS & DIAGNOSTICS
    # =========================================================================

    def status(self) -> Dict:
        """Get full trading brain status."""
        return {
            "mode": self._state.get("mode", "shadow"),
            "balance": self.get_balance(),
            "positions": len(self.get_positions()),
            "safeguards_active": self.safeguards is not None,
            "polymarket_connected": self.polymarket is not None and self.polymarket.trader is not None,
            "signal_gen_active": self.signal_gen is not None,
            "strategies_loaded": list(self.strategies.keys()),
            "config": {
                "min_confidence": self._state.get("min_confidence", 0.7),
                "max_position_size": self._state.get("max_position_size", 5.0),
                "daily_loss_limit": self._state.get("daily_loss_limit", 10.0)
            }
        }

    def set_mode(self, mode: str):
        """Set trading mode: live, shadow, or disabled."""
        if mode not in ["live", "shadow", "disabled"]:
            raise ValueError(f"Invalid mode: {mode}")
        self._state["mode"] = mode
        self._save_state()

    def set_config(self, **kwargs):
        """Update trading configuration."""
        for key, value in kwargs.items():
            if key in ["min_confidence", "max_position_size", "daily_loss_limit"]:
                self._state[key] = value
        self._save_state()


# Singleton instance
_brain: Optional[TradingBrain] = None


def get_trading_brain() -> TradingBrain:
    """Get the singleton trading brain instance."""
    global _brain
    if _brain is None:
        _brain = TradingBrain()
    return _brain


# ============================================================================
# CLI
# ============================================================================

def main():
    """CLI interface for trading brain."""
    import argparse

    parser = argparse.ArgumentParser(description="Unified Trading Brain")
    parser.add_argument("command", choices=[
        "status", "signals", "decide", "trade", "cycle",
        "mode", "config", "positions", "balance"
    ])
    parser.add_argument("--mode", help="Set mode: live, shadow, disabled")
    parser.add_argument("--min-confidence", type=float, help="Minimum signal confidence")

    args = parser.parse_args()
    brain = get_trading_brain()

    if args.command == "status":
        status = brain.status()
        print(json.dumps(status, indent=2))

    elif args.command == "signals":
        signals = brain.generate_signals()
        print(f"Found {len(signals)} signals:")
        for s in signals[:5]:
            print(f"  - {s.get('question', '?')[:50]}...")
            print(f"    {s.get('side')} @ ${s.get('price', 0):.4f}, conf: {s.get('confidence', 0):.0%}")
            print()

    elif args.command == "decide":
        decision = brain.should_trade()
        print(f"Should trade: {decision.should_trade}")
        print(f"Reason: {decision.reason}")
        print(f"Size: ${decision.size_usd:.2f}")
        print(f"Confidence: {decision.confidence:.0%}")

    elif args.command == "trade":
        result = brain.execute_trade()
        print(json.dumps(result, indent=2, default=str))

    elif args.command == "cycle":
        result = brain.run_cycle()
        print(json.dumps(result, indent=2, default=str))

    elif args.command == "mode":
        if args.mode:
            brain.set_mode(args.mode)
            print(f"Mode set to: {args.mode}")
        else:
            print(f"Current mode: {brain._state.get('mode', 'shadow')}")

    elif args.command == "positions":
        positions = brain.get_positions()
        print(f"Positions: {len(positions)}")
        for p in positions[:5]:
            print(f"  - {p}")

    elif args.command == "balance":
        balance = brain.get_balance()
        print(f"Balance: ${balance:.2f}")


if __name__ == "__main__":
    main()
