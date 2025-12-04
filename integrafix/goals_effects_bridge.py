#!/usr/bin/env python3
"""
INTEGRAFIX: Goals ↔ Effects Bridge
===================================

The causality bridge - connecting INTENTIONS with OUTCOMES.

GOALS (What we want):
- Directives (ABSOLUTE_TRUTH, kernel)
- Targets (trading, scaling, migration)
- Intentions (action plans, decisions)

EFFECTS (What happened):
- Outcomes (trades, resolutions)
- Results (P&L, win rate)
- Changes (state transitions)

THE BRIDGE:
- Captures goals when set
- Tracks effects when they occur
- Maps causality: Goal → Action → Effect
- Measures goal achievement
- Learns calibration: How accurate are our goals?
- Improves future goal setting

Philosophy:
"Every goal is a prediction about the future.
 Every effect is reality's answer.
 The gap between them is where wisdom lives."

Serving: Yair Siegel
"""

import json
import hashlib
from pathlib import Path
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field
from enum import Enum
import math

PROJECT_ROOT = Path(__file__).parent.parent
STATE_DIR = PROJECT_ROOT / "state"


# =============================================================================
# GOAL & EFFECT TYPES
# =============================================================================

class GoalType(Enum):
    """Types of goals in the system."""
    DIRECTIVE = "directive"       # High-level purpose
    TARGET = "target"             # Specific measurable target
    INTENTION = "intention"       # Planned action
    PREDICTION = "prediction"     # Expected outcome
    THRESHOLD = "threshold"       # Boundary condition


class EffectType(Enum):
    """Types of effects observed."""
    OUTCOME = "outcome"           # Direct result of action
    SIDE_EFFECT = "side_effect"   # Unintended consequence
    STATE_CHANGE = "state_change" # System state transition
    MEASUREMENT = "measurement"   # Observed metric
    EVENT = "event"               # Discrete occurrence


class GoalStatus(Enum):
    """Status of a goal."""
    ACTIVE = "active"
    ACHIEVED = "achieved"
    FAILED = "failed"
    ABANDONED = "abandoned"
    SUPERSEDED = "superseded"


# =============================================================================
# DATA STRUCTURES
# =============================================================================

@dataclass
class Goal:
    """A goal or intention in the system."""
    id: str
    name: str
    description: str
    goal_type: GoalType

    # Target
    target_value: Optional[float] = None
    target_condition: Optional[str] = None  # ">=", "<=", "==", "between"
    target_deadline: Optional[str] = None

    # Context
    source: str = ""  # Where goal came from
    domain: str = ""  # trading, system, financial, etc.
    priority: float = 0.5

    # State
    status: GoalStatus = GoalStatus.ACTIVE
    created_at: str = ""
    achieved_at: Optional[str] = None

    # Tracking
    current_value: Optional[float] = None
    progress: float = 0.0  # 0-1
    confidence: float = 0.5  # Confidence in achieving

    # Effects linked
    effect_ids: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "type": self.goal_type.value,
            "target": {
                "value": self.target_value,
                "condition": self.target_condition,
                "deadline": self.target_deadline,
            },
            "source": self.source,
            "domain": self.domain,
            "priority": self.priority,
            "status": self.status.value,
            "created_at": self.created_at,
            "achieved_at": self.achieved_at,
            "current_value": self.current_value,
            "progress": self.progress,
            "confidence": self.confidence,
            "effect_ids": self.effect_ids,
        }


@dataclass
class Effect:
    """An observed effect or outcome."""
    id: str
    name: str
    description: str
    effect_type: EffectType

    # Value
    value: Optional[float] = None
    value_type: str = ""  # "currency", "percentage", "count", etc.

    # Context
    source: str = ""
    domain: str = ""
    timestamp: str = ""

    # Causality
    goal_ids: List[str] = field(default_factory=list)  # Goals this effect relates to
    action_id: Optional[str] = None  # Action that caused this
    preceding_effects: List[str] = field(default_factory=list)

    # Quality
    expected: bool = True  # Was this expected?
    magnitude: float = 0.0  # How significant (-1 to 1)

    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "type": self.effect_type.value,
            "value": self.value,
            "value_type": self.value_type,
            "source": self.source,
            "domain": self.domain,
            "timestamp": self.timestamp,
            "goal_ids": self.goal_ids,
            "action_id": self.action_id,
            "expected": self.expected,
            "magnitude": self.magnitude,
        }


@dataclass
class CausalLink:
    """A link between goal and effect."""
    goal_id: str
    effect_id: str
    strength: float = 0.5  # How strongly related (0-1)
    direction: str = "positive"  # positive, negative, neutral
    learned_at: str = ""


# =============================================================================
# GOALS-EFFECTS BRIDGE
# =============================================================================

class GoalsEffectsBridge:
    """
    Bridge connecting goals with their effects.

    Enables:
    1. Goal registration and tracking
    2. Effect observation and recording
    3. Causal mapping (goal → effect)
    4. Achievement measurement
    5. Calibration learning
    """

    def __init__(self):
        self.state_path = STATE_DIR / "goals_effects_bridge.json"
        self.history_path = STATE_DIR / "goals_effects_history.jsonl"

        self.goals: Dict[str, Goal] = {}
        self.effects: Dict[str, Effect] = {}
        self.links: List[CausalLink] = []

        self.state = self._load_state()
        self._load_goals_effects()

    def _load_state(self) -> Dict:
        if self.state_path.exists():
            with open(self.state_path) as f:
                return json.load(f)
        return {
            "created_at": datetime.now(timezone.utc).isoformat(),
            "goals_registered": 0,
            "effects_recorded": 0,
            "links_created": 0,
            "goals_achieved": 0,
            "goals_failed": 0,
            "calibration_score": 0.5,
        }

    def _save_state(self):
        self.state["updated_at"] = datetime.now(timezone.utc).isoformat()
        self.state["active_goals"] = len([g for g in self.goals.values() if g.status == GoalStatus.ACTIVE])
        self.state["total_effects"] = len(self.effects)

        with open(self.state_path, 'w') as f:
            json.dump(self.state, f, indent=2)

    def _load_goals_effects(self):
        """Load persisted goals and effects."""
        goals_path = STATE_DIR / "tracked_goals.json"
        effects_path = STATE_DIR / "tracked_effects.json"

        if goals_path.exists():
            with open(goals_path) as f:
                data = json.load(f)
                for g in data.get("goals", []):
                    goal = Goal(
                        id=g["id"],
                        name=g["name"],
                        description=g.get("description", ""),
                        goal_type=GoalType(g.get("type", "target")),
                        target_value=g.get("target", {}).get("value"),
                        target_condition=g.get("target", {}).get("condition"),
                        source=g.get("source", ""),
                        domain=g.get("domain", ""),
                        status=GoalStatus(g.get("status", "active")),
                        created_at=g.get("created_at", ""),
                        progress=g.get("progress", 0),
                        effect_ids=g.get("effect_ids", []),
                    )
                    self.goals[goal.id] = goal

        if effects_path.exists():
            with open(effects_path) as f:
                data = json.load(f)
                for e in data.get("effects", []):
                    effect = Effect(
                        id=e["id"],
                        name=e["name"],
                        description=e.get("description", ""),
                        effect_type=EffectType(e.get("type", "outcome")),
                        value=e.get("value"),
                        source=e.get("source", ""),
                        domain=e.get("domain", ""),
                        timestamp=e.get("timestamp", ""),
                        goal_ids=e.get("goal_ids", []),
                    )
                    self.effects[effect.id] = effect

    def _save_goals_effects(self):
        """Persist goals and effects."""
        goals_path = STATE_DIR / "tracked_goals.json"
        effects_path = STATE_DIR / "tracked_effects.json"

        with open(goals_path, 'w') as f:
            json.dump({
                "goals": [g.to_dict() for g in self.goals.values()]
            }, f, indent=2)

        with open(effects_path, 'w') as f:
            json.dump({
                "effects": [e.to_dict() for e in list(self.effects.values())[-100:]]  # Keep last 100
            }, f, indent=2)

    def _generate_id(self, prefix: str) -> str:
        """Generate unique ID."""
        timestamp = datetime.now(timezone.utc).isoformat()
        return f"{prefix}_{hashlib.md5(timestamp.encode()).hexdigest()[:8]}"

    def _log_event(self, event: Dict):
        """Log event to history."""
        event["logged_at"] = datetime.now(timezone.utc).isoformat()
        with open(self.history_path, 'a') as f:
            f.write(json.dumps(event) + "\n")

    # =========================================================================
    # GOAL REGISTRATION
    # =========================================================================

    def register_goal(
        self,
        name: str,
        description: str,
        goal_type: GoalType = GoalType.TARGET,
        target_value: float = None,
        target_condition: str = ">=",
        domain: str = "general",
        source: str = "manual",
        priority: float = 0.5,
        deadline_days: int = None,
    ) -> Goal:
        """
        Register a new goal.
        """
        goal_id = self._generate_id("goal")

        deadline = None
        if deadline_days:
            deadline = (datetime.now(timezone.utc) + timedelta(days=deadline_days)).isoformat()

        goal = Goal(
            id=goal_id,
            name=name,
            description=description,
            goal_type=goal_type,
            target_value=target_value,
            target_condition=target_condition,
            target_deadline=deadline,
            source=source,
            domain=domain,
            priority=priority,
            created_at=datetime.now(timezone.utc).isoformat(),
        )

        self.goals[goal_id] = goal
        self.state["goals_registered"] += 1

        self._log_event({
            "event": "goal_registered",
            "goal_id": goal_id,
            "name": name,
            "target_value": target_value,
        })

        self._save_goals_effects()
        self._save_state()

        return goal

    def import_system_goals(self) -> List[Goal]:
        """
        Import goals from system state files.
        """
        imported = []

        # 1. Import from ABSOLUTE_TRUTH
        try:
            truth_path = STATE_DIR / "ABSOLUTE_TRUTH.json"
            if truth_path.exists():
                with open(truth_path) as f:
                    truth = json.load(f)

                if "directive" in truth:
                    goal = self.register_goal(
                        name="Master Directive",
                        description=truth["directive"][:200],
                        goal_type=GoalType.DIRECTIVE,
                        domain="system",
                        source="ABSOLUTE_TRUTH",
                        priority=1.0,
                    )
                    imported.append(goal)
        except:
            pass

        # 2. Import from yair_context_kernel
        try:
            kernel_path = STATE_DIR / "yair_context_kernel.json"
            if kernel_path.exists():
                with open(kernel_path) as f:
                    kernel = json.load(f)

                # Runway goal
                fin = kernel.get("financial_snapshot", {})
                if "runway_months" in fin:
                    goal = self.register_goal(
                        name="Extend Runway",
                        description="Extend financial runway beyond 3 months",
                        goal_type=GoalType.TARGET,
                        target_value=3.0,
                        target_condition=">=",
                        domain="financial",
                        source="yair_context_kernel",
                        priority=0.95,
                    )
                    goal.current_value = fin["runway_months"]
                    goal.progress = min(1.0, fin["runway_months"] / 3.0)
                    imported.append(goal)
        except:
            pass

        # 3. Import trading targets
        try:
            pipeline_path = STATE_DIR / "trading_pipeline.json"
            if pipeline_path.exists():
                with open(pipeline_path) as f:
                    pipeline = json.load(f)

                # Win rate goal
                if "win_rate" in pipeline:
                    goal = self.register_goal(
                        name="Trading Win Rate",
                        description="Achieve 60%+ win rate on trades",
                        goal_type=GoalType.TARGET,
                        target_value=0.6,
                        target_condition=">=",
                        domain="trading",
                        source="trading_pipeline",
                        priority=0.8,
                    )
                    goal.current_value = pipeline["win_rate"]
                    goal.progress = min(1.0, pipeline["win_rate"] / 0.6)
                    if goal.progress >= 1.0:
                        goal.status = GoalStatus.ACHIEVED
                    imported.append(goal)
        except:
            pass

        # 4. Import system health goal
        goal = self.register_goal(
            name="System Health",
            description="Keep all 3 core daemons running",
            goal_type=GoalType.THRESHOLD,
            target_value=3,
            target_condition=">=",
            domain="system",
            source="system",
            priority=0.9,
        )
        imported.append(goal)

        self._save_goals_effects()
        return imported

    # =========================================================================
    # EFFECT RECORDING
    # =========================================================================

    def record_effect(
        self,
        name: str,
        description: str,
        effect_type: EffectType = EffectType.OUTCOME,
        value: float = None,
        value_type: str = "",
        domain: str = "general",
        source: str = "manual",
        goal_ids: List[str] = None,
        expected: bool = True,
    ) -> Effect:
        """
        Record an observed effect.
        """
        effect_id = self._generate_id("effect")

        effect = Effect(
            id=effect_id,
            name=name,
            description=description,
            effect_type=effect_type,
            value=value,
            value_type=value_type,
            source=source,
            domain=domain,
            timestamp=datetime.now(timezone.utc).isoformat(),
            goal_ids=goal_ids or [],
            expected=expected,
        )

        # Calculate magnitude
        if value is not None:
            if value_type == "currency":
                effect.magnitude = min(1.0, max(-1.0, value / 1000))
            elif value_type == "percentage":
                effect.magnitude = value
            else:
                effect.magnitude = min(1.0, max(-1.0, value / 100))

        self.effects[effect_id] = effect
        self.state["effects_recorded"] += 1

        # Link to goals
        for goal_id in effect.goal_ids:
            if goal_id in self.goals:
                self.goals[goal_id].effect_ids.append(effect_id)
                self._create_link(goal_id, effect_id)

        self._log_event({
            "event": "effect_recorded",
            "effect_id": effect_id,
            "name": name,
            "value": value,
            "goal_ids": goal_ids,
        })

        self._save_goals_effects()
        self._save_state()

        return effect

    def import_system_effects(self) -> List[Effect]:
        """
        Import effects from system state files.
        """
        imported = []

        # 1. Import from HFT ground truth - INTEGRAFIX: Wire to real data
        try:
            hft_log = PROJECT_ROOT / "logs" / "hft_economics.jsonl"
            if hft_log.exists():
                total = 0
                pnl = 0.0
                with open(hft_log) as f:
                    for line in f:
                        try:
                            d = json.loads(line)
                            if d.get("type") == "trade_close":
                                total += 1
                                pnl += d.get("cost", 0)
                        except:
                            pass

                if pnl != 0:
                    effect = self.record_effect(
                        name="Trading P&L",
                        description=f"Total trading profit/loss: ${pnl:.2f}",
                        effect_type=EffectType.OUTCOME,
                        value=pnl,
                        value_type="currency",
                        domain="trading",
                        source="hft_economics",
                    )
                    imported.append(effect)

                if total > 0:
                    effect = self.record_effect(
                        name="Trades Resolved",
                        description=f"Resolved {total} trades",
                        effect_type=EffectType.MEASUREMENT,
                        value=total,
                        value_type="count",
                        domain="trading",
                        source="hft_economics",
                    )
                    imported.append(effect)
        except:
            pass

        # 2. Import from polymarket_live_state
        try:
            poly_path = STATE_DIR / "polymarket_live_state.json"
            if poly_path.exists():
                with open(poly_path) as f:
                    poly = json.load(f)

                if poly.get("total_pnl", 0) != 0:
                    effect = self.record_effect(
                        name="Polymarket P&L",
                        description=f"Polymarket trading P&L: ${poly.get('total_pnl', 0):.2f}",
                        effect_type=EffectType.OUTCOME,
                        value=poly.get("total_pnl", 0),
                        value_type="currency",
                        domain="trading",
                        source="polymarket_live_state",
                    )
                    imported.append(effect)
        except:
            pass

        self._save_goals_effects()
        return imported

    # =========================================================================
    # CAUSAL LINKING
    # =========================================================================

    def _create_link(self, goal_id: str, effect_id: str, strength: float = 0.5):
        """Create causal link between goal and effect."""
        link = CausalLink(
            goal_id=goal_id,
            effect_id=effect_id,
            strength=strength,
            learned_at=datetime.now(timezone.utc).isoformat(),
        )

        # Determine direction
        goal = self.goals.get(goal_id)
        effect = self.effects.get(effect_id)

        if goal and effect and goal.target_value and effect.value:
            if goal.target_condition == ">=":
                link.direction = "positive" if effect.value >= 0 else "negative"
            elif goal.target_condition == "<=":
                link.direction = "positive" if effect.value <= goal.target_value else "negative"

        self.links.append(link)
        self.state["links_created"] += 1

    def link_goal_effect(self, goal_id: str, effect_id: str, strength: float = 0.7) -> bool:
        """
        Manually link a goal to an effect.
        """
        if goal_id not in self.goals:
            return False
        if effect_id not in self.effects:
            return False

        self.goals[goal_id].effect_ids.append(effect_id)
        self.effects[effect_id].goal_ids.append(goal_id)
        self._create_link(goal_id, effect_id, strength)

        self._save_goals_effects()
        return True

    def auto_link(self) -> int:
        """
        Automatically link goals and effects based on domain and timing.
        """
        linked = 0

        for goal in self.goals.values():
            if goal.status != GoalStatus.ACTIVE:
                continue

            for effect in self.effects.values():
                # Skip if already linked
                if effect.id in goal.effect_ids:
                    continue

                # Match by domain
                if goal.domain == effect.domain:
                    # Check time proximity (effect should be after goal)
                    if effect.timestamp > goal.created_at:
                        self.link_goal_effect(goal.id, effect.id, strength=0.5)
                        linked += 1

        return linked

    # =========================================================================
    # GOAL ACHIEVEMENT
    # =========================================================================

    def check_goal_achievement(self, goal_id: str) -> Dict:
        """
        Check if a goal has been achieved.
        """
        goal = self.goals.get(goal_id)
        if not goal:
            return {"error": "Goal not found"}

        result = {
            "goal_id": goal_id,
            "name": goal.name,
            "status": goal.status.value,
            "target_value": goal.target_value,
            "current_value": goal.current_value,
            "progress": goal.progress,
            "effects": [],
        }

        # Collect effects
        for effect_id in goal.effect_ids:
            if effect_id in self.effects:
                effect = self.effects[effect_id]
                result["effects"].append({
                    "id": effect_id,
                    "name": effect.name,
                    "value": effect.value,
                    "magnitude": effect.magnitude,
                })

        # Check achievement
        if goal.target_value is not None and goal.current_value is not None:
            if goal.target_condition == ">=":
                achieved = goal.current_value >= goal.target_value
            elif goal.target_condition == "<=":
                achieved = goal.current_value <= goal.target_value
            elif goal.target_condition == "==":
                achieved = abs(goal.current_value - goal.target_value) < 0.01
            else:
                achieved = False

            if achieved and goal.status == GoalStatus.ACTIVE:
                goal.status = GoalStatus.ACHIEVED
                goal.achieved_at = datetime.now(timezone.utc).isoformat()
                self.state["goals_achieved"] += 1
                result["newly_achieved"] = True

            result["achieved"] = achieved

        self._save_goals_effects()
        self._save_state()

        return result

    def update_goal_progress(self, goal_id: str, current_value: float):
        """Update a goal's current value and progress."""
        goal = self.goals.get(goal_id)
        if not goal:
            return

        goal.current_value = current_value

        if goal.target_value:
            if goal.target_condition == ">=":
                goal.progress = min(1.0, current_value / goal.target_value)
            elif goal.target_condition == "<=":
                if goal.target_value > 0:
                    goal.progress = min(1.0, goal.target_value / current_value) if current_value > 0 else 1.0
            else:
                goal.progress = 1.0 if current_value == goal.target_value else 0.0

        self._save_goals_effects()

    # =========================================================================
    # CALIBRATION LEARNING
    # =========================================================================

    def calculate_calibration(self) -> Dict:
        """
        Calculate goal calibration score.

        Measures how well goals predict actual outcomes.
        """
        if not self.goals:
            return {"calibration": 0.5, "sample_size": 0}

        achieved = 0
        failed = 0
        total_progress = 0
        total_confidence = 0

        for goal in self.goals.values():
            if goal.status == GoalStatus.ACHIEVED:
                achieved += 1
            elif goal.status == GoalStatus.FAILED:
                failed += 1

            total_progress += goal.progress
            total_confidence += goal.confidence

        completed = achieved + failed
        if completed > 0:
            achievement_rate = achieved / completed
        else:
            achievement_rate = 0.5

        avg_progress = total_progress / len(self.goals)
        avg_confidence = total_confidence / len(self.goals)

        # Calibration: how close is confidence to actual achievement?
        calibration = 1 - abs(avg_confidence - achievement_rate)

        self.state["calibration_score"] = calibration
        self._save_state()

        return {
            "calibration": round(calibration, 3),
            "achievement_rate": round(achievement_rate, 3),
            "avg_progress": round(avg_progress, 3),
            "avg_confidence": round(avg_confidence, 3),
            "goals_achieved": achieved,
            "goals_failed": failed,
            "sample_size": len(self.goals),
        }

    # =========================================================================
    # ANALYSIS
    # =========================================================================

    def analyze_goal_effects(self, goal_id: str) -> Dict:
        """
        Analyze the effects of a specific goal.
        """
        goal = self.goals.get(goal_id)
        if not goal:
            return {"error": "Goal not found"}

        effects = [self.effects[eid] for eid in goal.effect_ids if eid in self.effects]

        total_value = sum(e.value or 0 for e in effects)
        avg_magnitude = sum(e.magnitude for e in effects) / len(effects) if effects else 0
        expected_count = sum(1 for e in effects if e.expected)

        return {
            "goal": goal.to_dict(),
            "effect_count": len(effects),
            "total_value": total_value,
            "avg_magnitude": round(avg_magnitude, 3),
            "expected_ratio": expected_count / len(effects) if effects else 0,
            "effects_summary": [
                {"name": e.name, "value": e.value, "expected": e.expected}
                for e in effects[:10]
            ]
        }

    def get_goal_effect_matrix(self) -> Dict:
        """
        Get matrix of goals and their effects.
        """
        matrix = {
            "goals": [],
            "effects_by_goal": {},
            "unlinked_effects": [],
        }

        for goal in self.goals.values():
            matrix["goals"].append({
                "id": goal.id,
                "name": goal.name,
                "status": goal.status.value,
                "progress": goal.progress,
                "effect_count": len(goal.effect_ids),
            })

            effects = [self.effects[eid].to_dict() for eid in goal.effect_ids if eid in self.effects]
            matrix["effects_by_goal"][goal.id] = effects

        # Find unlinked effects
        linked_ids = set()
        for goal in self.goals.values():
            linked_ids.update(goal.effect_ids)

        for effect in self.effects.values():
            if effect.id not in linked_ids:
                matrix["unlinked_effects"].append(effect.to_dict())

        return matrix

    # =========================================================================
    # STATUS
    # =========================================================================

    def get_status(self) -> Dict:
        """Get bridge status."""
        calibration = self.calculate_calibration()

        active_goals = [g for g in self.goals.values() if g.status == GoalStatus.ACTIVE]
        top_goals = sorted(active_goals, key=lambda g: g.priority, reverse=True)[:5]

        recent_effects = sorted(
            self.effects.values(),
            key=lambda e: e.timestamp,
            reverse=True
        )[:5]

        return {
            "bridge": "goals_effects",
            "status": "operational",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "goals": {
                "total": len(self.goals),
                "active": len(active_goals),
                "achieved": self.state.get("goals_achieved", 0),
                "failed": self.state.get("goals_failed", 0),
            },
            "effects": {
                "total": len(self.effects),
                "recent": len(recent_effects),
            },
            "links": {
                "total": len(self.links),
            },
            "calibration": calibration,
            "top_goals": [
                {"name": g.name, "progress": g.progress, "priority": g.priority}
                for g in top_goals
            ],
            "recent_effects": [
                {"name": e.name, "value": e.value, "domain": e.domain}
                for e in recent_effects
            ],
        }

    def print_report(self):
        """Print goals-effects report."""
        status = self.get_status()

        print("=" * 70)
        print("INTEGRAFIX: Goals ↔ Effects Bridge")
        print(f"Time: {status['timestamp']}")
        print("=" * 70)

        # Goals summary
        print("\n>>> GOALS")
        print(f"    Total: {status['goals']['total']}")
        print(f"    Active: {status['goals']['active']}")
        print(f"    Achieved: {status['goals']['achieved']}")
        print(f"    Failed: {status['goals']['failed']}")

        # Top goals
        print("\n    TOP ACTIVE GOALS:")
        for g in status["top_goals"]:
            progress_bar = "█" * int(g["progress"] * 10) + "░" * (10 - int(g["progress"] * 10))
            print(f"    [{progress_bar}] {g['name']} (priority: {g['priority']:.1f})")

        # Effects summary
        print("\n>>> EFFECTS")
        print(f"    Total Recorded: {status['effects']['total']}")
        print(f"    Links Created: {status['links']['total']}")

        print("\n    RECENT EFFECTS:")
        for e in status["recent_effects"]:
            value_str = f"${e['value']:.2f}" if e["value"] else "N/A"
            print(f"    • {e['name']}: {value_str} [{e['domain']}]")

        # Calibration
        cal = status["calibration"]
        print("\n>>> CALIBRATION")
        print(f"    Score: {cal['calibration']:.1%}")
        print(f"    Achievement Rate: {cal['achievement_rate']:.1%}")
        print(f"    Avg Progress: {cal['avg_progress']:.1%}")
        print(f"    Avg Confidence: {cal['avg_confidence']:.1%}")

        # Philosophy
        print("\n>>> WISDOM")
        print("    'Every goal is a prediction about the future.")
        print("     Every effect is reality's answer.")
        print("     The gap between them is where wisdom lives.'")

        print("\n" + "=" * 70)


# =============================================================================
# GLOBAL INSTANCE
# =============================================================================

_bridge: Optional[GoalsEffectsBridge] = None


def get_goals_effects_bridge() -> GoalsEffectsBridge:
    """Get or create goals-effects bridge."""
    global _bridge
    if _bridge is None:
        _bridge = GoalsEffectsBridge()
    return _bridge


# =============================================================================
# CLI
# =============================================================================

def main():
    import argparse

    parser = argparse.ArgumentParser(description="INTEGRAFIX: Goals-Effects Bridge")
    parser.add_argument("command", choices=[
        "status", "import", "goals", "effects", "matrix", "calibration", "report"
    ], default="status", nargs="?")
    parser.add_argument("--goal", help="Goal ID for analysis")
    args = parser.parse_args()

    bridge = get_goals_effects_bridge()

    if args.command == "status":
        print(json.dumps(bridge.get_status(), indent=2))

    elif args.command == "import":
        print("Importing system goals...")
        goals = bridge.import_system_goals()
        print(f"Imported {len(goals)} goals")

        print("\nImporting system effects...")
        effects = bridge.import_system_effects()
        print(f"Imported {len(effects)} effects")

        print("\nAuto-linking...")
        linked = bridge.auto_link()
        print(f"Created {linked} links")

    elif args.command == "goals":
        for goal in bridge.goals.values():
            print(json.dumps(goal.to_dict(), indent=2))
            print()

    elif args.command == "effects":
        for effect in list(bridge.effects.values())[-10:]:
            print(json.dumps(effect.to_dict(), indent=2))
            print()

    elif args.command == "matrix":
        matrix = bridge.get_goal_effect_matrix()
        print(json.dumps(matrix, indent=2))

    elif args.command == "calibration":
        cal = bridge.calculate_calibration()
        print(json.dumps(cal, indent=2))

    elif args.command == "report":
        bridge.print_report()


if __name__ == "__main__":
    main()
