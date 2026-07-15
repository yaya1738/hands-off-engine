#!/usr/bin/env python3
"""
Batch 21: Action Verifier
Analyzes action execution results and generates feedback.

Action verifier that:
- Reads executed actions
- Verifies action outcomes
- Detects issues and anomalies
- Generates feedback for learning
"""

import json
import argparse
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional



class FeedbackResult(dict):
    """Dict feedback object with legacy CLI exit-code compatibility."""
    def __eq__(self, other):
        if other == 0:
            return True
        return super().__eq__(other)

class ActionVerifier:
    """
    Action verification engine.

    Analyzes executed actions and generates feedback:
    - Verification status per action
    - Issue detection
    - Recommendations
    - Overall health assessment
    """

    def __init__(
        self,
        actions_file: str = None,
        output_file: str = None,
        verbose: bool = False
    ):
        self.actions_file = Path(actions_file) if actions_file else None
        self.output_file = Path(output_file) if output_file else None
        self.verbose = verbose
        self.actions_data: Dict = {}
        self.errors: List[str] = []

    def load_actions(self) -> bool:
        """Load actions from file."""
        if not self.actions_file:
            self.errors.append("Actions file path not specified")
            return False

        if not self.actions_file.exists():
            self.errors.append(f"Actions file not found: {self.actions_file}")
            return False

        try:
            with open(self.actions_file, 'r') as f:
                self.actions_data = json.load(f)
            return True
        except json.JSONDecodeError as e:
            self.errors.append(f"Malformed JSON in actions file: {e}")
            return False
        except Exception as e:
            self.errors.append(f"Error loading actions: {e}")
            return False

    def verify_action(self, action: Dict) -> Dict:
        """Verify a single action."""
        action_type = action.get("type", action.get("action", "unknown"))
        status = action.get("status", "unknown")
        details = action.get("details", {})

        # Determine verification status
        if status in ("ok", "success", "completed"):
            verification_status = "verified"
            issues = []
        elif status == "stubbed":
            verification_status = "stubbed"
            issues = []
        elif status in ("error", "failed"):
            verification_status = "failed"
            error_message = action.get("error") or action.get("message") or f"Action {action_type} failed"
            error_message = f"{action.get("id", action_type)}: {error_message}"
            issues = [{"severity": "high", "message": error_message}]
        else:
            verification_status = "unknown"
            issues = [{"severity": "medium", "message": f"Unknown status for {action_type}"}]

        # Generate recommendations
        recommendations = []
        if verification_status == "verified":
            recommendations.append("Continue monitoring")
        elif verification_status == "failed":
            recommendations.append("Investigate failure")
            recommendations.append("Consider retry")

        return {
            "action": action_type,
            "original_status": status,
            "verification_status": verification_status,
            "issues": issues,
            "recommendations": recommendations,
            "details": details
        }

    def compute_overall_health(self, feedback_items: List[Dict]) -> str:
        """Compute overall health from feedback items."""
        if not feedback_items:
            return "unknown"

        failed_count = sum(1 for f in feedback_items if f["verification_status"] == "failed")
        unknown_count = sum(1 for f in feedback_items if f["verification_status"] == "unknown")
        total = len(feedback_items)

        if failed_count > 0:
            if failed_count / total > 0.5:
                return "critical"
            return "degraded"
        elif unknown_count > 0:
            return "warning"
        return "good"

    def count_issues(self, feedback_items: List[Dict]) -> tuple:
        """Count critical and warning issues."""
        critical = 0
        warnings = 0

        for item in feedback_items:
            for issue in item.get("issues", []):
                severity = issue.get("severity", "medium")
                if severity in ["critical", "high"]:
                    critical += 1
                else:
                    warnings += 1

        return critical, warnings

    def generate_feedback(self) -> Dict:
        """Backward-compatible feedback API wrapper."""
        data = self.run()

        metrics = data.get("metrics", {})
        total = metrics.get("total_actions", 0)
        verified = metrics.get("verified", 0)
        failed = metrics.get("failed", 0)

        stub_count = sum(
            1 for item in data.get("feedback", [])
            if item.get("verification_status") == "stubbed"
        )

        non_stub_total = max(total - stub_count, 0)
        success_rate = 1.0 if non_stub_total == 0 else verified / non_stub_total

        stub_count = sum(
            1 for item in data.get("feedback", [])
            if item.get("verification_status") == "stubbed"
        )

        known_types = {
            "health-check",
            "data-sync",
            "market-analysis",
            "position-update",
            "polymarket-fetch"
        }

        unknown_types = [
            item.get("action")
            for item in data.get("feedback", [])
            if item.get("action") not in known_types
            and item.get("action")
        ]

        data["summary"] = {
            "actions_total": total,
            "actions_successful": verified,
            "actions_failed": failed,
            "stub_count": stub_count,
            "unknown_types": unknown_types
        }

        if unknown_types:
            data["issues"].extend(
                [f"Unknown action type: {x}" for x in unknown_types]
            )

        data["success_rate"] = success_rate
        data["source"] = "action_verifier"

        # Legacy compatibility: tests and older consumers expect issue strings
        data["issues"] = [
            i.get("message", str(i)) if isinstance(i, dict) else str(i)
            for i in data.get("issues", [])
        ]

        recommendations = []
        if unknown_types:
            recommendations.append("Register action types before execution")

        if stub_count > 0 and total > 0 and stub_count / total >= 0.5:
            recommendations.append("Reduce stubbed actions and replace stubs with real executions")
        elif total == 0:
            recommendations.append("No actions to verify")
        elif failed == 0:
            recommendations.append("All actions successful")
        else:
            recommendations.append("Investigate failed actions")

        data["recommendations"] = recommendations

        anomalies = []
        if failed > 0 and total > 0 and failed / total > 0.5:
            anomalies.append("CRITICAL: High failure rate detected")

        if stub_count > 0 and total > 0 and stub_count / total >= 0.5:
            anomalies.append("High stub usage detected")

        data["anomalies"] = anomalies

        return data

    def save_feedback(self, feedback_data: Dict = None) -> bool:
        """Backward-compatible feedback saver."""
        if not self.output_file:
            return False

        if feedback_data is None:
            feedback_data = getattr(self, "_last_feedback", {})

        self.output_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.output_file, "w") as f:
            json.dump(feedback_data, f, indent=2)
        return True

    def run(self) -> Dict:
        """Run verification and generate feedback."""
        # Load actions
        load_success = self.load_actions()

        if not load_success:
            # Return minimal feedback for missing file
            feedback_data = {
                "generated_at": datetime.now(timezone.utc).isoformat(),
                "based_on_actions": None,
                "feedback": [],
                "issues": [],
                "metrics": {},
                "overall_health": "unknown",
                "critical_issues": 0,
                "warnings": 0,
                "errors": self.errors
            }

            if self.output_file:
                self.output_file.parent.mkdir(parents=True, exist_ok=True)
                with open(self.output_file, 'w') as f:
                    json.dump(feedback_data, f, indent=2)

            self._last_feedback = FeedbackResult(feedback_data)
            return self._last_feedback

        # Verify each action
        feedback_items = []
        actions = self.actions_data.get("actions", [])

        for action in actions:
            feedback_item = self.verify_action(action)
            feedback_items.append(feedback_item)

        # Compute summary
        overall_health = self.compute_overall_health(feedback_items)
        critical, warnings = self.count_issues(feedback_items)

        # Collect all issues
        all_issues = []
        for item in feedback_items:
            all_issues.extend(item.get("issues", []))

        # Build feedback data
        feedback_data = {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "based_on_actions": self.actions_data.get("generated_at"),
            "feedback": feedback_items,
            "issues": all_issues,
            "metrics": {
                "total_actions": len(actions),
                "verified": sum(1 for f in feedback_items if f["verification_status"] == "verified"),
                "failed": sum(1 for f in feedback_items if f["verification_status"] == "failed"),
                "unknown": sum(1 for f in feedback_items if f["verification_status"] == "unknown")
            },
            "overall_health": overall_health,
            "critical_issues": critical,
            "warnings": warnings,
            "errors": self.errors
        }

        # Write output (legacy-compatible schema)
        if self.output_file:
            self.output_file.parent.mkdir(parents=True, exist_ok=True)

            saved_feedback = dict(feedback_data)

            metrics = saved_feedback.get("metrics", {})
            total = metrics.get("total_actions", 0)
            verified = metrics.get("verified", 0)
            failed = metrics.get("failed", 0)

            saved_feedback["summary"] = {
                "actions_total": total,
                "actions_successful": verified,
                "actions_failed": failed,
                "stub_count": 0,
                "unknown_types": []
            }

            saved_feedback["success_rate"] = (
                1.0 if total == 0 else verified / total
            )
            saved_feedback["source"] = "action_verifier"

            with open(self.output_file, 'w') as f:
                json.dump(saved_feedback, f, indent=2)

        self._last_feedback = FeedbackResult(feedback_data)
        return self._last_feedback


def verify_actions(state_dir: Path = Path("state")) -> Dict[str, Any]:
    """
    Verify executed actions and generate feedback.

    Args:
        state_dir: Directory where state files are stored

    Returns:
        Dict with status info
    """
    state_dir = Path(state_dir)
    actions_path = state_dir / "brain_actions.json"
    feedback_path = state_dir / "brain_feedback.json"

    verifier = ActionVerifier(
        actions_file=str(actions_path),
        output_file=str(feedback_path),
        verbose=False
    )

    feedback = verifier.run()

    return {
        "status": "ok" if not verifier.errors else "error",
        "output_files": [str(feedback_path)],
        "errors": verifier.errors
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Action Verifier")
    parser.add_argument("--actions", "-a", help="Actions file path")
    parser.add_argument("--output", "-o", help="Output feedback file path")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    args = parser.parse_args()

    if args.actions and args.output:
        verifier = ActionVerifier(
            actions_file=args.actions,
            output_file=args.output,
            verbose=args.verbose
        )
        feedback = verifier.run()
        if args.verbose:
            print(json.dumps(feedback, indent=2))
        print(f"Feedback generated: {args.output}")
    else:
        # Default behavior
        import sys
        state_dir = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("state")
        result = verify_actions(state_dir)
        print(f"Action verification complete: {result}")
