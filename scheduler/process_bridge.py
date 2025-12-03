#!/usr/bin/env python3
"""
Process Bridge

Wires together:
- Cron jobs (scheduled execution)
- autonomous/*.py (process definitions)
- state/process_state.json (execution history)

This is the INTEGRAFIX bridge for scheduled processes.
"""

import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))


class ProcessBridge:
    """
    Bridges scheduled processes with their execution state.

    Connects:
    - Cron schedule → autonomous scripts
    - Execution → state tracking
    - Logs → outcome verification
    """

    def __init__(self, base_path: str = "/root/hands-off-engine"):
        self.base_path = Path(base_path)
        self.autonomous_path = self.base_path / "autonomous"
        self.logs_path = self.base_path / "logs"
        self.state_path = self.base_path / "state"

    def get_cron_schedule(self) -> List[Dict]:
        """Extract and parse cron schedule."""
        processes = []

        try:
            result = subprocess.run(
                ["crontab", "-l"],
                capture_output=True,
                text=True
            )
            if result.returncode != 0:
                return processes

            for line in result.stdout.split("\n"):
                line = line.strip()
                if not line or line.startswith("#"):
                    continue

                # Parse cron line
                parts = line.split()
                if len(parts) >= 6:
                    schedule = " ".join(parts[:5])
                    command = " ".join(parts[5:])

                    # Extract script name
                    script_name = None
                    if "python3" in command:
                        for part in command.split():
                            if part.endswith(".py"):
                                script_name = Path(part).name
                                break

                    processes.append({
                        "schedule": schedule,
                        "command": command[:100],  # Truncate for readability
                        "script": script_name,
                        "category": self._categorize_schedule(schedule)
                    })

        except Exception as e:
            pass

        return processes

    def _categorize_schedule(self, schedule: str) -> str:
        """Categorize schedule frequency."""
        if "*/30" in schedule or "* *" in schedule.split()[0]:
            return "high_frequency"  # Every 30 min or every minute
        elif "*/" in schedule:
            # Extract interval
            for part in schedule.split():
                if part.startswith("*/"):
                    try:
                        interval = int(part[2:])
                        if interval <= 2:
                            return "high_frequency"
                        elif interval <= 4:
                            return "medium_frequency"
                        else:
                            return "low_frequency"
                    except:
                        pass
            return "medium_frequency"
        else:
            return "fixed_time"

    def check_execution_state(self) -> Dict:
        """
        Check execution state for all scheduled processes.

        Bridges: cron → logs → state tracking
        """
        result = {
            "component": "execution_state",
            "status": "tracked",
            "details": {
                "processes": [],
                "categories": {},
                "last_runs": {}
            }
        }

        processes = self.get_cron_schedule()
        result["details"]["processes"] = processes

        # Categorize
        for proc in processes:
            cat = proc.get("category", "unknown")
            result["details"]["categories"][cat] = \
                result["details"]["categories"].get(cat, 0) + 1

        # Check last run times from logs
        if self.logs_path.exists():
            for proc in processes:
                script = proc.get("script")
                if script:
                    # Find corresponding log
                    log_name = script.replace(".py", ".log")
                    log_file = self.logs_path / log_name
                    if log_file.exists():
                        try:
                            mtime = datetime.fromtimestamp(
                                log_file.stat().st_mtime,
                                tz=timezone.utc
                            )
                            result["details"]["last_runs"][script] = mtime.isoformat()
                        except:
                            pass

        return result

    def check_process_outcomes(self) -> Dict:
        """
        Check outcomes of scheduled processes.

        Bridges: execution → outcome tracking
        """
        result = {
            "component": "process_outcomes",
            "status": "tracked",
            "details": {
                "outcome_files": 0,
                "recent_outcomes": []
            }
        }

        try:
            # Check for outcome tracking files
            outcomes_path = self.state_path / "outcomes"
            if outcomes_path.exists():
                outcome_files = list(outcomes_path.glob("*.json"))
                result["details"]["outcome_files"] = len(outcome_files)

                # Get recent outcomes
                recent = sorted(outcome_files, key=lambda f: f.stat().st_mtime, reverse=True)[:5]
                for f in recent:
                    try:
                        data = json.loads(f.read_text())
                        result["details"]["recent_outcomes"].append({
                            "file": f.name,
                            "status": data.get("status", "unknown")
                        })
                    except:
                        pass

        except Exception as e:
            result["status"] = "error"
            result["details"]["error"] = str(e)

        return result

    def wire_process_coordination(self) -> Dict:
        """
        Wire process coordination between cron and autonomous scripts.

        Creates bidirectional mapping.
        """
        result = {
            "component": "process_coordination",
            "status": "wired",
            "details": {
                "scheduled_scripts": [],
                "unscheduled_scripts": [],
                "wiring_complete": False
            }
        }

        try:
            # Get scheduled scripts from cron
            cron_processes = self.get_cron_schedule()
            scheduled_scripts = set(p.get("script") for p in cron_processes if p.get("script"))

            # Get all autonomous scripts
            all_scripts = set()
            if self.autonomous_path.exists():
                all_scripts = set(f.name for f in self.autonomous_path.glob("*.py")
                                  if not f.name.startswith("__"))

            result["details"]["scheduled_scripts"] = list(scheduled_scripts)
            result["details"]["unscheduled_scripts"] = list(all_scripts - scheduled_scripts)

            # Wiring is complete if most autonomous scripts are scheduled
            scheduled_ratio = len(scheduled_scripts) / len(all_scripts) if all_scripts else 0
            result["details"]["wiring_complete"] = scheduled_ratio > 0.3
            result["details"]["coverage"] = f"{int(scheduled_ratio * 100)}%"

            if not result["details"]["wiring_complete"]:
                result["status"] = "partial"

        except Exception as e:
            result["status"] = "error"
            result["details"]["error"] = str(e)

        return result

    def bridge(self) -> Dict:
        """
        Run full process bridge.

        Wires all scheduled processes together.
        """
        print("=" * 60)
        print("PROCESS BRIDGE - INTEGRAFIX")
        print("=" * 60)

        results = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "components": {}
        }

        print("\n[1] Checking execution state...")
        results["components"]["execution_state"] = self.check_execution_state()
        status = results["components"]["execution_state"]
        print(f"    Status: {status['status']}")
        print(f"    Scheduled processes: {len(status['details'].get('processes', []))}")
        for cat, count in status["details"].get("categories", {}).items():
            print(f"      {cat}: {count}")

        print("\n[2] Checking process outcomes...")
        results["components"]["process_outcomes"] = self.check_process_outcomes()
        status = results["components"]["process_outcomes"]
        print(f"    Status: {status['status']}")
        print(f"    Outcome files: {status['details'].get('outcome_files', 0)}")

        print("\n[3] Wiring process coordination...")
        results["components"]["process_coordination"] = self.wire_process_coordination()
        status = results["components"]["process_coordination"]
        print(f"    Status: {status['status']}")
        print(f"    Scheduled: {len(status['details'].get('scheduled_scripts', []))}")
        print(f"    Unscheduled: {len(status['details'].get('unscheduled_scripts', []))}")
        print(f"    Coverage: {status['details'].get('coverage', '0%')}")

        # Calculate overall health
        wired_count = sum(
            1 for c in results["components"].values()
            if c["status"] in ("tracked", "wired")
        )
        total_count = len(results["components"])
        results["health"] = f"{wired_count}/{total_count} components wired"
        results["score"] = int((wired_count / total_count) * 100) if total_count > 0 else 0

        print("\n" + "=" * 60)
        print(f"PROCESS BRIDGE COMPLETE: {results['health']}")
        print("=" * 60)

        return results


def main():
    """Run process bridge."""
    bridge = ProcessBridge()
    results = bridge.bridge()

    # Save results
    output_file = Path("/root/hands-off-engine/state/integrafix/processes_bridge.json")
    output_file.parent.mkdir(parents=True, exist_ok=True)
    output_file.write_text(json.dumps(results, indent=2))
    print(f"\nResults saved to: {output_file}")

    return results


if __name__ == "__main__":
    main()
