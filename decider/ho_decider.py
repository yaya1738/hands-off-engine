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
from typing import List

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from audit import get_audit_logger


@dataclass
class PlannedAction:
    """Structured representation of a planned trading action"""
    market_id: str
    market_name: str
    side: str  # "YES" or "NO"
    amount: float  # Dollar amount to risk
    confidence: float  # 0.0 to 1.0
    reasoning: str  # Why this action makes sense


class Decider:
    """
    The Decider is the brain of the pipeline.
    It takes alpha signals and produces planned actions.
    """

    def __init__(self, bankroll: float = 1000.0):
        """
        Initialize the Decider.
        
        Args:
            bankroll: Total bankroll for position sizing (default: $1000)
        """
        self.bankroll = bankroll
        self.audit = get_audit_logger(component="decider")

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
        planned_actions = []

        for signal in alpha_signals:
            # Get edge and model confidence
            edge = signal.get('edge', 0.0)
            model_confidence = signal.get('model_confidence')
            
            # Use model confidence if available, otherwise derive from edge
            if model_confidence is not None:
                confidence = model_confidence
            else:
                confidence = 0.5 + (edge * 5)  # Simple scaling: 5% edge -> 0.75 confidence
                confidence = max(0.0, min(1.0, confidence))  # Clamp to [0, 1]

            # Size position based on edge and confidence
            # Kelly criterion approximation: f = (edge * confidence) / odds
            # Simplified: use a fraction of bankroll proportional to edge * confidence
            kelly_fraction = edge * confidence
            max_fraction = 0.10  # Never risk more than 10% of bankroll per position
            size_fraction = min(kelly_fraction, max_fraction)
            amount = self.bankroll * size_fraction

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
                reasoning=reasoning
            )

            planned_actions.append(action)

        return planned_actions


# Instantiate and decide (for backwards compatibility)
if __name__ == "__main__":
    decider = Decider()
    decider.decide()
