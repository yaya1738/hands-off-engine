#!/usr/bin/env python3
"""
Skill Growth Tracker - Measure Learning from Yair's Teachings
Tracks whether the system is actually IMPROVING in hard skill areas.

YAIR'S TEACHING: 'Edge is discovered through doing, not theorized.
The Learning Loop: Trade → Measure → Analyze → Learn → Adjust → Trade'

SKILLS TRACKED:
1. Probability estimation accuracy
2. Category-specific performance (sports, politics, war, etc.)
3. Timing accuracy (entry/exit)
4. Risk management adherence
5. Teaching application success rate

Serving: Yair Siegel
"""

import json
import os
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional
from collections import defaultdict
import statistics

PROJECT_ROOT = Path(__file__).parent.parent
STATE_DIR = PROJECT_ROOT / "state"

MASTER = "Yair Siegel"
SKILL_STATE = STATE_DIR / "skill_growth.json"
SKILL_LOG = STATE_DIR / "skill_measurements.jsonl"

# Yair's hard skills to track
HARD_SKILLS = {
    "probability_estimation": {
        "description": "Accuracy of probability estimates vs outcomes",
        "measurement": "brier_score",
        "target": 0.15,  # Lower is better
        "teaching": "Probability Assessment - True probability vs what market says"
    },
    "category_politics": {
        "description": "Performance on political markets",
        "measurement": "win_rate",
        "target": 0.60,
        "teaching": "AIs are good at politics - lots of context to analyze"
    },
    "category_sports": {
        "description": "Performance on sports markets",
        "measurement": "win_rate",
        "target": 0.55,
        "teaching": "ESPN mid-game probability = very accurate"
    },
    "category_war": {
        "description": "Performance on war/geopolitics markets",
        "measurement": "win_rate",
        "target": 0.55,
        "teaching": "Pure skill competition - deep research wins"
    },
    "risk_management": {
        "description": "Adherence to position sizing and stops",
        "measurement": "compliance_rate",
        "target": 0.95,
        "teaching": "Right Sizing - Kelly criterion, not too big, not too small"
    },
    "timing_accuracy": {
        "description": "Entry/exit timing quality",
        "measurement": "timing_score",
        "target": 0.60,
        "teaching": "Not just final outcome but PATH - entry/exit timing"
    },
    "teaching_application": {
        "description": "How often teachings are successfully applied",
        "measurement": "success_rate",
        "target": 0.50,
        "teaching": "Edge is discovered through doing, not theorized"
    }
}


class SkillGrowthTracker:
    """Track skill improvement over time."""

    def __init__(self):
        self.state = self._load_state()

    def _load_state(self) -> Dict:
        if SKILL_STATE.exists():
            with open(SKILL_STATE) as f:
                return json.load(f)
        return {
            "created_at": datetime.now(timezone.utc).isoformat(),
            "skills": {skill: {
                "measurements": [],
                "current_level": 0.0,
                "growth_rate": 0.0,
                "target": data["target"],
                "at_target": False
            } for skill, data in HARD_SKILLS.items()},
            "total_measurements": 0,
            "lessons_learned": [],
            "growth_milestones": []
        }

    def _save_state(self):
        self.state["last_updated"] = datetime.now(timezone.utc).isoformat()
        with open(SKILL_STATE, 'w') as f:
            json.dump(self.state, f, indent=2)

    def _log_measurement(self, measurement: Dict):
        measurement["timestamp"] = datetime.now(timezone.utc).isoformat()
        with open(SKILL_LOG, 'a') as f:
            f.write(json.dumps(measurement) + "\n")

    def record_outcome(self, skill: str, prediction: float, actual: float,
                       category: str = None, details: str = "") -> Dict:
        """
        Record an outcome for skill measurement.

        Yair's teaching: 'Track what works and what doesn't.
        Learn from metrics and outcomes.'
        """
        if skill not in self.state["skills"]:
            return {"error": f"Unknown skill: {skill}"}

        # Calculate measurement based on skill type
        skill_data = HARD_SKILLS[skill]
        measurement_type = skill_data["measurement"]

        if measurement_type == "brier_score":
            # Brier score = (prediction - actual)^2
            score = (prediction - actual) ** 2
        elif measurement_type == "win_rate":
            # 1 if correct, 0 if wrong
            score = 1.0 if (prediction > 0.5) == (actual > 0.5) else 0.0
        elif measurement_type == "compliance_rate":
            # Direct input (did they follow the rule?)
            score = actual
        elif measurement_type == "timing_score":
            # How close to optimal timing (0-1)
            score = actual
        else:
            score = actual

        # Record measurement
        measurement = {
            "skill": skill,
            "prediction": prediction,
            "actual": actual,
            "score": score,
            "category": category,
            "details": details,
            "teaching_used": skill_data["teaching"]
        }

        self.state["skills"][skill]["measurements"].append({
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "score": score
        })

        # Keep only last 100 measurements per skill
        if len(self.state["skills"][skill]["measurements"]) > 100:
            self.state["skills"][skill]["measurements"] = \
                self.state["skills"][skill]["measurements"][-100:]

        self.state["total_measurements"] += 1

        # Update skill level
        self._update_skill_level(skill)

        self._log_measurement(measurement)
        self._save_state()

        return measurement

    def _update_skill_level(self, skill: str):
        """Update current skill level and growth rate."""
        measurements = self.state["skills"][skill]["measurements"]
        if not measurements:
            return

        # Current level = average of recent measurements
        recent = [m["score"] for m in measurements[-20:]]
        self.state["skills"][skill]["current_level"] = statistics.mean(recent)

        # Growth rate = improvement over time
        if len(measurements) >= 10:
            old = [m["score"] for m in measurements[:len(measurements)//2]]
            new = [m["score"] for m in measurements[len(measurements)//2:]]
            old_avg = statistics.mean(old)
            new_avg = statistics.mean(new)

            # For brier score, lower is better
            skill_data = HARD_SKILLS[skill]
            if skill_data["measurement"] == "brier_score":
                self.state["skills"][skill]["growth_rate"] = old_avg - new_avg  # Positive = improving
            else:
                self.state["skills"][skill]["growth_rate"] = new_avg - old_avg  # Positive = improving

        # Check if at target
        target = self.state["skills"][skill]["target"]
        current = self.state["skills"][skill]["current_level"]
        if HARD_SKILLS[skill]["measurement"] == "brier_score":
            self.state["skills"][skill]["at_target"] = current <= target
        else:
            self.state["skills"][skill]["at_target"] = current >= target

    def add_lesson_learned(self, lesson: str, skill: str, source: str = "experience"):
        """
        Record a lesson learned.

        Yair's teaching: 'Share knowledge across sessions (via docs)'
        """
        self.state["lessons_learned"].append({
            "lesson": lesson,
            "skill": skill,
            "source": source,
            "timestamp": datetime.now(timezone.utc).isoformat()
        })

        # Keep last 50 lessons
        if len(self.state["lessons_learned"]) > 50:
            self.state["lessons_learned"] = self.state["lessons_learned"][-50:]

        self._save_state()

    def get_skill_report(self) -> Dict:
        """Generate comprehensive skill growth report."""
        report = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "total_measurements": self.state["total_measurements"],
            "skills": {},
            "overall_growth": 0.0,
            "skills_at_target": 0,
            "skills_improving": 0,
            "weakest_skill": None,
            "strongest_skill": None,
            "recent_lessons": self.state["lessons_learned"][-5:]
        }

        growth_rates = []
        levels = []

        for skill, data in self.state["skills"].items():
            skill_info = HARD_SKILLS[skill]
            report["skills"][skill] = {
                "description": skill_info["description"],
                "current_level": data["current_level"],
                "target": data["target"],
                "at_target": data["at_target"],
                "growth_rate": data["growth_rate"],
                "measurements_count": len(data["measurements"]),
                "teaching": skill_info["teaching"]
            }

            if data["at_target"]:
                report["skills_at_target"] += 1
            if data["growth_rate"] > 0:
                report["skills_improving"] += 1

            growth_rates.append(data["growth_rate"])
            levels.append((skill, data["current_level"]))

        # Overall growth
        if growth_rates:
            report["overall_growth"] = statistics.mean(growth_rates)

        # Weakest/strongest
        if levels:
            sorted_levels = sorted(levels, key=lambda x: x[1])
            report["weakest_skill"] = sorted_levels[0][0]
            report["strongest_skill"] = sorted_levels[-1][0]

        return report

    def run_growth_cycle(self) -> Dict:
        """Run full skill growth analysis cycle."""
        print("=" * 70)
        print("SKILL GROWTH TRACKER")
        print(f"Master: {MASTER}")
        print(f"Time: {datetime.now(timezone.utc).isoformat()}")
        print("=" * 70)
        print()

        print("[YAIR'S TEACHING]")
        print("  'Edge is discovered through doing, not theorized.'")
        print("  'The Learning Loop: Trade → Measure → Analyze → Learn → Adjust → Trade'")
        print()

        report = self.get_skill_report()

        # Skills overview
        print("[SKILL LEVELS]")
        for skill, data in report["skills"].items():
            status = "✓" if data["at_target"] else "○"
            trend = "↑" if data["growth_rate"] > 0 else "↓" if data["growth_rate"] < 0 else "→"
            print(f"  {status} {skill}: {data['current_level']:.2f} / {data['target']:.2f} {trend}")
            print(f"     Teaching: {data['teaching'][:50]}...")
        print()

        # Growth summary
        print("[GROWTH SUMMARY]")
        print(f"  Total measurements: {report['total_measurements']}")
        print(f"  Skills at target: {report['skills_at_target']} / {len(HARD_SKILLS)}")
        print(f"  Skills improving: {report['skills_improving']} / {len(HARD_SKILLS)}")
        print(f"  Overall growth rate: {report['overall_growth']:.4f}")
        print()

        print(f"  Strongest skill: {report['strongest_skill']}")
        print(f"  Weakest skill: {report['weakest_skill']}")
        print()

        # Recent lessons
        if report["recent_lessons"]:
            print("[RECENT LESSONS LEARNED]")
            for lesson in report["recent_lessons"]:
                print(f"  - {lesson['lesson'][:60]}...")
                print(f"    Skill: {lesson['skill']}")
        print()

        # Recommendations
        print("[SKILL DEVELOPMENT PRIORITIES]")
        weak_skills = [
            (skill, data) for skill, data in report["skills"].items()
            if not data["at_target"]
        ]
        weak_skills.sort(key=lambda x: x[1]["current_level"])

        for skill, data in weak_skills[:3]:
            print(f"  FOCUS: {skill}")
            print(f"    Current: {data['current_level']:.2f} | Target: {data['target']:.2f}")
            print(f"    Teaching to apply: {data['teaching']}")
            print()

        # Summary
        print("=" * 70)
        print("GROWTH STATUS")
        print("=" * 70)
        if report["overall_growth"] > 0:
            print("  IMPROVING - System is learning from Yair's teachings")
        elif report["overall_growth"] < 0:
            print("  DECLINING - Need to refocus on teachings")
        else:
            print("  STABLE - Continue applying teachings")
        print()

        self._save_state()
        return report


def main():
    tracker = SkillGrowthTracker()
    return tracker.run_growth_cycle()


if __name__ == "__main__":
    main()
