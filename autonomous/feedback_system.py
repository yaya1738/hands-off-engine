#!/usr/bin/env python3
"""
FEEDBACK LOOPS - Learn from outcomes
=====================================

Records:
- Action taken
- Expected outcome
- Actual outcome
- Delta (learning signal)

Feeds back to improve future decisions.

Master: Yair Siegel
"""

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Optional, Tuple

BASE_DIR = Path(__file__).parent.parent
STATE_DIR = BASE_DIR / "state"
FEEDBACK_STATE = STATE_DIR / "feedback_system.json"
FEEDBACK_LOG = STATE_DIR / "feedback_loop.jsonl"
LEARNINGS = STATE_DIR / "learnings.json"


class FeedbackSystem:
    """Learn from every action's outcome."""

    def __init__(self):
        self.state = self._load_state()
        self.learnings = self._load_learnings()

    def _load_state(self) -> Dict:
        if FEEDBACK_STATE.exists():
            return json.load(open(FEEDBACK_STATE))
        return {
            "pending_feedback": {},
            "total_actions": 0,
            "total_feedback": 0,
            "accuracy": 0
        }

    def _save_state(self):
        self.state["last_updated"] = datetime.now(timezone.utc).isoformat()
        with open(FEEDBACK_STATE, 'w') as f:
            json.dump(self.state, f, indent=2)

    def _load_learnings(self) -> Dict:
        if LEARNINGS.exists():
            return json.load(open(LEARNINGS))
        return {"patterns": {}, "rules": []}

    def _save_learnings(self):
        with open(LEARNINGS, 'w') as f:
            json.dump(self.learnings, f, indent=2)

    def record_action(self, action_id: str, action_type: str, expected_outcome: str, metadata: Dict = None) -> str:
        """Record an action with expected outcome."""
        now = datetime.now(timezone.utc)

        self.state["pending_feedback"][action_id] = {
            "action_type": action_type,
            "expected_outcome": expected_outcome,
            "metadata": metadata or {},
            "recorded_at": now.isoformat()
        }

        self.state["total_actions"] += 1
        self._save_state()

        return action_id

    def record_outcome(self, action_id: str, actual_outcome: str, success: bool) -> Dict:
        """Record actual outcome and learn."""
        now = datetime.now(timezone.utc)

        if action_id not in self.state["pending_feedback"]:
            return {"error": "Action not found"}

        action = self.state["pending_feedback"].pop(action_id)

        # Calculate delta
        expected = action["expected_outcome"]
        delta = "correct" if (success and expected == "success") or (not success and expected == "failure") else "incorrect"

        feedback_entry = {
            "action_id": action_id,
            "action_type": action["action_type"],
            "expected": expected,
            "actual": actual_outcome,
            "success": success,
            "delta": delta,
            "timestamp": now.isoformat()
        }

        # Log feedback
        with open(FEEDBACK_LOG, 'a') as f:
            f.write(json.dumps(feedback_entry) + '\n')

        # Update accuracy
        self.state["total_feedback"] += 1
        correct = 1 if delta == "correct" else 0
        self.state["accuracy"] = (
            (self.state["accuracy"] * (self.state["total_feedback"] - 1) + correct) /
            self.state["total_feedback"]
        )

        # Learn pattern
        self._learn_pattern(action["action_type"], success, action.get("metadata", {}))

        self._save_state()

        return feedback_entry

    def _learn_pattern(self, action_type: str, success: bool, metadata: Dict):
        """Extract learning from outcome."""
        if action_type not in self.learnings["patterns"]:
            self.learnings["patterns"][action_type] = {
                "successes": 0,
                "failures": 0,
                "success_conditions": [],
                "failure_conditions": []
            }

        pattern = self.learnings["patterns"][action_type]

        if success:
            pattern["successes"] += 1
            if metadata:
                pattern["success_conditions"].append(metadata)
        else:
            pattern["failures"] += 1
            if metadata:
                pattern["failure_conditions"].append(metadata)

        # Keep only last 20 conditions
        pattern["success_conditions"] = pattern["success_conditions"][-20:]
        pattern["failure_conditions"] = pattern["failure_conditions"][-20:]

        # Generate rule if clear pattern
        total = pattern["successes"] + pattern["failures"]
        if total >= 10:
            success_rate = pattern["successes"] / total
            if success_rate > 0.8:
                rule = f"{action_type} usually succeeds ({success_rate:.0%})"
                if rule not in self.learnings["rules"]:
                    self.learnings["rules"].append(rule)
            elif success_rate < 0.2:
                rule = f"{action_type} usually fails ({1-success_rate:.0%})"
                if rule not in self.learnings["rules"]:
                    self.learnings["rules"].append(rule)

        self._save_learnings()

    def should_try(self, action_type: str) -> Tuple[bool, float, str]:
        """Based on learnings, should we try this action type?"""
        if action_type not in self.learnings["patterns"]:
            return True, 0.5, "No data - try it"

        pattern = self.learnings["patterns"][action_type]
        total = pattern["successes"] + pattern["failures"]

        if total < 5:
            return True, 0.5, "Insufficient data - try it"

        success_rate = pattern["successes"] / total

        if success_rate > 0.5:
            return True, success_rate, f"Good odds ({success_rate:.0%} success rate)"
        else:
            return False, success_rate, f"Bad odds ({success_rate:.0%} success rate)"

    def get_learnings(self) -> Dict:
        """Get all learnings."""
        return {
            "patterns": self.learnings["patterns"],
            "rules": self.learnings["rules"],
            "accuracy": self.state["accuracy"],
            "total_feedback": self.state["total_feedback"]
        }


def get_feedback_system() -> FeedbackSystem:
    return FeedbackSystem()


if __name__ == "__main__":
    import sys
    fb = get_feedback_system()

    if len(sys.argv) > 1 and sys.argv[1] == "learnings":
        print(json.dumps(fb.get_learnings(), indent=2))
    else:
        print("Usage: python feedback_system.py learnings")
