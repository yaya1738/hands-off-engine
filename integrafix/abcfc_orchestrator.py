#!/usr/bin/env python3
"""
INTEGRAFIX: ABCFC Orchestrator
==============================

Unified orchestrator for all ABCFC components and integrafix bridges.

WIRES TOGETHER:
===============
1. YairMasterABCFC - Master hierarchy with risk modifiers
2. ABCFCSystem - Core hierarchy math
3. ABCFCNexus/Cloud - Decision space exploration (theoretical)
4. ABCFCLiveNexus - Live market data + executable actions (practical)
5. RealityBridge - Current financial state
6. RiskManagementBridge - Risk factor analysis
7. GoalsEffectsBridge - Goal tracking and causality
8. PaymentsBridge - Subscription ROI
9. CloudFlyer - Autonomous decision execution

ABCFC FLOW:
===========
1. OBSERVE: Load all bridge data → Build ABCFC hierarchy
2. EVALUATE: Generate nexus cloud → Score all futures
3. DECIDE: Select optimal action based on risk aversion
4. EXECUTE: Take action (or recommend in dry run)
5. TRACK: Record outcome → Update reality → Loop

Serving: Yair Siegel
"""

import json
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field

PROJECT_ROOT = Path(__file__).parent.parent
STATE_DIR = PROJECT_ROOT / "state"
STATE_DIR.mkdir(parents=True, exist_ok=True)

ORCHESTRATOR_STATE = STATE_DIR / "abcfc_orchestrator.json"
ORCHESTRATOR_LOG = STATE_DIR / "abcfc_orchestrator.jsonl"


@dataclass
class ABCFCState:
    """Complete ABCFC system state."""
    timestamp: str

    # Hierarchy
    hierarchy_nodes: int
    total_bounds: tuple
    total_expected: float

    # Risk
    risk_modifiers: List[str]
    risk_adjusted_worst: float
    risk_adjusted_expected: float

    # Nexus Cloud (Theoretical)
    cloud_size: int
    cloud_bounds: Dict

    # Recommendation
    recommended_action: str
    recommended_node: str
    recommended_score: float

    # Sources
    sources_loaded: List[str]

    # Live Nexus (Practical) - defaults at end
    live_nexus_markets: int = 0
    live_nexus_actions: int = 0
    live_nexus_approved: int = 0


class ABCFCOrchestrator:
    """
    Unified orchestrator for ABCFC system.

    Coordinates all integrafix bridges into coherent ABCFC hierarchy
    and nexus cloud for decision making.
    """

    def __init__(self, risk_aversion: float = 0.6, dry_run: bool = True):
        self.risk_aversion = risk_aversion
        self.dry_run = dry_run

        # Component state
        self._master = None
        self._reality = None
        self._risk = None
        self._goals = None
        self._payments = None
        self._live_nexus = None

        # Orchestrator state
        self.state: Optional[ABCFCState] = None
        self.history: List[Dict] = []

    # =========================================================================
    # COMPONENT LOADING
    # =========================================================================

    def _load_master(self):
        """Load YairMasterABCFC."""
        if self._master is None:
            try:
                from integrafix.yair_master_abcfc import YairMasterABCFC
                self._master = YairMasterABCFC(risk_aversion=self.risk_aversion)
                self._master.build()
            except Exception as e:
                print(f"Warning: Could not load master ABCFC: {e}")
                self._master = None
        return self._master

    def _load_reality(self) -> Dict:
        """Load current reality from RealityBridge."""
        if self._reality is None:
            try:
                from integrafix.reality_bridge import RealityBridge
                bridge = RealityBridge()
                snapshot = bridge.snapshot_reality()
                self._reality = {
                    "liquid_usd": snapshot.liquid_usd,
                    "deployable": snapshot.deployable,
                    "runway_months": snapshot.runway_months,
                    "monthly_burn": snapshot.monthly_burn,
                    "win_rate": snapshot.win_rate,
                    "total_pnl": snapshot.total_pnl,
                    "reality_score": snapshot.reality_score(),
                    "health_score": snapshot.health_score,
                }
            except Exception as e:
                self._reality = {"error": str(e)}
        return self._reality

    def _load_risk(self) -> Dict:
        """Load risk analysis from RiskManagementBridge."""
        if self._risk is None:
            try:
                from integrafix.risk_management_bridge import RiskManagementBridge
                bridge = RiskManagementBridge()
                self._risk = {
                    "accounts": bridge.get_account_summary(),
                    "incorporation": bridge.get_incorporation_analysis(),
                    "centralization": bridge.get_centralization_analysis(),
                    "risk_summary": bridge.get_risk_summary(),
                }
            except Exception as e:
                self._risk = {"error": str(e)}
        return self._risk

    def _load_goals(self) -> Dict:
        """Load goals from GoalsEffectsBridge."""
        if self._goals is None:
            try:
                from integrafix.goals_effects_bridge import GoalsEffectsBridge
                bridge = GoalsEffectsBridge()
                bridge.import_system_goals()
                bridge.import_system_effects()
                self._goals = {
                    "goals": len(bridge.goals),
                    "effects": len(bridge.effects),
                    "calibration": bridge.calculate_calibration(),
                }
            except Exception as e:
                self._goals = {"error": str(e)}
        return self._goals

    def _load_payments(self) -> Dict:
        """Load payments analysis from PaymentsBridge."""
        if self._payments is None:
            try:
                from integrafix.payments_bridge import PaymentsBridge
                bridge = PaymentsBridge()
                self._payments = {
                    "subscriptions": bridge.get_subscription_summary(),
                    "optimization": bridge.get_optimization_report(),
                }
            except Exception as e:
                self._payments = {"error": str(e)}
        return self._payments

    def _load_live_nexus(self) -> Dict:
        """Load live nexus for real market actions."""
        if self._live_nexus is None:
            try:
                from integrafix.abcfc_live_nexus import ABCFCLiveNexus
                self._live_nexus = ABCFCLiveNexus(
                    risk_aversion=self.risk_aversion,
                    dry_run=self.dry_run
                )
                self._live_nexus.observe()
                self._live_nexus.generate_actions()
            except Exception as e:
                self._live_nexus = None
                return {"error": str(e)}

        return {
            "markets_scanned": len(self._live_nexus.market_data),
            "actions_proposed": len(self._live_nexus.proposed_actions),
            "positions": len(self._live_nexus.current_positions),
        }

    # =========================================================================
    # OBSERVE - Build State
    # =========================================================================

    def observe(self) -> ABCFCState:
        """
        Observe current state by loading all bridge data.

        This is step 1 of the ABCFC flow:
        Load all integrafix bridges → Build unified ABCFC state
        """
        sources = []

        # Load master ABCFC
        master = self._load_master()
        if master and master.built:
            sources.append("YairMasterABCFC")

        # Load supporting data
        reality = self._load_reality()
        if "error" not in reality:
            sources.append("RealityBridge")

        risk = self._load_risk()
        if "error" not in risk:
            sources.append("RiskManagementBridge")

        goals = self._load_goals()
        if "error" not in goals:
            sources.append("GoalsEffectsBridge")

        payments = self._load_payments()
        if "error" not in payments:
            sources.append("PaymentsBridge")

        # Load live nexus (practical market data)
        live_nexus = self._load_live_nexus()
        if "error" not in live_nexus:
            sources.append("ABCFCLiveNexus")

        # Build state
        if master and master.built:
            summary = master.get_summary()
            cloud = master.get_nexus_cloud()
            best = master.get_best_action()

            self.state = ABCFCState(
                timestamp=datetime.now(timezone.utc).isoformat(),
                hierarchy_nodes=summary.get("hierarchy_nodes", 0),
                total_bounds=(summary["bounds"]["worst"], summary["bounds"]["best"]),
                total_expected=summary["bounds"]["expected"],
                risk_modifiers=summary.get("risk_modifiers", []),
                risk_adjusted_worst=summary["risk_adjusted"]["worst"],
                risk_adjusted_expected=summary["risk_adjusted"]["expected"],
                cloud_size=len(cloud.get("futures", [])),
                cloud_bounds=cloud.get("cloud_bounds", {}),
                recommended_action=best.get("action", "hold"),
                recommended_node=best.get("target_node", "root"),
                recommended_score=best.get("score", 0),
                sources_loaded=sources,
                # Live nexus fields (optional)
                live_nexus_markets=live_nexus.get("markets_scanned", 0),
                live_nexus_actions=live_nexus.get("actions_proposed", 0),
                live_nexus_approved=len([a for a in (self._live_nexus.proposed_actions if self._live_nexus else [])
                                         if hasattr(a, 'status') and a.status.value == "approved"]),
            )
        else:
            # Fallback minimal state
            self.state = ABCFCState(
                timestamp=datetime.now(timezone.utc).isoformat(),
                hierarchy_nodes=0,
                total_bounds=(0, 0),
                total_expected=0,
                risk_modifiers=[],
                risk_adjusted_worst=0,
                risk_adjusted_expected=0,
                cloud_size=0,
                cloud_bounds={},
                recommended_action="hold",
                recommended_node="none",
                recommended_score=0,
                sources_loaded=sources,
                # Live nexus fields (optional)
                live_nexus_markets=live_nexus.get("markets_scanned", 0),
                live_nexus_actions=live_nexus.get("actions_proposed", 0),
                live_nexus_approved=0,
            )

        return self.state

    # =========================================================================
    # EVALUATE - Nexus Cloud
    # =========================================================================

    def evaluate(self, custom_actions: List = None) -> Dict:
        """
        Evaluate all possible futures via nexus cloud.

        This is step 2 of the ABCFC flow:
        Generate nexus cloud → Score all futures
        """
        if self.state is None:
            self.observe()

        master = self._load_master()
        if not master or not master.built:
            return {"error": "Master ABCFC not available"}

        # Get nexus cloud
        if custom_actions:
            cloud = master.get_nexus_cloud(custom_actions)
        else:
            cloud = master.get_nexus_cloud()

        # Enhance with risk data
        risk = self._load_risk()

        # Get live nexus cloud (practical trading actions)
        live_nexus_cloud = {}
        if self._live_nexus:
            live_nexus_cloud = self._live_nexus.get_nexus_cloud_data()

        return {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "current": cloud.get("current", {}),
            "cloud_bounds": cloud.get("cloud_bounds", {}),
            "futures_evaluated": len(cloud.get("futures", [])),
            "top_futures": cloud.get("futures", [])[:5],
            "risk_context": {
                "incorporation": risk.get("incorporation", {}).get("current_status", "Unknown"),
                "centralization_score": risk.get("centralization", {}).get("score", 0),
            },
            # Live nexus (practical trading)
            "live_nexus": {
                "markets_scanned": live_nexus_cloud.get("markets", 0),
                "actions_proposed": len(live_nexus_cloud.get("actions", [])),
                "actions_approved": len(live_nexus_cloud.get("approved", [])),
                "live_cloud_bounds": live_nexus_cloud.get("cloud_bounds", {}),
                "top_live_actions": live_nexus_cloud.get("approved", [])[:3],
            }
        }

    # =========================================================================
    # DECIDE - Select Action
    # =========================================================================

    def decide(self, risk_aversion: float = None) -> Dict:
        """
        Select optimal action from nexus cloud.

        This is step 3 of the ABCFC flow:
        Score futures → Select best action
        """
        if risk_aversion is not None:
            self.risk_aversion = risk_aversion

        master = self._load_master()
        if not master or not master.built:
            return {"action": "hold", "reason": "Master ABCFC not available"}

        master.system.risk_aversion = self.risk_aversion
        best = master.get_best_action(self.risk_aversion)

        # Get path alternatives
        path = master.get_optimal_path()

        # Get live nexus decision (practical trading)
        live_decisions = []
        if self._live_nexus:
            approved = self._live_nexus.decide(max_actions=3)
            live_decisions = [a.to_dict() for a in approved]

        return {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "risk_aversion": self.risk_aversion,
            "decision": {
                "action": best.get("action"),
                "target_node": best.get("target_node"),
                "score": best.get("score"),
                "delta": best.get("delta"),
            },
            "alternatives": path.get("alternatives", []),
            "rationale": self._generate_rationale(best),
            # Live nexus decisions (executable trades)
            "live_decisions": live_decisions,
            "live_decision_count": len(live_decisions),
        }

    def _generate_rationale(self, best: Dict) -> str:
        """Generate human-readable rationale for decision."""
        action = best.get("action", "hold")
        node = best.get("target_node", "root")
        score = best.get("score", 0)
        delta = best.get("delta", {})

        exp_delta = delta.get("expected", 0)
        worst_delta = delta.get("worst", 0)

        if action == "hold":
            return "No action improves risk-adjusted position"

        parts = [f"Action '{action}' on {node}:"]

        if exp_delta > 0:
            parts.append(f"Improves expected by +${exp_delta:.0f}")
        elif exp_delta < 0:
            parts.append(f"Reduces expected by ${exp_delta:.0f}")

        if worst_delta > 0:
            parts.append(f"Improves worst-case by +${worst_delta:.0f}")
        elif worst_delta < 0:
            parts.append(f"Worsens worst-case by ${worst_delta:.0f}")

        parts.append(f"Score: {score:.1f} (risk_aversion={self.risk_aversion})")

        return " | ".join(parts)

    # =========================================================================
    # EXECUTE - Take Action
    # =========================================================================

    def execute(self, decision: Dict = None) -> Dict:
        """
        Execute the decided action.

        This is step 4 of the ABCFC flow:
        Take action (or log in dry run)

        Now integrates with ABCFCLiveNexus for practical trading execution.
        """
        if decision is None:
            decision = self.decide()

        action = decision.get("decision", {}).get("action", "hold")
        node = decision.get("decision", {}).get("target_node", "root")

        result = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "action": action,
            "node": node,
            "dry_run": self.dry_run,
            "executed": False,
            "live_execution": [],
        }

        if self.dry_run:
            result["status"] = "DRY_RUN"
            result["note"] = "Would execute in live mode"
        else:
            # Real execution would happen here
            # This would integrate with trading pipeline
            result["status"] = "EXECUTED"
            result["executed"] = True

        # Execute live nexus actions (practical trades)
        if self._live_nexus:
            live_decisions = decision.get("live_decisions", [])
            if live_decisions:
                # Convert back to LiveAction objects for execution
                approved_actions = [a for a in self._live_nexus.proposed_actions
                                   if hasattr(a, 'status') and a.status.value == "approved"]
                live_results = self._live_nexus.execute(approved_actions)
                result["live_execution"] = live_results
                result["live_trades_proposed"] = len(live_decisions)
                result["live_trades_executed"] = sum(1 for r in live_results if r.get("executed"))

        # Log to history
        self.history.append({
            "timestamp": result["timestamp"],
            "decision": decision,
            "result": result,
        })

        # Log to file
        self._log_execution(decision, result)

        return result

    def _log_execution(self, decision: Dict, result: Dict):
        """Log execution to file."""
        entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "decision": decision,
            "result": result,
        }
        with open(ORCHESTRATOR_LOG, 'a') as f:
            f.write(json.dumps(entry) + '\n')

    # =========================================================================
    # TRACK - Record Outcome
    # =========================================================================

    def track(self, outcome: Dict) -> Dict:
        """
        Record outcome of executed action.

        This is step 5 of the ABCFC flow:
        Record outcome → Update reality → Enable learning
        """
        if not self.history:
            return {"error": "No decisions to track"}

        # Get most recent decision
        last = self.history[-1]
        last["outcome"] = outcome

        # Try to update goals/effects bridge
        try:
            from integrafix.goals_effects_bridge import GoalsEffectsBridge, EffectType
            bridge = GoalsEffectsBridge()
            bridge.record_effect(
                name=f"Action: {last['decision'].get('decision', {}).get('action')}",
                description=f"Outcome of ABCFC decision",
                effect_type=EffectType.OUTCOME,
                value=outcome.get("pnl", 0),
                value_type="currency",
            )
        except:
            pass

        return {
            "tracked": True,
            "decision_id": last["timestamp"],
            "outcome": outcome,
        }

    # =========================================================================
    # FULL CYCLE
    # =========================================================================

    def run_cycle(self) -> Dict:
        """
        Run one complete ABCFC cycle.

        OBSERVE → EVALUATE → DECIDE → EXECUTE
        """
        # 1. Observe
        state = self.observe()

        # 2. Evaluate
        evaluation = self.evaluate()

        # 3. Decide
        decision = self.decide()

        # 4. Execute
        result = self.execute(decision)

        # Save state
        self._save_state()

        return {
            "cycle_timestamp": datetime.now(timezone.utc).isoformat(),
            "state": {
                "hierarchy_nodes": state.hierarchy_nodes,
                "total_bounds": state.total_bounds,
                "total_expected": state.total_expected,
                "sources": state.sources_loaded,
            },
            "evaluation": {
                "cloud_size": evaluation.get("futures_evaluated", 0),
                "cloud_bounds": evaluation.get("cloud_bounds", {}),
            },
            "decision": decision.get("decision"),
            "rationale": decision.get("rationale"),
            "result": result,
        }

    def _save_state(self):
        """Save orchestrator state."""
        if self.state is None:
            return

        state_dict = {
            "timestamp": self.state.timestamp,
            "hierarchy_nodes": self.state.hierarchy_nodes,
            "total_bounds": self.state.total_bounds,
            "total_expected": self.state.total_expected,
            "risk_modifiers": self.state.risk_modifiers,
            "risk_adjusted_worst": self.state.risk_adjusted_worst,
            "risk_adjusted_expected": self.state.risk_adjusted_expected,
            "cloud_size": self.state.cloud_size,
            "cloud_bounds": self.state.cloud_bounds,
            "recommended_action": self.state.recommended_action,
            "recommended_node": self.state.recommended_node,
            "recommended_score": self.state.recommended_score,
            "sources_loaded": self.state.sources_loaded,
            "history_length": len(self.history),
        }

        with open(ORCHESTRATOR_STATE, 'w') as f:
            json.dump(state_dict, f, indent=2)

    # =========================================================================
    # REPORTING
    # =========================================================================

    def print_status(self):
        """Print current orchestrator status."""
        if self.state is None:
            self.observe()

        state = self.state

        print("=" * 70)
        print("ABCFC ORCHESTRATOR STATUS")
        print(f"Generated: {state.timestamp}")
        print("=" * 70)

        print(f"\n>>> HIERARCHY")
        print(f"    Nodes: {state.hierarchy_nodes}")
        print(f"    Bounds: [{state.total_bounds[0]:+,.0f}, {state.total_bounds[1]:+,.0f}]")
        print(f"    Expected: {state.total_expected:+,.0f}")

        print(f"\n>>> RISK ADJUSTMENTS")
        print(f"    Modifiers: {', '.join(state.risk_modifiers) if state.risk_modifiers else 'None'}")
        print(f"    Adjusted Worst: {state.risk_adjusted_worst:+,.0f}")
        print(f"    Adjusted Expected: {state.risk_adjusted_expected:+,.0f}")

        print(f"\n>>> NEXUS CLOUD (Theoretical)")
        print(f"    Futures Evaluated: {state.cloud_size}")
        if state.cloud_bounds:
            cb = state.cloud_bounds
            print(f"    Worst Possible: {cb.get('worst_possible', 0):+,.0f}")
            print(f"    Best Possible: {cb.get('best_possible', 0):+,.0f}")

        print(f"\n>>> LIVE NEXUS (Practical)")
        print(f"    Markets Scanned: {state.live_nexus_markets}")
        print(f"    Actions Proposed: {state.live_nexus_actions}")
        print(f"    Actions Approved: {state.live_nexus_approved}")

        print(f"\n>>> RECOMMENDATION")
        print(f"    Action: {state.recommended_action} on {state.recommended_node}")
        print(f"    Score: {state.recommended_score:.1f}")

        print(f"\n>>> SOURCES")
        for src in state.sources_loaded:
            print(f"    ✓ {src}")

        print(f"\n>>> MODE: {'DRY RUN' if self.dry_run else 'LIVE'}")
        print(f"    Risk Aversion: {self.risk_aversion}")

        print("\n" + "=" * 70)

    def get_dashboard_data(self) -> Dict:
        """Get data for dashboard display."""
        if self.state is None:
            self.observe()

        state = self.state
        reality = self._load_reality()

        return {
            "timestamp": state.timestamp,
            "mode": "DRY_RUN" if self.dry_run else "LIVE",
            "risk_aversion": self.risk_aversion,
            "hierarchy": {
                "nodes": state.hierarchy_nodes,
                "bounds": state.total_bounds,
                "expected": state.total_expected,
            },
            "risk": {
                "modifiers": state.risk_modifiers,
                "adjusted_worst": state.risk_adjusted_worst,
                "adjusted_expected": state.risk_adjusted_expected,
            },
            "nexus": {
                "cloud_size": state.cloud_size,
                "cloud_bounds": state.cloud_bounds,
            },
            "live_nexus": {
                "markets_scanned": state.live_nexus_markets,
                "actions_proposed": state.live_nexus_actions,
                "actions_approved": state.live_nexus_approved,
                "data": self._live_nexus.get_nexus_cloud_data() if self._live_nexus else {},
            },
            "recommendation": {
                "action": state.recommended_action,
                "node": state.recommended_node,
                "score": state.recommended_score,
            },
            "reality": reality,
            "sources": state.sources_loaded,
        }


# =============================================================================
# CLI
# =============================================================================

def main():
    import argparse

    parser = argparse.ArgumentParser(description="ABCFC Orchestrator")
    parser.add_argument("command", choices=[
        "status", "observe", "evaluate", "decide", "execute", "cycle", "dashboard"
    ], default="status", nargs="?")
    parser.add_argument("--risk", type=float, default=0.6, help="Risk aversion (0-1)")
    parser.add_argument("--live", action="store_true", help="Execute actions (default: dry run)")
    args = parser.parse_args()

    orchestrator = ABCFCOrchestrator(
        risk_aversion=args.risk,
        dry_run=not args.live
    )

    if args.command == "status":
        orchestrator.print_status()

    elif args.command == "observe":
        state = orchestrator.observe()
        print(json.dumps({
            "timestamp": state.timestamp,
            "hierarchy_nodes": state.hierarchy_nodes,
            "total_bounds": state.total_bounds,
            "total_expected": state.total_expected,
            "sources": state.sources_loaded,
        }, indent=2))

    elif args.command == "evaluate":
        result = orchestrator.evaluate()
        print(json.dumps(result, indent=2))

    elif args.command == "decide":
        result = orchestrator.decide()
        print(json.dumps(result, indent=2))

    elif args.command == "execute":
        decision = orchestrator.decide()
        result = orchestrator.execute(decision)
        print(json.dumps(result, indent=2))

    elif args.command == "cycle":
        result = orchestrator.run_cycle()
        print(json.dumps(result, indent=2))

    elif args.command == "dashboard":
        data = orchestrator.get_dashboard_data()
        print(json.dumps(data, indent=2))


if __name__ == "__main__":
    main()
