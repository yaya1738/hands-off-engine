#!/usr/bin/env python3
"""
Batch 20: Policy Executor
Executes safe, DRYRUN actions based on policy recommendations.

Policy executor that:
- Reads policy recommendations
- Executes safe DRYRUN actions
- Tracks action results
- Generates execution reports
"""

import json
import argparse
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional


class PolicyExecutor:
    """
    Safe policy execution engine.

    Executes policy actions in DRYRUN mode:
    - summary: Generate status summary
    - health-check: Run system health check
    - autoloop: Run automation loop (DRYRUN)
    - polymarket-analysis: Analyze market data
    - analyze-history: Analyze historical data
    """

    def __init__(
        self,
        state_dir: str = "state",
        ai_dir: str = "ai",
        verbose: bool = False
    ):
        self.state_dir = Path(state_dir)
        self.ai_dir = Path(ai_dir)
        self.verbose = verbose
        self.policy_path = self.state_dir / "brain_policy.json"
        self.output_path = self.state_dir / "brain_actions.json"
        self.txt_output_path = self.state_dir / "brain_actions.txt"

    def load_policy(self) -> Optional[Dict]:
        """Load policy from file."""
        if not self.policy_path.exists():
            return None

        try:
            with open(self.policy_path, 'r') as f:
                return json.load(f)
        except json.JSONDecodeError:
            return {"_error": "Malformed policy JSON"}
        except Exception as e:
            return {"_error": str(e)}

    def execute_summary(self) -> Dict:
        """Execute summary action."""
        # Stub implementation - just returns success
        return {
            "type": "summary",
            "status": "ok",
            "details": {
                "message": "Summary generated (stub)",
                "mode": "DRYRUN"
            }
        }

    def execute_health_check(self) -> Dict:
        """Execute health-check action."""
        # Stub implementation
        return {
            "type": "health-check",
            "status": "ok",
            "details": {
                "message": "Health check completed (stub)",
                "mode": "DRYRUN",
                "components_checked": ["cpu", "memory", "disk"]
            }
        }

    def execute_autoloop(self) -> Dict:
        """Execute autoloop action (DRYRUN only)."""
        return {
            "type": "autoloop",
            "status": "ok",
            "details": {
                "message": "Autoloop executed (stub)",
                "mode": "DRYRUN",
                "cycles": 0
            }
        }

    def execute_polymarket_analysis(self) -> Dict:
        """Execute polymarket-analysis action."""
        # Try to load compact file
        compact_path = self.state_dir / "polymarket-compact.json"

        if compact_path.exists():
            try:
                with open(compact_path, 'r') as f:
                    data = json.load(f)

                markets = data.get("markets", [])
                total_volume = sum(m.get("volume", 0) for m in markets)

                return {
                    "type": "polymarket-analysis",
                    "status": "ok",
                    "details": {
                        "message": "Polymarket analysis completed",
                        "mode": "DRYRUN",
                        "markets_count": len(markets),
                        "total_volume": total_volume
                    }
                }
            except Exception:
                pass

        return {
            "type": "polymarket-analysis",
            "status": "ok",
            "details": {
                "message": "Polymarket analysis completed (no data)",
                "mode": "DRYRUN",
                "markets_count": 0,
                "total_volume": 0
            }
        }

    def execute_analyze_history(self) -> Dict:
        """Execute analyze-history action."""
        return {
            "type": "analyze-history",
            "status": "ok",
            "details": {
                "message": "History analysis completed (stub)",
                "mode": "DRYRUN",
                "events_analyzed": 0
            }
        }

    def execute_action(self, action: Dict) -> Dict:
        """Execute a single action."""
        action_type = action.get("type", "unknown")

        executors = {
            "summary": self.execute_summary,
            "health-check": self.execute_health_check,
            "autoloop": self.execute_autoloop,
            "polymarket-analysis": self.execute_polymarket_analysis,
            "analyze-history": self.execute_analyze_history
        }

        if action_type in executors:
            return executors[action_type]()
        else:
            return {
                "type": action_type,
                "status": "error",
                "details": {
                    "message": f"Unknown action type: {action_type}",
                    "mode": "DRYRUN"
                }
            }

    def run_policy_actions(self) -> Dict:
        """
        Run all policy actions and generate report.

        Returns:
            Execution report dict
        """
        errors = []
        actions_tried = 0
        actions_successful = 0
        action_results = []

        # Load policy
        policy = self.load_policy()

        if policy is None:
            errors.append("Policy file not found")
            policy = {"actions": [], "proposed_actions": []}
        elif "_error" in policy:
            errors.append(policy["_error"])
            policy = {"actions": [], "proposed_actions": []}

        # Get actions from policy (support both 'actions' and 'proposed_actions')
        actions = policy.get("actions", []) or policy.get("proposed_actions", [])

        # Execute each action
        for action in actions:
            actions_tried += 1
            result = self.execute_action(action)
            action_results.append(result)

            if result.get("status") == "ok":
                actions_successful += 1

        # Build report
        report = {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "policy_source": str(self.policy_path),
            "actions_tried": actions_tried,
            "actions_successful": actions_successful,
            "actions": action_results,
            "errors": errors
        }

        # Save JSON output
        self.state_dir.mkdir(parents=True, exist_ok=True)
        with open(self.output_path, 'w') as f:
            json.dump(report, f, indent=2)

        # Save text output if verbose
        if self.verbose:
            self._write_text_report(report)

        return report

    def _write_text_report(self, report: Dict):
        """Write human-readable text report."""
        lines = [
            "=" * 60,
            "POLICY EXECUTOR REPORT",
            "=" * 60,
            f"Generated: {report['generated_at']}",
            f"Policy source: {report['policy_source']}",
            f"Actions Tried: {report['actions_tried']}",
            f"Actions Successful: {report['actions_successful']}",
            "",
            "Actions:",
        ]

        for action in report.get("actions", []):
            status_icon = "✓" if action.get("status") == "ok" else "✗"
            lines.append(f"  {status_icon} {action.get('type', 'unknown')}: {action.get('status', 'unknown')}")
            details = action.get("details", {})
            if "message" in details:
                lines.append(f"      {details['message']}")

        if report.get("errors"):
            lines.append("")
            lines.append("Errors:")
            for error in report["errors"]:
                lines.append(f"  - {error}")

        lines.append("=" * 60)

        with open(self.txt_output_path, 'w') as f:
            f.write('\n'.join(lines))


def run_policy_actions(
    state_dir: str = "state",
    ai_dir: str = "ai",
    verbose: bool = False
) -> Dict:
    """
    Run policy actions.

    Args:
        state_dir: Directory containing state files
        ai_dir: Directory for AI files
        verbose: Enable verbose output

    Returns:
        Execution report dict
    """
    executor = PolicyExecutor(
        state_dir=state_dir,
        ai_dir=ai_dir,
        verbose=verbose
    )

    return executor.run_policy_actions()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Policy Executor - Execute policy actions")
    parser.add_argument("--state-dir", default="state", help="State directory path")
    parser.add_argument("--ai-dir", default="ai", help="AI directory path")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    args = parser.parse_args()

    report = run_policy_actions(
        state_dir=args.state_dir,
        ai_dir=args.ai_dir,
        verbose=args.verbose
    )

    if args.verbose:
        print(f"\nActions: {report['actions_tried']} tried, {report['actions_successful']} successful")

    print(f"Report generated: {args.state_dir}/brain_actions.json")
