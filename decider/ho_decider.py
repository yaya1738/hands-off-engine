"""
Decider: The "Brain" of the Hands-Off Engine

This module converts alpha signals into structured planned actions.
It produces PlannedAction objects that represent trading intentions,
which are then validated and executed by the Executor (body).
"""

from dataclasses import dataclass
from typing import List


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

    def __init__(self):
        pass

    def decide(self):
        """Legacy method - kept for backwards compatibility"""
        print("Making a decision...")

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

        Returns:
            List of PlannedAction objects representing trading intentions
        """
        planned_actions = []

        for signal in alpha_signals:
            # Convert edge to confidence (simple linear mapping)
            # In production, this would use Kelly criterion or more sophisticated sizing
            edge = signal.get('edge', 0.0)
            confidence = 0.5 + (edge * 5)  # Simple scaling: 5% edge -> 0.75 confidence
            confidence = max(0.0, min(1.0, confidence))  # Clamp to [0, 1]

            # Size position based on edge and confidence
            # In production, this would consider bankroll, Kelly sizing, etc.
            base_size = 50.0  # Base position size in dollars
            amount = base_size * confidence

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
