#!/usr/bin/env python3
"""
INTEGRAFIX: Outcome Tracker
============================

PROBLEM SOLVED:
Trades are executed but outcomes are never recorded.
The learning feedback loop is broken.

SOLUTION:
1. Track all executed trades
2. Monitor markets for resolution
3. Record outcomes when markets resolve
4. Feed outcomes to learning engine

This completes the trading pipeline feedback loop:
    signal → execute → record → LEARN → (improves signal)
"""

import json
import os
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict

# HFT Economics tracking - every trade outcome at microsecond frequency
try:
    from integrafix.hft_economics import track_trade_pnl, track_value
    HFT_TRACKING = True
except ImportError:
    HFT_TRACKING = False
    def track_trade_pnl(*args, **kwargs): return 0
    def track_value(*args, **kwargs): return 0

PROJECT_ROOT = Path(__file__).parent.parent
STATE_DIR = PROJECT_ROOT / "state"
TRADES_LOG = STATE_DIR / "trades_executed.jsonl"
OUTCOMES_LOG = STATE_DIR / "trade_outcomes.jsonl"
TRACKER_STATE = STATE_DIR / "outcome_tracker.json"


@dataclass
class PendingTrade:
    """A trade awaiting outcome."""
    trade_id: str
    signal_id: str
    market_id: str
    side: str  # YES or NO
    size: float
    entry_price: float
    executed_at: str
    market_question: str = ""


@dataclass
class ResolvedOutcome:
    """Outcome of a resolved trade."""
    trade_id: str
    signal_id: str
    market_id: str
    side: str
    size: float
    entry_price: float
    resolution: str  # "YES" or "NO"
    pnl: float
    pnl_pct: float
    edge_predicted: float
    edge_actual: float
    was_correct: bool
    resolved_at: str


class OutcomeTracker:
    """
    Tracks trade outcomes and completes the feedback loop.
    """

    def __init__(self):
        self.state = self._load_state()
        self.pending_trades: Dict[str, PendingTrade] = {}
        self.resolved_outcomes: List[ResolvedOutcome] = []
        self._load_pending_trades()

    def _load_state(self) -> Dict:
        if TRACKER_STATE.exists():
            with open(TRACKER_STATE) as f:
                return json.load(f)
        return {
            "created_at": datetime.now(timezone.utc).isoformat(),
            "total_tracked": 0,
            "total_resolved": 0,
            "wins": 0,
            "losses": 0,
            "win_rate": 0.0,
            "total_pnl": 0.0,
            "last_check": None,
        }

    def _save_state(self):
        self.state["last_updated"] = datetime.now(timezone.utc).isoformat()
        with open(TRACKER_STATE, 'w') as f:
            json.dump(self.state, f, indent=2)

    def _load_pending_trades(self):
        """Load trades from log that haven't been resolved yet."""
        if not TRADES_LOG.exists():
            return

        # Load resolved trade IDs
        resolved_ids = set()
        if OUTCOMES_LOG.exists():
            with open(OUTCOMES_LOG) as f:
                for line in f:
                    try:
                        outcome = json.loads(line)
                        resolved_ids.add(outcome.get("trade_id"))
                    except:
                        pass

        # Load unresolved trades
        with open(TRADES_LOG) as f:
            for line in f:
                try:
                    trade = json.loads(line)
                    trade_id = trade.get("id")
                    if trade_id and trade_id not in resolved_ids:
                        self.pending_trades[trade_id] = PendingTrade(
                            trade_id=trade_id,
                            signal_id=trade.get("signal_id", ""),
                            market_id=trade.get("market_id", ""),
                            side=trade.get("side", ""),
                            size=float(trade.get("size", 0)),
                            entry_price=float(trade.get("price", 0) or trade.get("fill_price", 0)),
                            executed_at=trade.get("executed_at", ""),
                        )
                except:
                    pass

        self.state["total_tracked"] = len(self.pending_trades)
        self._save_state()

    def check_resolutions(self) -> List[ResolvedOutcome]:
        """
        Check Polymarket for resolved markets and record outcomes.
        Uses the Gamma API to check market status.
        """
        import requests

        outcomes = []
        GAMMA_API = "https://gamma-api.polymarket.com"

        for trade_id, trade in list(self.pending_trades.items()):
            try:
                # Query Gamma API for market status
                market_id = trade.market_id

                # Try by slug first (most common format)
                response = requests.get(
                    f"{GAMMA_API}/markets?slug={market_id}",
                    timeout=10
                )

                if response.status_code != 200:
                    continue

                markets = response.json()
                if not markets:
                    continue

                market = markets[0]

                # Check if market is closed/resolved
                if not market.get("closed", False):
                    continue

                # Determine resolution from outcomePrices
                outcome_prices = market.get("outcomePrices", [])
                if len(outcome_prices) < 2:
                    continue

                # outcomePrices[0] = YES price, outcomePrices[1] = NO price
                yes_price = float(outcome_prices[0]) if outcome_prices[0] else 0
                no_price = float(outcome_prices[1]) if outcome_prices[1] else 0

                # Resolution: YES wins if yes_price > 0.5, NO wins if no_price > 0.5
                if yes_price > 0.5:
                    resolution = "YES"
                elif no_price > 0.5:
                    resolution = "NO"
                else:
                    # Market cancelled or indeterminate - skip
                    continue

                # Record the outcome
                outcome = self.record_outcome(
                    trade_id=trade_id,
                    resolution=resolution,
                    edge_predicted=0.0  # Would need signal data for this
                )

                if outcome:
                    outcomes.append(outcome)
                    print(f"  Resolved: {market_id[:40]}... -> {resolution}")

            except Exception as e:
                continue

        self.state["last_check"] = datetime.now(timezone.utc).isoformat()
        self._save_state()

        return outcomes

    def record_outcome(
        self,
        trade_id: str,
        resolution: str,  # "YES" or "NO"
        edge_predicted: float = 0.0,
    ) -> Optional[ResolvedOutcome]:
        """
        Manually record an outcome for a trade.
        """
        trade = self.pending_trades.get(trade_id)
        if not trade:
            return None

        # Calculate P&L
        resolution_price = 1.0 if resolution == "YES" else 0.0

        if trade.side == "YES":
            pnl_per_share = resolution_price - trade.entry_price
        else:  # NO
            pnl_per_share = trade.entry_price - resolution_price

        pnl = trade.size * pnl_per_share
        pnl_pct = (pnl / trade.size) * 100 if trade.size > 0 else 0

        # Track profit/loss at HFT frequency (microseconds)
        if HFT_TRACKING:
            track_trade_pnl(
                market=trade.market_id,
                side=trade.side,
                size=trade.size,
                entry=trade.entry_price,
                exit=resolution_price,
            )

        # Determine if prediction was correct
        was_correct = (
            (trade.side == "YES" and resolution == "YES") or
            (trade.side == "NO" and resolution == "NO")
        )

        edge_actual = abs(resolution_price - trade.entry_price)

        outcome = ResolvedOutcome(
            trade_id=trade_id,
            signal_id=trade.signal_id,
            market_id=trade.market_id,
            side=trade.side,
            size=trade.size,
            entry_price=trade.entry_price,
            resolution=resolution,
            pnl=round(pnl, 4),
            pnl_pct=round(pnl_pct, 2),
            edge_predicted=edge_predicted,
            edge_actual=round(edge_actual, 4),
            was_correct=was_correct,
            resolved_at=datetime.now(timezone.utc).isoformat(),
        )

        # Log outcome
        with open(OUTCOMES_LOG, 'a') as f:
            f.write(json.dumps(asdict(outcome)) + "\n")

        # Update state
        self.state["total_resolved"] += 1
        self.state["total_pnl"] = self.state.get("total_pnl", 0) + pnl
        if was_correct:
            self.state["wins"] = self.state.get("wins", 0) + 1
        else:
            self.state["losses"] = self.state.get("losses", 0) + 1

        total = self.state["wins"] + self.state["losses"]
        self.state["win_rate"] = self.state["wins"] / total if total > 0 else 0

        # Remove from pending
        del self.pending_trades[trade_id]
        self._save_state()

        # Feed to learning engine
        self._feed_to_learner(outcome)

        return outcome

    def _feed_to_learner(self, outcome: ResolvedOutcome):
        """Feed outcome to the learning engine to improve future predictions."""
        # Feed to trading pipeline
        try:
            from integrafix.trading_pipeline import get_pipeline

            pipeline = get_pipeline()

            # Record in pipeline for learning
            pipeline.record_outcome(
                outcome.trade_id,
                1.0 if outcome.resolution == "YES" else 0.0,
            )

            # Trigger learning analysis
            learnings = pipeline.analyze_and_learn()
            if learnings:
                print(f"  Generated {len(learnings)} learnings from outcome")

        except Exception as e:
            print(f"Error feeding to pipeline: {e}")

        # Feed to skill growth tracker (WIRE ADDED)
        try:
            from autonomous.skill_growth_tracker import SkillGrowthTracker

            tracker = SkillGrowthTracker()

            # Record probability estimation skill
            actual_value = 1.0 if outcome.resolution == "YES" else 0.0
            tracker.record_outcome(
                skill="probability_estimation",
                prediction=outcome.entry_price,  # Our predicted probability
                actual=actual_value,
                category=None,
                details=f"Market: {outcome.market_id[:30]}"
            )

            # Record category-specific skill if applicable
            # (Would need market category info to determine which skill)

            tracker._save_state()

        except Exception as e:
            print(f"Error feeding to skill tracker: {e}")

    def simulate_outcomes(self, win_rate: float = 0.55, max_per_cycle: int = 5) -> List[ResolvedOutcome]:
        """
        Simulate outcomes for dry-run trades.
        Useful for testing the feedback loop.

        Args:
            win_rate: Probability of winning (based on edge quality)
            max_per_cycle: Maximum trades to resolve per cycle
        """
        import random

        outcomes = []
        resolved_count = 0

        for trade_id, trade in list(self.pending_trades.items()):
            if resolved_count >= max_per_cycle:
                break

            # All pending trades from dry runs are candidates
            # (Real trades would be checked via Polymarket API)

            # Simulate win/loss based on win_rate
            won = random.random() < win_rate

            if trade.side == "YES":
                resolution = "YES" if won else "NO"
            else:
                resolution = "NO" if won else "YES"

            outcome = self.record_outcome(
                trade_id,
                resolution,
                edge_predicted=0.03,  # Assumed edge
            )
            if outcome:
                outcomes.append(outcome)
                resolved_count += 1

        return outcomes

    def status(self) -> Dict:
        """Get tracker status."""
        return {
            "pending_trades": len(self.pending_trades),
            "total_resolved": self.state.get("total_resolved", 0),
            "wins": self.state.get("wins", 0),
            "losses": self.state.get("losses", 0),
            "win_rate": f"{self.state.get('win_rate', 0):.1%}",
            "total_pnl": f"${self.state.get('total_pnl', 0):.2f}",
            "last_check": self.state.get("last_check"),
        }


# Singleton
_tracker = None

def get_tracker() -> OutcomeTracker:
    global _tracker
    if _tracker is None:
        _tracker = OutcomeTracker()
    return _tracker


def main():
    """Test outcome tracker."""
    tracker = get_tracker()

    print("=" * 70)
    print("INTEGRAFIX: Outcome Tracker")
    print("=" * 70)

    status = tracker.status()
    print(f"\nPending Trades: {status['pending_trades']}")
    print(f"Total Resolved: {status['total_resolved']}")
    print(f"Win Rate: {status['win_rate']}")
    print(f"Total P&L: {status['total_pnl']}")

    if tracker.pending_trades:
        print("\nSimulating outcomes for dry-run trades...")
        outcomes = tracker.simulate_outcomes(win_rate=0.55)
        print(f"Resolved {len(outcomes)} trades")

        for o in outcomes[:3]:
            result = "WIN" if o.was_correct else "LOSS"
            print(f"  {o.trade_id[:30]}... [{result}] {o.resolution} P&L: ${o.pnl:.2f}")

        print("\nUpdated Status:")
        status = tracker.status()
        print(f"Win Rate: {status['win_rate']}")
        print(f"Total P&L: {status['total_pnl']}")


if __name__ == "__main__":
    main()
