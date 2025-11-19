#!/usr/bin/env python3
"""
Hands-Off Policy Brain v2 - Learning-Weighted Decision Engine

This module integrates consensus reasoning (Batch 22) with learning-based
adaptation (Batch 23) to produce intelligent, self-improving policy decisions.

SAFETY: DRYRUN ONLY - No external calls, no execution, deterministic output.
"""

import json
import sys
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
from dataclasses import dataclass, asdict


@dataclass
class PolicyAction:
    """Represents a single policy action with priority and reasoning."""
    action_type: str
    priority: float  # 0.0 - 1.0
    confidence: str  # "low", "medium", "high"
    reasoning: List[str]
    triggers: List[str]
    recommended_next_step: str
    source_agents: List[str]
    learning_weight: float


class PolicyBrainV2:
    """
    Learning-Weighted Decision Engine

    Combines:
    - Consensus reasoning (multi-agent agreement)
    - Learning state (historical accuracy, trends)

    Produces:
    - Prioritized action policies
    - Learning-weighted recommendations
    - Self-improving decision guidance
    """

    def __init__(self, state_dir: Path = None, verbose: bool = False):
        """
        Initialize Policy Brain v2.

        Args:
            state_dir: Directory containing state files (default: ./state)
            verbose: Enable verbose output
        """
        self.state_dir = state_dir or Path("state")
        self.verbose = verbose
        self.errors: List[str] = []
        self.notes: List[str] = []

    def log(self, message: str, level: str = "INFO"):
        """Log message if verbose mode is enabled."""
        if self.verbose:
            print(f"[{level}] {message}")

    def load_json_file(self, filepath: Path) -> Optional[Dict[str, Any]]:
        """
        Load and validate JSON file.

        Args:
            filepath: Path to JSON file

        Returns:
            Parsed JSON data or None if error
        """
        try:
            if not filepath.exists():
                self.errors.append(f"File not found: {filepath}")
                self.log(f"File not found: {filepath}", "ERROR")
                return None

            with open(filepath, 'r') as f:
                data = json.load(f)

            self.log(f"Loaded {filepath}")
            return data

        except json.JSONDecodeError as e:
            self.errors.append(f"Invalid JSON in {filepath}: {str(e)}")
            self.log(f"Invalid JSON in {filepath}: {str(e)}", "ERROR")
            return None

        except Exception as e:
            self.errors.append(f"Error loading {filepath}: {str(e)}")
            self.log(f"Error loading {filepath}: {str(e)}", "ERROR")
            return None

    def load_consensus_state(self) -> Optional[Dict[str, Any]]:
        """Load brain_consensus.json (Batch 22 output)."""
        return self.load_json_file(self.state_dir / "brain_consensus.json")

    def load_learning_state(self) -> Optional[Dict[str, Any]]:
        """Load brain_learning.json (Batch 23 output)."""
        return self.load_json_file(self.state_dir / "brain_learning.json")

    def compute_learning_weight(
        self,
        agent_name: str,
        learning_state: Dict[str, Any]
    ) -> float:
        """
        Compute learning-based weight for an agent.

        Formula:
            weight = base_weight * accuracy_factor * trend_factor

        Args:
            agent_name: Name of the agent
            learning_state: Learning state data

        Returns:
            Learning weight (0.0 - 1.0)
        """
        try:
            weights = learning_state.get("weights", {})
            agent_weights = weights.get(agent_name, {})

            # Extract components
            base_weight = agent_weights.get("base_weight", 0.5)
            accuracy = agent_weights.get("accuracy", 0.5)
            trend = agent_weights.get("trend", 0.0)

            # Compute accuracy factor (0.5 - 1.5)
            accuracy_factor = 0.5 + accuracy

            # Compute trend factor (0.8 - 1.2)
            # Positive trend increases weight, negative decreases
            trend_factor = 1.0 + (trend * 0.2)
            trend_factor = max(0.8, min(1.2, trend_factor))

            # Final weight
            weight = base_weight * accuracy_factor * trend_factor
            weight = max(0.0, min(1.0, weight))

            self.log(f"Agent {agent_name}: weight={weight:.3f} "
                    f"(base={base_weight:.2f}, acc={accuracy:.2f}, trend={trend:.2f})")

            return weight

        except Exception as e:
            self.log(f"Error computing weight for {agent_name}: {e}", "WARN")
            return 0.5  # Default weight

    def compute_action_priority(
        self,
        action: Dict[str, Any],
        consensus_state: Dict[str, Any],
        learning_state: Dict[str, Any]
    ) -> Tuple[float, List[str]]:
        """
        Compute priority score for an action.

        Factors:
        1. Consensus confidence (agent agreement)
        2. Learning weights (historical accuracy)
        3. Issue recurrence (repeated patterns)
        4. Trend metrics (improving/degrading)

        Args:
            action: Action data from consensus
            consensus_state: Consensus state data
            learning_state: Learning state data

        Returns:
            (priority_score, reasoning_list)
        """
        reasoning = []

        # Factor 1: Consensus confidence (0.0 - 1.0)
        consensus_score = action.get("consensus_score", 0.5)
        reasoning.append(f"Consensus score: {consensus_score:.2f}")

        # Factor 2: Agent learning weights
        agent_names = action.get("agents", [])
        if agent_names:
            weights = [
                self.compute_learning_weight(name, learning_state)
                for name in agent_names
            ]
            avg_weight = sum(weights) / len(weights)
            reasoning.append(f"Avg agent weight: {avg_weight:.2f}")
        else:
            avg_weight = 0.5
            reasoning.append("No agent data, using default weight")

        # Factor 3: Issue recurrence (higher recurrence = higher priority)
        issue_type = action.get("type", "unknown")
        issue_history = learning_state.get("issue_history", {})
        recurrence_count = issue_history.get(issue_type, {}).get("count", 0)
        recurrence_factor = min(1.0, recurrence_count / 10.0)  # Normalize to 0-1
        reasoning.append(f"Recurrence factor: {recurrence_factor:.2f} ({recurrence_count} occurrences)")

        # Factor 4: Trend influence
        trend_metrics = learning_state.get("trend_metrics", {})
        issue_trend = trend_metrics.get(issue_type, {}).get("trend", 0.0)
        # Negative trend (degrading) increases priority
        trend_factor = 1.0 - (issue_trend * 0.2)  # 0.8 - 1.2
        trend_factor = max(0.8, min(1.2, trend_factor))
        reasoning.append(f"Trend factor: {trend_factor:.2f} (trend={issue_trend:.2f})")

        # Combine factors
        # Priority = (consensus * 0.4) + (learning_weight * 0.3) +
        #            (recurrence * 0.2) + (trend * 0.1)
        priority = (
            consensus_score * 0.4 +
            avg_weight * 0.3 +
            recurrence_factor * 0.2 +
            (trend_factor - 0.9) * 10 * 0.1  # Normalize trend to 0-1
        )
        priority = max(0.0, min(1.0, priority))

        reasoning.append(f"FINAL PRIORITY: {priority:.3f}")

        return priority, reasoning

    def determine_confidence(self, priority: float) -> str:
        """
        Determine confidence level based on priority score.

        Args:
            priority: Priority score (0.0 - 1.0)

        Returns:
            Confidence level: "low", "medium", or "high"
        """
        if priority >= 0.7:
            return "high"
        elif priority >= 0.4:
            return "medium"
        else:
            return "low"

    def generate_policy_actions(
        self,
        consensus_state: Dict[str, Any],
        learning_state: Dict[str, Any]
    ) -> List[PolicyAction]:
        """
        Generate prioritized policy actions.

        Args:
            consensus_state: Consensus state data
            learning_state: Learning state data

        Returns:
            List of PolicyAction objects, sorted by priority (descending)
        """
        actions = []

        # Extract recommendations from consensus
        recommendations = consensus_state.get("final_recommendations", [])

        for rec in recommendations:
            # Compute priority
            priority, reasoning = self.compute_action_priority(
                rec, consensus_state, learning_state
            )

            # Determine confidence
            confidence = self.determine_confidence(priority)

            # Extract action details
            action_type = rec.get("type", "unknown")
            triggers = rec.get("triggers", [])
            next_step = rec.get("next_step", "Review and assess")
            source_agents = rec.get("agents", [])

            # Compute average learning weight for this action
            if source_agents:
                weights = [
                    self.compute_learning_weight(name, learning_state)
                    for name in source_agents
                ]
                learning_weight = sum(weights) / len(weights)
            else:
                learning_weight = 0.5

            # Create PolicyAction
            action = PolicyAction(
                action_type=action_type,
                priority=priority,
                confidence=confidence,
                reasoning=reasoning,
                triggers=triggers,
                recommended_next_step=next_step,
                source_agents=source_agents,
                learning_weight=learning_weight
            )

            actions.append(action)

            self.log(f"Generated action: {action_type} (priority={priority:.3f}, confidence={confidence})")

        # Sort by priority (descending)
        actions.sort(key=lambda a: a.priority, reverse=True)

        return actions

    def generate_policy_output(
        self,
        actions: List[PolicyAction],
        consensus_state: Dict[str, Any],
        learning_state: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Generate final policy output JSON.

        Args:
            actions: List of PolicyAction objects
            consensus_state: Consensus state data
            learning_state: Learning state data

        Returns:
            Policy output dictionary
        """
        # Extract weights used
        weights_used = learning_state.get("weights", {})

        # Convert actions to dict format
        actions_list = []
        for action in actions:
            action_dict = {
                "type": action.action_type,
                "priority": round(action.priority, 3),
                "confidence": action.confidence,
                "reasoning": action.reasoning,
                "triggers": action.triggers,
                "recommended_next_step": action.recommended_next_step,
                "source_agents": action.source_agents,
                "learning_weight": round(action.learning_weight, 3)
            }
            actions_list.append(action_dict)

        # Build output
        output = {
            "generated_at": datetime.utcnow().isoformat() + "Z",
            "source_consensus": str(self.state_dir / "brain_consensus.json"),
            "source_learning": str(self.state_dir / "brain_learning.json"),
            "weights_used": weights_used,
            "actions": actions_list,
            "notes": self.notes,
            "errors": self.errors
        }

        return output

    def save_policy_output(self, output: Dict[str, Any]) -> bool:
        """
        Save policy output to brain_policy_v2.json.

        Args:
            output: Policy output dictionary

        Returns:
            True if saved successfully, False otherwise
        """
        try:
            output_path = self.state_dir / "brain_policy_v2.json"

            with open(output_path, 'w') as f:
                json.dump(output, f, indent=2)

            self.log(f"Saved policy output to {output_path}")
            return True

        except Exception as e:
            self.errors.append(f"Error saving output: {str(e)}")
            self.log(f"Error saving output: {str(e)}", "ERROR")
            return False

    def run(self) -> bool:
        """
        Execute the Policy Brain v2 pipeline.

        Returns:
            True if successful, False otherwise
        """
        self.log("=" * 60)
        self.log("POLICY BRAIN V2 - LEARNING-WEIGHTED DECISION ENGINE")
        self.log("=" * 60)

        # Step 1: Load consensus state
        self.log("\n[Step 1] Loading consensus state...")
        consensus_state = self.load_consensus_state()
        if consensus_state is None:
            self.log("Failed to load consensus state", "ERROR")
            return False

        # Step 2: Load learning state
        self.log("\n[Step 2] Loading learning state...")
        learning_state = self.load_learning_state()
        if learning_state is None:
            self.log("Failed to load learning state", "ERROR")
            return False

        # Step 3: Generate policy actions
        self.log("\n[Step 3] Generating policy actions...")
        actions = self.generate_policy_actions(consensus_state, learning_state)
        self.log(f"Generated {len(actions)} policy actions")

        # Step 4: Generate output
        self.log("\n[Step 4] Generating policy output...")
        output = self.generate_policy_output(actions, consensus_state, learning_state)

        # Step 5: Save output
        self.log("\n[Step 5] Saving policy output...")
        success = self.save_policy_output(output)

        if success:
            self.log("\n" + "=" * 60)
            self.log("POLICY BRAIN V2 COMPLETED SUCCESSFULLY")
            self.log("=" * 60)
        else:
            self.log("\n" + "=" * 60)
            self.log("POLICY BRAIN V2 COMPLETED WITH ERRORS")
            self.log("=" * 60)

        return success


def main():
    """CLI entry point for Policy Brain v2."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Hands-Off Policy Brain v2 - Learning-Weighted Decision Engine"
    )
    parser.add_argument(
        "--state-dir",
        type=Path,
        default=Path("state"),
        help="Directory containing state files (default: ./state)"
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable verbose output"
    )

    args = parser.parse_args()

    # Create and run Policy Brain
    brain = PolicyBrainV2(state_dir=args.state_dir, verbose=args.verbose)
    success = brain.run()

    # Exit with appropriate code
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
