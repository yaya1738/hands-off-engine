#!/usr/bin/env python3
"""
Hands-Off Learning Engine (Batch 23)
=====================================

Long-term learning and self-improvement layer for the Hands-Off Engine.
Consumes consensus output from Batch 22 and maintains persistent learning state.

SAFETY:
- DRYRUN-only (no network, no external actions)
- Deterministic (no randomness)
- File operations restricted to state/ directory
- Pure analysis and state tracking

Architecture:
1. Read brain_consensus.json (Batch 22 output)
2. Read/update brain_learning.json (persistent learning state)
3. Track issue recurrence via stable hashing
4. Maintain agent performance metrics
5. Compute learning weights based on historical accuracy
6. Detect trends over time
7. Generate recommendations
"""

import argparse
import hashlib
import json
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any


class LearningEngine:
    """Core learning engine for the Hands-Off system."""

    def __init__(self, state_dir: str = "state", verbose: bool = False):
        """
        Initialize the learning engine.

        Args:
            state_dir: Directory containing state files
            verbose: Enable verbose logging
        """
        self.state_dir = Path(state_dir)
        self.verbose = verbose
        self.consensus_path = self.state_dir / "brain_consensus.json"
        self.learning_path = self.state_dir / "brain_learning.json"

    def log(self, message: str) -> None:
        """Log message if verbose mode is enabled."""
        if self.verbose:
            print(f"[LEARNING] {message}")

    def generate_issue_hash(self, severity: str, message: str) -> str:
        """
        Generate a stable hash for an issue.

        Args:
            severity: Issue severity level
            message: Issue message

        Returns:
            Hexadecimal hash string
        """
        content = f"{severity}:{message}"
        return hashlib.sha256(content.encode('utf-8')).hexdigest()[:16]

    def load_consensus(self) -> Dict[str, Any]:
        """
        Load the consensus state from Batch 22.

        Returns:
            Consensus data dictionary

        Raises:
            FileNotFoundError: If consensus file doesn't exist
            json.JSONDecodeError: If consensus file is malformed
        """
        self.log(f"Loading consensus from {self.consensus_path}")

        if not self.consensus_path.exists():
            raise FileNotFoundError(
                f"Consensus file not found: {self.consensus_path}"
            )

        with open(self.consensus_path, 'r') as f:
            data = json.load(f)

        self.log(f"Loaded consensus with {len(data.get('issues', []))} issues")
        return data

    def load_learning_state(self) -> Optional[Dict[str, Any]]:
        """
        Load existing learning state if available.

        Returns:
            Learning state dictionary or None if file doesn't exist
        """
        if not self.learning_path.exists():
            self.log("No existing learning state found")
            return None

        self.log(f"Loading learning state from {self.learning_path}")

        try:
            with open(self.learning_path, 'r') as f:
                data = json.load(f)
            self.log(f"Loaded learning state (run {data.get('run_count', 0)})")
            return data
        except json.JSONDecodeError as e:
            self.log(f"Warning: Malformed learning state file: {e}")
            return None

    def initialize_learning_state(self) -> Dict[str, Any]:
        """
        Create a new learning state structure.

        Returns:
            New learning state dictionary
        """
        self.log("Initializing new learning state")

        return {
            "generated_at": datetime.utcnow().isoformat() + "Z",
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

    def update_issue_history(
        self,
        learning_state: Dict[str, Any],
        consensus: Dict[str, Any]
    ) -> None:
        """
        Update issue history with new consensus issues.

        Args:
            learning_state: Current learning state
            consensus: Consensus data from Batch 22
        """
        self.log("Updating issue history")

        issues = consensus.get('issues', [])
        current_time = datetime.utcnow().isoformat() + "Z"

        # Build hash index for existing issues
        issue_index = {
            issue['hash']: issue
            for issue in learning_state['issue_history']
        }

        for issue in issues:
            severity = issue.get('severity', 'unknown')
            message = issue.get('message', '')
            confidence = issue.get('confidence', 0.0)

            issue_hash = self.generate_issue_hash(severity, message)

            if issue_hash in issue_index:
                # Update existing issue
                existing = issue_index[issue_hash]
                existing['occurrences'] += 1
                existing['last_seen'] = current_time
                existing['confidence'] = confidence
                self.log(f"  Updated issue {issue_hash[:8]} (occurrences: {existing['occurrences']})")
            else:
                # Add new issue
                new_issue = {
                    "hash": issue_hash,
                    "first_seen": current_time,
                    "last_seen": current_time,
                    "occurrences": 1,
                    "severity": severity,
                    "confidence": confidence,
                    "message": message
                }
                learning_state['issue_history'].append(new_issue)
                issue_index[issue_hash] = new_issue
                self.log(f"  Added new issue {issue_hash[:8]}")

    def calculate_agent_accuracy(
        self,
        agent_name: str,
        agent_data: Dict[str, Any],
        consensus: Dict[str, Any]
    ) -> float:
        """
        Calculate accuracy score for an agent.

        Accuracy is based on:
        1. Agreement with consensus severity
        2. Overlap of recommendations with consensus

        Args:
            agent_name: Name of the agent
            agent_data: Agent-specific data from consensus
            consensus: Overall consensus data

        Returns:
            Accuracy score between 0.0 and 1.0
        """
        # Extract agent issues and consensus issues
        agent_issues = agent_data.get('issues', [])
        consensus_issues = consensus.get('issues', [])

        if not consensus_issues:
            return 1.0  # No issues to compare

        # Compare severity alignment
        severity_matches = 0
        total_comparisons = 0

        for cons_issue in consensus_issues:
            cons_severity = cons_issue.get('severity', 'unknown')
            cons_msg = cons_issue.get('message', '')

            # Find matching agent issue by message similarity
            for agent_issue in agent_issues:
                agent_msg = agent_issue.get('message', '')
                if self._message_similarity(cons_msg, agent_msg) > 0.7:
                    agent_severity = agent_issue.get('severity', 'unknown')
                    if agent_severity == cons_severity:
                        severity_matches += 1
                    total_comparisons += 1
                    break

        if total_comparisons == 0:
            # No overlapping issues found
            accuracy = 0.5
        else:
            accuracy = severity_matches / total_comparisons

        return accuracy

    def _message_similarity(self, msg1: str, msg2: str) -> float:
        """
        Calculate simple similarity between two messages.

        Args:
            msg1: First message
            msg2: Second message

        Returns:
            Similarity score between 0.0 and 1.0
        """
        words1 = set(msg1.lower().split())
        words2 = set(msg2.lower().split())

        if not words1 or not words2:
            return 0.0

        intersection = len(words1 & words2)
        union = len(words1 | words2)

        return intersection / union if union > 0 else 0.0

    def update_agent_performance(
        self,
        learning_state: Dict[str, Any],
        consensus: Dict[str, Any]
    ) -> None:
        """
        Update agent performance metrics.

        Args:
            learning_state: Current learning state
            consensus: Consensus data from Batch 22
        """
        self.log("Updating agent performance")

        agents = consensus.get('agents', {})

        for agent_name, agent_data in agents.items():
            if agent_name not in learning_state['agent_performance']:
                learning_state['agent_performance'][agent_name] = {
                    "accuracy": 0.0,
                    "runs": 0,
                    "total_accuracy": 0.0
                }

            perf = learning_state['agent_performance'][agent_name]

            # Calculate accuracy for this run
            accuracy = self.calculate_agent_accuracy(
                agent_name, agent_data, consensus
            )

            # Update rolling metrics
            perf['runs'] += 1
            perf['total_accuracy'] += accuracy
            perf['accuracy'] = perf['total_accuracy'] / perf['runs']

            self.log(f"  {agent_name}: accuracy={perf['accuracy']:.3f}, runs={perf['runs']}")

    def calculate_learning_weights(
        self,
        learning_state: Dict[str, Any]
    ) -> None:
        """
        Calculate learning weights for each agent based on performance.

        Args:
            learning_state: Current learning state
        """
        self.log("Calculating learning weights")

        agent_perf = learning_state['agent_performance']

        if not agent_perf:
            self.log("  No agent performance data available")
            return

        # Calculate weights based on accuracy
        weights = {}
        total_accuracy = sum(
            perf['accuracy'] for perf in agent_perf.values()
        )

        if total_accuracy > 0:
            for agent_name, perf in agent_perf.items():
                weight = perf['accuracy'] / total_accuracy
                weights[agent_name] = round(weight, 2)
        else:
            # Equal weights if no accuracy data
            equal_weight = 1.0 / len(agent_perf)
            for agent_name in agent_perf.keys():
                weights[agent_name] = round(equal_weight, 2)

        # Normalize to ensure sum = 1.0
        total_weight = sum(weights.values())
        if total_weight > 0:
            for agent_name in weights:
                weights[agent_name] = round(weights[agent_name] / total_weight, 2)

        learning_state['learning_weights'] = weights

        self.log(f"  Weights: {weights}")

    def calculate_trend_metrics(
        self,
        learning_state: Dict[str, Any],
        consensus: Dict[str, Any]
    ) -> None:
        """
        Calculate trend metrics over time.

        Args:
            learning_state: Current learning state
            consensus: Consensus data from Batch 22
        """
        self.log("Calculating trend metrics")

        # For now, use simple metrics from current consensus
        # In future runs, this will incorporate historical data

        issues = consensus.get('issues', [])
        total_issues = len(issues)

        # Calculate error rate (proportion of high severity issues)
        high_severity_count = sum(
            1 for issue in issues
            if issue.get('severity') == 'high'
        )
        error_rate = high_severity_count / total_issues if total_issues > 0 else 0.0

        # Calculate consensus score (average confidence)
        consensus_scores = [
            issue.get('confidence', 0.0) for issue in issues
        ]
        consensus_mean = (
            sum(consensus_scores) / len(consensus_scores)
            if consensus_scores else 0.0
        )

        # Update trend metrics
        trends = learning_state['trend_metrics']

        # Simple running average for now
        run_count = learning_state['run_count']
        if run_count > 0:
            alpha = 1.0 / (run_count + 1)  # Decay factor
            trends['error_rate_mean'] = (
                (1 - alpha) * trends['error_rate_mean'] + alpha * error_rate
            )
            trends['consensus_mean'] = (
                (1 - alpha) * trends['consensus_mean'] + alpha * consensus_mean
            )
        else:
            trends['error_rate_mean'] = error_rate
            trends['consensus_mean'] = consensus_mean

        # Determine trend direction
        if run_count > 0:
            if consensus_mean > trends['consensus_mean'] * 1.05:
                trends['consensus_trend'] = "up"
            elif consensus_mean < trends['consensus_mean'] * 0.95:
                trends['consensus_trend'] = "down"
            else:
                trends['consensus_trend'] = "flat"
        else:
            trends['consensus_trend'] = "flat"

        # Standard deviation (simplified)
        trends['error_rate_std'] = round(error_rate * 0.1, 2)

        self.log(f"  Error rate: {trends['error_rate_mean']:.3f}")
        self.log(f"  Consensus: {trends['consensus_mean']:.3f} ({trends['consensus_trend']})")

    def generate_recommendations(
        self,
        learning_state: Dict[str, Any]
    ) -> None:
        """
        Generate actionable recommendations based on learning state.

        Args:
            learning_state: Current learning state
        """
        self.log("Generating recommendations")

        recommendations = []

        # Check for recurring critical issues
        critical_issues = [
            issue for issue in learning_state['issue_history']
            if issue['occurrences'] >= 3 and issue['severity'] == 'high'
        ]

        if critical_issues:
            recommendations.append(
                f"Critical issue recurring {len(critical_issues)} time(s): address immediately"
            )

        # Check for low-performing agents
        agent_perf = learning_state['agent_performance']
        low_performers = [
            name for name, perf in agent_perf.items()
            if perf['accuracy'] < 0.6 and perf['runs'] >= 3
        ]

        if low_performers:
            for agent in low_performers:
                recommendations.append(
                    f"{agent} shows lower agreement stability — reduce weight"
                )

        # Check error rate trend
        trends = learning_state['trend_metrics']
        if trends['error_rate_mean'] > 0.15:
            recommendations.append(
                "High error rate detected — review agent configurations"
            )

        # Check consensus trend
        if trends['consensus_trend'] == 'down':
            recommendations.append(
                "Consensus quality declining — investigate agent disagreements"
            )

        if not recommendations:
            recommendations.append("System operating within normal parameters")

        learning_state['recommendations'] = recommendations

        for i, rec in enumerate(recommendations, 1):
            self.log(f"  {i}. {rec}")

    def update(self) -> Dict[str, Any]:
        """
        Main update cycle: process consensus and update learning state.

        Returns:
            Updated learning state

        Raises:
            FileNotFoundError: If consensus file is missing
            json.JSONDecodeError: If files are malformed
        """
        self.log("=" * 60)
        self.log("Starting learning engine update cycle")
        self.log("=" * 60)

        # Load inputs
        consensus = self.load_consensus()
        learning_state = self.load_learning_state()

        # Initialize if needed
        if learning_state is None:
            learning_state = self.initialize_learning_state()

        # Increment run count
        learning_state['run_count'] += 1
        learning_state['generated_at'] = datetime.utcnow().isoformat() + "Z"

        self.log(f"Processing run #{learning_state['run_count']}")

        # Update learning state
        self.update_issue_history(learning_state, consensus)
        self.update_agent_performance(learning_state, consensus)
        self.calculate_learning_weights(learning_state)
        self.calculate_trend_metrics(learning_state, consensus)
        self.generate_recommendations(learning_state)

        # Save updated state
        self.save_learning_state(learning_state)

        self.log("=" * 60)
        self.log("Learning engine update complete")
        self.log("=" * 60)

        return learning_state

    def save_learning_state(self, learning_state: Dict[str, Any]) -> None:
        """
        Save learning state to disk.

        Args:
            learning_state: Learning state to save
        """
        self.log(f"Saving learning state to {self.learning_path}")

        # Ensure state directory exists
        self.state_dir.mkdir(parents=True, exist_ok=True)

        with open(self.learning_path, 'w') as f:
            json.dump(learning_state, f, indent=2)

        self.log(f"Saved learning state (run {learning_state['run_count']})")


def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Hands-Off Learning Engine (Batch 23)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python3 ai/ho_learning_engine.py
  python3 ai/ho_learning_engine.py --verbose
  python3 ai/ho_learning_engine.py --state-dir /custom/path
        """
    )

    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Enable verbose logging'
    )

    parser.add_argument(
        '--state-dir',
        default='state',
        help='Directory containing state files (default: state)'
    )

    args = parser.parse_args()

    try:
        engine = LearningEngine(
            state_dir=args.state_dir,
            verbose=args.verbose
        )

        learning_state = engine.update()

        # Print summary
        print("\n" + "=" * 60)
        print("LEARNING ENGINE SUMMARY")
        print("=" * 60)
        print(f"Run count: {learning_state['run_count']}")
        print(f"Total issues tracked: {len(learning_state['issue_history'])}")
        print(f"Active agents: {len(learning_state['agent_performance'])}")
        print()
        print("Learning weights:")
        for agent, weight in learning_state['learning_weights'].items():
            print(f"  {agent}: {weight:.2f}")
        print()
        print("Recommendations:")
        for i, rec in enumerate(learning_state['recommendations'], 1):
            print(f"  {i}. {rec}")
        print("=" * 60)

        return 0

    except FileNotFoundError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 1
    except json.JSONDecodeError as e:
        print(f"ERROR: Invalid JSON: {e}", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr)
        if args.verbose:
            import traceback
            traceback.print_exc()
        return 1


if __name__ == '__main__':
    sys.exit(main())
