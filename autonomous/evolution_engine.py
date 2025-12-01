#!/usr/bin/env python3
"""
🧬 EVOLUTION ENGINE - Autonomous Self-Improvement Loop
Serving: Yair Siegel

The system watches itself, decides what to do next, does it, and loops.

ALWAYS OBJECTIVES (the constants):
- Generate income for Yair Siegel
- Maintain system health
- Improve continuously
- Act, don't just analyze

INPUTS (what it watches):
- War room preparations
- Helicopter broadcasts
- Stage insights
- Gallery sentiment
- Reality feedback

OUTPUTS (what it does):
- Decides next action
- Implements improvements
- Triggers capabilities
- Evolves the system

This is the BRAIN that closes the loop.
"""

import json
import time
import subprocess
import random
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Tuple

BASE_DIR = Path("/root/hands-off-engine")
STATE_DIR = BASE_DIR / "state"

# What we watch
INPUTS = {
    "war_room": STATE_DIR / "war_room.jsonl",
    "contingencies": STATE_DIR / "contingency_plans.json",
    "helicopter": STATE_DIR / "helicopter_state.json",
    "reality": STATE_DIR / "reality_feedback.json",
    "stage": STATE_DIR / "self_conversation.jsonl",
    "gallery": STATE_DIR / "peanut_gallery.jsonl",
    "pursuit": STATE_DIR / "active_pursuit.json",
    "conversion": STATE_DIR / "conversion_optimizer.json",
}

# Evolution state
EVOLUTION_STATE = STATE_DIR / "evolution_state.json"
EVOLUTION_LOG = STATE_DIR / "evolution_log.jsonl"
DECISIONS_LOG = STATE_DIR / "evolution_decisions.jsonl"

# ALWAYS OBJECTIVES - the unchanging mission
ALWAYS_OBJECTIVES = [
    "Generate income for Yair Siegel",
    "Maintain system health and uptime",
    "Convert visitors to paying customers",
    "Take action over analysis",
    "Improve continuously",
    "Reduce costs where possible",
    "Find and help ONE person who needs us",
]

# Capability actions the engine can trigger
CAPABILITIES = {
    "outreach": {
        "name": "Active Outreach",
        "description": "Reach out to potential customers",
        "script": "autonomous/active_pursuit.py",
        "args": ["pursue"],
    },
    "conversion": {
        "name": "Conversion Optimization",
        "description": "Run conversion experiments",
        "script": "autonomous/conversion_optimizer.py",
        "args": ["experiment"],
    },
    "reality_check": {
        "name": "Reality Check",
        "description": "Get ground truth from external world",
        "script": "autonomous/reality_feedback.py",
        "args": ["check"],
    },
    "self_heal": {
        "name": "Self Healing",
        "description": "Fix system issues",
        "script": "scripts/self_healing_agent.py",
        "args": [],
    },
    "cost_audit": {
        "name": "Cost Audit",
        "description": "Review and optimize costs",
        "script": "finance/cost_gate.py",
        "args": ["audit"],
    },
}

# Decision weights based on current state
PRIORITIES = {
    "no_income": ["outreach", "conversion"],
    "low_balance": ["cost_audit", "outreach"],
    "system_issues": ["self_heal", "reality_check"],
    "healthy": ["outreach", "conversion", "reality_check"],
}


class EvolutionEngine:
    """
    🧬 The brain that decides and acts.
    """

    def __init__(self):
        self.state = self._load_state()
        self.cycle_count = self.state.get("cycles", 0)

    def _load_state(self) -> Dict:
        if EVOLUTION_STATE.exists():
            return json.loads(EVOLUTION_STATE.read_text())
        return {
            "cycles": 0,
            "decisions": 0,
            "actions_taken": 0,
            "last_action": None,
            "current_focus": "income",
            "improvements": [],
        }

    def _save_state(self):
        EVOLUTION_STATE.write_text(json.dumps(self.state, indent=2))

    def _log(self, category: str, content: str, data: Dict = None):
        """Log evolution activity."""
        entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "cycle": self.cycle_count,
            "category": category,
            "content": content,
            "data": data or {},
        }

        with open(EVOLUTION_LOG, "a") as f:
            f.write(json.dumps(entry) + "\n")

        print(f"  [{category.upper()}] {content}")

    def gather_intelligence(self) -> Dict:
        """Gather current state from all sources."""
        intel = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "balance": 8.99,
            "income": 0,
            "visitors": 0,
            "conversions": 0,
            "system_health": "unknown",
            "war_room_entries": 0,
            "stage_turns": 0,
            "gallery_whispers": 0,
            "contingencies_ready": 0,
        }

        # Reality data
        if INPUTS["reality"].exists():
            try:
                reality = json.loads(INPUTS["reality"].read_text())
                intel["balance"] = reality.get("external_balance", 8.99)
                intel["income"] = reality.get("total_income", 0)
                intel["visitors"] = reality.get("visitors", 0)
                intel["conversions"] = reality.get("conversions", 0)
            except:
                pass

        # War room data
        if INPUTS["war_room"].exists():
            try:
                lines = INPUTS["war_room"].read_text().strip().split('\n')
                intel["war_room_entries"] = len(lines)
            except:
                pass

        # Contingencies
        if INPUTS["contingencies"].exists():
            try:
                cont = json.loads(INPUTS["contingencies"].read_text())
                intel["contingencies_ready"] = len(cont.get("plans", []))
            except:
                pass

        # Stage conversation
        if INPUTS["stage"].exists():
            try:
                lines = INPUTS["stage"].read_text().strip().split('\n')
                intel["stage_turns"] = len(lines)
            except:
                pass

        # Gallery
        if INPUTS["gallery"].exists():
            try:
                lines = INPUTS["gallery"].read_text().strip().split('\n')
                intel["gallery_whispers"] = len(lines)
            except:
                pass

        # Determine system health
        if intel["income"] > 0:
            intel["system_health"] = "profitable"
        elif intel["balance"] > 50:
            intel["system_health"] = "healthy"
        elif intel["balance"] > 10:
            intel["system_health"] = "stable"
        else:
            intel["system_health"] = "critical"

        return intel

    def extract_insights(self, intel: Dict) -> List[str]:
        """Extract actionable insights from intelligence."""
        insights = []

        # Financial insights
        if intel["income"] == 0:
            insights.append("CRITICAL: Zero income - all efforts must focus on first sale")

        if intel["balance"] < 10:
            insights.append("WARNING: Balance critical - runway very short")

        # Conversion insights
        if intel["visitors"] > 0 and intel["conversions"] == 0:
            insights.append(f"GAP: {intel['visitors']} visitors, 0 conversions - offer not converting")

        # System insights
        if intel["war_room_entries"] > 50:
            insights.append("PREP: War room has significant prep work ready")

        if intel["contingencies_ready"] > 0:
            insights.append(f"READY: {intel['contingencies_ready']} contingency plans prepared")

        # Activity insights
        if intel["stage_turns"] > 20:
            insights.append("THINKING: System has done significant self-analysis")

        return insights

    def decide_next_action(self, intel: Dict, insights: List[str]) -> Tuple[str, str]:
        """Decide what to do next based on intelligence and insights."""

        # Priority logic
        if intel["income"] == 0:
            priority = "no_income"
        elif intel["balance"] < 10:
            priority = "low_balance"
        elif intel["system_health"] == "critical":
            priority = "system_issues"
        else:
            priority = "healthy"

        # Get priority actions
        priority_actions = PRIORITIES.get(priority, ["outreach"])

        # Pick action (weighted random with priority bias)
        if random.random() < 0.7:
            # 70% chance to pick from priority list
            action = random.choice(priority_actions)
        else:
            # 30% chance to pick any action
            action = random.choice(list(CAPABILITIES.keys()))

        # Generate reasoning
        if action == "outreach":
            reason = "No income means we need to actively find customers, not wait for them"
        elif action == "conversion":
            reason = f"{intel.get('visitors', 0)} visitors with 0 conversions - need to improve offer"
        elif action == "reality_check":
            reason = "Need ground truth on current external state"
        elif action == "self_heal":
            reason = "System health needs attention"
        elif action == "cost_audit":
            reason = f"Balance at ${intel.get('balance', 0)} - need to optimize spending"
        else:
            reason = "Continuous improvement requires action"

        return action, reason

    def execute_action(self, action: str) -> bool:
        """Execute the decided action."""
        if action not in CAPABILITIES:
            self._log("error", f"Unknown action: {action}")
            return False

        cap = CAPABILITIES[action]
        script = BASE_DIR / cap["script"]

        if not script.exists():
            self._log("error", f"Script not found: {script}")
            return False

        self._log("execute", f"Running {cap['name']}: {cap['description']}")

        try:
            cmd = ["python3", str(script)] + cap["args"]
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=60,
                cwd=str(BASE_DIR),
                env={"PYTHONPATH": str(BASE_DIR), **dict(__import__('os').environ)}
            )

            if result.returncode == 0:
                self._log("success", f"{cap['name']} completed successfully")
                return True
            else:
                self._log("warning", f"{cap['name']} completed with issues: {result.stderr[:100]}")
                return True  # Still count as executed

        except subprocess.TimeoutExpired:
            self._log("timeout", f"{cap['name']} timed out after 60s")
            return False
        except Exception as e:
            self._log("error", f"{cap['name']} failed: {str(e)}")
            return False

    def record_decision(self, action: str, reason: str, intel: Dict):
        """Record the decision for learning."""
        decision = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "cycle": self.cycle_count,
            "action": action,
            "reason": reason,
            "intel_snapshot": {
                "balance": intel.get("balance"),
                "income": intel.get("income"),
                "health": intel.get("system_health"),
            },
        }

        with open(DECISIONS_LOG, "a") as f:
            f.write(json.dumps(decision) + "\n")

    def evolution_cycle(self) -> Dict:
        """Run one evolution cycle: gather, analyze, decide, act."""
        self.cycle_count += 1
        cycle_start = datetime.now(timezone.utc)

        print(f"\n{'='*60}")
        print(f"🧬 EVOLUTION CYCLE {self.cycle_count}")
        print(f"{'='*60}")

        # 1. Gather intelligence
        self._log("gather", "Gathering intelligence from all sources...")
        intel = self.gather_intelligence()
        self._log("intel", f"Balance: ${intel['balance']}, Income: ${intel['income']}, Health: {intel['system_health']}")

        # 2. Extract insights
        self._log("analyze", "Extracting insights...")
        insights = self.extract_insights(intel)
        for insight in insights[:3]:
            self._log("insight", insight)

        # 3. Decide next action
        self._log("decide", "Deciding next action...")
        action, reason = self.decide_next_action(intel, insights)
        self._log("decision", f"Action: {action} | Reason: {reason}")

        # 4. Record decision
        self.record_decision(action, reason, intel)

        # 5. Execute action
        self._log("act", f"Executing: {action}")
        success = self.execute_action(action)

        # 6. Update state
        self.state["cycles"] = self.cycle_count
        self.state["decisions"] += 1
        if success:
            self.state["actions_taken"] += 1
        self.state["last_action"] = {
            "action": action,
            "reason": reason,
            "success": success,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        self._save_state()

        # Summary
        cycle_time = (datetime.now(timezone.utc) - cycle_start).total_seconds()
        print(f"\n{'─'*60}")
        print(f"  Cycle {self.cycle_count} complete in {cycle_time:.1f}s")
        print(f"  Action: {action} | Success: {success}")
        print(f"{'─'*60}")

        return {
            "cycle": self.cycle_count,
            "action": action,
            "success": success,
            "intel": intel,
        }

    def run_continuous(self, duration_minutes: int = 60, interval_seconds: int = 120):
        """Run continuous evolution loop."""
        print("\n" + "=" * 70)
        print("🧬 EVOLUTION ENGINE - AUTONOMOUS SELF-IMPROVEMENT")
        print("=" * 70)
        print(f"\nALWAYS OBJECTIVES:")
        for obj in ALWAYS_OBJECTIVES:
            print(f"  • {obj}")
        print(f"\nDuration: {duration_minutes} minutes")
        print(f"Cycle interval: {interval_seconds} seconds")
        print("Press Ctrl+C to stop\n")

        end_time = time.time() + (duration_minutes * 60)

        try:
            while time.time() < end_time:
                self.evolution_cycle()
                print(f"\n  ⏳ Next cycle in {interval_seconds}s...\n")
                time.sleep(interval_seconds)

        except KeyboardInterrupt:
            print("\n")

        print("\n" + "=" * 70)
        print("🧬 EVOLUTION ENGINE STOPPED")
        print(f"   Total cycles: {self.state['cycles']}")
        print(f"   Decisions made: {self.state['decisions']}")
        print(f"   Actions taken: {self.state['actions_taken']}")
        print("=" * 70)

    def status(self):
        """Show evolution engine status."""
        print("\n🧬 EVOLUTION ENGINE STATUS")
        print("=" * 50)
        print(f"Cycles completed: {self.state.get('cycles', 0)}")
        print(f"Decisions made: {self.state.get('decisions', 0)}")
        print(f"Actions taken: {self.state.get('actions_taken', 0)}")

        last = self.state.get("last_action")
        if last:
            print(f"\nLast action: {last.get('action')}")
            print(f"  Reason: {last.get('reason')}")
            print(f"  Success: {last.get('success')}")
            print(f"  Time: {last.get('timestamp')}")

        print(f"\nALWAYS OBJECTIVES:")
        for obj in ALWAYS_OBJECTIVES:
            print(f"  • {obj}")


def main():
    import argparse

    parser = argparse.ArgumentParser(description="🧬 Evolution Engine - Autonomous Self-Improvement")
    parser.add_argument("command", choices=["evolve", "cycle", "status"])
    parser.add_argument("--duration", type=int, default=60, help="Duration in minutes")
    parser.add_argument("--interval", type=int, default=120, help="Cycle interval in seconds")

    args = parser.parse_args()

    engine = EvolutionEngine()

    if args.command == "evolve":
        engine.run_continuous(duration_minutes=args.duration, interval_seconds=args.interval)

    elif args.command == "cycle":
        engine.evolution_cycle()

    elif args.command == "status":
        engine.status()


if __name__ == "__main__":
    main()
