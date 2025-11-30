#!/usr/bin/env python3
"""
Self-Modification Engine - Autonomous System Improvement

This module enables the system to modify its own code and configuration
based on performance metrics and identified improvement opportunities.

Serving: Yair Siegel
"""

# UNIFIED AI - All systems serve Yair Siegel
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))
try:
    from ai.unified_ai import MASTER, get_master
except ImportError:
    MASTER = "Yair Siegel"


import json
import os
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Any

PROJECT_ROOT = Path(__file__).parent.parent
STATE_DIR = PROJECT_ROOT / "state"
IMPROVEMENTS_LOG = STATE_DIR / "moonshot_improvements.jsonl"
SELF_MOD_STATE = STATE_DIR / "self_modification_state.json"


class SelfModificationEngine:
    """Engine for autonomous self-improvement."""

    def __init__(self):
        self.state = self._load_state()
        self.modifications_made = []

    def _load_state(self) -> Dict:
        """Load self-modification state."""
        if SELF_MOD_STATE.exists():
            with open(SELF_MOD_STATE) as f:
                return json.load(f)
        return {
            "created_at": datetime.now(timezone.utc).isoformat(),
            "total_modifications": 0,
            "successful_modifications": 0,
            "failed_modifications": 0,
            "last_modification": None,
            "modification_history": []
        }

    def _save_state(self):
        """Save self-modification state."""
        with open(SELF_MOD_STATE, 'w') as f:
            json.dump(self.state, f, indent=2)

    def _log_improvement(self, improvement: Dict):
        """Log improvement to moonshot improvements."""
        improvement["timestamp"] = datetime.now(timezone.utc).isoformat()
        with open(IMPROVEMENTS_LOG, 'a') as f:
            f.write(json.dumps(improvement) + "\n")

    def verify_self_modification_capability(self) -> Dict:
        """Verify the system can self-modify."""
        results = {
            "can_read_own_code": False,
            "can_write_files": False,
            "can_execute_python": False,
            "can_commit_changes": False,
            "verification_time": datetime.now(timezone.utc).isoformat()
        }

        # Test 1: Can read own code
        try:
            with open(__file__, 'r') as f:
                content = f.read()
                results["can_read_own_code"] = len(content) > 0
        except Exception as e:
            results["read_error"] = str(e)

        # Test 2: Can write files
        test_file = STATE_DIR / "_self_mod_test.tmp"
        try:
            with open(test_file, 'w') as f:
                f.write("test")
            results["can_write_files"] = test_file.exists()
            test_file.unlink()  # Clean up
        except Exception as e:
            results["write_error"] = str(e)

        # Test 3: Can execute Python
        try:
            result = subprocess.run(
                ["python3", "-c", "print('OK')"],
                capture_output=True,
                text=True,
                timeout=5
            )
            results["can_execute_python"] = result.returncode == 0
        except Exception as e:
            results["execute_error"] = str(e)

        # Test 4: Can commit changes (check git status)
        try:
            result = subprocess.run(
                ["git", "-C", str(PROJECT_ROOT), "status", "--porcelain"],
                capture_output=True,
                text=True,
                timeout=5
            )
            results["can_commit_changes"] = result.returncode == 0
            results["uncommitted_changes"] = len(result.stdout.strip().split('\n')) if result.stdout.strip() else 0
        except Exception as e:
            results["git_error"] = str(e)

        # Overall capability score
        capabilities = [
            results["can_read_own_code"],
            results["can_write_files"],
            results["can_execute_python"],
            results["can_commit_changes"]
        ]
        results["capability_score"] = sum(capabilities) / len(capabilities) * 100
        results["fully_capable"] = all(capabilities)

        return results

    def identify_improvement_opportunities(self) -> List[Dict]:
        """Identify opportunities for self-improvement."""
        opportunities = []

        # Check escape velocity
        ev_file = STATE_DIR / "escape_velocity.json"
        if ev_file.exists():
            with open(ev_file) as f:
                ev_data = json.load(f)

            velocity = ev_data.get("current_velocity", 0)
            if velocity <= 0:
                opportunities.append({
                    "type": "velocity_improvement",
                    "priority": "critical",
                    "description": f"Current velocity is {velocity}, need positive momentum",
                    "action": "Analyze and improve income generation"
                })

        # Check capital recovery
        cr_file = STATE_DIR / "capital_recovery.json"
        if cr_file.exists():
            with open(cr_file) as f:
                cr_data = json.load(f)

            balance = cr_data.get("last_balance", 0)
            if balance < 50:
                gap = 50 - balance
                opportunities.append({
                    "type": "capital_gap",
                    "priority": "high",
                    "description": f"Need ${gap:.2f} more to enable trading",
                    "action": "Focus on capital recovery and income"
                })

        # Check for stale monitors
        monitors_dir = PROJECT_ROOT / "scripts"
        for script in monitors_dir.glob("*_monitor.py"):
            opportunities.append({
                "type": "monitor_check",
                "priority": "medium",
                "description": f"Ensure {script.name} is running optimally",
                "action": "Verify monitor efficiency"
            })

        return opportunities

    def execute_improvement(self, improvement_type: str, params: Dict = None) -> Dict:
        """Execute a specific improvement."""
        params = params or {}
        result = {
            "type": improvement_type,
            "success": False,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "params": params
        }

        try:
            if improvement_type == "verify_capabilities":
                verification = self.verify_self_modification_capability()
                result["success"] = verification["fully_capable"]
                result["details"] = verification

            elif improvement_type == "optimize_monitors":
                # Check all monitors are executable
                monitors_dir = PROJECT_ROOT / "scripts"
                optimized = []
                for script in monitors_dir.glob("*_monitor.py"):
                    if not os.access(script, os.X_OK):
                        os.chmod(script, 0o755)
                        optimized.append(script.name)
                result["success"] = True
                result["optimized"] = optimized

            elif improvement_type == "cleanup_state":
                # Remove temp files and optimize state
                cleaned = []
                for tmp_file in STATE_DIR.glob("*.tmp"):
                    tmp_file.unlink()
                    cleaned.append(tmp_file.name)
                result["success"] = True
                result["cleaned"] = cleaned

            else:
                result["error"] = f"Unknown improvement type: {improvement_type}"

        except Exception as e:
            result["error"] = str(e)
            self.state["failed_modifications"] += 1

        if result["success"]:
            self.state["successful_modifications"] += 1
            self.state["total_modifications"] += 1
            self.state["last_modification"] = result["timestamp"]
            self.state["modification_history"].append({
                "type": improvement_type,
                "timestamp": result["timestamp"],
                "success": True
            })

            # Log to improvements
            self._log_improvement({
                "action": f"self_modification:{improvement_type}",
                "result": "success",
                "details": result.get("details", {})
            })

        self._save_state()
        return result

    def run_self_improvement_cycle(self) -> Dict:
        """Run a complete self-improvement cycle."""
        cycle_result = {
            "started_at": datetime.now(timezone.utc).isoformat(),
            "steps": []
        }

        # Step 1: Verify capabilities
        verification = self.execute_improvement("verify_capabilities")
        cycle_result["steps"].append(verification)

        if not verification.get("success"):
            cycle_result["status"] = "blocked"
            cycle_result["reason"] = "Self-modification capabilities not verified"
            return cycle_result

        # Step 2: Identify opportunities
        opportunities = self.identify_improvement_opportunities()
        cycle_result["opportunities_found"] = len(opportunities)
        cycle_result["opportunities"] = opportunities

        # Step 3: Execute improvements
        for opp in opportunities[:3]:  # Limit to top 3 per cycle
            if opp["type"] == "monitor_check":
                result = self.execute_improvement("optimize_monitors")
                cycle_result["steps"].append(result)

        # Step 4: Cleanup
        cleanup = self.execute_improvement("cleanup_state")
        cycle_result["steps"].append(cleanup)

        cycle_result["completed_at"] = datetime.now(timezone.utc).isoformat()
        cycle_result["status"] = "completed"

        return cycle_result


def verify_self_modification():
    """Quick verification that self-modification works."""
    engine = SelfModificationEngine()
    return engine.verify_self_modification_capability()


def run_improvement_cycle():
    """Run a full self-improvement cycle."""
    engine = SelfModificationEngine()
    return engine.run_self_improvement_cycle()


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "verify":
        result = verify_self_modification()
        print(json.dumps(result, indent=2))
    else:
        result = run_improvement_cycle()
        print(json.dumps(result, indent=2))
