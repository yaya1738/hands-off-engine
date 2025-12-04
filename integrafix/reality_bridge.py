#!/usr/bin/env python3
"""
INTEGRAFIX: Reality ↔ Potential Reality Bridge
===============================================

The deepest integration: connecting WHAT IS with WHAT COULD BE.

REALITY (Current State):
- Financial position (deployable, runway, burn)
- Trading positions (open, P&L)
- System health (daemons, bridges, automations)
- Knowledge state (teachings applied, insights pending)

POTENTIAL REALITY (Nexus Cloud):
- All possible futures from available actions
- ABCFC bounds for each future
- Probability-weighted outcomes
- Path scores to desired states

THE BRIDGE:
- Snapshots reality at any moment
- Projects potential realities via ABCFC
- Scores paths from current to desired state
- Recommends optimal action sequence
- Learns from reality→outcome mappings

Philosophy:
"The present is a knife edge between infinite pasts and infinite futures.
 We can only act in the present, but we must see the cloud of possibilities."

Serving: Yair Siegel
"""

import json
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field
from enum import Enum
import math

PROJECT_ROOT = Path(__file__).parent.parent
STATE_DIR = PROJECT_ROOT / "state"


# =============================================================================
# REALITY SNAPSHOT
# =============================================================================

class RealityDomain(Enum):
    """Domains of reality we track."""
    FINANCIAL = "financial"
    POSITIONS = "positions"
    SYSTEM = "system"
    KNOWLEDGE = "knowledge"
    TEMPORAL = "temporal"


@dataclass
class RealitySnapshot:
    """
    A snapshot of current reality.

    Captures the complete state at a moment in time.
    """
    timestamp: str

    # Financial reality
    liquid_usd: float = 0.0
    deployable: float = 0.0
    runway_months: float = 0.0
    monthly_burn: float = 0.0

    # Position reality
    open_positions: int = 0
    total_exposure: float = 0.0
    unrealized_pnl: float = 0.0

    # Outcome reality
    total_trades: int = 0
    resolved_trades: int = 0
    win_rate: float = 0.0
    total_pnl: float = 0.0

    # System reality
    daemons_running: int = 0
    bridges_active: int = 0
    cron_jobs: int = 0
    health_score: float = 0.0

    # Knowledge reality
    teachings_applied: int = 0
    insights_pending: int = 0
    wisdom_score: float = 0.0

    def to_dict(self) -> Dict:
        return {
            "timestamp": self.timestamp,
            "financial": {
                "liquid_usd": self.liquid_usd,
                "deployable": self.deployable,
                "runway_months": self.runway_months,
                "monthly_burn": self.monthly_burn,
            },
            "positions": {
                "open": self.open_positions,
                "exposure": self.total_exposure,
                "unrealized_pnl": self.unrealized_pnl,
            },
            "outcomes": {
                "total_trades": self.total_trades,
                "resolved": self.resolved_trades,
                "win_rate": self.win_rate,
                "total_pnl": self.total_pnl,
            },
            "system": {
                "daemons": self.daemons_running,
                "bridges": self.bridges_active,
                "cron_jobs": self.cron_jobs,
                "health_score": self.health_score,
            },
            "knowledge": {
                "teachings_applied": self.teachings_applied,
                "insights_pending": self.insights_pending,
                "wisdom_score": self.wisdom_score,
            }
        }

    def reality_score(self) -> float:
        """
        Overall reality score (0-1).

        Combines all domains into single measure of "how good is reality".
        """
        # Financial score (runway is critical)
        if self.runway_months < 1:
            financial_score = self.runway_months * 0.5  # Penalize heavily
        elif self.runway_months < 3:
            financial_score = 0.5 + (self.runway_months - 1) * 0.15
        else:
            financial_score = min(1.0, 0.8 + self.runway_months * 0.02)

        # Trading score
        trading_score = self.win_rate if self.total_trades > 0 else 0.5

        # System score
        system_score = self.health_score

        # Knowledge score
        knowledge_score = self.wisdom_score

        # Weighted average (financial matters most when runway is low)
        if self.runway_months < 1:
            weights = [0.5, 0.3, 0.1, 0.1]  # Financial critical
        else:
            weights = [0.25, 0.35, 0.2, 0.2]  # Balanced

        scores = [financial_score, trading_score, system_score, knowledge_score]
        return sum(w * s for w, s in zip(weights, scores))


# =============================================================================
# POTENTIAL REALITY (FUTURES)
# =============================================================================

@dataclass
class PotentialReality:
    """
    A potential future state - what reality COULD become.

    Generated from ABCFC nexus cloud exploration.
    """
    id: str
    name: str
    description: str

    # Probability and timeline
    probability: float = 0.5
    time_horizon_days: float = 30.0

    # Financial bounds
    worst_outcome: float = 0.0
    best_outcome: float = 0.0
    expected_outcome: float = 0.0

    # Required actions
    actions_required: List[str] = field(default_factory=list)

    # Conditions
    conditions: List[str] = field(default_factory=list)
    blockers: List[str] = field(default_factory=list)

    # Score
    desirability: float = 0.0  # How much we want this future
    achievability: float = 0.0  # How achievable it is

    def path_score(self, risk_aversion: float = 0.5) -> float:
        """Score this potential reality as a destination."""
        # Expected value adjusted for risk
        range_val = max(abs(self.best_outcome), abs(self.worst_outcome), 1)

        ev_score = self.expected_outcome / range_val
        risk_penalty = risk_aversion * (self.worst_outcome / range_val)
        upside_bonus = (1 - risk_aversion) * (self.best_outcome / range_val) * 0.2

        base_score = ev_score + risk_penalty + upside_bonus

        # Adjust for probability and achievability
        return base_score * self.probability * self.achievability * self.desirability

    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "probability": self.probability,
            "time_horizon_days": self.time_horizon_days,
            "bounds": {
                "worst": self.worst_outcome,
                "best": self.best_outcome,
                "expected": self.expected_outcome,
            },
            "actions_required": self.actions_required,
            "conditions": self.conditions,
            "blockers": self.blockers,
            "scores": {
                "desirability": self.desirability,
                "achievability": self.achievability,
                "path_score": self.path_score(),
            }
        }


# =============================================================================
# REALITY BRIDGE
# =============================================================================

class RealityBridge:
    """
    Bridge between Reality and Potential Reality.

    Core functions:
    1. snapshot_reality() - Capture current state
    2. project_futures() - Generate potential realities
    3. find_path() - Best path from current to desired
    4. recommend_action() - What to do NOW
    """

    def __init__(self):
        self.state_path = STATE_DIR / "reality_bridge.json"
        self.history_path = STATE_DIR / "reality_history.jsonl"
        self.state = self._load_state()

    def _load_state(self) -> Dict:
        if self.state_path.exists():
            with open(self.state_path) as f:
                return json.load(f)
        return {
            "created_at": datetime.now(timezone.utc).isoformat(),
            "snapshots_taken": 0,
            "futures_projected": 0,
            "paths_found": 0,
            "actions_recommended": 0,
            "reality_transitions": [],
        }

    def _save_state(self):
        self.state["updated_at"] = datetime.now(timezone.utc).isoformat()
        with open(self.state_path, 'w') as f:
            json.dump(self.state, f, indent=2)

    def _log_snapshot(self, snapshot: RealitySnapshot):
        """Log snapshot to history."""
        with open(self.history_path, 'a') as f:
            f.write(json.dumps(snapshot.to_dict()) + "\n")

    # =========================================================================
    # SNAPSHOT REALITY
    # =========================================================================

    def snapshot_reality(self) -> RealitySnapshot:
        """
        Capture complete snapshot of current reality.
        """
        snapshot = RealitySnapshot(
            timestamp=datetime.now(timezone.utc).isoformat()
        )

        # Financial reality
        try:
            kernel_path = STATE_DIR / "yair_context_kernel.json"
            if kernel_path.exists():
                with open(kernel_path) as f:
                    kernel = json.load(f)
                fin = kernel.get("financial_snapshot", {})
                snapshot.liquid_usd = fin.get("liquid_usd", 0)
                snapshot.deployable = fin.get("deployable", 0)
                snapshot.runway_months = fin.get("runway_months", 0)

            finance_path = PROJECT_ROOT / "finance" / "yair_finance_hub.json"
            if finance_path.exists():
                with open(finance_path) as f:
                    finance = json.load(f)
                snapshot.monthly_burn = finance.get("monthly_burn", {}).get("total_usd", 0)
        except:
            pass

        # Position reality
        try:
            positions_path = STATE_DIR / "positions.json"
            if positions_path.exists():
                with open(positions_path) as f:
                    positions = json.load(f)
                pos_list = positions.get("positions", {})
                snapshot.open_positions = len(pos_list)

                total_exposure = 0
                unrealized = 0
                for pos in pos_list.values():
                    if isinstance(pos, dict):
                        total_exposure += abs(pos.get("size", 0) * pos.get("entry_price", 0))
                        unrealized += pos.get("unrealized_pnl", 0)

                snapshot.total_exposure = total_exposure
                snapshot.unrealized_pnl = unrealized
        except:
            pass

        # Outcome reality - INTEGRAFIX: Read from HFT ground truth
        try:
            hft_log = PROJECT_ROOT / "logs" / "hft_economics.jsonl"
            if hft_log.exists():
                wins = 0
                total = 0
                pnl = 0.0
                with open(hft_log) as f:
                    for line in f:
                        try:
                            d = json.loads(line)
                            if d.get("type") == "trade_close":
                                total += 1
                                cost = d.get("cost", 0)
                                pnl += cost
                                if cost > 0:
                                    wins += 1
                        except:
                            pass
                snapshot.total_trades = total
                snapshot.resolved_trades = total
                snapshot.win_rate = wins / total if total > 0 else 0
                snapshot.total_pnl = pnl
        except:
            pass

        # System reality
        try:
            import subprocess

            # Count running daemons
            daemons = ["hardware_brain", "self_healer", "backend_loop"]
            running = 0
            for d in daemons:
                result = subprocess.run(["pgrep", "-f", d], capture_output=True)
                if result.returncode == 0:
                    running += 1
            snapshot.daemons_running = running

            # Count bridges
            bridges = list((PROJECT_ROOT / "integrafix").glob("*.py"))
            snapshot.bridges_active = len([b for b in bridges if not b.stem.startswith("_")])

            # Count cron jobs
            result = subprocess.run(["crontab", "-l"], capture_output=True, text=True)
            if result.returncode == 0:
                lines = [l for l in result.stdout.split("\n") if l.strip() and not l.startswith("#")]
                snapshot.cron_jobs = len(lines)

            # Health score
            snapshot.health_score = running / len(daemons) if daemons else 0
        except:
            pass

        # Knowledge reality
        try:
            wisdom_path = STATE_DIR / "yair_wisdom.json"
            if wisdom_path.exists():
                with open(wisdom_path) as f:
                    wisdom = json.load(f)
                snapshot.teachings_applied = wisdom.get("teachings_applied", 0)

            # Calculate wisdom score
            snapshot.wisdom_score = min(1.0, snapshot.teachings_applied / 100)
        except:
            pass

        # Log and save
        self._log_snapshot(snapshot)
        self.state["snapshots_taken"] += 1
        self.state["last_snapshot"] = snapshot.to_dict()
        self._save_state()

        return snapshot

    # =========================================================================
    # PROJECT FUTURES (POTENTIAL REALITIES)
    # =========================================================================

    def project_futures(self, current: RealitySnapshot = None) -> List[PotentialReality]:
        """
        Project potential realities from current state.

        Generates futures based on:
        1. Available actions (trading, business, employment)
        2. Current constraints (capital, time, knowledge)
        3. Market conditions (opportunities available)
        """
        if current is None:
            current = self.snapshot_reality()

        futures = []

        # =================================================================
        # FUTURE 1: Status Quo (Do Nothing)
        # =================================================================
        status_quo = PotentialReality(
            id="status_quo",
            name="Status Quo",
            description="Continue current trajectory without major changes",
            probability=0.9,  # Very achievable
            time_horizon_days=30,
            worst_outcome=-current.monthly_burn,  # Burn through money
            best_outcome=current.unrealized_pnl * 1.2,  # Positions improve
            expected_outcome=-current.monthly_burn * 0.5,  # Net burn
            actions_required=[],
            conditions=["Market stability"],
            blockers=[],
            desirability=0.3,  # Not desirable if runway < 1
            achievability=0.95,
        )
        futures.append(status_quo)

        # =================================================================
        # FUTURE 2: Aggressive Trading
        # =================================================================
        if current.deployable > 50:
            aggressive = PotentialReality(
                id="aggressive_trading",
                name="Aggressive Trading",
                description="Deploy all capital into high-conviction trades",
                probability=0.6,
                time_horizon_days=30,
                worst_outcome=-current.deployable,  # Lose it all
                best_outcome=current.deployable * 5,  # 5x return
                expected_outcome=current.deployable * 0.3,  # 30% return
                actions_required=[
                    "Find merge arbitrage opportunities",
                    "Deploy capital to Polymarket",
                    "Apply ESPN algorithm to sports",
                    "Hunt thin book edges",
                ],
                conditions=[
                    "Merge arb opportunities exist",
                    "Market liquidity sufficient",
                ],
                blockers=["No capital" if current.deployable < 50 else None],
                desirability=0.8 if current.runway_months < 1 else 0.5,
                achievability=0.7,
            )
            futures.append(aggressive)

        # =================================================================
        # FUTURE 3: Conservative Trading
        # =================================================================
        conservative = PotentialReality(
            id="conservative_trading",
            name="Conservative Trading",
            description="Small, safe trades with guaranteed edges",
            probability=0.8,
            time_horizon_days=30,
            worst_outcome=-current.deployable * 0.2,  # Risk 20%
            best_outcome=current.deployable * 0.5,  # 50% return
            expected_outcome=current.deployable * 0.1,  # 10% return
            actions_required=[
                "Only take merge arbitrage",
                "Small position sizes",
                "Quick exits",
            ],
            conditions=["Arb opportunities exist"],
            blockers=[],
            desirability=0.5,
            achievability=0.85,
        )
        futures.append(conservative)

        # =================================================================
        # FUTURE 4: Income Generation Focus
        # =================================================================
        income_focus = PotentialReality(
            id="income_generation",
            name="Income Generation",
            description="Focus on generating consistent income, not trading gains",
            probability=0.5,
            time_horizon_days=60,
            worst_outcome=-500,  # Job search costs
            best_outcome=5000 * 2,  # 2 months income
            expected_outcome=2000,  # Some income
            actions_required=[
                "Activate income streams",
                "Freelance/consulting work",
                "Reduce AI costs if no ROI",
            ],
            conditions=["Time available", "Skills marketable"],
            blockers=[],
            desirability=0.7 if current.runway_months < 2 else 0.4,
            achievability=0.6,
        )
        futures.append(income_focus)

        # =================================================================
        # FUTURE 5: Optimal Path (Best of all)
        # =================================================================
        optimal = PotentialReality(
            id="optimal_path",
            name="Optimal Path",
            description="Execute all high-EV actions across domains",
            probability=0.4,  # Harder to achieve
            time_horizon_days=30,
            worst_outcome=-current.deployable * 0.5,
            best_outcome=current.deployable * 3 + 3000,  # Trading + income
            expected_outcome=current.deployable * 0.5 + 1000,
            actions_required=[
                "Trading: Deploy to best opportunities",
                "Business: Activate AI ROI paths",
                "Income: Start revenue activities",
                "System: Keep all daemons running",
            ],
            conditions=[
                "Full execution capability",
                "Time management",
                "No major blockers",
            ],
            blockers=[],
            desirability=1.0,  # Most desirable
            achievability=0.5,  # Medium difficulty
        )
        futures.append(optimal)

        # =================================================================
        # FUTURE 6: Worst Case (Avoid)
        # =================================================================
        worst_case = PotentialReality(
            id="worst_case",
            name="Worst Case",
            description="Everything goes wrong - avoid this future",
            probability=0.1,
            time_horizon_days=30,
            worst_outcome=-current.liquid_usd,  # Lose everything
            best_outcome=-current.monthly_burn,  # Just burn
            expected_outcome=-current.liquid_usd * 0.3,
            actions_required=[],
            conditions=["Market crash", "System failure", "No action"],
            blockers=[],
            desirability=0.0,  # Never want this
            achievability=0.2,  # Hopefully low
        )
        futures.append(worst_case)

        self.state["futures_projected"] += len(futures)
        self._save_state()

        return futures

    # =========================================================================
    # FIND PATH (Reality → Potential Reality)
    # =========================================================================

    def find_path(
        self,
        current: RealitySnapshot = None,
        target_id: str = "optimal_path",
        risk_aversion: float = 0.5
    ) -> Dict:
        """
        Find the best path from current reality to target future.

        Returns action sequence with scores.
        """
        if current is None:
            current = self.snapshot_reality()

        futures = self.project_futures(current)

        # Find target
        target = None
        for f in futures:
            if f.id == target_id:
                target = f
                break

        if target is None:
            return {"error": f"Target future '{target_id}' not found"}

        # Score all futures
        scored_futures = []
        for f in futures:
            score = f.path_score(risk_aversion)
            scored_futures.append((f, score))

        scored_futures.sort(key=lambda x: x[1], reverse=True)

        # Build path
        path = {
            "current_reality": {
                "score": current.reality_score(),
                "runway_months": current.runway_months,
                "deployable": current.deployable,
            },
            "target_future": target.to_dict(),
            "path_score": target.path_score(risk_aversion),
            "actions": target.actions_required,
            "conditions": target.conditions,
            "blockers": [b for b in target.blockers if b],
            "alternatives": [
                {"id": f.id, "name": f.name, "score": s}
                for f, s in scored_futures[:3]
            ]
        }

        self.state["paths_found"] += 1
        self._save_state()

        return path

    # =========================================================================
    # RECOMMEND ACTION (What to do NOW)
    # =========================================================================

    def recommend_action(self, risk_aversion: float = 0.5) -> Dict:
        """
        Recommend the best action to take RIGHT NOW.

        Based on:
        1. Current reality state
        2. Best achievable future
        3. Immediate blockers
        4. Time sensitivity
        """
        current = self.snapshot_reality()
        futures = self.project_futures(current)

        # Score and rank futures
        ranked = []
        for f in futures:
            if f.desirability > 0:  # Exclude undesirable futures
                score = f.path_score(risk_aversion)
                ranked.append((f, score))

        ranked.sort(key=lambda x: x[1], reverse=True)

        # Find best achievable future
        best_future = ranked[0][0] if ranked else None

        if not best_future:
            return {"action": "HOLD", "reason": "No viable futures identified"}

        # Determine immediate action
        if current.runway_months < 1:
            urgency = "CRITICAL"
            focus = "income_or_trading"
        elif current.runway_months < 3:
            urgency = "HIGH"
            focus = "growth"
        else:
            urgency = "NORMAL"
            focus = "optimization"

        # Get first action from best path
        immediate_action = None
        if best_future.actions_required:
            immediate_action = best_future.actions_required[0]

        recommendation = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "urgency": urgency,
            "focus": focus,
            "current_reality_score": round(current.reality_score(), 2),
            "best_future": {
                "id": best_future.id,
                "name": best_future.name,
                "expected_outcome": best_future.expected_outcome,
                "path_score": round(best_future.path_score(risk_aversion), 3),
            },
            "immediate_action": immediate_action,
            "all_actions": best_future.actions_required,
            "blockers": [b for b in best_future.blockers if b],
            "alternative_futures": [
                {"id": f.id, "name": f.name, "score": round(s, 3)}
                for f, s in ranked[1:4]
            ]
        }

        self.state["actions_recommended"] += 1
        self._save_state()

        return recommendation

    # =========================================================================
    # VISUALIZE REALITY CLOUD
    # =========================================================================

    def visualize(self, save_path: str = None) -> Dict:
        """
        Visualize reality and potential realities.
        """
        try:
            import matplotlib
            matplotlib.use('Agg')
            import matplotlib.pyplot as plt
            import numpy as np
        except ImportError:
            return {"success": False, "error": "matplotlib not available"}

        current = self.snapshot_reality()
        futures = self.project_futures(current)

        fig, axes = plt.subplots(1, 2, figsize=(16, 8))

        # === Left: Reality Score Breakdown ===
        ax1 = axes[0]

        categories = ['Financial', 'Trading', 'System', 'Knowledge']
        scores = [
            min(1, current.runway_months / 3),  # Financial
            current.win_rate,  # Trading
            current.health_score,  # System
            current.wisdom_score,  # Knowledge
        ]

        colors = ['#ff6b6b' if s < 0.5 else '#4ecdc4' if s < 0.8 else '#45b7d1' for s in scores]

        bars = ax1.barh(categories, scores, color=colors)
        ax1.set_xlim(0, 1)
        ax1.set_xlabel('Score')
        ax1.set_title(f'Current Reality (Score: {current.reality_score():.2f})')
        ax1.axvline(x=0.5, color='gray', linestyle='--', alpha=0.5)

        for bar, score in zip(bars, scores):
            ax1.text(score + 0.02, bar.get_y() + bar.get_height()/2,
                    f'{score:.2f}', va='center')

        # === Right: Potential Realities ===
        ax2 = axes[1]

        t = np.linspace(0, 30, 100)

        for f in futures:
            if f.desirability > 0:
                # Plot expected trajectory
                expected_line = [f.expected_outcome * (ti/30) for ti in t]
                worst_line = [f.worst_outcome * (ti/30) for ti in t]
                best_line = [f.best_outcome * (ti/30) for ti in t]

                alpha = 0.3 + f.desirability * 0.5
                ax2.fill_between(t, worst_line, best_line, alpha=alpha*0.3, label=f.name)
                ax2.plot(t, expected_line, '-', lw=2, alpha=alpha)

        ax2.axhline(y=0, color='black', linestyle='-', lw=1)
        ax2.set_xlabel('Days')
        ax2.set_ylabel('Outcome ($)')
        ax2.set_title('Potential Realities (Nexus Cloud)')
        ax2.legend(loc='upper left', fontsize=9)
        ax2.grid(True, alpha=0.3)

        plt.tight_layout()

        if save_path is None:
            save_path = '/tmp/reality_bridge.png'

        plt.savefig(save_path, dpi=150)
        plt.close()

        return {
            "success": True,
            "chart_path": save_path,
            "current_score": current.reality_score(),
            "futures_plotted": len([f for f in futures if f.desirability > 0])
        }

    # =========================================================================
    # STATUS
    # =========================================================================

    def get_status(self) -> Dict:
        """Get bridge status."""
        current = self.snapshot_reality()
        recommendation = self.recommend_action()

        return {
            "bridge": "reality",
            "status": "operational",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "current_reality": {
                "score": round(current.reality_score(), 2),
                "runway_months": current.runway_months,
                "deployable": current.deployable,
                "open_positions": current.open_positions,
                "health_score": current.health_score,
            },
            "recommendation": {
                "urgency": recommendation["urgency"],
                "immediate_action": recommendation["immediate_action"],
                "best_future": recommendation["best_future"]["name"],
            },
            "stats": {
                "snapshots_taken": self.state.get("snapshots_taken", 0),
                "futures_projected": self.state.get("futures_projected", 0),
                "paths_found": self.state.get("paths_found", 0),
                "actions_recommended": self.state.get("actions_recommended", 0),
            }
        }

    def print_report(self):
        """Print reality bridge report."""
        current = self.snapshot_reality()
        futures = self.project_futures(current)
        recommendation = self.recommend_action()

        print("=" * 70)
        print("INTEGRAFIX: Reality ↔ Potential Reality Bridge")
        print(f"Time: {datetime.now(timezone.utc).isoformat()}")
        print("=" * 70)

        # Current Reality
        print("\n>>> CURRENT REALITY")
        print(f"    Overall Score: {current.reality_score():.2f}")
        print(f"    Financial:")
        print(f"      - Deployable: ${current.deployable:.0f}")
        print(f"      - Runway: {current.runway_months:.1f} months")
        print(f"      - Monthly Burn: ${current.monthly_burn:.0f}")
        print(f"    Trading:")
        print(f"      - Open Positions: {current.open_positions}")
        print(f"      - Win Rate: {current.win_rate:.1%}")
        print(f"      - Total P&L: ${current.total_pnl:.2f}")
        print(f"    System:")
        print(f"      - Daemons: {current.daemons_running}/3")
        print(f"      - Bridges: {current.bridges_active}")
        print(f"      - Cron Jobs: {current.cron_jobs}")

        # Potential Realities
        print("\n>>> POTENTIAL REALITIES")
        for f in sorted(futures, key=lambda x: x.path_score(), reverse=True):
            if f.desirability > 0:
                print(f"    [{f.id}] {f.name}")
                print(f"      Expected: ${f.expected_outcome:+.0f} | Range: [${f.worst_outcome:+.0f}, ${f.best_outcome:+.0f}]")
                print(f"      Score: {f.path_score():.3f} | Desirability: {f.desirability:.1f} | Achievability: {f.achievability:.1f}")

        # Recommendation
        print("\n>>> RECOMMENDATION")
        print(f"    Urgency: {recommendation['urgency']}")
        print(f"    Focus: {recommendation['focus']}")
        print(f"    Best Path: {recommendation['best_future']['name']}")
        print(f"    Expected Outcome: ${recommendation['best_future']['expected_outcome']:+.0f}")
        print(f"    Immediate Action: {recommendation['immediate_action']}")

        if recommendation.get("blockers"):
            print(f"    Blockers: {', '.join(recommendation['blockers'])}")

        print("\n" + "=" * 70)


# =============================================================================
# GLOBAL INSTANCE
# =============================================================================

_bridge: Optional[RealityBridge] = None


def get_reality_bridge() -> RealityBridge:
    """Get or create reality bridge."""
    global _bridge
    if _bridge is None:
        _bridge = RealityBridge()
    return _bridge


# =============================================================================
# CLI
# =============================================================================

def main():
    import argparse

    parser = argparse.ArgumentParser(description="INTEGRAFIX: Reality Bridge")
    parser.add_argument("command", choices=["status", "snapshot", "futures", "path", "recommend", "visualize", "report"],
                       default="status", nargs="?")
    parser.add_argument("--target", help="Target future ID for path finding")
    parser.add_argument("--risk", type=float, default=0.5, help="Risk aversion (0-1)")
    args = parser.parse_args()

    bridge = get_reality_bridge()

    if args.command == "status":
        print(json.dumps(bridge.get_status(), indent=2))

    elif args.command == "snapshot":
        snapshot = bridge.snapshot_reality()
        print(json.dumps(snapshot.to_dict(), indent=2))

    elif args.command == "futures":
        futures = bridge.project_futures()
        for f in futures:
            print(json.dumps(f.to_dict(), indent=2))
            print()

    elif args.command == "path":
        target = args.target or "optimal_path"
        path = bridge.find_path(target_id=target, risk_aversion=args.risk)
        print(json.dumps(path, indent=2))

    elif args.command == "recommend":
        rec = bridge.recommend_action(risk_aversion=args.risk)
        print(json.dumps(rec, indent=2))

    elif args.command == "visualize":
        result = bridge.visualize()
        print(json.dumps(result, indent=2))

    elif args.command == "report":
        bridge.print_report()


if __name__ == "__main__":
    main()
