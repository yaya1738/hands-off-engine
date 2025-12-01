#!/usr/bin/env python3
"""
Hands-Off Engine: Policy Executor (Batch 20)

DRYRUN-only safe action engine that interprets brain_policy.json and executes
safe system actions without performing trading or dangerous operations.

This is the glue between "what the Policy Brain thinks" and "what the system does."

Safety guarantees:
- DRYRUN ONLY - no real execution
- No network calls
- No Polymarket API calls
- No touching Termux directories
- File-read/write ONLY inside state/ and ai/
"""

import argparse
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional


class PolicyExecutor:
    """
    Safe DRYRUN Policy Executor

    Reads state/brain_policy.json and executes safe actions like:
    - Generating summaries
    - Health checks
    - Autoloop iterations
    - Market analysis
    - History analysis
    """

    def __init__(self, state_dir: str = "state", ai_dir: str = "ai", verbose: bool = False):
        """
        Initialize the Policy Executor.

        Args:
            state_dir: Directory for state files (default: "state")
            ai_dir: Directory for AI modules (default: "ai")
            verbose: Enable verbose output
        """
        self.state_dir = Path(state_dir)
        self.ai_dir = Path(ai_dir)
        self.verbose = verbose
        self.actions_tried = 0
        self.actions_successful = 0
        self.actions: List[Dict[str, Any]] = []
        self.errors: List[str] = []

    def log(self, msg: str) -> None:
        """Log message if verbose mode is enabled."""
        if self.verbose:
            print(f"[PolicyExecutor] {msg}")

    def load_policy(self) -> Optional[Dict[str, Any]]:
        """
        Load the brain policy from state/brain_policy.json.

        Returns:
            Policy dict or None if file doesn't exist or is malformed.
        """
        policy_path = self.state_dir / "brain_policy.json"

        if not policy_path.exists():
            self.log(f"Policy file not found: {policy_path}")
            self.errors.append(f"Policy file not found: {policy_path}")
            return None

        try:
            with open(policy_path, 'r') as f:
                policy = json.load(f)
                self.log(f"Loaded policy from {policy_path}")
                return policy
        except json.JSONDecodeError as e:
            self.log(f"Malformed policy JSON: {e}")
            self.errors.append(f"Malformed policy JSON: {e}")
            return None
        except Exception as e:
            self.log(f"Error loading policy: {e}")
            self.errors.append(f"Error loading policy: {e}")
            return None

    def execute_action_summary(self) -> Dict[str, Any]:
        """
        Execute summary action - generate brain summary report.

        Returns:
            Action result dict with status and details.
        """
        self.log("Executing action: summary")

        try:
            # Try to import and call the brain report module
            try:
                from reports.ho_brain_report import write_brain_summary
                result = write_brain_summary(state_dir=str(self.state_dir), verbose=self.verbose)
                return {
                    "type": "summary",
                    "status": "ok",
                    "details": {
                        "module": "reports.ho_brain_report",
                        "result": result
                    }
                }
            except ImportError:
                # Module doesn't exist yet - stub behavior
                self.log("Brain report module not found - using stub")
                return {
                    "type": "summary",
                    "status": "ok",
                    "details": {
                        "module": "reports.ho_brain_report",
                        "note": "Module not implemented yet - stub execution",
                        "stub": True
                    }
                }
        except Exception as e:
            return {
                "type": "summary",
                "status": "error",
                "details": {
                    "error": str(e)
                }
            }

    def execute_action_health_check(self) -> Dict[str, Any]:
        """
        Execute health-check action - run system health diagnostics.

        Returns:
            Action result dict with status and details.
        """
        self.log("Executing action: health-check")

        try:
            # Try to import and call the health check module
            try:
                from health.ho_healthcheck import write_health_status
                result = write_health_status(state_dir=str(self.state_dir), verbose=self.verbose)
                return {
                    "type": "health-check",
                    "status": "ok",
                    "details": {
                        "module": "health.ho_healthcheck",
                        "result": result
                    }
                }
            except ImportError:
                # Module doesn't exist yet - stub behavior
                self.log("Health check module not found - using stub")
                return {
                    "type": "health-check",
                    "status": "ok",
                    "details": {
                        "module": "health.ho_healthcheck",
                        "note": "Module not implemented yet - stub execution",
                        "stub": True,
                        "health_status": "unknown"
                    }
                }
        except Exception as e:
            return {
                "type": "health-check",
                "status": "error",
                "details": {
                    "error": str(e)
                }
            }

    def execute_action_autoloop(self) -> Dict[str, Any]:
        """
        Execute autoloop action - run one DRYRUN AI loop iteration.

        IMPORTANT: This is DRYRUN only and must not trigger dangerous actions.

        Returns:
            Action result dict with status and details.
        """
        self.log("Executing action: autoloop (DRYRUN)")

        try:
            # Try to import and call the AI loop module
            try:
                from ai.ho_ai_loop import run_once
                result = run_once(state_dir=str(self.state_dir), dryrun=True, verbose=self.verbose)
                return {
                    "type": "autoloop",
                    "status": "ok",
                    "details": {
                        "module": "ai.ho_ai_loop",
                        "mode": "DRYRUN",
                        "result": result
                    }
                }
            except ImportError:
                # Module doesn't exist yet - stub behavior
                self.log("AI loop module not found - using stub")
                return {
                    "type": "autoloop",
                    "status": "ok",
                    "details": {
                        "module": "ai.ho_ai_loop",
                        "mode": "DRYRUN",
                        "note": "Module not implemented yet - stub execution",
                        "stub": True
                    }
                }
        except Exception as e:
            return {
                "type": "autoloop",
                "status": "error",
                "details": {
                    "error": str(e)
                }
            }

    def execute_action_polymarket_analysis(self) -> Dict[str, Any]:
        """
        Execute polymarket-analysis action - safe market data analysis.

        This only reads existing data files and computes basic stats.
        NO API calls, NO trading execution.

        Returns:
            Action result dict with status and details.
        """
        self.log("Executing action: polymarket-analysis (safe)")

        try:
            # Look for polymarket compact summary file
            compact_path = self.state_dir / "polymarket-compact.json"

            if compact_path.exists():
                with open(compact_path, 'r') as f:
                    data = json.load(f)

                # Compute basic stats
                markets_count = len(data.get("markets", []))
                total_volume = sum(m.get("volume", 0) for m in data.get("markets", []))

                return {
                    "type": "polymarket-analysis",
                    "status": "ok",
                    "details": {
                        "markets_count": markets_count,
                        "total_volume": total_volume,
                        "source_file": str(compact_path)
                    }
                }
            else:
                self.log("Polymarket compact file not found")
                return {
                    "type": "polymarket-analysis",
                    "status": "ok",
                    "details": {
                        "note": "No polymarket data file found",
                        "markets_count": 0
                    }
                }
        except Exception as e:
            return {
                "type": "polymarket-analysis",
                "status": "error",
                "details": {
                    "error": str(e)
                }
            }

    def execute_action_analyze_history(self) -> Dict[str, Any]:
        """
        Execute analyze-history action - build historical analysis summary.

        Returns:
            Action result dict with status and details.
        """
        self.log("Executing action: analyze-history")

        try:
            # Try to import and call the history report module
            try:
                from reports.ho_history_report import build_history_summary
                result = build_history_summary(state_dir=str(self.state_dir), verbose=self.verbose)
                return {
                    "type": "analyze-history",
                    "status": "ok",
                    "details": {
                        "module": "reports.ho_history_report",
                        "result": result
                    }
                }
            except ImportError:
                # Module doesn't exist yet - stub behavior
                self.log("History report module not found - using stub")
                return {
                    "type": "analyze-history",
                    "status": "ok",
                    "details": {
                        "module": "reports.ho_history_report",
                        "note": "Module not implemented yet - stub execution",
                        "stub": True
                    }
                }
        except Exception as e:
            return {
                "type": "analyze-history",
                "status": "error",
                "details": {
                    "error": str(e)
                }
            }

    def execute_action(self, action_type: str) -> Dict[str, Any]:
        """
        Execute a single action based on type.

        Args:
            action_type: Type of action to execute

        Returns:
            Action result dict with status and details.
        """
        action_handlers = {
            "summary": self.execute_action_summary,
            "health-check": self.execute_action_health_check,
            "autoloop": self.execute_action_autoloop,
            "polymarket-analysis": self.execute_action_polymarket_analysis,
            "analyze-history": self.execute_action_analyze_history,
        }

        handler = action_handlers.get(action_type)
        if handler:
            return handler()
        else:
            self.log(f"Unknown action type: {action_type}")
            return {
                "type": action_type,
                "status": "error",
                "details": {
                    "error": f"Unknown action type: {action_type}"
                }
            }

    def run_policy_actions(self) -> Dict[str, Any]:
        """
        Main execution function - load policy and execute all actions.

        Returns:
            Complete execution report dict.
        """
        self.log("Starting policy executor")

        # Load the policy
        policy = self.load_policy()

        # If no policy or empty policy, return no-op result
        if not policy or not policy.get("actions"):
            self.log("No policy actions to execute")
            result = {
                "generated_at": datetime.now(timezone.utc).isoformat(),
                "policy_source": str(self.state_dir / "brain_policy.json"),
                "actions_tried": 0,
                "actions_successful": 0,
                "actions": [],
                "errors": self.errors
            }
            self.write_output(result)
            return result

        # Execute each action
        for action in policy.get("actions", []):
            action_type = action.get("type") if isinstance(action, dict) else action

            self.actions_tried += 1
            self.log(f"Action {self.actions_tried}: {action_type}")

            result = self.execute_action(action_type)

            if result.get("status") == "ok":
                self.actions_successful += 1

            self.actions.append(result)

        # Build final report
        report = {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "policy_source": str(self.state_dir / "brain_policy.json"),
            "actions_tried": self.actions_tried,
            "actions_successful": self.actions_successful,
            "actions": self.actions,
            "errors": self.errors
        }

        # Write output
        self.write_output(report)

        self.log(f"Execution complete: {self.actions_successful}/{self.actions_tried} successful")

        return report

    def write_output(self, report: Dict[str, Any]) -> None:
        """
        Write the execution report to state/brain_actions.json.

        Args:
            report: Complete execution report dict.
        """
        output_path = self.state_dir / "brain_actions.json"

        try:
            # Ensure state directory exists
            self.state_dir.mkdir(parents=True, exist_ok=True)

            with open(output_path, 'w') as f:
                json.dump(report, f, indent=2)

            self.log(f"Wrote execution report to {output_path}")

            # Optionally write human-readable summary
            if self.verbose:
                self.write_text_summary(report)

        except Exception as e:
            error_msg = f"Failed to write output: {e}"
            self.log(error_msg)
            self.errors.append(error_msg)
            # This is a catastrophic error - re-raise
            raise

    def write_text_summary(self, report: Dict[str, Any]) -> None:
        """
        Write a human-readable text summary alongside the JSON report.

        Args:
            report: Complete execution report dict.
        """
        output_path = self.state_dir / "brain_actions.txt"

        try:
            with open(output_path, 'w') as f:
                f.write("=" * 70 + "\n")
                f.write("HANDS-OFF ENGINE: POLICY EXECUTOR REPORT\n")
                f.write("=" * 70 + "\n\n")

                f.write(f"Generated: {report['generated_at']}\n")
                f.write(f"Policy Source: {report['policy_source']}\n\n")

                f.write(f"Actions Tried: {report['actions_tried']}\n")
                f.write(f"Actions Successful: {report['actions_successful']}\n\n")

                if report['actions']:
                    f.write("=" * 70 + "\n")
                    f.write("ACTIONS EXECUTED\n")
                    f.write("=" * 70 + "\n\n")

                    for idx, action in enumerate(report['actions'], 1):
                        f.write(f"{idx}. {action['type'].upper()}\n")
                        f.write(f"   Status: {action['status']}\n")
                        f.write(f"   Details: {json.dumps(action['details'], indent=6)}\n\n")

                if report['errors']:
                    f.write("=" * 70 + "\n")
                    f.write("ERRORS\n")
                    f.write("=" * 70 + "\n\n")

                    for idx, error in enumerate(report['errors'], 1):
                        f.write(f"{idx}. {error}\n")

            self.log(f"Wrote text summary to {output_path}")

        except Exception as e:
            self.log(f"Failed to write text summary: {e}")


def run_policy_actions(
    state_dir: str = "state",
    ai_dir: str = "ai",
    verbose: bool = False
) -> Dict[str, Any]:
    """
    Main entry point for policy execution.

    Args:
        state_dir: Directory for state files (default: "state")
        ai_dir: Directory for AI modules (default: "ai")
        verbose: Enable verbose output

    Returns:
        Complete execution report dict.
    """
    executor = PolicyExecutor(state_dir=state_dir, ai_dir=ai_dir, verbose=verbose)
    return executor.run_policy_actions()


def main() -> int:
    """
    CLI entry point.

    Returns:
        Exit code (0 = success, 1 = catastrophic error)
    """
    parser = argparse.ArgumentParser(
        description="Hands-Off Engine: Policy Executor (DRYRUN-only safe action engine)"
    )
    parser.add_argument(
        "--state-dir",
        default="state",
        help="Directory for state files (default: state)"
    )
    parser.add_argument(
        "--ai-dir",
        default="ai",
        help="Directory for AI modules (default: ai)"
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose output"
    )

    args = parser.parse_args()

    try:
        report = run_policy_actions(
            state_dir=args.state_dir,
            ai_dir=args.ai_dir,
            verbose=args.verbose
        )

        if args.verbose:
            print("\n" + "=" * 70)
            print("EXECUTION SUMMARY")
            print("=" * 70)
            print(f"Actions tried: {report['actions_tried']}")
            print(f"Actions successful: {report['actions_successful']}")
            print(f"Output: {args.state_dir}/brain_actions.json")

            if report['errors']:
                print(f"\nWarnings/Errors: {len(report['errors'])}")
                for error in report['errors']:
                    print(f"  - {error}")

        return 0

    except Exception as e:
        print(f"CATASTROPHIC ERROR: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
