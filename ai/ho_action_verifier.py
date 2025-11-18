#!/usr/bin/env python3
"""
Hands-Off Engine: Action Verifier (Batch 21)
=============================================

This module evaluates the results of executed actions from the Policy Executor
(Batch 20) and produces structured feedback for the Policy Brain (Batch 19).

Key Features:
- DRYRUN-only, no network calls
- File operations restricted to state/ directory
- Graceful error handling for missing/malformed input
- Comprehensive anomaly detection
- Actionable recommendations

Input:  state/brain_actions.json
Output: state/brain_feedback.json
"""

import json
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional


class ActionVerifier:
    """
    Evaluates action execution results and generates structured feedback.

    This class implements the feedback loop for the Hands-Off Engine,
    analyzing action outcomes and providing recommendations for improvement.
    """

    # Known action types that should be supported
    KNOWN_ACTION_TYPES = {
        "health-check",
        "polymarket-fetch",
        "data-sync",
        "risk-calculation",
        "position-update",
        "market-analysis"
    }

    # Status values that indicate successful execution
    SUCCESS_STATUSES = {"success", "completed", "ok"}

    # Status values that indicate failure
    FAILURE_STATUSES = {"failed", "error", "timeout", "rejected"}

    # Status value that indicates stubbed/placeholder execution
    STUB_STATUS = "stubbed"

    def __init__(self, actions_file: str = "state/brain_actions.json",
                 output_file: str = "state/brain_feedback.json",
                 verbose: bool = False):
        """
        Initialize the Action Verifier.

        Args:
            actions_file: Path to input file with action results
            output_file: Path to output file for feedback
            verbose: Enable verbose logging
        """
        self.actions_file = Path(actions_file)
        self.output_file = Path(output_file)
        self.verbose = verbose

        self.actions_data: Optional[Dict[str, Any]] = None
        self.feedback: Dict[str, Any] = {}

    def log(self, message: str) -> None:
        """Log message if verbose mode is enabled."""
        if self.verbose:
            print(f"[ActionVerifier] {message}")

    def load_actions(self) -> bool:
        """
        Load action execution results from brain_actions.json.

        Returns:
            True if loaded successfully, False otherwise
        """
        self.log(f"Loading actions from {self.actions_file}")

        if not self.actions_file.exists():
            self.log(f"WARNING: Actions file not found: {self.actions_file}")
            self.actions_data = {"actions": []}
            return False

        try:
            with open(self.actions_file, 'r') as f:
                self.actions_data = json.load(f)

            # Validate structure
            if not isinstance(self.actions_data, dict):
                self.log("ERROR: Actions file is not a JSON object")
                self.actions_data = {"actions": []}
                return False

            # Ensure actions list exists
            if "actions" not in self.actions_data:
                self.log("WARNING: No 'actions' field in data, using empty list")
                self.actions_data["actions"] = []

            self.log(f"Loaded {len(self.actions_data.get('actions', []))} actions")
            return True

        except json.JSONDecodeError as e:
            self.log(f"ERROR: Malformed JSON in {self.actions_file}: {e}")
            self.actions_data = {"actions": []}
            return False
        except Exception as e:
            self.log(f"ERROR: Failed to load {self.actions_file}: {e}")
            self.actions_data = {"actions": []}
            return False

    def verify_actions(self) -> Dict[str, Any]:
        """
        Analyze all actions and compute metrics.

        Returns:
            Dictionary with verification results and metrics
        """
        if self.actions_data is None:
            self.load_actions()

        actions = self.actions_data.get("actions", [])

        total = len(actions)
        successful = 0
        failed = 0
        stubbed = 0
        unknown_types = set()
        issues = []
        failure_reasons = []

        self.log(f"Verifying {total} actions")

        for idx, action in enumerate(actions):
            action_id = action.get("id", f"action-{idx}")
            action_type = action.get("type", "unknown")
            status = action.get("status", "unknown")

            # Check for unknown action types
            if action_type not in self.KNOWN_ACTION_TYPES and action_type != "unknown":
                unknown_types.add(action_type)
                issues.append(f"Unknown action type: {action_type}")
                self.log(f"  Action {action_id}: unknown type '{action_type}'")

            # Count status categories
            if status in self.SUCCESS_STATUSES:
                successful += 1
                self.log(f"  Action {action_id}: SUCCESS")
            elif status in self.FAILURE_STATUSES:
                failed += 1
                error_msg = action.get("error", action.get("message", "Unknown error"))
                issues.append(f"Action '{action_id}' ({action_type}) failed: {error_msg}")
                failure_reasons.append(f"{action_type}: {error_msg}")
                self.log(f"  Action {action_id}: FAILED - {error_msg}")
            elif status == self.STUB_STATUS:
                stubbed += 1
                self.log(f"  Action {action_id}: STUBBED")
            else:
                # Unknown status - treat as potential issue
                issues.append(f"Action '{action_id}' has unknown status: {status}")
                self.log(f"  Action {action_id}: UNKNOWN STATUS '{status}'")

        # Calculate success rate
        if total > 0:
            # Don't count stubs as failures for success rate
            actual_executions = total - stubbed
            if actual_executions > 0:
                success_rate = successful / actual_executions
            else:
                success_rate = 1.0 if stubbed > 0 else 0.0
        else:
            success_rate = 1.0  # No actions = no failures

        results = {
            "success_rate": round(success_rate, 3),
            "total": total,
            "successful": successful,
            "failed": failed,
            "stubbed": stubbed,
            "unknown_types": sorted(list(unknown_types)),
            "issues": issues,
            "failure_reasons": failure_reasons
        }

        self.log(f"Verification complete: {success_rate:.1%} success rate")
        return results

    def detect_anomalies(self, verification_results: Dict[str, Any]) -> List[str]:
        """
        Detect anomalies in action execution patterns.

        Args:
            verification_results: Results from verify_actions()

        Returns:
            List of detected anomalies
        """
        anomalies = []

        # Check for high stub usage
        if verification_results["stubbed"] > 0:
            stub_ratio = verification_results["stubbed"] / verification_results["total"]
            if stub_ratio >= 0.5:
                anomalies.append(
                    f"High stub usage: {verification_results['stubbed']}/{verification_results['total']} "
                    f"({stub_ratio:.1%}) actions are stubbed"
                )

        # Check for high failure rate
        if verification_results["total"] > 0:
            fail_ratio = verification_results["failed"] / verification_results["total"]
            if fail_ratio >= 0.3:
                anomalies.append(
                    f"High failure rate: {verification_results['failed']}/{verification_results['total']} "
                    f"({fail_ratio:.1%}) actions failed"
                )

        # Check for unknown action types
        if verification_results["unknown_types"]:
            anomalies.append(
                f"Unknown action types detected: {', '.join(verification_results['unknown_types'])}"
            )

        # Check for complete failure (all actions failed)
        if verification_results["total"] > 0 and verification_results["successful"] == 0:
            if verification_results["stubbed"] < verification_results["total"]:
                anomalies.append("CRITICAL: All non-stub actions failed")

        # Check for stale data
        if self.actions_data:
            generated_at = self.actions_data.get("generated_at")
            if generated_at:
                try:
                    # Simple staleness check - could be enhanced
                    anomalies.append(f"Data timestamp: {generated_at}")
                except Exception:
                    pass

        self.log(f"Detected {len(anomalies)} anomalies")
        return anomalies

    def generate_recommendations(self,
                                verification_results: Dict[str, Any],
                                anomalies: List[str]) -> List[str]:
        """
        Generate actionable recommendations based on results and anomalies.

        Args:
            verification_results: Results from verify_actions()
            anomalies: Anomalies from detect_anomalies()

        Returns:
            List of recommendations
        """
        recommendations = []

        # Recommendations for stubs
        if verification_results["stubbed"] > 0:
            recommendations.append(
                "Consider implementing real modules for stubbed actions to improve system capability"
            )
            if verification_results["stubbed"] >= 3:
                recommendations.append(
                    "High stub count detected - prioritize implementing core action types"
                )

        # Recommendations for failures
        if verification_results["failed"] > 0:
            recommendations.append(
                "Review failure reasons and add error handling or retry logic"
            )
            if verification_results["failure_reasons"]:
                # Group similar failures
                unique_failure_types = set()
                for reason in verification_results["failure_reasons"]:
                    action_type = reason.split(":")[0] if ":" in reason else "unknown"
                    unique_failure_types.add(action_type)

                recommendations.append(
                    f"Focus on fixing failures in: {', '.join(sorted(unique_failure_types))}"
                )

        # Recommendations for unknown types
        if verification_results["unknown_types"]:
            recommendations.append(
                f"Register action types in verifier: {', '.join(verification_results['unknown_types'])}"
            )

        # General recommendations
        if verification_results["total"] == 0:
            recommendations.append(
                "No actions executed - verify Policy Brain and Executor are working correctly"
            )
        elif verification_results["success_rate"] < 0.5:
            recommendations.append(
                "Success rate below 50% - system stability needs immediate attention"
            )
        elif verification_results["success_rate"] == 1.0 and verification_results["total"] > 0:
            recommendations.append(
                "All actions successful - system operating normally"
            )

        # Add file-specific recommendations
        if not self.actions_file.exists():
            recommendations.append(
                f"Create {self.actions_file} by running Policy Executor (Batch 20)"
            )

        self.log(f"Generated {len(recommendations)} recommendations")
        return recommendations

    def generate_feedback(self) -> Dict[str, Any]:
        """
        Generate complete feedback structure.

        Returns:
            Complete feedback dictionary ready for JSON serialization
        """
        # Verify actions
        verification_results = self.verify_actions()

        # Detect anomalies
        anomalies = self.detect_anomalies(verification_results)

        # Generate recommendations
        recommendations = self.generate_recommendations(verification_results, anomalies)

        # Build feedback structure
        feedback = {
            "generated_at": datetime.utcnow().isoformat() + "Z",
            "source": str(self.actions_file),
            "success_rate": verification_results["success_rate"],
            "summary": {
                "actions_total": verification_results["total"],
                "actions_successful": verification_results["successful"],
                "actions_failed": verification_results["failed"],
                "stub_count": verification_results["stubbed"],
                "unknown_types": verification_results["unknown_types"]
            },
            "issues": verification_results["issues"],
            "anomalies": anomalies,
            "recommendations": recommendations
        }

        self.feedback = feedback
        return feedback

    def save_feedback(self) -> bool:
        """
        Save feedback to output file.

        Returns:
            True if saved successfully, False otherwise
        """
        if not self.feedback:
            self.log("No feedback to save - generating first")
            self.generate_feedback()

        try:
            # Ensure output directory exists
            self.output_file.parent.mkdir(parents=True, exist_ok=True)

            self.log(f"Saving feedback to {self.output_file}")

            with open(self.output_file, 'w') as f:
                json.dump(self.feedback, f, indent=2)

            self.log(f"Feedback saved successfully ({os.path.getsize(self.output_file)} bytes)")
            return True

        except Exception as e:
            self.log(f"ERROR: Failed to save feedback: {e}")
            return False

    def run(self) -> int:
        """
        Execute the complete verification workflow.

        Returns:
            Exit code (0 = success, 1 = failure)
        """
        self.log("=" * 60)
        self.log("Hands-Off Engine: Action Verifier (Batch 21)")
        self.log("=" * 60)

        try:
            # Load actions
            loaded = self.load_actions()

            # Generate feedback (works even if loading failed)
            feedback = self.generate_feedback()

            # Save feedback
            saved = self.save_feedback()

            # Display summary
            self.log("")
            self.log("Summary:")
            self.log(f"  Actions Analyzed: {feedback['summary']['actions_total']}")
            self.log(f"  Success Rate: {feedback['success_rate']:.1%}")
            self.log(f"  Issues Found: {len(feedback['issues'])}")
            self.log(f"  Recommendations: {len(feedback['recommendations'])}")
            self.log("")

            if saved:
                self.log(f"Feedback written to: {self.output_file}")
                return 0
            else:
                self.log("Failed to save feedback")
                return 1

        except Exception as e:
            self.log(f"FATAL ERROR: {e}")
            import traceback
            if self.verbose:
                traceback.print_exc()
            return 1


def main():
    """CLI entry point."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Hands-Off Engine: Action Verifier (Batch 21)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python3 ai/ho_action_verifier.py
  python3 ai/ho_action_verifier.py --verbose
  python3 ai/ho_action_verifier.py --input custom_actions.json --output custom_feedback.json
        """
    )

    parser.add_argument(
        "--input",
        default="state/brain_actions.json",
        help="Input file with action results (default: state/brain_actions.json)"
    )

    parser.add_argument(
        "--output",
        default="state/brain_feedback.json",
        help="Output file for feedback (default: state/brain_feedback.json)"
    )

    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Enable verbose logging"
    )

    args = parser.parse_args()

    # Create verifier and run
    verifier = ActionVerifier(
        actions_file=args.input,
        output_file=args.output,
        verbose=args.verbose
    )

    exit_code = verifier.run()
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
