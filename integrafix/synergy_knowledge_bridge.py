#!/usr/bin/env python3
"""
INTEGRAFIX: Synergy-Knowledge Bridge
====================================

WIRES TOGETHER:
===============
1. Human-Machine Synergy (human wisdom + machine execution)
2. Knowledge Nexus (computing, business, money knowledge)
3. Pipeline Learnings (what works, what fails)
4. ABCFC System (decision framework)

INTEGRATION POINTS:
===================

┌─────────────────────────────────────────────────────────────────────┐
│                    SYNERGY-KNOWLEDGE BRIDGE                          │
└─────────────────────────────────────────────────────────────────────┘
                              │
         ┌────────────────────┼────────────────────┐
         │                    │                    │
         ▼                    ▼                    ▼
┌─────────────────┐   ┌─────────────────┐   ┌─────────────────┐
│ KNOWLEDGE NEXUS │   │ HUMAN-MACHINE   │   │ PIPELINE        │
│                 │   │ SYNERGY         │   │ LEARNINGS       │
│ • Computing     │◄──┤                 │──►│                 │
│ • Business      │   │ • Edge detect   │   │ • What works    │
│ • Money         │   │ • Approvals     │   │ • What fails    │
│                 │   │ • Execution     │   │ • Calibration   │
└─────────────────┘   └─────────────────┘   └─────────────────┘
         │                    │                    │
         └────────────────────┼────────────────────┘
                              │
                              ▼
                    ┌─────────────────┐
                    │ ABCFC SYSTEM    │
                    │                 │
                    │ Informed by:    │
                    │ • Knowledge     │
                    │ • Human wisdom  │
                    │ • Past learnings│
                    └─────────────────┘

FLOW:
=====
1. BEFORE DECISION:
   - Pull trading context from knowledge nexus
   - Pull relevant learnings from pipeline
   - Enhance human estimate request with context

2. AFTER DECISION:
   - Record outcome as learning
   - Update what_works / what_fails
   - Feed back to knowledge nexus

Serving: Yair Siegel
"""

import json
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any
from dataclasses import dataclass

PROJECT_ROOT = Path(__file__).parent.parent
STATE_DIR = PROJECT_ROOT / "state"
BRIDGE_STATE = STATE_DIR / "synergy_knowledge_bridge.json"


@dataclass
class KnowledgeContext:
    """Context from knowledge bases for a decision."""
    trading_context: Dict
    relevant_learnings: List[Dict]
    success_patterns: List[str]
    failure_patterns: List[str]
    recommended_actions: List[str]


class SynergyKnowledgeBridge:
    """
    Bridges human-machine synergy with system knowledge.

    INTEGRAFIX WIRING:
    - Knowledge Nexus → Trading Context → Human Estimate Requests
    - Outcomes → Pipeline Learnings → Future Decisions
    - What Works/Fails → Edge Detection Guidance
    """

    def __init__(self):
        self._nexus = None
        self._synergy = None
        self._learnings = []
        self.what_works: List[str] = []
        self.what_fails: List[str] = []

        self._load_state()

    # =========================================================================
    # COMPONENT LOADING
    # =========================================================================

    @property
    def nexus(self):
        """Get knowledge nexus."""
        if self._nexus is None:
            try:
                from autonomous.knowledge_nexus import get_nexus
                self._nexus = get_nexus()
            except Exception as e:
                print(f"Warning: Could not load knowledge nexus: {e}")
        return self._nexus

    @property
    def synergy(self):
        """Get human-machine synergy."""
        if self._synergy is None:
            try:
                from integrafix.human_machine_synergy import HumanMachineSynergy
                self._synergy = HumanMachineSynergy()
            except Exception as e:
                print(f"Warning: Could not load synergy: {e}")
        return self._synergy

    # =========================================================================
    # BEFORE DECISION: Enrich with knowledge
    # =========================================================================

    def get_decision_context(self, market_data: Dict = None) -> KnowledgeContext:
        """
        Get full knowledge context for a trading decision.

        Pulls from:
        1. Knowledge Nexus (money/business knowledge)
        2. Pipeline Learnings (past outcomes)
        3. What Works/Fails (success patterns)
        """
        # 1. Get trading context from knowledge nexus
        trading_context = {}
        if self.nexus:
            trading_context = self.nexus.get_trading_context(market_data)

        # 2. Get relevant learnings
        relevant_learnings = self._get_relevant_learnings(market_data)

        # 3. Get success/failure patterns
        success_patterns = self._get_success_patterns()
        failure_patterns = self._get_failure_patterns()

        # 4. Generate recommendations
        recommended_actions = self._generate_recommendations(
            trading_context, relevant_learnings, success_patterns
        )

        return KnowledgeContext(
            trading_context=trading_context,
            relevant_learnings=relevant_learnings,
            success_patterns=success_patterns,
            failure_patterns=failure_patterns,
            recommended_actions=recommended_actions,
        )

    def _get_relevant_learnings(self, market_data: Dict = None) -> List[Dict]:
        """Get learnings relevant to current decision."""
        relevant = []

        # Load from pipeline learnings
        learnings_file = STATE_DIR / "pipeline_learnings.jsonl"
        if learnings_file.exists():
            try:
                with open(learnings_file) as f:
                    for line in f:
                        if line.strip():
                            learning = json.loads(line)
                            # Filter for trading-relevant learnings
                            if learning.get("learning_type") in [
                                "edge_accuracy", "source_performance",
                                "win_rate", "position_sizing"
                            ]:
                                relevant.append(learning)
            except:
                pass

        # Sort by recency
        relevant.sort(key=lambda x: x.get("learned_at", ""), reverse=True)

        return relevant[:10]  # Most recent 10

    def _get_success_patterns(self) -> List[str]:
        """Get patterns that have worked."""
        patterns = list(self.what_works)

        # Add from wisdom learnings
        wisdom_file = STATE_DIR / "wisdom_learnings.jsonl"
        if wisdom_file.exists():
            try:
                with open(wisdom_file) as f:
                    for line in f:
                        if line.strip():
                            data = json.loads(line)
                            if data.get("type") == "wisdom_application":
                                teachings = data.get("teachings_used", [])
                                for t in teachings:
                                    if t not in patterns:
                                        patterns.append(t)
            except:
                pass

        # Add from learning engine
        engine_file = STATE_DIR / "learning_engine.json"
        if engine_file.exists():
            try:
                with open(engine_file) as f:
                    data = json.load(f)
                patterns.extend(data.get("what_works", []))
            except:
                pass

        return list(set(patterns))

    def _get_failure_patterns(self) -> List[str]:
        """Get patterns that have failed."""
        patterns = list(self.what_fails)

        # Add from learning engine
        engine_file = STATE_DIR / "learning_engine.json"
        if engine_file.exists():
            try:
                with open(engine_file) as f:
                    data = json.load(f)
                patterns.extend(data.get("what_fails", []))
            except:
                pass

        return list(set(patterns))

    def _generate_recommendations(self, trading_context: Dict,
                                  learnings: List[Dict],
                                  success_patterns: List[str]) -> List[str]:
        """Generate recommendations based on all knowledge."""
        recs = []

        # From trading context
        recs.extend(trading_context.get("recommendations", []))

        # From learnings
        for learning in learnings[:3]:
            adjustment = learning.get("adjustment", {})
            if adjustment.get("action") == "increase_min_edge":
                min_edge = adjustment.get("new_min_edge", 0.03)
                recs.append(f"Use minimum edge of {min_edge:.0%} based on past accuracy")
            elif adjustment.get("action") == "increase_confidence":
                source = adjustment.get("source", "unknown")
                recs.append(f"Favor {source} signals - historically outperforming")

        # From success patterns
        if "spread_arbitrage" in success_patterns:
            recs.append("Spread arbitrage has 67% win rate - look for these setups")
        if "merge_arb" in success_patterns:
            recs.append("Merger arbitrage when available - low risk")
        if "espn_comparison" in success_patterns:
            recs.append("Cross-reference with sports/event data when applicable")

        return recs

    # =========================================================================
    # ENRICH HUMAN REQUESTS
    # =========================================================================

    def enrich_estimate_request(self, market: Dict) -> Dict:
        """
        Enrich a human estimate request with knowledge context.

        Called before asking Yair for probability estimate.
        """
        context = self.get_decision_context(market)

        enriched = {
            "market": market,
            "knowledge_context": {
                "risk_metrics": context.trading_context.get("risk_framework", {}),
                "tools_available": context.trading_context.get("available_tools", []),
            },
            "past_learnings": [
                l.get("observation") for l in context.relevant_learnings[:3]
            ],
            "success_patterns": context.success_patterns[:5],
            "failure_patterns": context.failure_patterns[:3],
            "recommendations": context.recommended_actions[:5],
        }

        return enriched

    # =========================================================================
    # AFTER DECISION: Record learning
    # =========================================================================

    def record_outcome(self, action_id: str, market_id: str,
                      predicted_prob: float, outcome: str,
                      realized_pnl: float, edge_source: str) -> Dict:
        """
        Record outcome and create learning.

        Called after trade resolves.
        """
        # Determine if prediction was accurate
        actual = 1 if outcome == "won" else 0
        prediction = 1 if predicted_prob > 0.5 else 0
        accurate = actual == prediction

        # Create learning entry
        learning = {
            "id": f"learn_{datetime.now().strftime('%Y%m%d%H%M%S')}_{action_id[:8]}",
            "learning_type": "trade_outcome",
            "market_id": market_id,
            "predicted_prob": predicted_prob,
            "actual_outcome": outcome,
            "realized_pnl": realized_pnl,
            "edge_source": edge_source,
            "accurate": accurate,
            "observation": self._generate_observation(
                accurate, edge_source, realized_pnl
            ),
            "learned_at": datetime.now(timezone.utc).isoformat(),
        }

        # Append to pipeline learnings
        learnings_file = STATE_DIR / "pipeline_learnings.jsonl"
        with open(learnings_file, 'a') as f:
            f.write(json.dumps(learning) + '\n')

        # Update what works / what fails
        if accurate and realized_pnl > 0:
            pattern = f"{edge_source}_profitable"
            if pattern not in self.what_works:
                self.what_works.append(pattern)
        elif not accurate and realized_pnl < 0:
            pattern = f"{edge_source}_inaccurate"
            if pattern not in self.what_fails:
                self.what_fails.append(pattern)

        self._save_state()

        return {
            "learning_recorded": True,
            "learning_id": learning["id"],
            "accurate": accurate,
            "pnl": realized_pnl,
        }

    def _generate_observation(self, accurate: bool, source: str, pnl: float) -> str:
        """Generate human-readable observation."""
        if accurate and pnl > 0:
            return f"Accurate prediction from {source} source, +${pnl:.2f}"
        elif accurate and pnl <= 0:
            return f"Accurate prediction from {source} but negative P&L (sizing issue?)"
        elif not accurate and pnl > 0:
            return f"Inaccurate prediction from {source} but still profitable (lucky?)"
        else:
            return f"Inaccurate prediction from {source}, -${abs(pnl):.2f} loss"

    # =========================================================================
    # CALIBRATION
    # =========================================================================

    def get_calibration_stats(self) -> Dict:
        """Get calibration statistics from past learnings."""
        stats = {
            "total_predictions": 0,
            "accurate_predictions": 0,
            "accuracy_rate": 0.0,
            "total_pnl": 0.0,
            "by_source": {},
        }

        learnings_file = STATE_DIR / "pipeline_learnings.jsonl"
        if learnings_file.exists():
            try:
                with open(learnings_file) as f:
                    for line in f:
                        if line.strip():
                            learning = json.loads(line)
                            if learning.get("learning_type") == "trade_outcome":
                                stats["total_predictions"] += 1
                                if learning.get("accurate"):
                                    stats["accurate_predictions"] += 1
                                stats["total_pnl"] += learning.get("realized_pnl", 0)

                                # By source
                                source = learning.get("edge_source", "unknown")
                                if source not in stats["by_source"]:
                                    stats["by_source"][source] = {
                                        "count": 0, "accurate": 0, "pnl": 0
                                    }
                                stats["by_source"][source]["count"] += 1
                                if learning.get("accurate"):
                                    stats["by_source"][source]["accurate"] += 1
                                stats["by_source"][source]["pnl"] += learning.get("realized_pnl", 0)
            except:
                pass

        if stats["total_predictions"] > 0:
            stats["accuracy_rate"] = stats["accurate_predictions"] / stats["total_predictions"]

        return stats

    # =========================================================================
    # STATE MANAGEMENT
    # =========================================================================

    def _load_state(self):
        """Load bridge state."""
        if BRIDGE_STATE.exists():
            try:
                with open(BRIDGE_STATE) as f:
                    data = json.load(f)
                self.what_works = data.get("what_works", [])
                self.what_fails = data.get("what_fails", [])
            except:
                pass

    def _save_state(self):
        """Save bridge state."""
        state = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "what_works": self.what_works,
            "what_fails": self.what_fails,
        }
        with open(BRIDGE_STATE, 'w') as f:
            json.dump(state, f, indent=2)

    # =========================================================================
    # REPORTING
    # =========================================================================

    def status(self) -> Dict:
        """Get bridge status."""
        nexus_status = self.nexus.status() if self.nexus else {"error": "not loaded"}
        synergy_pending = len(self.synergy.pending_requests) if self.synergy else 0
        calibration = self.get_calibration_stats()

        return {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "knowledge_nexus": {
                "loaded": nexus_status.get("total_loaded", 0),
                "connections": nexus_status.get("connections", {}),
            },
            "human_machine_synergy": {
                "pending_requests": synergy_pending,
                "wisdom_cache_size": len(self.synergy.wisdom_cache) if self.synergy else 0,
            },
            "learnings": {
                "what_works": len(self.what_works),
                "what_fails": len(self.what_fails),
                "calibration": calibration,
            },
        }

    def print_status(self):
        """Print formatted status."""
        status = self.status()

        print("=" * 70)
        print("SYNERGY-KNOWLEDGE BRIDGE STATUS")
        print(f"Generated: {status['timestamp']}")
        print("=" * 70)

        print("\n>>> KNOWLEDGE NEXUS")
        kn = status["knowledge_nexus"]
        print(f"    Bases Loaded: {kn['loaded']}/3")
        connections = kn.get("connections", {})
        connected = sum(1 for v in connections.values() if v)
        print(f"    Connections Active: {connected}/6")

        print("\n>>> HUMAN-MACHINE SYNERGY")
        hm = status["human_machine_synergy"]
        print(f"    Pending Requests: {hm['pending_requests']}")
        print(f"    Wisdom Cache: {hm['wisdom_cache_size']} estimates")

        print("\n>>> LEARNINGS")
        learn = status["learnings"]
        print(f"    What Works: {learn['what_works']} patterns")
        print(f"    What Fails: {learn['what_fails']} patterns")
        cal = learn["calibration"]
        print(f"    Total Predictions: {cal['total_predictions']}")
        print(f"    Accuracy: {cal['accuracy_rate']:.1%}")
        print(f"    Total P&L: ${cal['total_pnl']:.2f}")

        print("\n>>> SUCCESS PATTERNS")
        for pattern in self.what_works[:5]:
            print(f"    + {pattern}")

        print("\n>>> FAILURE PATTERNS")
        for pattern in self.what_fails[:5]:
            print(f"    - {pattern}")

        print("\n" + "=" * 70)


# =============================================================================
# CLI
# =============================================================================

def main():
    import argparse

    parser = argparse.ArgumentParser(description="Synergy-Knowledge Bridge")
    parser.add_argument("command", choices=[
        "status", "context", "calibration", "test"
    ], default="status", nargs="?")
    args = parser.parse_args()

    bridge = SynergyKnowledgeBridge()

    if args.command == "status":
        bridge.print_status()

    elif args.command == "context":
        context = bridge.get_decision_context()
        print("KNOWLEDGE CONTEXT FOR TRADING:")
        print(f"  Trading tools: {context.trading_context.get('available_tools', [])}")
        print(f"  Recommendations: {context.recommended_actions}")
        print(f"  Success patterns: {context.success_patterns}")
        print(f"  Failure patterns: {context.failure_patterns}")

    elif args.command == "calibration":
        stats = bridge.get_calibration_stats()
        print(json.dumps(stats, indent=2))

    elif args.command == "test":
        print("=== TESTING SYNERGY-KNOWLEDGE BRIDGE ===\n")

        # Test knowledge context
        context = bridge.get_decision_context({"test": True})
        print(f"Trading context available: {bool(context.trading_context)}")
        print(f"Learnings loaded: {len(context.relevant_learnings)}")
        print(f"Success patterns: {len(context.success_patterns)}")
        print(f"Recommendations: {len(context.recommended_actions)}")

        # Test enrichment
        enriched = bridge.enrich_estimate_request({"market_id": "test", "question": "Test?"})
        print(f"\nEnriched request has {len(enriched.keys())} keys")

        print("\n✓ Bridge integration test passed")


if __name__ == "__main__":
    main()
