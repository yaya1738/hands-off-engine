#!/usr/bin/env python3
"""
Learning Engine - Adaptive Improvement System
Learns from outcomes and improves strategy over time.

Serving: Yair Siegel
"""

import json
import os
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Dict, List, Any
from collections import defaultdict

PROJECT_ROOT = Path(__file__).parent.parent
STATE_DIR = PROJECT_ROOT / "state"

MASTER = "Yair Siegel"
LEARNING_STATE = STATE_DIR / "learning_engine.json"
OUTCOME_LOG = STATE_DIR / "outcomes.jsonl"


class LearningEngine:
    """Learn from outcomes and adapt strategies."""

    def __init__(self):
        self.state = self._load_state()
        self.outcomes = self._load_outcomes()

    def _load_state(self) -> Dict:
        if LEARNING_STATE.exists():
            with open(LEARNING_STATE) as f:
                return json.load(f)
        return {
            "created_at": datetime.now(timezone.utc).isoformat(),
            "total_experiments": 0,
            "strategies": {},
            "what_works": [],
            "what_fails": [],
            "current_focus": None,
            "learning_rate": 0.1
        }

    def _save_state(self):
        self.state["last_updated"] = datetime.now(timezone.utc).isoformat()
        with open(LEARNING_STATE, 'w') as f:
            json.dump(self.state, f, indent=2)

    def _load_outcomes(self) -> List[Dict]:
        """Load outcome history."""
        outcomes = []
        if OUTCOME_LOG.exists():
            with open(OUTCOME_LOG) as f:
                for line in f:
                    try:
                        outcomes.append(json.loads(line))
                    except:
                        pass
        return outcomes

    def record_outcome(self, action: str, category: str,
                       success: bool, value: float = 0.0,
                       details: str = "") -> Dict:
        """Record an outcome for learning."""
        outcome = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "action": action,
            "category": category,
            "success": success,
            "value": value,
            "details": details
        }

        with open(OUTCOME_LOG, 'a') as f:
            f.write(json.dumps(outcome) + "\n")

        self.outcomes.append(outcome)

        # Update strategy scores
        if category not in self.state["strategies"]:
            self.state["strategies"][category] = {
                "attempts": 0,
                "successes": 0,
                "total_value": 0.0,
                "score": 0.5
            }

        strategy = self.state["strategies"][category]
        strategy["attempts"] += 1
        if success:
            strategy["successes"] += 1
        strategy["total_value"] += value

        # Update score with learning rate
        lr = self.state["learning_rate"]
        if success:
            strategy["score"] = strategy["score"] * (1 - lr) + 1.0 * lr
        else:
            strategy["score"] = strategy["score"] * (1 - lr) + 0.0 * lr

        self._save_state()
        return outcome

    def analyze_patterns(self) -> Dict:
        """Analyze patterns in outcomes."""
        analysis = {
            "by_category": defaultdict(lambda: {"successes": 0, "failures": 0, "value": 0}),
            "by_day": defaultdict(lambda: {"successes": 0, "failures": 0}),
            "by_hour": defaultdict(lambda: {"successes": 0, "failures": 0}),
            "trends": []
        }

        for outcome in self.outcomes:
            cat = outcome.get("category", "unknown")
            success = outcome.get("success", False)
            value = outcome.get("value", 0)

            analysis["by_category"][cat]["value"] += value
            if success:
                analysis["by_category"][cat]["successes"] += 1
            else:
                analysis["by_category"][cat]["failures"] += 1

            # Time patterns
            try:
                ts = datetime.fromisoformat(outcome["timestamp"].replace("Z", "+00:00"))
                day = ts.strftime("%A")
                hour = ts.hour

                if success:
                    analysis["by_day"][day]["successes"] += 1
                    analysis["by_hour"][hour]["successes"] += 1
                else:
                    analysis["by_day"][day]["failures"] += 1
                    analysis["by_hour"][hour]["failures"] += 1
            except:
                pass

        # Convert defaultdicts to regular dicts
        analysis["by_category"] = dict(analysis["by_category"])
        analysis["by_day"] = dict(analysis["by_day"])
        analysis["by_hour"] = dict(analysis["by_hour"])

        # Identify trends
        for cat, data in analysis["by_category"].items():
            total = data["successes"] + data["failures"]
            if total > 0:
                rate = data["successes"] / total
                if rate > 0.5:
                    analysis["trends"].append({
                        "category": cat,
                        "success_rate": rate,
                        "recommendation": "INCREASE"
                    })
                elif rate < 0.2:
                    analysis["trends"].append({
                        "category": cat,
                        "success_rate": rate,
                        "recommendation": "DECREASE or CHANGE"
                    })

        return analysis

    def get_recommendations(self) -> List[Dict]:
        """Get strategic recommendations based on learning."""
        recommendations = []

        # Analyze current strategies
        strategies = self.state.get("strategies", {})

        # Sort by score
        sorted_strategies = sorted(
            strategies.items(),
            key=lambda x: x[1].get("score", 0),
            reverse=True
        )

        # Top performers
        for name, data in sorted_strategies[:3]:
            if data.get("score", 0) > 0.5:
                recommendations.append({
                    "priority": "high",
                    "action": f"INCREASE {name}",
                    "reason": f"Score: {data['score']:.2f}, Success rate: {data['successes']}/{data['attempts']}",
                    "potential": "High based on historical performance"
                })

        # Bottom performers
        for name, data in sorted_strategies[-3:]:
            if data.get("score", 0) < 0.3 and data.get("attempts", 0) > 3:
                recommendations.append({
                    "priority": "medium",
                    "action": f"STOP or CHANGE {name}",
                    "reason": f"Score: {data['score']:.2f}, Success rate: {data['successes']}/{data['attempts']}",
                    "suggestion": "Try different approach or abandon"
                })

        # Untested strategies
        untested = [
            {"name": "github_sponsors", "potential": "$5-500/month"},
            {"name": "gumroad_course", "potential": "$50-500/sale"},
            {"name": "consulting_retainer", "potential": "$2000-5000/month"},
            {"name": "hacker_news_post", "potential": "Traffic + leads"},
            {"name": "reddit_post", "potential": "Traffic + leads"}
        ]

        for strategy in untested:
            if strategy["name"] not in strategies:
                recommendations.append({
                    "priority": "try",
                    "action": f"TEST {strategy['name']}",
                    "reason": "Not yet attempted",
                    "potential": strategy["potential"]
                })

        return recommendations

    def generate_next_experiment(self) -> Dict:
        """Generate the next experiment to run."""
        recommendations = self.get_recommendations()

        # Prioritize untested strategies
        untested = [r for r in recommendations if r.get("priority") == "try"]
        if untested:
            chosen = untested[0]
            experiment = {
                "id": f"exp_{datetime.now().strftime('%Y%m%d%H%M%S')}",
                "strategy": chosen["action"].replace("TEST ", ""),
                "hypothesis": f"Testing {chosen['action']} may generate {chosen.get('potential', 'value')}",
                "success_criteria": "Any positive response or conversion",
                "duration": "7 days",
                "status": "proposed"
            }
            return experiment

        # Otherwise pick highest priority
        if recommendations:
            chosen = recommendations[0]
            experiment = {
                "id": f"exp_{datetime.now().strftime('%Y%m%d%H%M%S')}",
                "strategy": chosen["action"],
                "hypothesis": chosen["reason"],
                "success_criteria": "Improved conversion or revenue",
                "duration": "7 days",
                "status": "proposed"
            }
            return experiment

        return {"status": "no_experiment_needed", "reason": "All strategies tested"}

    def run_learning_cycle(self) -> Dict:
        """Run a full learning cycle."""
        print("=" * 70)
        print("LEARNING ENGINE - ADAPTIVE IMPROVEMENT")
        print(f"Master: {MASTER}")
        print(f"Time: {datetime.now(timezone.utc).isoformat()}")
        print("=" * 70)
        print()

        results = {
            "timestamp": datetime.now(timezone.utc).isoformat()
        }

        # Analyze patterns
        print("[PATTERN ANALYSIS]")
        analysis = self.analyze_patterns()
        results["analysis"] = analysis
        print(f"  Categories tracked: {len(analysis['by_category'])}")
        print(f"  Total outcomes: {len(self.outcomes)}")
        print()

        # Show strategy scores
        print("[STRATEGY SCORES]")
        strategies = self.state.get("strategies", {})
        for name, data in sorted(strategies.items(), key=lambda x: x[1].get("score", 0), reverse=True):
            print(f"  {name}: {data.get('score', 0):.2f} ({data.get('successes', 0)}/{data.get('attempts', 0)})")
        print()

        # Get recommendations
        print("[RECOMMENDATIONS]")
        recommendations = self.get_recommendations()
        results["recommendations"] = recommendations
        for rec in recommendations[:5]:
            priority_icon = {"high": "🔥", "medium": "⚠️", "try": "🧪"}.get(rec["priority"], "•")
            print(f"  {priority_icon} [{rec['priority'].upper()}] {rec['action']}")
            print(f"     Reason: {rec.get('reason', 'N/A')}")
        print()

        # Generate next experiment
        print("[NEXT EXPERIMENT]")
        experiment = self.generate_next_experiment()
        results["next_experiment"] = experiment
        print(f"  Strategy: {experiment.get('strategy', 'N/A')}")
        print(f"  Hypothesis: {experiment.get('hypothesis', 'N/A')}")
        print()

        # Summary
        print("=" * 70)
        print("LEARNING SUMMARY")
        print("=" * 70)
        print(f"  Outcomes recorded: {len(self.outcomes)}")
        print(f"  Strategies tracked: {len(strategies)}")
        print(f"  Recommendations: {len(recommendations)}")
        print()

        print("TO RECORD AN OUTCOME:")
        print("  python3 -c \"")
        print("  from autonomous.learning_engine import LearningEngine")
        print("  le = LearningEngine()")
        print("  le.record_outcome('applied_to_job', 'upwork', True, 500, 'Got hired!')\"")

        self._save_state()
        return results


def main():
    engine = LearningEngine()
    return engine.run_learning_cycle()


if __name__ == "__main__":
    main()
