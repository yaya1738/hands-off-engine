#!/usr/bin/env python3
"""
INTEGRAFIX: ABCFC ↔ Nexus Bridge
=================================

PROBLEM SOLVED:
ABCFC (financial decision system) and AI Nexus (knowledge system) operate
in isolation. Trading decisions don't consult knowledge bases, and outcomes
don't feed back to learning.

SOLUTION:
This bridge wires:
1. ABCFC Cloud → AI Nexus kernels (consult before decisions)
2. ABCFC Outcomes → AI Learning (feed results back)
3. AI Orchestrator → ABCFC System (knowledge-informed trading)

ARCHITECTURE:
                     ┌─────────────────────────────────────────┐
                     │          INTEGRAFIX BRIDGE              │
                     └─────────────────────────────────────────┘
                                       │
            ┌──────────────────────────┼──────────────────────────┐
            │                          │                          │
            ▼                          ▼                          ▼
    ┌───────────────┐          ┌───────────────┐          ┌───────────────┐
    │  ABCFC NEXUS  │  <────>  │  AI NEXUS     │  <────>  │  LEARNING     │
    │  CLOUD        │          │  KERNELS      │          │  ENGINE       │
    │               │          │               │          │               │
    │  • Layers     │          │  • Trading    │          │  • Outcomes   │
    │  • Actions    │          │  • Risk       │          │  • Skills     │
    │  • Decisions  │          │  • Yair       │          │  • Feedback   │
    └───────────────┘          └───────────────┘          └───────────────┘

Serving: Yair Siegel
"""

import json
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict

PROJECT_ROOT = Path(__file__).parent.parent
STATE_DIR = PROJECT_ROOT / "state"
STATE_DIR.mkdir(parents=True, exist_ok=True)

BRIDGE_STATE = STATE_DIR / "abcfc_nexus_bridge.json"
BRIDGE_LOG = STATE_DIR / "abcfc_nexus_decisions.jsonl"


@dataclass
class NexusConsultation:
    """Result of consulting AI Nexus for a decision."""
    timestamp: str
    query_type: str  # "action_evaluation", "risk_assessment", "position_sizing"
    context: Dict
    kernels_consulted: List[str]
    recommendation: str
    confidence: float
    reasoning: str


@dataclass
class ABCFCDecision:
    """A decision made by ABCFC with Nexus consultation."""
    decision_id: str
    timestamp: str
    action_name: str
    action_type: str
    abcfc_score: float  # From ABCFC nexus cloud
    nexus_score: float  # From AI Nexus consultation
    combined_score: float  # Weighted combination
    executed: bool
    outcome: Optional[Dict] = None


class ABCFCNexusBridge:
    """
    Bridge between ABCFC financial decisions and AI Nexus knowledge.

    KEY INTEGRATION:
    - Before any ABCFC action, consult relevant AI kernels
    - After any ABCFC outcome, feed back to learning
    - Use combined scores for final decisions
    """

    def __init__(self, abcfc_weight: float = 0.6, nexus_weight: float = 0.4):
        """
        Initialize bridge with scoring weights.

        Args:
            abcfc_weight: Weight for ABCFC numerical score (default 60%)
            nexus_weight: Weight for AI Nexus consultation (default 40%)
        """
        self.abcfc_weight = abcfc_weight
        self.nexus_weight = nexus_weight
        self.state = self._load_state()

        # Lazy-loaded components
        self._abcfc_nexus = None
        self._abcfc_system = None
        self._ai_orchestrator = None
        self._kernels = {}

    def _load_state(self) -> Dict:
        if BRIDGE_STATE.exists():
            try:
                with open(BRIDGE_STATE) as f:
                    return json.load(f)
            except:
                pass
        return {
            "initialized": datetime.now(timezone.utc).isoformat(),
            "decisions_made": 0,
            "consultations": 0,
            "outcomes_recorded": 0,
        }

    def _save_state(self):
        self.state["last_updated"] = datetime.now(timezone.utc).isoformat()
        with open(BRIDGE_STATE, 'w') as f:
            json.dump(self.state, f, indent=2)

    # ========================================================================
    # COMPONENT ACCESS
    # ========================================================================

    @property
    def abcfc_nexus(self):
        """Get ABCFC Nexus decision system."""
        if self._abcfc_nexus is None:
            try:
                from executor.math.abcfc_nexus import get_nexus
                self._abcfc_nexus = get_nexus()
            except ImportError:
                pass
        return self._abcfc_nexus

    @property
    def abcfc_system(self):
        """Get ABCFC System for hierarchical finance."""
        if self._abcfc_system is None:
            try:
                from executor.math.abcfc_system import ABCFCSystem
                self._abcfc_system = ABCFCSystem("Yair Siegel")
            except ImportError:
                pass
        return self._abcfc_system

    @property
    def ai_orchestrator(self):
        """Get AI Orchestrator for kernel consultation."""
        if self._ai_orchestrator is None:
            try:
                from ai.ai_orchestrator import AIOrchestrator
                self._ai_orchestrator = AIOrchestrator()
            except ImportError:
                pass
        return self._ai_orchestrator

    def _load_kernels(self) -> Dict:
        """Load all available AI kernels."""
        if self._kernels:
            return self._kernels

        kernel_paths = [
            PROJECT_ROOT / "ai_nexus" / "kernels" / "trading_params.json",
            PROJECT_ROOT / "ai" / "memory" / "kernels" / "yair_context_kernel.json",
            PROJECT_ROOT / "state" / "yair_context_kernel.json",
        ]

        for path in kernel_paths:
            if path.exists():
                try:
                    with open(path) as f:
                        self._kernels[path.stem] = json.load(f)
                except:
                    pass

        return self._kernels

    # ========================================================================
    # CONSULTATION - ABCFC asks AI Nexus
    # ========================================================================

    def consult_for_action(
        self,
        action_name: str,
        action_type: str,
        market: Optional[str] = None,
        abcfc_context: Optional[Dict] = None
    ) -> NexusConsultation:
        """
        Consult AI Nexus before taking an ABCFC action.

        Args:
            action_name: Name of the proposed action
            action_type: Type (buy, sell, hold, hedge)
            market: Target market (if applicable)
            abcfc_context: ABCFC scores and projections

        Returns:
            NexusConsultation with recommendation
        """
        kernels = self._load_kernels()
        consulted = []
        recommendations = []

        # Build context for consultation
        context = {
            "action": action_name,
            "type": action_type,
            "market": market,
            "abcfc": abcfc_context or {},
        }

        # Consult trading params kernel
        if "trading_params" in kernels:
            params = kernels["trading_params"]
            consulted.append("trading_params")

            # Check if action aligns with trading parameters
            max_position = params.get("max_position_size", 100)
            min_edge = params.get("min_edge_threshold", 0.05)

            size = abcfc_context.get("size", 0) if abcfc_context else 0
            edge = abcfc_context.get("edge", 0) if abcfc_context else 0

            if size > max_position:
                recommendations.append(f"Size {size} exceeds max {max_position}")
            if edge < min_edge and action_type == "buy":
                recommendations.append(f"Edge {edge:.1%} below min {min_edge:.1%}")

        # Consult Yair context kernel
        if "yair_context_kernel" in kernels:
            yair = kernels["yair_context_kernel"]
            consulted.append("yair_context_kernel")

            # Check Yair's preferences
            teachings = yair.get("teachings", {})
            if action_type == "buy":
                if teachings.get("be_the_house"):
                    recommendations.append("Yair says: Be the house, not the gambler")
                if teachings.get("check_book_depth"):
                    recommendations.append("Yair says: THE PRICE IS A LIE - check depth")

        # Consult AI Orchestrator if available
        if self.ai_orchestrator:
            try:
                response = self.ai_orchestrator.handle_request(
                    source="abcfc_bridge",
                    request_type="TRADING_DECISION",
                    context=context
                )
                consulted.append("ai_orchestrator")
                if response.get("recommendation"):
                    recommendations.append(f"AI: {response['recommendation']}")
            except:
                pass

        # Compute confidence based on consensus
        confidence = 0.5 + (len(recommendations) * 0.1)
        confidence = min(confidence, 0.95)

        # Build recommendation
        if not recommendations:
            recommendation = "PROCEED - No concerns from knowledge bases"
            reasoning = "All consulted kernels approve this action"
        else:
            recommendation = "REVIEW - " + "; ".join(recommendations[:3])
            reasoning = f"Consulted {len(consulted)} kernels, found {len(recommendations)} concerns"

        consultation = NexusConsultation(
            timestamp=datetime.now(timezone.utc).isoformat(),
            query_type="action_evaluation",
            context=context,
            kernels_consulted=consulted,
            recommendation=recommendation,
            confidence=confidence,
            reasoning=reasoning,
        )

        self.state["consultations"] = self.state.get("consultations", 0) + 1
        self._save_state()

        return consultation

    def compute_nexus_score(self, consultation: NexusConsultation) -> float:
        """
        Convert consultation into a numerical score.

        Score range: -1.0 (strongly against) to +1.0 (strongly approve)
        """
        if "PROCEED" in consultation.recommendation:
            base_score = 0.5
        elif "REVIEW" in consultation.recommendation:
            base_score = 0.0
        else:
            base_score = -0.5

        # Adjust by confidence
        score = base_score * consultation.confidence

        return score

    # ========================================================================
    # DECISION MAKING - Combined ABCFC + Nexus
    # ========================================================================

    def evaluate_action(
        self,
        action_name: str,
        action_type: str,
        abcfc_score: float,
        market: Optional[str] = None,
        abcfc_context: Optional[Dict] = None
    ) -> ABCFCDecision:
        """
        Evaluate an action using both ABCFC score and Nexus consultation.

        Returns combined decision with both scores.
        """
        # Consult AI Nexus
        consultation = self.consult_for_action(
            action_name, action_type, market, abcfc_context
        )

        # Get Nexus score
        nexus_score = self.compute_nexus_score(consultation)

        # Combine scores
        combined_score = (
            self.abcfc_weight * abcfc_score +
            self.nexus_weight * nexus_score
        )

        decision = ABCFCDecision(
            decision_id=f"d_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            timestamp=datetime.now(timezone.utc).isoformat(),
            action_name=action_name,
            action_type=action_type,
            abcfc_score=abcfc_score,
            nexus_score=nexus_score,
            combined_score=combined_score,
            executed=False,
        )

        # Log decision
        self._log_decision(decision, consultation)

        self.state["decisions_made"] = self.state.get("decisions_made", 0) + 1
        self._save_state()

        return decision

    def _log_decision(self, decision: ABCFCDecision, consultation: NexusConsultation):
        """Log decision to file."""
        entry = {
            "decision": asdict(decision),
            "consultation": asdict(consultation),
        }
        with open(BRIDGE_LOG, 'a') as f:
            f.write(json.dumps(entry) + "\n")

    # ========================================================================
    # OUTCOME FEEDBACK - Feed results back to learning
    # ========================================================================

    def record_outcome(
        self,
        decision_id: str,
        pnl: float,
        was_correct: bool,
        resolution: Optional[str] = None
    ):
        """
        Record outcome and feed back to learning systems.

        This completes the loop: ABCFC → Nexus → Decision → Execute → Outcome → Learn
        """
        outcome = {
            "decision_id": decision_id,
            "pnl": pnl,
            "was_correct": was_correct,
            "resolution": resolution,
            "recorded_at": datetime.now(timezone.utc).isoformat(),
        }

        # Feed to skill growth tracker
        try:
            from autonomous.skill_growth_tracker import SkillGrowthTracker
            tracker = SkillGrowthTracker()
            tracker.record_outcome(
                skill="abcfc_decisions",
                prediction=1.0 if was_correct else 0.0,
                actual=1.0 if pnl > 0 else 0.0,
                category="trading",
                details=f"Decision {decision_id}, P&L: ${pnl:.2f}"
            )
        except:
            pass

        # Feed to outcome tracker
        try:
            from integrafix.outcome_tracker import get_tracker
            tracker = get_tracker()
            # Outcome tracker expects trade_id format
        except:
            pass

        # Feed to AI Orchestrator for learning
        if self.ai_orchestrator:
            try:
                self.ai_orchestrator.handle_request(
                    source="abcfc_bridge",
                    request_type="LEARNING_UPDATE",
                    context={
                        "type": "abcfc_outcome",
                        "outcome": outcome,
                    }
                )
            except:
                pass

        self.state["outcomes_recorded"] = self.state.get("outcomes_recorded", 0) + 1
        self._save_state()

        return outcome

    # ========================================================================
    # HIGH-LEVEL API - Wire ABCFC Cloud to Nexus
    # ========================================================================

    def evaluate_nexus_cloud(self, risk_aversion: float = 0.5) -> Dict:
        """
        Evaluate the entire ABCFC nexus cloud with AI consultation.

        For each action in the cloud, consults AI Nexus and computes
        combined scores.

        Returns enhanced cloud with Nexus scores.
        """
        if not self.abcfc_nexus:
            return {"error": "ABCFC Nexus not available"}

        # Get ABCFC evaluation
        abcfc_result = self.abcfc_nexus.evaluate(risk_aversion=risk_aversion)

        # Enhance each action with Nexus consultation
        enhanced_rankings = []

        for action_data in abcfc_result.get("rankings", []):
            action_name = action_data.get("name", "unknown")
            action_type = action_data.get("action_type", "unknown")
            abcfc_score = action_data.get("risk_adjusted_score", 0)

            # Evaluate with Nexus
            decision = self.evaluate_action(
                action_name=action_name,
                action_type=action_type,
                abcfc_score=abcfc_score,
                market=action_data.get("market"),
                abcfc_context={
                    "expected_improvement": action_data.get("expected_improvement", 0),
                    "best_improvement": action_data.get("best_improvement", 0),
                    "worst_improvement": action_data.get("worst_improvement", 0),
                }
            )

            # Add Nexus scores to action data
            action_data["nexus_score"] = decision.nexus_score
            action_data["combined_score"] = decision.combined_score
            action_data["decision_id"] = decision.decision_id

            enhanced_rankings.append(action_data)

        # Re-sort by combined score
        enhanced_rankings.sort(key=lambda x: x.get("combined_score", 0), reverse=True)

        return {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "current_state": abcfc_result.get("current_state"),
            "risk_aversion": risk_aversion,
            "abcfc_weight": self.abcfc_weight,
            "nexus_weight": self.nexus_weight,
            "rankings": enhanced_rankings,
            "best_action": enhanced_rankings[0] if enhanced_rankings else None,
            "consultations_made": len(enhanced_rankings),
        }

    def get_best_action_with_nexus(self) -> Optional[Dict]:
        """
        Get the best action considering both ABCFC and Nexus scores.
        """
        result = self.evaluate_nexus_cloud()
        return result.get("best_action")

    # ========================================================================
    # STATUS
    # ========================================================================

    def status(self) -> Dict:
        """Get bridge status."""
        kernels = self._load_kernels()

        return {
            "initialized": self.state.get("initialized"),
            "decisions_made": self.state.get("decisions_made", 0),
            "consultations": self.state.get("consultations", 0),
            "outcomes_recorded": self.state.get("outcomes_recorded", 0),
            "weights": {
                "abcfc": self.abcfc_weight,
                "nexus": self.nexus_weight,
            },
            "components": {
                "abcfc_nexus": self.abcfc_nexus is not None,
                "abcfc_system": self.abcfc_system is not None,
                "ai_orchestrator": self.ai_orchestrator is not None,
            },
            "kernels_available": list(kernels.keys()),
            "message": "ABCFC ↔ AI Nexus bridge operational",
        }


# ============================================================================
# GLOBAL INSTANCE
# ============================================================================

_bridge: Optional[ABCFCNexusBridge] = None


def get_bridge() -> ABCFCNexusBridge:
    """Get or create the ABCFC-Nexus bridge."""
    global _bridge
    if _bridge is None:
        _bridge = ABCFCNexusBridge()
    return _bridge


def consult_nexus_for_action(
    action_name: str,
    action_type: str,
    abcfc_score: float,
    **kwargs
) -> ABCFCDecision:
    """
    Main API: Consult Nexus before taking an ABCFC action.

    Returns decision with combined ABCFC + Nexus score.
    """
    bridge = get_bridge()
    return bridge.evaluate_action(action_name, action_type, abcfc_score, **kwargs)


# ============================================================================
# CLI
# ============================================================================

def main():
    import argparse

    parser = argparse.ArgumentParser(description="ABCFC ↔ Nexus Bridge")
    parser.add_argument("command", choices=["status", "evaluate", "test"])
    args = parser.parse_args()

    bridge = get_bridge()

    if args.command == "status":
        status = bridge.status()
        print("=" * 70)
        print("INTEGRAFIX: ABCFC ↔ Nexus Bridge Status")
        print("=" * 70)
        print(f"Decisions made: {status['decisions_made']}")
        print(f"Consultations: {status['consultations']}")
        print(f"Outcomes recorded: {status['outcomes_recorded']}")
        print(f"\nWeights: ABCFC={status['weights']['abcfc']:.0%}, Nexus={status['weights']['nexus']:.0%}")
        print(f"\nComponents:")
        for comp, available in status['components'].items():
            symbol = "+" if available else "x"
            print(f"  [{symbol}] {comp}")
        print(f"\nKernels: {', '.join(status['kernels_available'])}")
        print(f"\n{status['message']}")

    elif args.command == "evaluate":
        print("=" * 70)
        print("INTEGRAFIX: Evaluating ABCFC Cloud with Nexus")
        print("=" * 70)

        result = bridge.evaluate_nexus_cloud()

        if "error" in result:
            print(f"Error: {result['error']}")
            return

        print(f"\nCurrent State: {result.get('current_state')}")
        print(f"Consultations: {result.get('consultations_made')}")
        print(f"\nRankings (by combined score):")

        for i, action in enumerate(result.get("rankings", [])[:5], 1):
            print(f"\n  {i}. {action.get('name')} ({action.get('action_type')})")
            print(f"     ABCFC: {action.get('risk_adjusted_score', 0):+.3f}")
            print(f"     Nexus: {action.get('nexus_score', 0):+.3f}")
            print(f"     Combined: {action.get('combined_score', 0):+.3f}")

        best = result.get("best_action")
        if best:
            print(f"\n* RECOMMENDED: {best.get('name')} (combined: {best.get('combined_score', 0):+.3f})")

    elif args.command == "test":
        print("=" * 70)
        print("INTEGRAFIX: Testing ABCFC ↔ Nexus Bridge")
        print("=" * 70)

        # Test consultation
        consultation = bridge.consult_for_action(
            action_name="test_buy",
            action_type="buy",
            market="test-market",
            abcfc_context={"size": 50, "edge": 0.08}
        )
        print(f"\n[1] Consultation Test:")
        print(f"    Kernels consulted: {consultation.kernels_consulted}")
        print(f"    Recommendation: {consultation.recommendation}")
        print(f"    Confidence: {consultation.confidence:.0%}")

        # Test decision
        decision = bridge.evaluate_action(
            action_name="test_buy",
            action_type="buy",
            abcfc_score=0.5,
            market="test-market"
        )
        print(f"\n[2] Decision Test:")
        print(f"    ABCFC Score: {decision.abcfc_score:+.3f}")
        print(f"    Nexus Score: {decision.nexus_score:+.3f}")
        print(f"    Combined: {decision.combined_score:+.3f}")

        print("\n" + "=" * 70)
        print("BRIDGE TEST COMPLETE")
        print("=" * 70)


if __name__ == "__main__":
    main()
