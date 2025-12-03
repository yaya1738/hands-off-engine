#!/usr/bin/env python3
"""
Monitoring Bridge

Wires together:
- health/ho_healthcheck.py (system health)
- autonomous/* (running processes)
- logs/* (log files)
- audit/* (audit trails)

This is the INTEGRAFIX bridge for monitoring.
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


class MonitoringBridge:
    """
    Bridges monitoring across all system layers.

    Monitors:
    - Process health (cron jobs, background processes)
    - Log freshness (recent activity)
    - Audit completeness (tracked vs untracked)
    - Health check integration
    """

    def __init__(self, base_path: str = "/root/hands-off-engine"):
        self.base_path = Path(base_path)
        self.logs_path = self.base_path / "logs"
        self.audit_path = self.base_path / "audit"
        self.state_path = self.base_path / "state"

    def check_process_health(self) -> Dict:
        """
        Check health of all autonomous processes.

        Bridges: autonomous/*.py ↔ cron jobs ↔ logs/*.log
        """
        result = {
            "component": "process_health",
            "status": "healthy",
            "details": {
                "cron_jobs": 0,
                "running_processes": [],
                "recent_activity": {}
            }
        }

        try:
            # Count cron jobs
            cron_output = subprocess.run(
                ["crontab", "-l"],
                capture_output=True,
                text=True
            )
            if cron_output.returncode == 0:
                cron_lines = [l for l in cron_output.stdout.split("\n")
                              if l.strip() and not l.startswith("#")]
                result["details"]["cron_jobs"] = len(cron_lines)

            # Check running Python processes
            ps_output = subprocess.run(
                ["pgrep", "-f", "python.*autonomous"],
                capture_output=True,
                text=True
            )
            if ps_output.returncode == 0:
                pids = ps_output.stdout.strip().split("\n")
                result["details"]["running_processes"] = [p for p in pids if p]

            # Check log freshness
            if self.logs_path.exists():
                now = datetime.now(timezone.utc)
                for log_file in self.logs_path.glob("*.log"):
                    try:
                        mtime = datetime.fromtimestamp(
                            log_file.stat().st_mtime,
                            tz=timezone.utc
                        )
                        age_hours = (now - mtime).total_seconds() / 3600
                        result["details"]["recent_activity"][log_file.name] = {
                            "age_hours": round(age_hours, 1),
                            "fresh": age_hours < 4
                        }
                    except:
                        pass

            # Determine overall status
            if result["details"]["cron_jobs"] == 0:
                result["status"] = "degraded"
            elif len(result["details"]["running_processes"]) == 0:
                result["status"] = "idle"

        except Exception as e:
            result["status"] = "error"
            result["details"]["error"] = str(e)

        return result

    def check_log_health(self) -> Dict:
        """
        Check health of logging system.

        Bridges: logs/*.log ↔ log rotation ↔ error tracking
        """
        result = {
            "component": "log_health",
            "status": "healthy",
            "details": {
                "log_files": 0,
                "total_size_mb": 0,
                "recent_errors": 0
            }
        }

        try:
            if not self.logs_path.exists():
                result["status"] = "missing"
                return result

            log_files = list(self.logs_path.glob("*.log"))
            result["details"]["log_files"] = len(log_files)

            total_size = sum(f.stat().st_size for f in log_files)
            result["details"]["total_size_mb"] = round(total_size / (1024 * 1024), 2)

            # Count recent errors across logs
            error_count = 0
            for log_file in log_files[:10]:  # Check first 10 logs
                try:
                    content = log_file.read_text(errors='ignore')
                    # Count error keywords
                    error_count += content.lower().count("error")
                    error_count += content.lower().count("exception")
                    error_count += content.lower().count("traceback")
                except:
                    pass

            result["details"]["recent_errors"] = error_count

            if result["details"]["total_size_mb"] > 100:
                result["status"] = "needs_rotation"
            elif error_count > 50:
                result["status"] = "has_errors"

        except Exception as e:
            result["status"] = "error"
            result["details"]["error"] = str(e)

        return result

    def check_audit_health(self) -> Dict:
        """
        Check health of audit system.

        Bridges: audit/*.py ↔ ai_nexus/ledger.py ↔ state/audit/
        """
        result = {
            "component": "audit_health",
            "status": "healthy",
            "details": {
                "audit_files": 0,
                "tracked_operations": 0
            }
        }

        try:
            if not self.audit_path.exists():
                result["status"] = "missing"
                return result

            audit_files = list(self.audit_path.glob("*.py"))
            result["details"]["audit_files"] = len(audit_files)

            # Check for audit logs in state
            audit_state = self.state_path / "audit"
            if audit_state.exists():
                audit_logs = list(audit_state.glob("*.json"))
                result["details"]["tracked_operations"] = len(audit_logs)

        except Exception as e:
            result["status"] = "error"
            result["details"]["error"] = str(e)

        return result

    def check_healthcheck_integration(self) -> Dict:
        """
        Check that ho_healthcheck.py is properly integrated.

        Bridges: health/ho_healthcheck.py ↔ monitoring dashboard
        """
        result = {
            "component": "healthcheck_integration",
            "status": "healthy",
            "details": {}
        }

        try:
            # Try to run healthcheck
            from health.ho_healthcheck import gather_health

            health_data = gather_health(str(self.state_path))
            result["details"]["overall_status"] = health_data.get("status", "unknown")
            result["details"]["components"] = health_data.get("components", {})
            result["details"]["errors"] = len(health_data.get("errors", []))

            if health_data.get("status") == "error":
                result["status"] = "degraded"

        except ImportError:
            result["status"] = "not_integrated"
            result["details"]["error"] = "ho_healthcheck.py not importable"
        except Exception as e:
            result["status"] = "error"
            result["details"]["error"] = str(e)

        return result

    def monitor(self) -> Dict:
        """
        Run full monitoring check.

        Wires all monitoring subsystems together.
        """
        print("=" * 60)
        print("MONITORING BRIDGE - INTEGRAFIX")
        print("=" * 60)

        results = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "components": {}
        }

        # Check all components
        print("\n[1] Checking process health...")
        results["components"]["process_health"] = self.check_process_health()
        status = results["components"]["process_health"]
        print(f"    Status: {status['status']}")
        print(f"    Cron jobs: {status['details'].get('cron_jobs', 0)}")
        print(f"    Running: {len(status['details'].get('running_processes', []))}")

        print("\n[2] Checking log health...")
        results["components"]["log_health"] = self.check_log_health()
        status = results["components"]["log_health"]
        print(f"    Status: {status['status']}")
        print(f"    Log files: {status['details'].get('log_files', 0)}")
        print(f"    Size: {status['details'].get('total_size_mb', 0)} MB")

        print("\n[3] Checking audit health...")
        results["components"]["audit_health"] = self.check_audit_health()
        status = results["components"]["audit_health"]
        print(f"    Status: {status['status']}")

        print("\n[4] Checking healthcheck integration...")
        results["components"]["healthcheck_integration"] = self.check_healthcheck_integration()
        status = results["components"]["healthcheck_integration"]
        print(f"    Status: {status['status']}")
        if "overall_status" in status["details"]:
            print(f"    System status: {status['details']['overall_status']}")

        # Calculate overall health
        healthy_count = sum(
            1 for c in results["components"].values()
            if c["status"] in ("healthy", "idle")
        )
        total_count = len(results["components"])
        results["health"] = f"{healthy_count}/{total_count} components healthy"
        results["score"] = int((healthy_count / total_count) * 100) if total_count > 0 else 0

        print("\n" + "=" * 60)
        print(f"MONITORING COMPLETE: {results['health']}")
        print("=" * 60)

        return results


def main():
    """Run monitoring bridge."""
    bridge = MonitoringBridge()
    results = bridge.monitor()

    # Save results
    output_file = Path("/root/hands-off-engine/state/integrafix/monitoring.json")
    output_file.parent.mkdir(parents=True, exist_ok=True)
    output_file.write_text(json.dumps(results, indent=2))
    print(f"\nResults saved to: {output_file}")

    return results


if __name__ == "__main__":
    main()
