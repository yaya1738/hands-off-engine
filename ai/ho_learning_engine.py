#!/usr/bin/env python3
"""
Batch 23: Learning Integration Layer
Tracks issue recurrence, agent performance, and learning weights.

Learning engine that:
- Tracks issue recurrence across runs
- Scores agent performance
- Normalizes learning weights
- Calculates trend metrics
- Generates recommendations
"""

import json
import argparse
import hashlib
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field


class LearningEngine:
    """
    Learning engine for tracking system performance over time.

    Tracks:
    - Issue recurrence patterns
    - Agent performance scores
    - System trend metrics
    - Learning weights for decision making
    """

    def __init__(self, state_dir: str = "state", verbose: bool = False):
        self.state_dir = Path(state_dir)
        self.verbose = verbose
        self.consensus_path = self.state_dir / "brain_consensus.json"
        self.learning_path = self.state_dir / "brain_learning.json"
        self.learning_state: Dict = {}

    def generate_issue_hash(self, severity: str, message: str) -> str:
        """Generate stable hash for issue deduplication."""
        content = f"{severity}:{message}".lower()
        return hashlib.sha256(content.encode()).hexdigest()[:16]

    def load_learning_state(self) -> Dict:
        """Load existing learning state or create new one."""
        if self.learning_path.exists():
            try:
                with open(self.learning_path, 'r') as f:
                    return json.load(f)
            except json.JSONDecodeError:
                # Malformed file, start fresh
                pass

        return {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "source": str(self.consensus_path),
            "run_count": 0,
            "issue_history": [],
            "agent_performance": {},
            "trend_metrics": {
                "error_rate_mean": 0.0,
                "error_rate_std": 0.0,
                "consensus_mean": 0.0,
                "consensus_trend": "flat"
            },
            "learning_weights": {},
            "recommendations": []
        }

    def load_consensus(self) -> Dict:
        """Load consensus data."""
        if not self.consensus_path.exists():
            raise FileNotFoundError(f"Missing required input: {self.consensus_path}")

        with open(self.consensus_path, 'r') as f:
            return json.load(f)

    def update_issue_history(self, consensus: Dict) -> List[Dict]:
        """Update issue history with new issues from consensus."""
        existing = {i["hash"]: i for i in self.learning_state.get("issue_history", [])}

        # Get issues from consensus
        issues = consensus.get("issues", [])

        now = datetime.now(timezone.utc).isoformat()

        for issue in issues:
            severity = issue.get("severity", "medium")
            message = issue.get("message", str(issue))
            issue_hash = self.generate_issue_hash(severity, message)

            if issue_hash in existing:
                # Update existing issue
                existing[issue_hash]["occurrences"] += 1
                existing[issue_hash]["last_seen"] = now
                existing[issue_hash]["confidence"] = issue.get("confidence", existing[issue_hash].get("confidence", 0.5))
            else:
                # Add new issue
                existing[issue_hash] = {
                    "hash": issue_hash,
                    "first_seen": now,
                    "last_seen": now,
                    "occurrences": 1,
                    "severity": severity,
                    "message": message,
                    "confidence": issue.get("confidence", 0.5)
                }

        return list(existing.values())

    def update_agent_performance(self, consensus: Dict) -> Dict[str, Dict]:
        """Update agent performance based on consensus."""
        existing = self.learning_state.get("agent_performance", {})
        agents = consensus.get("agents", {})

        for agent_name, agent_data in agents.items():
            if agent_name not in existing:
                existing[agent_name] = {
                    "accuracy": 0.0,
                    "runs": 0,
                    "total_accuracy": 0.0
                }

            # Get confidence as proxy for accuracy
            confidence = agent_data.get("confidence", 0.5)
            existing[agent_name]["runs"] += 1
            existing[agent_name]["total_accuracy"] += confidence
            existing[agent_name]["accuracy"] = existing[agent_name]["total_accuracy"] / existing[agent_name]["runs"]

        return existing

    def compute_learning_weights(self, agent_performance: Dict) -> Dict[str, float]:
        """Compute normalized learning weights from agent performance."""
        if not agent_performance:
            return {}

        # Sum all accuracies
        total_accuracy = sum(p["accuracy"] for p in agent_performance.values())

        if total_accuracy == 0:
            # Equal weights
            n = len(agent_performance)
            return {name: 1.0 / n for name in agent_performance}

        # Normalize to sum to 1.0
        weights = {}
        for name, perf in agent_performance.items():
            weights[name] = perf["accuracy"] / total_accuracy

        return weights

    def compute_trend_metrics(self, issue_history: List[Dict]) -> Dict:
        """Compute trend metrics from issue history."""
        if not issue_history:
            return {
                "error_rate_mean": 0.0,
                "error_rate_std": 0.0,
                "consensus_mean": 0.5,
                "consensus_trend": "flat"
            }

        # Compute error rate from issue occurrences
        occurrences = [i.get("occurrences", 1) for i in issue_history]
        mean_occurrences = sum(occurrences) / len(occurrences)

        # Simple variance calculation
        variance = sum((o - mean_occurrences) ** 2 for o in occurrences) / len(occurrences)
        std = variance ** 0.5

        # Normalize to 0-1 range
        error_rate_mean = min(1.0, mean_occurrences / 10.0)
        error_rate_std = min(1.0, std / 5.0)

        # Compute consensus mean from confidences
        confidences = [i.get("confidence", 0.5) for i in issue_history]
        consensus_mean = sum(confidences) / len(confidences) if confidences else 0.5

        # Determine trend direction
        run_count = self.learning_state.get("run_count", 0)
        prev_mean = self.learning_state.get("trend_metrics", {}).get("consensus_mean", 0.5)

        if run_count <= 1:
            trend = "flat"
        elif consensus_mean > prev_mean + 0.05:
            trend = "up"
        elif consensus_mean < prev_mean - 0.05:
            trend = "down"
        else:
            trend = "flat"

        return {
            "error_rate_mean": error_rate_mean,
            "error_rate_std": error_rate_std,
            "consensus_mean": consensus_mean,
            "consensus_trend": trend
        }

    def generate_recommendations(self, issue_history: List[Dict]) -> List[str]:
        """Generate recommendations based on learning."""
        recommendations = []

        # Find recurring issues
        recurring = [i for i in issue_history if i.get("occurrences", 1) >= 3]
        if recurring:
            recommendations.append(f"Found {len(recurring)} recurring issues - prioritize fixes")

        # Find high severity issues
        high_severity = [i for i in issue_history if i.get("severity") in ["high", "critical"]]
        if high_severity:
            recommendations.append(f"Found {len(high_severity)} high/critical severity issues")

        # Check run count
        run_count = self.learning_state.get("run_count", 0) + 1
        if run_count <= 3:
            recommendations.append("Early learning phase - gathering baseline data")
        elif run_count > 10:
            recommendations.append("Sufficient data for trend analysis")

        if not recommendations:
            recommendations.append("System learning progressing normally")

        return recommendations

    def update(self) -> Dict:
        """
        Run learning update cycle.

        Returns:
            Updated learning state
        """
        # Load existing state
        self.learning_state = self.load_learning_state()

        # Load consensus
        consensus = self.load_consensus()

        # Increment run count
        self.learning_state["run_count"] = self.learning_state.get("run_count", 0) + 1

        # Update components
        self.learning_state["issue_history"] = self.update_issue_history(consensus)
        self.learning_state["agent_performance"] = self.update_agent_performance(consensus)
        self.learning_state["learning_weights"] = self.compute_learning_weights(
            self.learning_state["agent_performance"]
        )
        self.learning_state["trend_metrics"] = self.compute_trend_metrics(
            self.learning_state["issue_history"]
        )
        self.learning_state["recommendations"] = self.generate_recommendations(
            self.learning_state["issue_history"]
        )

        # Update metadata
        self.learning_state["generated_at"] = datetime.now(timezone.utc).isoformat()
        self.learning_state["source"] = str(self.consensus_path)

        # Save state
        self.state_dir.mkdir(parents=True, exist_ok=True)
        with open(self.learning_path, 'w') as f:
            json.dump(self.learning_state, f, indent=2)

        return self.learning_state

    def print_summary(self):
        """Print learning summary."""
        state = self.learning_state
        print("\n" + "=" * 60)
        print("LEARNING ENGINE SUMMARY")
        print("=" * 60)
        print(f"Run count: {state.get('run_count', 0)}")
        print(f"Issues tracked: {len(state.get('issue_history', []))}")
        print(f"Agents tracked: {len(state.get('agent_performance', {}))}")

        print("\nAgent Performance:")
        for agent, perf in state.get("agent_performance", {}).items():
            print(f"  {agent}: accuracy={perf.get('accuracy', 0):.2f}, runs={perf.get('runs', 0)}")

        print("\nLearning Weights:")
        for agent, weight in state.get("learning_weights", {}).items():
            print(f"  {agent}: {weight:.3f}")

        print("\nTrend Metrics:")
        trends = state.get("trend_metrics", {})
        print(f"  Error rate mean: {trends.get('error_rate_mean', 0):.3f}")
        print(f"  Consensus mean: {trends.get('consensus_mean', 0):.3f}")
        print(f"  Consensus trend: {trends.get('consensus_trend', 'flat')}")

        print("\nRecommendations:")
        for rec in state.get("recommendations", []):
            print(f"  - {rec}")
        print("=" * 60)


def update_learning(state_dir: Path = Path("state")) -> Dict[str, Any]:
    """
    Update learning weights based on consensus.

    Args:
        state_dir: Directory where state files are stored

    Returns:
        Dict with status info
    """
    state_dir = Path(state_dir)
    engine = LearningEngine(state_dir=str(state_dir), verbose=False)

    try:
        learning_state = engine.update()
        return {
            "status": "ok",
            "output_files": [str(state_dir / "brain_learning.json")]
        }
    except FileNotFoundError as e:
        return {
            "status": "error",
            "error": str(e)
        }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Learning Integration Layer")
    parser.add_argument("--state-dir", default="state", help="State directory path")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    args = parser.parse_args()

    engine = LearningEngine(state_dir=args.state_dir, verbose=args.verbose)

    try:
        engine.update()
        if args.verbose:
            engine.print_summary()
        print(f"Learning updated: {engine.learning_path}")
    except FileNotFoundError as e:
        print(f"Error: {e}")
        exit(1)
