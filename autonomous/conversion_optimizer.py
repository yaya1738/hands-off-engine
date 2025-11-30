#!/usr/bin/env python3
"""
CONVERSION OPTIMIZER - Bridge the gap between visitors and income
Serving: Yair Siegel

THE PROBLEM:
- 85 visitors
- 0 conversions
- $0 income

THE SOLUTION:
Systematic A/B testing and adaptation to find what converts.
"""

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import random
import hashlib

STATE_FILE = Path("/root/hands-off-engine/state/conversion_optimizer.json")
EXPERIMENTS_FILE = Path("/root/hands-off-engine/state/conversion_experiments.jsonl")

# What we can vary to improve conversion
CONVERSION_LEVERS = {
    "pricing": {
        "variations": ["$99", "$149", "$199", "$49", "Free audit + paid implementation"],
        "current": "$500",  # Original price
        "hypothesis": "Price may be too high for cold traffic"
    },
    "offer": {
        "variations": [
            "Free 15-min consultation",
            "Sample report on your system",
            "Pay only if you're satisfied",
            "First fix free",
            "Money-back guarantee"
        ],
        "current": "Paid audit",
        "hypothesis": "Need trust-building first action"
    },
    "headline": {
        "variations": [
            "Your trading system is leaking money. I'll find where.",
            "I built autonomous systems. Let me optimize yours.",
            "Stop losing trades to bad infrastructure.",
            "AI-powered system audit in 48 hours.",
            "From $0 to profitable: The system that did it"
        ],
        "current": "AI Nexus Consulting",
        "hypothesis": "Need specific pain point, not generic brand"
    },
    "cta": {
        "variations": [
            "Get free diagnosis",
            "See what's broken",
            "Book 15-min call",
            "Send me your logs",
            "Start now - pay later"
        ],
        "current": "Contact for quote",
        "hypothesis": "CTA has too much friction"
    },
    "audience": {
        "variations": [
            "Crypto traders losing to latency",
            "DevOps teams with reliability issues",
            "Startups burning cash on infra",
            "Solo developers overwhelmed by ops",
            "Trading firms seeking edge"
        ],
        "current": "General tech audience",
        "hypothesis": "Need to target specific pain"
    }
}


class ConversionOptimizer:
    """Optimize for conversion, not vanity metrics."""

    def __init__(self):
        self.state = self._load_state()
        self.experiments = self._load_experiments()

    def _load_state(self) -> Dict:
        if STATE_FILE.exists():
            return json.loads(STATE_FILE.read_text())
        return {
            "master": "Yair Siegel",
            "total_experiments": 0,
            "conversions": 0,
            "best_combination": None,
            "current_test": None,
            "visitors_since_change": 0,
            "last_adaptation": None
        }

    def _save_state(self):
        STATE_FILE.write_text(json.dumps(self.state, indent=2))

    def _load_experiments(self) -> List[Dict]:
        if not EXPERIMENTS_FILE.exists():
            return []
        experiments = []
        for line in EXPERIMENTS_FILE.read_text().strip().split('\n'):
            if line:
                experiments.append(json.loads(line))
        return experiments

    def _log_experiment(self, experiment: Dict):
        with open(EXPERIMENTS_FILE, 'a') as f:
            f.write(json.dumps(experiment) + '\n')
        self.experiments.append(experiment)

    def diagnose_conversion_gap(self) -> Dict:
        """
        Analyze why 85 visitors = 0 conversions.
        """
        # Get reality data
        reality_file = Path("/root/hands-off-engine/state/reality_feedback.json")
        reality = {}
        if reality_file.exists():
            reality = json.loads(reality_file.read_text())

        visitors = 85  # Known from reality check
        conversions = reality.get("total_income", 0) > 0

        diagnosis = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "visitors": visitors,
            "conversions": 0 if not conversions else "unknown",
            "conversion_rate": "0%",
            "likely_issues": [],
            "recommended_tests": []
        }

        # Diagnose based on current setup
        if visitors > 50 and not conversions:
            diagnosis["likely_issues"].append({
                "issue": "PRICE_BARRIER",
                "evidence": "$500 is high for cold traffic with no trust",
                "severity": "high"
            })
            diagnosis["likely_issues"].append({
                "issue": "NO_TRUST_SIGNAL",
                "evidence": "No samples, no testimonials, no proof",
                "severity": "high"
            })
            diagnosis["likely_issues"].append({
                "issue": "HIGH_FRICTION_CTA",
                "evidence": "'Contact for quote' requires too much commitment",
                "severity": "medium"
            })
            diagnosis["likely_issues"].append({
                "issue": "GENERIC_MESSAGING",
                "evidence": "No specific pain point addressed",
                "severity": "medium"
            })

        # Recommend tests based on issues
        for issue in diagnosis["likely_issues"]:
            if issue["issue"] == "PRICE_BARRIER":
                diagnosis["recommended_tests"].append({
                    "lever": "pricing",
                    "test": "Try $49 entry offer",
                    "expected_lift": "5-10x conversions"
                })
                diagnosis["recommended_tests"].append({
                    "lever": "offer",
                    "test": "Free audit with paid implementation",
                    "expected_lift": "Remove price barrier entirely"
                })
            elif issue["issue"] == "NO_TRUST_SIGNAL":
                diagnosis["recommended_tests"].append({
                    "lever": "offer",
                    "test": "Free sample report",
                    "expected_lift": "Demonstrate value before asking for money"
                })
            elif issue["issue"] == "HIGH_FRICTION_CTA":
                diagnosis["recommended_tests"].append({
                    "lever": "cta",
                    "test": "'Get free diagnosis' button",
                    "expected_lift": "2-3x click rate"
                })

        return diagnosis

    def generate_experiment(self) -> Dict:
        """
        Generate next experiment based on what hasn't been tested.
        """
        # Find least-tested lever
        lever_test_counts = {lever: 0 for lever in CONVERSION_LEVERS}
        for exp in self.experiments:
            if exp.get("lever") in lever_test_counts:
                lever_test_counts[exp["lever"]] += 1

        # Pick lever with fewest tests, prioritizing high-impact ones
        priority_order = ["pricing", "offer", "cta", "headline", "audience"]
        best_lever = None
        for lever in priority_order:
            if lever_test_counts.get(lever, 0) < 2:  # Test each at least twice
                best_lever = lever
                break

        if not best_lever:
            # All tested, pick random
            best_lever = random.choice(list(CONVERSION_LEVERS.keys()))

        lever_config = CONVERSION_LEVERS[best_lever]

        # Pick untested variation
        tested_variations = set()
        for exp in self.experiments:
            if exp.get("lever") == best_lever:
                tested_variations.add(exp.get("variation"))

        available = [v for v in lever_config["variations"] if v not in tested_variations]
        if not available:
            available = lever_config["variations"]

        variation = random.choice(available)

        experiment = {
            "id": hashlib.md5(f"{best_lever}:{variation}:{datetime.now()}".encode()).hexdigest()[:8],
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "lever": best_lever,
            "variation": variation,
            "original": lever_config["current"],
            "hypothesis": lever_config["hypothesis"],
            "status": "active",
            "visitors": 0,
            "conversions": 0,
            "outcome": None
        }

        return experiment

    def start_experiment(self, experiment: Dict) -> str:
        """
        Start an experiment and return actionable instructions.
        """
        self.state["current_test"] = experiment
        self.state["total_experiments"] += 1
        self.state["visitors_since_change"] = 0
        self.state["last_adaptation"] = datetime.now(timezone.utc).isoformat()
        self._save_state()
        self._log_experiment(experiment)

        # Generate specific action based on lever
        actions = []

        if experiment["lever"] == "pricing":
            actions.append(f"UPDATE landing page price to: {experiment['variation']}")
            actions.append(f"UPDATE outreach template with new price")

        elif experiment["lever"] == "offer":
            actions.append(f"CHANGE offer to: {experiment['variation']}")
            actions.append("UPDATE CTA to match new offer")

        elif experiment["lever"] == "headline":
            actions.append(f"REPLACE headline with: {experiment['variation']}")

        elif experiment["lever"] == "cta":
            actions.append(f"CHANGE button text to: {experiment['variation']}")

        elif experiment["lever"] == "audience":
            actions.append(f"TARGET: {experiment['variation']}")
            actions.append("ADJUST messaging for this audience")

        return {
            "experiment_id": experiment["id"],
            "lever": experiment["lever"],
            "change": f"{experiment['original']} → {experiment['variation']}",
            "actions": actions,
            "measure_after": "50 visitors or 7 days"
        }

    def record_outcome(self, experiment_id: str, visitors: int, conversions: int, revenue: float = 0) -> Dict:
        """
        Record experiment outcome and learn from it.
        """
        for i, exp in enumerate(self.experiments):
            if exp.get("id") == experiment_id:
                self.experiments[i]["visitors"] = visitors
                self.experiments[i]["conversions"] = conversions
                self.experiments[i]["revenue"] = revenue
                self.experiments[i]["status"] = "completed"

                # Determine if winner
                conversion_rate = conversions / max(visitors, 1)
                if conversion_rate > 0:
                    self.experiments[i]["outcome"] = "WINNER"
                    # Update best combination
                    if not self.state["best_combination"]:
                        self.state["best_combination"] = {}
                    self.state["best_combination"][exp["lever"]] = exp["variation"]
                else:
                    self.experiments[i]["outcome"] = "NO_CONVERSION"

                self._save_state()

                # Rewrite experiments file with updates
                with open(EXPERIMENTS_FILE, 'w') as f:
                    for e in self.experiments:
                        f.write(json.dumps(e) + '\n')

                return self.experiments[i]

        return {"error": "Experiment not found"}

    def get_winning_combination(self) -> Dict:
        """
        Return the best-performing combination so far.
        """
        winners = {}
        for exp in self.experiments:
            if exp.get("outcome") == "WINNER":
                lever = exp["lever"]
                if lever not in winners or exp.get("conversions", 0) > winners[lever].get("conversions", 0):
                    winners[lever] = exp

        return {
            "winning_levers": {k: v["variation"] for k, v in winners.items()},
            "experiments_run": self.state["total_experiments"],
            "total_conversions": sum(e.get("conversions", 0) for e in self.experiments)
        }

    def adapt_now(self) -> Dict:
        """
        Run full adaptation cycle:
        1. Diagnose current gap
        2. Generate experiment
        3. Return specific actions to take
        """
        diagnosis = self.diagnose_conversion_gap()
        experiment = self.generate_experiment()
        instructions = self.start_experiment(experiment)

        return {
            "diagnosis": diagnosis,
            "experiment": experiment,
            "instructions": instructions,
            "message": f"ADAPT: Testing {experiment['lever']} - {experiment['variation']}"
        }


def get_conversion_optimizer() -> ConversionOptimizer:
    return ConversionOptimizer()


if __name__ == "__main__":
    import sys

    optimizer = get_conversion_optimizer()

    if len(sys.argv) < 2:
        print("Usage: conversion_optimizer.py [diagnose|adapt|status|record]")
        sys.exit(1)

    cmd = sys.argv[1]

    if cmd == "diagnose":
        print("=" * 60)
        print("CONVERSION DIAGNOSIS")
        print("=" * 60)
        diagnosis = optimizer.diagnose_conversion_gap()
        print(f"\nVisitors: {diagnosis['visitors']}")
        print(f"Conversions: {diagnosis['conversions']}")
        print(f"Rate: {diagnosis['conversion_rate']}")

        print("\n[LIKELY ISSUES]")
        for issue in diagnosis["likely_issues"]:
            print(f"  {issue['severity'].upper()}: {issue['issue']}")
            print(f"    Evidence: {issue['evidence']}")

        print("\n[RECOMMENDED TESTS]")
        for test in diagnosis["recommended_tests"]:
            print(f"  Lever: {test['lever']}")
            print(f"    Test: {test['test']}")
            print(f"    Expected: {test['expected_lift']}")

    elif cmd == "adapt":
        print("=" * 60)
        print("ADAPTATION CYCLE")
        print("=" * 60)
        result = optimizer.adapt_now()

        print("\n[DIAGNOSIS]")
        for issue in result["diagnosis"]["likely_issues"][:2]:
            print(f"  - {issue['issue']}: {issue['evidence']}")

        print(f"\n[EXPERIMENT #{result['experiment']['id']}]")
        print(f"  Testing: {result['experiment']['lever']}")
        print(f"  Change: {result['instructions']['change']}")

        print("\n[ACTIONS TO TAKE]")
        for action in result["instructions"]["actions"]:
            print(f"  → {action}")

        print(f"\n[MEASURE AFTER]: {result['instructions']['measure_after']}")

    elif cmd == "status":
        print("=" * 60)
        print("CONVERSION OPTIMIZER STATUS")
        print("=" * 60)
        print(f"Total experiments: {optimizer.state['total_experiments']}")
        print(f"Current test: {optimizer.state.get('current_test', {}).get('lever', 'None')}")
        print(f"Last adaptation: {optimizer.state.get('last_adaptation', 'Never')}")

        winners = optimizer.get_winning_combination()
        print(f"\nWinning combinations: {len(winners['winning_levers'])}")
        for lever, variation in winners["winning_levers"].items():
            print(f"  {lever}: {variation}")

    elif cmd == "record":
        if len(sys.argv) < 5:
            print("Usage: record <experiment_id> <visitors> <conversions> [revenue]")
            sys.exit(1)
        exp_id = sys.argv[2]
        visitors = int(sys.argv[3])
        conversions = int(sys.argv[4])
        revenue = float(sys.argv[5]) if len(sys.argv) > 5 else 0

        result = optimizer.record_outcome(exp_id, visitors, conversions, revenue)
        print(f"Recorded: {result}")
