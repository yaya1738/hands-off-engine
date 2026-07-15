#!/usr/bin/env python3
"""
Batch 25: Brain Orchestrator

End-to-end cognitive pipeline runner that orchestrates all brain stages (18-24)
in a safe, DRYRUN-only mode.

This orchestrator:
- Runs the complete cognitive pipeline in sequence
- Captures success/failure for each stage
- Produces machine-readable (JSON) and human-readable (TXT) reports
- Continues execution even if individual stages fail
- Never crashes - always produces a final report
"""

import sys
import json
import time
import argparse
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List, Optional
import traceback

# Add parent directory to path for imports
_SCRIPT_DIR = Path(__file__).parent.parent
if str(_SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPT_DIR))


class BrainOrchestrator:
    """
    Orchestrates the entire cognitive pipeline (Batches 18-24).

    Stages:
    1. Brain Summary (Batch 18)
    2. Policy Agent v1 (Batch 19)
    3. Policy Executor (Batch 20)
    4. Action Verifier (Batch 21)
    5. Consensus Engine (Batch 22)
    6. Learning Engine (Batch 23)
    7. Policy Brain v2 (Batch 24)
    """

    def __init__(self, state_dir: Path, verbose: bool = False):
        """
        Initialize orchestrator.

        Args:
            state_dir: Directory for all state files
            verbose: Enable verbose logging to stdout
        """
        self.state_dir = Path(state_dir)
        self.verbose = verbose
        self.stages_results: List[Dict[str, Any]] = []
        self.start_time = None
        self.end_time = None

    def log(self, message: str) -> None:
        """Log message if verbose mode is enabled."""
        if self.verbose:
            print(f"[{datetime.utcnow().strftime('%H:%M:%S')}] {message}")

    def run_stage_18_brain_summary(self) -> Dict[str, Any]:
        """Run Batch 18: Brain Summary"""
        stage_name = "brain_summary"
        batch = 18
        self.log(f"Starting Stage 1: {stage_name} (Batch {batch})")

        start_ms = int(time.time() * 1000)
        result = {
            "name": stage_name,
            "batch": batch,
            "status": "ok",
            "duration_ms": 0,
            "input_files": [],
            "output_files": [],
            "errors": []
        }

        try:
            # Import and run
            from reports.ho_brain_report import write_brain_summary
            output = write_brain_summary(self.state_dir)

            result["output_files"] = output.get("output_files", [])
            result["status"] = "ok"
            self.log(f"  ✓ Completed: {len(result['output_files'])} files generated")

        except Exception as e:
            result["status"] = "error"
            result["errors"].append(str(e))
            if self.verbose:
                result["errors"].append(traceback.format_exc())
            self.log(f"  ✗ Failed: {e}")

        result["duration_ms"] = int(time.time() * 1000) - start_ms
        return result

    def run_stage_19_policy_agent(self) -> Dict[str, Any]:
        """Run Batch 19: Policy Agent v1"""
        stage_name = "policy_agent_v1"
        batch = 19
        self.log(f"Starting Stage 2: {stage_name} (Batch {batch})")

        start_ms = int(time.time() * 1000)
        result = {
            "name": stage_name,
            "batch": batch,
            "status": "ok",
            "duration_ms": 0,
            "input_files": [str(self.state_dir / "hands_off_brain.json")],
            "output_files": [],
            "errors": []
        }

        try:
            from ai.ho_policy_agent import write_policy_recommendation
            output = write_policy_recommendation(self.state_dir)

            result["output_files"] = output.get("output_files", [])
            result["status"] = "ok"
            self.log(f"  ✓ Completed: {len(result['output_files'])} files generated")

        except FileNotFoundError as e:
            result["status"] = "error"
            result["errors"].append(f"Missing input file: {e}")
            self.log(f"  ✗ Failed: Missing input - {e}")
        except Exception as e:
            result["status"] = "error"
            result["errors"].append(str(e))
            if self.verbose:
                result["errors"].append(traceback.format_exc())
            self.log(f"  ✗ Failed: {e}")

        result["duration_ms"] = int(time.time() * 1000) - start_ms
        return result

    def run_stage_20_policy_executor(self) -> Dict[str, Any]:
        """Run Batch 20: Policy Executor"""
        stage_name = "policy_executor"
        batch = 20
        self.log(f"Starting Stage 3: {stage_name} (Batch {batch})")

        start_ms = int(time.time() * 1000)
        result = {
            "name": stage_name,
            "batch": batch,
            "status": "ok",
            "duration_ms": 0,
            "input_files": [str(self.state_dir / "brain_policy.json")],
            "output_files": [],
            "errors": []
        }

        try:
            from ai.ho_policy_executor import run_policy_actions
            output = run_policy_actions(self.state_dir)

            result["output_files"] = output.get("output_files", [])
            result["status"] = "ok"
            self.log(f"  ✓ Completed: {len(result['output_files'])} files generated")

        except FileNotFoundError as e:
            result["status"] = "error"
            result["errors"].append(f"Missing input file: {e}")
            self.log(f"  ✗ Failed: Missing input - {e}")
        except Exception as e:
            result["status"] = "error"
            result["errors"].append(str(e))
            if self.verbose:
                result["errors"].append(traceback.format_exc())
            self.log(f"  ✗ Failed: {e}")

        result["duration_ms"] = int(time.time() * 1000) - start_ms
        return result

    def run_stage_21_action_verifier(self) -> Dict[str, Any]:
        """Run Batch 21: Action Verifier"""
        stage_name = "action_verifier"
        batch = 21
        self.log(f"Starting Stage 4: {stage_name} (Batch {batch})")

        start_ms = int(time.time() * 1000)
        result = {
            "name": stage_name,
            "batch": batch,
            "status": "ok",
            "duration_ms": 0,
            "input_files": [str(self.state_dir / "brain_actions.json")],
            "output_files": [],
            "errors": []
        }

        try:
            from ai.ho_action_verifier import verify_actions
            output = verify_actions(self.state_dir)

            result["output_files"] = output.get("output_files", [])
            result["status"] = "ok"
            self.log(f"  ✓ Completed: {len(result['output_files'])} files generated")

        except FileNotFoundError as e:
            result["status"] = "error"
            result["errors"].append(f"Missing input file: {e}")
            self.log(f"  ✗ Failed: Missing input - {e}")
        except Exception as e:
            result["status"] = "error"
            result["errors"].append(str(e))
            if self.verbose:
                result["errors"].append(traceback.format_exc())
            self.log(f"  ✗ Failed: {e}")

        result["duration_ms"] = int(time.time() * 1000) - start_ms
        return result

    def run_stage_22_consensus_engine(self) -> Dict[str, Any]:
        """Run Batch 22: Consensus Engine"""
        stage_name = "consensus_engine"
        batch = 22
        self.log(f"Starting Stage 5: {stage_name} (Batch {batch})")

        start_ms = int(time.time() * 1000)
        result = {
            "name": stage_name,
            "batch": batch,
            "status": "ok",
            "duration_ms": 0,
            "input_files": [str(self.state_dir / "brain_feedback.json")],
            "output_files": [],
            "errors": []
        }

        try:
            from ai.ho_consensus_engine import run_consensus
            output = run_consensus(self.state_dir)

            result["output_files"] = output.get("output_files", [])
            result["status"] = "ok"
            self.log(f"  ✓ Completed: {len(result['output_files'])} files generated")

        except FileNotFoundError as e:
            result["status"] = "error"
            result["errors"].append(f"Missing input file: {e}")
            self.log(f"  ✗ Failed: Missing input - {e}")
        except Exception as e:
            result["status"] = "error"
            result["errors"].append(str(e))
            if self.verbose:
                result["errors"].append(traceback.format_exc())
            self.log(f"  ✗ Failed: {e}")

        result["duration_ms"] = int(time.time() * 1000) - start_ms
        return result

    def run_stage_23_learning_engine(self) -> Dict[str, Any]:
        """Run Batch 23: Learning Engine"""
        stage_name = "learning_engine"
        batch = 23
        self.log(f"Starting Stage 6: {stage_name} (Batch {batch})")

        start_ms = int(time.time() * 1000)
        result = {
            "name": stage_name,
            "batch": batch,
            "status": "ok",
            "duration_ms": 0,
            "input_files": [str(self.state_dir / "brain_consensus.json")],
            "output_files": [],
            "errors": []
        }

        try:
            from ai.ho_learning_engine import update_learning
            output = update_learning(self.state_dir)

            result["output_files"] = output.get("output_files", [])
            result["status"] = "ok"
            self.log(f"  ✓ Completed: {len(result['output_files'])} files generated")

        except FileNotFoundError as e:
            result["status"] = "error"
            result["errors"].append(f"Missing input file: {e}")
            self.log(f"  ✗ Failed: Missing input - {e}")
        except Exception as e:
            result["status"] = "error"
            result["errors"].append(str(e))
            if self.verbose:
                result["errors"].append(traceback.format_exc())
            self.log(f"  ✗ Failed: {e}")

        result["duration_ms"] = int(time.time() * 1000) - start_ms
        return result

    def run_stage_24_policy_brain_v2(self) -> Dict[str, Any]:
        """Run Batch 24: Policy Brain v2"""
        stage_name = "policy_brain_v2"
        batch = 24
        self.log(f"Starting Stage 7: {stage_name} (Batch {batch})")

        start_ms = int(time.time() * 1000)
        result = {
            "name": stage_name,
            "batch": batch,
            "status": "ok",
            "duration_ms": 0,
            "input_files": [
                str(self.state_dir / "brain_consensus.json"),
                str(self.state_dir / "brain_learning.json")
            ],
            "output_files": [],
            "errors": []
        }

        try:
            from ai.ho_policy_brain_v2 import generate_policy_v2
            output = generate_policy_v2(self.state_dir)

            result["output_files"] = output.get("output_files", [])
            result["status"] = "ok"
            self.log(f"  ✓ Completed: {len(result['output_files'])} files generated")

        except FileNotFoundError as e:
            result["status"] = "error"
            result["errors"].append(f"Missing input file: {e}")
            self.log(f"  ✗ Failed: Missing input - {e}")
        except Exception as e:
            result["status"] = "error"
            result["errors"].append(str(e))
            if self.verbose:
                result["errors"].append(traceback.format_exc())
            self.log(f"  ✗ Failed: {e}")

        result["duration_ms"] = int(time.time() * 1000) - start_ms
        return result


    def run_stage_25_policy_v2_adapter(self) -> Dict[str, Any]:
        """Run Batch 25: Policy Brain v2 Adapter"""
        stage_name = "policy_v2_adapter"
        batch = 25

        result = {
            "name": stage_name,
            "batch": batch,
            "status": "ok",
            "duration_ms": 0,
            "input_files": [str(self.state_dir / "brain_policy_v2.json")],
            "output_files": [],
            "errors": []
        }

        start_ms = int(time.time() * 1000)

        try:
            from ai.ho_policy_v2_adapter import adapt_policy_v2
            output = adapt_policy_v2(self.state_dir)

            result["output_files"] = output.get("output_files", [])
            result["status"] = output.get("status", "ok")

        except Exception as e:
            result["status"] = "error"
            result["errors"].append(str(e))

        result["duration_ms"] = int(time.time() * 1000) - start_ms
        return result


    def run_all(self) -> Dict[str, Any]:
        """
        Run all stages in sequence.

        Returns:
            Complete orchestrator report
        """
        self.log("=" * 60)
        self.log("BRAIN ORCHESTRATOR - Starting cognitive pipeline")
        self.log("=" * 60)

        self.start_time = datetime.utcnow()

        # Run stages sequentially with dependency propagation
        self.stages_results = []

        stage_18 = self.run_stage_18_brain_summary()
        self.stages_results.append(stage_18)

        previous_failed = stage_18["status"] != "ok"

        for stage_func in [
            self.run_stage_19_policy_agent,
            self.run_stage_20_policy_executor,
            self.run_stage_21_action_verifier,
            self.run_stage_22_consensus_engine,
            self.run_stage_23_learning_engine,
            self.run_stage_24_policy_brain_v2,
            self.run_stage_25_policy_v2_adapter,
        ]:
            result = stage_func()

            if previous_failed:
                if result["status"] == "ok":
                    result["status"] = "error"
                result["errors"].append(
                    "Blocked by failed dependency: Stage 18 brain_summary"
                )

            self.stages_results.append(result)

        self.end_time = datetime.utcnow()

        # Compute summary
        stages_total = len(self.stages_results)
        stages_ok = sum(1 for s in self.stages_results if s["status"] == "ok")
        stages_error = sum(1 for s in self.stages_results if s["status"] == "error")
        stages_skipped = sum(1 for s in self.stages_results if s["status"] == "skipped")

        # Determine overall status
        if stages_error == 0:
            overall_status = "ok"
        elif stages_ok > 0:
            overall_status = "degraded"
        else:
            overall_status = "failed"

        # Collect notes
        notes = []
        for stage in self.stages_results:
            if stage["status"] == "error":
                notes.append(
                    f"{stage['name']} (Batch {stage['batch']}) failed: "
                    f"{stage['errors'][0] if stage['errors'] else 'unknown error'}"
                )

        report = {
            "generated_at": self.start_time.isoformat() + "Z",
            "completed_at": self.end_time.isoformat() + "Z",
            "stages": self.stages_results,
            "summary": {
                "stages_total": stages_total,
                "stages_ok": stages_ok,
                "stages_error": stages_error,
                "stages_skipped": stages_skipped,
                "overall_status": overall_status,
                "notes": notes
            }
        }

        self.log("=" * 60)
        self.log(f"Pipeline complete: {overall_status.upper()}")
        self.log(f"  Total stages: {stages_total}")
        self.log(f"  Successful:   {stages_ok}")
        self.log(f"  Failed:       {stages_error}")
        self.log(f"  Skipped:      {stages_skipped}")
        self.log("=" * 60)

        return report

    def write_reports(self, report: Dict[str, Any]) -> None:
        """
        Write both JSON and TXT reports.

        Args:
            report: Orchestrator report data
        """
        # Ensure state directory exists
        self.state_dir.mkdir(parents=True, exist_ok=True)

        # Write JSON report
        json_path = self.state_dir / "brain_orchestrator_report.json"
        with open(json_path, 'w') as f:
            json.dump(report, f, indent=2)
        self.log(f"Wrote JSON report: {json_path}")

        # Write TXT report
        txt_path = self.state_dir / "brain_orchestrator_report.txt"
        with open(txt_path, 'w') as f:
            f.write("=" * 60 + "\n")
            f.write("HANDS-OFF ENGINE - BRAIN ORCHESTRATOR (BATCH 25)\n")
            f.write("=" * 60 + "\n\n")
            f.write(f"Generated at: {report['generated_at']}\n")
            f.write(f"Completed at: {report['completed_at']}\n\n")

            f.write("Stages:\n")
            for i, stage in enumerate(report["stages"], 1):
                status_marker = "[OK]" if stage["status"] == "ok" else "[ERR]" if stage["status"] == "error" else "[SKIP]"
                f.write(f"  {i}. {status_marker:6} Batch {stage['batch']:2d} - {stage['name']}\n")

                if stage["errors"]:
                    for error in stage["errors"]:
                        # Only write first line of error to keep report concise
                        error_line = error.split('\n')[0]
                        f.write(f"       Reason: {error_line}\n")

            f.write("\nSummary:\n")
            summary = report["summary"]
            f.write(f"  Stages total: {summary['stages_total']}\n")
            f.write(f"  Successful:   {summary['stages_ok']}\n")
            f.write(f"  Failed:       {summary['stages_error']}\n")
            f.write(f"  Skipped:      {summary['stages_skipped']}\n\n")
            f.write(f"  Overall status: {summary['overall_status'].upper()}\n\n")

            if summary['notes']:
                f.write("Notes:\n")
                for note in summary['notes']:
                    f.write(f"  - {note}\n")
                f.write("\n")

            f.write("=" * 60 + "\n")

        self.log(f"Wrote TXT report: {txt_path}")


def main() -> int:
    """
    Main entry point for CLI.

    Returns:
        Exit code (0 = success, 1 = catastrophic failure)
    """
    parser = argparse.ArgumentParser(
        description="Brain Orchestrator - Run the complete cognitive pipeline (Batches 18-24)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python3 ai/ho_brain_orchestrator.py
  python3 ai/ho_brain_orchestrator.py --verbose
  python3 ai/ho_brain_orchestrator.py --state-dir /tmp/brain_state --verbose

Exit codes:
  0 = Orchestrator ran successfully (report generated)
  1 = Catastrophic error (could not generate report)
"""
    )

    parser.add_argument(
        "--state-dir",
        type=Path,
        default=Path("state"),
        help="Directory for state files (default: state)"
    )

    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose logging to stdout"
    )

    args = parser.parse_args()

    try:
        orchestrator = BrainOrchestrator(
            state_dir=args.state_dir,
            verbose=args.verbose
        )

        report = orchestrator.run_all()
        orchestrator.write_reports(report)

        # Exit 0 even if some stages failed - we successfully generated a report
        return 0

    except Exception as e:
        # Catastrophic error - couldn't even generate the report
        print(f"CATASTROPHIC ERROR: {e}", file=sys.stderr)
        if args.verbose:
            traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
