"""
Decider: The "Brain" of the Hands-Off Engine

This module converts alpha signals into structured planned actions.
It produces PlannedAction objects that represent trading intentions,
which are then validated and executed by the Executor (body).
"""

import json
import sys
import os
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from audit import AuditLogger

try:
    from ai_nexus.history_log import log_kernel_history_event
except ImportError:
    # History log may not be available in all configurations
    log_kernel_history_event = None


@dataclass
class PlannedAction:
    """Structured representation of a planned trading action"""
    market_id: str  # Slug for display/logging
    market_name: str
    side: str  # "YES" or "NO"
    amount: float  # Dollar amount to risk
    confidence: float  # 0.0 to 1.0
    reasoning: str  # Why this action makes sense
    token_id: Optional[str] = None  # Actual CLOB token ID for trading


class Decider:
    """
    The Decider is the brain of the pipeline.
    It takes alpha signals and produces planned actions.
    """

    def __init__(self, bankroll: float = 5000.0):
        """
        Initialize the Decider.

        Args:
            bankroll: Total bankroll for position sizing (default: $5000)
        """
        self.bankroll = bankroll
        self.audit = AuditLogger()

        # Load max position from risk profile to align with executor limits
        self.max_position_usd = self._load_max_position()

    def _load_max_position(self) -> float:
        """Load max position size from risk profile, default to $50."""
        try:
            risk_path = Path(__file__).parent.parent / "state" / "risk_profile.json"
            if risk_path.exists():
                with open(risk_path) as f:
                    profile = json.load(f)
                return profile.get("max_position_usd", 50.0)
        except Exception:
            pass
        return 50.0  # Conservative default

    def decide(self):
        """Legacy method - kept for backwards compatibility"""
        print("Making a decision...")
        
        # Audit the decision
        self.audit.log_decision(
            decision_type="pipeline_decision",
            inputs={},
            outputs={"decision": "pending"}
        )

    def load_model_signals(self, model_path: Path) -> List[dict]:
        """
        Load alpha signals from polymarket-model.json file.
        
        Args:
            model_path: Path to polymarket-model.json
        
        Returns:
            List of alpha signal dicts in the format expected by plan_actions
        """
        with open(model_path, 'r') as f:
            model_data = json.load(f)
        
        # Transform model format to internal alpha signals format
        alpha_signals = []
        for market in model_data.get('markets', []):
            signal = {
                'market_id': market['market_id'],
                'token_id': market.get('token_id'),  # Actual CLOB token for trading
                'market_name': market['question'],
                'edge': market['model_edge'],
                'current_odds': market['market_price'],
                'side': market['side'],
                'model_confidence': market['model_confidence'],
                'fair_price': market['fair_price']
            }
            alpha_signals.append(signal)

        return alpha_signals

    def plan_actions(self, alpha_signals: List[dict]) -> List[PlannedAction]:
        """
        Convert alpha signals into planned actions.

        Args:
            alpha_signals: List of dicts with keys:
                - market_id: str
                - market_name: str
                - edge: float (expected edge, e.g., 0.05 for 5%)
                - current_odds: float (current market odds)
                - side: str ("YES" or "NO")
                - model_confidence: float (optional, from model)

        Returns:
            List of PlannedAction objects representing trading intentions
        """
        # POLYMARKET MINIMUM ORDER SIZE IS $1
        MIN_TRADE_SIZE = 1.0

        # Calculate max trades we can afford
        max_trades = int(self.bankroll // MIN_TRADE_SIZE)
        if max_trades < 1:
            print(f"[DECIDER] Bankroll ${self.bankroll:.2f} insufficient for ${MIN_TRADE_SIZE} min trades")
            return []

        # Sort signals by edge * confidence to prioritize best opportunities
        def signal_score(s):
            edge = s.get('edge', 0.0)
            conf = s.get('model_confidence', 0.5 + edge * 5)
            return edge * conf

        sorted_signals = sorted(alpha_signals, key=signal_score, reverse=True)

        # Only take top N signals we can afford
        selected_signals = sorted_signals[:max_trades]
        print(f"[DECIDER] Selecting top {len(selected_signals)} of {len(alpha_signals)} signals (bankroll ${self.bankroll:.2f}, min ${MIN_TRADE_SIZE})")

        planned_actions = []

        for signal in selected_signals:
            # Get edge and model confidence
            edge = signal.get('edge', 0.0)
            model_confidence = signal.get('model_confidence')
            
            # Use model confidence if available, otherwise derive from edge
            if model_confidence is not None:
                confidence = model_confidence
            else:
                confidence = 0.5 + (edge * 5)  # Simple scaling: 5% edge -> 0.75 confidence
                confidence = max(0.0, min(1.0, confidence))  # Clamp to [0, 1]

            # Size position - with limited capital, use equal allocation
            # Each trade gets bankroll / num_selected_trades
            num_trades = len(selected_signals)
            base_amount = self.bankroll / num_trades

            # Ensure minimum $1 per trade (Polymarket minimum)
            amount = max(base_amount, MIN_TRADE_SIZE)

            # Cap at risk profile max position
            amount = min(amount, self.max_position_usd)

            # Kelly factor - use it to prioritize (already sorted) but don't reduce below minimum
            kelly_fraction = edge * confidence

            # Create reasoning string
            reasoning = (
                f"Edge: {edge:.1%}, Current odds: {signal.get('current_odds', 0):.2f}, "
                f"Confidence: {confidence:.1%}"
            )

            action = PlannedAction(
                market_id=signal['market_id'],
                market_name=signal['market_name'],
                side=signal['side'],
                amount=amount,
                confidence=confidence,
                reasoning=reasoning,
                token_id=signal.get('token_id')  # Pass through for actual trading
            )

            planned_actions.append(action)

            # Log risk decision for Spark Plug kernels (if available)
            if log_kernel_history_event:
                try:
                    log_kernel_history_event(
                        kernel_ids=["risk_model_v2", "trading_philosophy"],
                        kind="risk_decision",
                        source="risk_model_v2",
                        summary=f"Risk decision for {signal['market_id']}: f={kelly_fraction:.3f}, size=${amount:.2f}, edge={edge:.3f}, conf={confidence:.2f}",
                        details={
                            "market_id": signal['market_id'],
                            "market_name": signal['market_name'],
                            "side": signal['side'],
                            "edge": edge,
                            "confidence": confidence,
                            "kelly_raw": kelly_fraction,
                            "kelly_used": kelly_fraction,
                            "size_usd": amount,
                            "current_odds": signal.get('current_odds', None),
                            "fair_price": signal.get('fair_price', None),
                        },
                        importance=8,
                        tags=["risk_v2", "kelly"],
                    )
                except Exception as e:
                    # Best-effort logging - never crash the decider
                    print(f"[history_log] Warning: Failed to log risk decision: {e}")

        # Log aggregate decider outcome for Spark Plug kernels (if available)
        if log_kernel_history_event:
            try:
                total_risk_usd = sum(action.amount for action in planned_actions)
                num_buys = sum(1 for action in planned_actions if action.side == "YES")
                num_sells = sum(1 for action in planned_actions if action.side == "NO")

                log_kernel_history_event(
                    kernel_ids=["risk_model_v2", "alpha_polymarket_core", "trading_philosophy"],
                    kind="decider_outcome",
                    source="ho_decider",
                    summary=f"Decider produced {len(planned_actions)} decisions, total_risk=${total_risk_usd:.2f}, buys={num_buys}, sells={num_sells}",
                    details={
                        "num_decisions": len(planned_actions),
                        "total_risk_usd": total_risk_usd,
                        "num_buys": num_buys,
                        "num_sells": num_sells,
                        "market_ids": [action.market_id for action in planned_actions],
                        "bankroll": self.bankroll,
                    },
                    importance=7,
                    tags=["decider", "aggregate"],
                )
            except Exception as e:
                # Best-effort logging - never crash the decider
                print(f"[history_log] Warning: Failed to log decider outcome: {e}")

        return planned_actions


# Instantiate and decide (for backwards compatibility)
if __name__ == "__main__":
    decider = Decider()
    decider.decide()
