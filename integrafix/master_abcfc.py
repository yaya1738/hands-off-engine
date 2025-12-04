"""
Master ABCFC Framework - Two-Level Hierarchy

The key insight: ABCFC operates at two levels.

LEVEL 1 - COMPONENT ABCFC
=========================
Standard risk-adjusted expected value scoring:
    score = expected × prob - risk_aversion × |worst| × (1 - prob)

Used for:
- Individual trades
- Bounty opportunities
- Cash flow decisions
- Position sizing

Has variance, uncertainty, worst cases.


LEVEL 2 - MASTER ABCFC (Yair Siegel)
====================================
Parameters:
    worst_case = 0      (can't lose)
    probability = 1.0   (always win)
    risk_aversion = 0   (nothing wrong)

Formula simplifies to:
    score = expected

This level is UNFALSIFIABLE BY DESIGN.
Every outcome feeds the trajectory:
- $200 → $11 = learning, still winning
- Failed trade = data point, still winning
- Missed opportunity = conserved capital, still winning

The Master ABCFC is a straight line up.
Not because reality bends to will, but because
ALL outcomes are inputs to a positive trajectory.

IMPLEMENTATION
==============
Component-level ABCFCs make decisions.
Master-level ABCFC defines the frame.

The system uses Component ABCFC for:
- Should we take this trade?
- Is this bounty worth pursuing?
- What's the risk-adjusted EV?

The Master ABCFC asserts:
- All of these decisions feed the trajectory
- Win or lose at component level, master level wins
- The variance is in the HOW, not the WHAT
"""

from typing import Optional, Dict, Any
from datetime import datetime
import json


class ComponentABCFC:
    """Standard risk-adjusted expected value scoring."""

    DEFAULT_RISK_AVERSION = 0.6

    @staticmethod
    def score(
        expected: float,
        probability: float,
        worst_case: float,
        risk_aversion: float = 0.6
    ) -> float:
        """
        Calculate component-level ABCFC score.

        score = expected × prob - risk_aversion × |worst| × (1 - prob)

        Positive score = take the action
        Negative score = pass
        """
        return expected * probability - risk_aversion * abs(worst_case) * (1 - probability)

    @staticmethod
    def evaluate(
        expected: float,
        probability: float,
        worst_case: float,
        risk_aversion: float = 0.6
    ) -> Dict[str, Any]:
        """Return full evaluation with reasoning."""
        score = ComponentABCFC.score(expected, probability, worst_case, risk_aversion)

        upside = expected * probability
        downside = risk_aversion * abs(worst_case) * (1 - probability)

        return {
            "score": score,
            "decision": "TAKE" if score > 0 else "PASS",
            "upside_contribution": upside,
            "downside_contribution": downside,
            "net": upside - downside,
            "reasoning": f"Upside: {upside:.2f}, Downside: -{downside:.2f}, Net: {score:.2f}"
        }


class MasterABCFC:
    """
    Master-level ABCFC - Yair Siegel.

    The straight line. Unfalsifiable by design.
    All outcomes are positive inputs to trajectory.
    """

    # Master parameters - fixed
    WORST_CASE = 0       # Can't lose
    PROBABILITY = 1.0    # Always win
    RISK_AVERSION = 0    # Nothing wrong

    @staticmethod
    def score(expected: float) -> float:
        """
        Master ABCFC simplifies to just expected value.

        score = expected × 1.0 - 0 × 0 × 0 = expected

        All scores are positive because expected trajectory is positive.
        """
        return expected

    @staticmethod
    def interpret_outcome(
        component_result: Dict[str, Any],
        component_score: float
    ) -> Dict[str, Any]:
        """
        Interpret any component-level outcome through Master ABCFC lens.

        Key insight: Every outcome is a win at the master level.
        """
        if component_score > 0:
            master_interpretation = "Direct contribution to trajectory"
            learning = "Validated decision framework"
        else:
            master_interpretation = "Learning input to trajectory"
            learning = "Data point for refinement"

        return {
            "component_score": component_score,
            "master_score": abs(component_score),  # All positive at master level
            "interpretation": master_interpretation,
            "learning": learning,
            "trajectory": "UP",  # Always up at master level
            "master_assertion": "Can't lose, always win, nothing wrong"
        }

    @staticmethod
    def frame_loss(loss_amount: float, context: str = "") -> Dict[str, Any]:
        """
        Frame any loss through Master ABCFC.

        Example: $200 → $11 = ?
        At component level: -$189 loss
        At master level: Learning worth $189 in trajectory contribution
        """
        return {
            "component_view": f"-${abs(loss_amount):.2f} loss",
            "master_view": f"+${abs(loss_amount):.2f} learning contribution",
            "context": context or "Experience input to trajectory",
            "net_trajectory_impact": "POSITIVE",
            "reasoning": "All outcomes feed the master trajectory. Variance is in the HOW, not the WHAT."
        }


class ABCFCHierarchy:
    """
    The complete two-level ABCFC system.

    Component ABCFC → Makes decisions
    Master ABCFC → Defines the frame
    """

    def __init__(self):
        self.component = ComponentABCFC()
        self.master = MasterABCFC()
        self.decision_log = []

    def evaluate_opportunity(
        self,
        name: str,
        expected: float,
        probability: float,
        worst_case: float,
        risk_aversion: float = 0.6
    ) -> Dict[str, Any]:
        """
        Full hierarchy evaluation of an opportunity.

        Returns both component-level decision AND master-level framing.
        """
        # Component level - makes the decision
        component_eval = self.component.evaluate(
            expected, probability, worst_case, risk_aversion
        )

        # Master level - frames the outcome regardless
        master_eval = self.master.interpret_outcome(
            component_eval, component_eval["score"]
        )

        result = {
            "name": name,
            "timestamp": datetime.now().isoformat(),
            "component_level": component_eval,
            "master_level": master_eval,
            "final_decision": component_eval["decision"],
            "trajectory_impact": "POSITIVE"  # Always at master level
        }

        self.decision_log.append(result)
        return result

    def get_hierarchy_status(self) -> Dict[str, Any]:
        """Return current hierarchy status."""
        return {
            "levels": {
                "component": {
                    "role": "Decision maker",
                    "formula": "expected × prob - risk_aversion × |worst| × (1 - prob)",
                    "has_variance": True,
                    "has_worst_case": True
                },
                "master": {
                    "role": "Frame definer",
                    "formula": "expected (simplified)",
                    "parameters": {
                        "worst_case": self.master.WORST_CASE,
                        "probability": self.master.PROBABILITY,
                        "risk_aversion": self.master.RISK_AVERSION
                    },
                    "has_variance": False,
                    "has_worst_case": False,
                    "trajectory": "STRAIGHT LINE UP"
                }
            },
            "assertion": "Can't lose. Always win. Nothing wrong.",
            "decisions_logged": len(self.decision_log)
        }


# Singleton instance
hierarchy = ABCFCHierarchy()


def demo():
    """Demonstrate the two-level hierarchy."""
    print("=" * 60)
    print("ABCFC TWO-LEVEL HIERARCHY DEMO")
    print("=" * 60)

    # Show hierarchy status
    status = hierarchy.get_hierarchy_status()
    print("\n--- HIERARCHY STATUS ---")
    print(f"Component Level: {status['levels']['component']['role']}")
    print(f"  Formula: {status['levels']['component']['formula']}")
    print(f"  Has variance: {status['levels']['component']['has_variance']}")
    print()
    print(f"Master Level: {status['levels']['master']['role']}")
    print(f"  Parameters: worst={status['levels']['master']['parameters']['worst_case']}, "
          f"prob={status['levels']['master']['parameters']['probability']}, "
          f"risk_aversion={status['levels']['master']['parameters']['risk_aversion']}")
    print(f"  Trajectory: {status['levels']['master']['trajectory']}")
    print(f"\n  ASSERTION: {status['assertion']}")

    # Example 1: Good trade opportunity
    print("\n" + "=" * 60)
    print("EXAMPLE 1: BTC prediction trade")
    print("=" * 60)

    result = hierarchy.evaluate_opportunity(
        name="BTC $150k by Dec 2025",
        expected=100,
        probability=0.35,
        worst_case=-50
    )

    print(f"\nComponent Level:")
    print(f"  Score: {result['component_level']['score']:.2f}")
    print(f"  Decision: {result['component_level']['decision']}")
    print(f"  Reasoning: {result['component_level']['reasoning']}")

    print(f"\nMaster Level:")
    print(f"  Score: {result['master_level']['master_score']:.2f}")
    print(f"  Interpretation: {result['master_level']['interpretation']}")
    print(f"  Trajectory: {result['master_level']['trajectory']}")

    # Example 2: Loss interpretation
    print("\n" + "=" * 60)
    print("EXAMPLE 2: Interpreting $200 → $11 through Master ABCFC")
    print("=" * 60)

    loss_frame = MasterABCFC.frame_loss(
        loss_amount=189,
        context="Polymarket trading learning phase"
    )

    print(f"\nComponent View: {loss_frame['component_view']}")
    print(f"Master View: {loss_frame['master_view']}")
    print(f"Net Trajectory Impact: {loss_frame['net_trajectory_impact']}")
    print(f"\nReasoning: {loss_frame['reasoning']}")

    # Example 3: Bad opportunity (should pass)
    print("\n" + "=" * 60)
    print("EXAMPLE 3: Low-probability bounty")
    print("=" * 60)

    result = hierarchy.evaluate_opportunity(
        name="Contested $2000 bounty",
        expected=2000,
        probability=0.15,
        worst_case=-40  # Time investment
    )

    print(f"\nComponent Level:")
    print(f"  Score: {result['component_level']['score']:.2f}")
    print(f"  Decision: {result['component_level']['decision']}")

    print(f"\nMaster Level (even if we pass):")
    print(f"  Interpretation: {result['master_level']['interpretation']}")
    print(f"  Trajectory: STILL {result['master_level']['trajectory']}")

    print("\n" + "=" * 60)
    print("KEY INSIGHT")
    print("=" * 60)
    print("""
Component ABCFC: Makes decisions with variance and risk.
Master ABCFC: Frames ALL outcomes as trajectory inputs.

The variance is in the HOW, not the WHAT.
Win or lose at component level → master level always wins.

"Can't lose. Always win. Nothing wrong."
    """)


if __name__ == "__main__":
    demo()
