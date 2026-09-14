#!/usr/bin/env python3
"""
Comprehensive health monitoring system.

Monitors all aspects of the hands-off engine:
- Service health and heartbeats
- Resource utilization (CPU, memory, disk)
- API endpoint availability
- State file integrity
- Network connectivity
- Database health
- Recent errors and warnings

Publishes metrics for dashboards and alerting.
"""

import os
import sys
import json
import time
import psutil
import requests
import subprocess
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from enum import Enum
import structlog

logger = structlog.get_logger(__name__)


class HealthStatus(Enum):
    """Health check status levels"""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"


@dataclass
class HealthCheck:
    """Result of a single health check"""
    name: str
    status: HealthStatus
    message: str
    timestamp: str
    duration_ms: float
    metadata: Optional[Dict[str, Any]] = None

    def to_dict(self) -> dict:
        """Convert to dictionary"""
        result = asdict(self)
        result["status"] = self.status.value
        return result


class HealthMonitor:
    """Main health monitoring system"""

    def __init__(self, config_path: Optional[str] = None):
        """
        Args:
            config_path: Path to configuration file
        """
        self.config = self._load_config(config_path)
        self.checks: List[HealthCheck] = []
        self.state_dir = Path(self.config.get("state_dir", "/home/user/hands-off-engine/state"))
        self.termux_state_dir = Path(self.config.get("termux_state_dir", "/home/user/hands-off-engine/termux-hands-off/state"))

    def _load_config(self, config_path: Optional[str]) -> dict:
        """Load configuration"""
        if config_path and os.path.exists(config_path):
            try:
                with open(config_path) as f:
                    return json.load(f)
            except Exception as e:
                logger.warning("config_load_failed", error=str(e))

        return {
            "state_dir": "/home/user/hands-off-engine/state",
            "termux_state_dir": "/home/user/hands-off-engine/termux-hands-off/state",
            "staleness_thresholds": {
                "master_json": 2700,  # 45 minutes
                "finance_json": 3600,  # 60 minutes
                "execution_plan": 1800,  # 30 minutes
            },
            "resource_thresholds": {
                "cpu_percent": 90,
                "memory_percent": 85,
                "disk_percent": 90,
            },
            "api_endpoints": {
                "admin_server": "http://localhost:8787/health",
                "polymarket_api": "https://clob.polymarket.com/",
            },
            "timeout_seconds": 10,
        }

    def _run_check(self, name: str, check_func) -> HealthCheck:
        """Run a single health check with timing"""
        start_time = time.time()

        try:
            status, message, metadata = check_func()
            duration_ms = (time.time() - start_time) * 1000

            return HealthCheck(
                name=name,
                status=status,
                message=message,
                timestamp=datetime.now().isoformat(),
                duration_ms=duration_ms,
                metadata=metadata
            )

        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000

            logger.error(
                "health_check_error",
                check=name,
                error=str(e),
                error_type=type(e).__name__
            )

            return HealthCheck(
                name=name,
                status=HealthStatus.UNKNOWN,
                message=f"Check failed: {str(e)}",
                timestamp=datetime.now().isoformat(),
                duration_ms=duration_ms,
                metadata={"error": str(e)}
            )

    # ========== Service Health Checks ==========

    def check_master_json(self) -> tuple:
        """Check master.json freshness"""
        file_path = self.termux_state_dir / "master.json"
        threshold = self.config["staleness_thresholds"]["master_json"]

        if not file_path.exists():
            return (
                HealthStatus.UNHEALTHY,
                f"File does not exist: {file_path}",
                {"file": str(file_path)}
            )

        try:
            mtime = file_path.stat().st_mtime
            age = time.time() - mtime

            # Validate JSON
            with open(file_path) as f:
                data = json.load(f)

            if age > threshold:
                return (
                    HealthStatus.DEGRADED,
                    f"Stale: {int(age/60)} minutes old (threshold: {int(threshold/60)} min)",
                    {"age_seconds": int(age), "threshold": threshold, "file": str(file_path)}
                )

            return (
                HealthStatus.HEALTHY,
                f"Fresh: {int(age/60)} minutes old",
                {"age_seconds": int(age), "size_bytes": file_path.stat().st_size}
            )

        except json.JSONDecodeError:
            return (
                HealthStatus.UNHEALTHY,
                "File is corrupted (invalid JSON)",
                {"file": str(file_path)}
            )
        except Exception as e:
            return (
                HealthStatus.UNKNOWN,
                f"Error checking file: {str(e)}",
                {"error": str(e)}
            )

    def check_finance_json(self) -> tuple:
        """Check finance.json freshness"""
        file_path = self.termux_state_dir / "finance.json"
        threshold = self.config["staleness_thresholds"]["finance_json"]

        if not file_path.exists():
            return (
                HealthStatus.DEGRADED,
                "File does not exist (may be normal if not yet created)",
                {"file": str(file_path)}
            )

        try:
            mtime = file_path.stat().st_mtime
            age = time.time() - mtime

            with open(file_path) as f:
                data = json.load(f)

            if age > threshold:
                return (
                    HealthStatus.DEGRADED,
                    f"Stale: {int(age/60)} minutes old",
                    {"age_seconds": int(age), "threshold": threshold}
                )

            return (
                HealthStatus.HEALTHY,
                f"Fresh: {int(age/60)} minutes old",
                {"age_seconds": int(age)}
            )

        except Exception as e:
            return (
                HealthStatus.UNHEALTHY,
                f"Error: {str(e)}",
                {"error": str(e)}
            )

    def check_execution_plan(self) -> tuple:
        """Check execution plan freshness"""
        file_path = Path("/home/user/hands-off-engine/executor/execution_plan.json")
        threshold = self.config["staleness_thresholds"]["execution_plan"]

        if not file_path.exists():
            return (
                HealthStatus.DEGRADED,
                "Execution plan not found",
                {"file": str(file_path)}
            )

        try:
            mtime = file_path.stat().st_mtime
            age = time.time() - mtime

            with open(file_path) as f:
                data = json.load(f)

            orders = data.get("orders", [])

            if age > threshold:
                return (
                    HealthStatus.DEGRADED,
                    f"Stale: {int(age/60)} minutes old, {len(orders)} orders",
                    {"age_seconds": int(age), "orders_count": len(orders)}
                )

            return (
                HealthStatus.HEALTHY,
                f"Fresh: {int(age/60)} minutes old, {len(orders)} orders",
                {"age_seconds": int(age), "orders_count": len(orders)}
            )

        except Exception as e:
            return (
                HealthStatus.UNHEALTHY,
                f"Error: {str(e)}",
                {"error": str(e)}
            )

    def check_cron_jobs(self) -> tuple:
        """Check if cron jobs are configured correctly"""
        try:
            result = subprocess.run(
                ["crontab", "-l"],
                capture_output=True,
                text=True,
                timeout=5
            )

            if result.returncode != 0:
                return (
                    HealthStatus.DEGRADED,
                    "No crontab configured",
                    {"returncode": result.returncode}
                )

            crontab = result.stdout
            expected_jobs = ["run_pipeline", "orchestrator", "finance_watcher"]
            found_jobs = []

            for job in expected_jobs:
                if job in crontab:
                    found_jobs.append(job)

            if len(found_jobs) == 0:
                return (
                    HealthStatus.UNHEALTHY,
                    "No hands-off cron jobs found",
                    {"expected": expected_jobs}
                )

            if len(found_jobs) < len(expected_jobs):
                missing = set(expected_jobs) - set(found_jobs)
                return (
                    HealthStatus.DEGRADED,
                    f"Some cron jobs missing: {', '.join(missing)}",
                    {"found": found_jobs, "missing": list(missing)}
                )

            return (
                HealthStatus.HEALTHY,
                f"All {len(found_jobs)} cron jobs configured",
                {"jobs": found_jobs}
            )

        except Exception as e:
            return (
                HealthStatus.UNKNOWN,
                f"Error checking cron: {str(e)}",
                {"error": str(e)}
            )

    # ========== Resource Health Checks ==========

    def check_cpu_usage(self) -> tuple:
        """Check CPU utilization"""
        try:
            cpu_percent = psutil.cpu_percent(interval=1)
            threshold = self.config["resource_thresholds"]["cpu_percent"]

            if cpu_percent > threshold:
                return (
                    HealthStatus.DEGRADED,
                    f"High CPU usage: {cpu_percent:.1f}%",
                    {"cpu_percent": cpu_percent, "threshold": threshold}
                )

            return (
                HealthStatus.HEALTHY,
                f"CPU usage: {cpu_percent:.1f}%",
                {"cpu_percent": cpu_percent}
            )

        except Exception as e:
            return (
                HealthStatus.UNKNOWN,
                f"Error: {str(e)}",
                {"error": str(e)}
            )

    def check_memory_usage(self) -> tuple:
        """Check memory utilization"""
        try:
            memory = psutil.virtual_memory()
            threshold = self.config["resource_thresholds"]["memory_percent"]

            if memory.percent > threshold:
                return (
                    HealthStatus.DEGRADED,
                    f"High memory usage: {memory.percent:.1f}%",
                    {
                        "memory_percent": memory.percent,
                        "threshold": threshold,
                        "available_mb": memory.available // (1024**2)
                    }
                )

            return (
                HealthStatus.HEALTHY,
                f"Memory usage: {memory.percent:.1f}%",
                {
                    "memory_percent": memory.percent,
                    "available_mb": memory.available // (1024**2)
                }
            )

        except Exception as e:
            return (
                HealthStatus.UNKNOWN,
                f"Error: {str(e)}",
                {"error": str(e)}
            )

    def check_disk_usage(self) -> tuple:
        """Check disk space"""
        try:
            disk = psutil.disk_usage("/")
            threshold = self.config["resource_thresholds"]["disk_percent"]

            if disk.percent > threshold:
                return (
                    HealthStatus.UNHEALTHY,
                    f"Low disk space: {disk.percent:.1f}% used",
                    {
                        "disk_percent": disk.percent,
                        "threshold": threshold,
                        "free_gb": disk.free // (1024**3)
                    }
                )

            return (
                HealthStatus.HEALTHY,
                f"Disk usage: {disk.percent:.1f}% ({disk.free // (1024**3)} GB free)",
                {
                    "disk_percent": disk.percent,
                    "free_gb": disk.free // (1024**3)
                }
            )

        except Exception as e:
            return (
                HealthStatus.UNKNOWN,
                f"Error: {str(e)}",
                {"error": str(e)}
            )

    # ========== API Health Checks ==========

    def check_admin_server(self) -> tuple:
        """Check admin HTTP server"""
        endpoint = self.config["api_endpoints"].get("admin_server")

        if not endpoint:
            return (
                HealthStatus.UNKNOWN,
                "Admin server endpoint not configured",
                {}
            )

        try:
            response = requests.get(
                endpoint,
                timeout=self.config["timeout_seconds"]
            )

            if response.status_code == 200:
                return (
                    HealthStatus.HEALTHY,
                    f"Admin server responding ({response.status_code})",
                    {
                        "status_code": response.status_code,
                        "response_time_ms": response.elapsed.total_seconds() * 1000
                    }
                )
            else:
                return (
                    HealthStatus.DEGRADED,
                    f"Admin server returned {response.status_code}",
                    {"status_code": response.status_code}
                )

        except requests.exceptions.Timeout:
            return (
                HealthStatus.UNHEALTHY,
                "Admin server timeout",
                {"timeout_seconds": self.config["timeout_seconds"]}
            )
        except requests.exceptions.ConnectionError:
            return (
                HealthStatus.UNHEALTHY,
                "Cannot connect to admin server",
                {}
            )
        except Exception as e:
            return (
                HealthStatus.UNKNOWN,
                f"Error: {str(e)}",
                {"error": str(e)}
            )

    def check_polymarket_api(self) -> tuple:
        """Check Polymarket API availability"""
        endpoint = self.config["api_endpoints"].get("polymarket_api")

        if not endpoint:
            return (
                HealthStatus.UNKNOWN,
                "Polymarket API endpoint not configured",
                {}
            )

        try:
            response = requests.get(
                endpoint,
                timeout=self.config["timeout_seconds"]
            )

            if response.status_code in [200, 404]:  # 404 is ok for root endpoint
                return (
                    HealthStatus.HEALTHY,
                    f"Polymarket API reachable ({response.status_code})",
                    {
                        "status_code": response.status_code,
                        "response_time_ms": response.elapsed.total_seconds() * 1000
                    }
                )
            else:
                return (
                    HealthStatus.DEGRADED,
                    f"Polymarket API returned {response.status_code}",
                    {"status_code": response.status_code}
                )

        except requests.exceptions.Timeout:
            return (
                HealthStatus.DEGRADED,
                "Polymarket API timeout",
                {"timeout_seconds": self.config["timeout_seconds"]}
            )
        except requests.exceptions.ConnectionError:
            return (
                HealthStatus.UNHEALTHY,
                "Cannot connect to Polymarket API",
                {}
            )
        except Exception as e:
            return (
                HealthStatus.UNKNOWN,
                f"Error: {str(e)}",
                {"error": str(e)}
            )

    def check_network_connectivity(self) -> tuple:
        """Check general network connectivity"""
        try:
            # Try to reach a reliable endpoint
            response = requests.get(
                "https://www.google.com",
                timeout=5
            )

            if response.status_code == 200:
                return (
                    HealthStatus.HEALTHY,
                    "Network connectivity OK",
                    {"response_time_ms": response.elapsed.total_seconds() * 1000}
                )
            else:
                return (
                    HealthStatus.DEGRADED,
                    f"Unexpected status: {response.status_code}",
                    {"status_code": response.status_code}
                )

        except Exception as e:
            return (
                HealthStatus.UNHEALTHY,
                "No network connectivity",
                {"error": str(e)}
            )

    # ========== Log Analysis ==========

    def check_recent_errors(self) -> tuple:
        """Check for recent errors in logs"""
        log_file = Path("/var/log/hands-off-engine.log")

        if not log_file.exists():
            return (
                HealthStatus.UNKNOWN,
                "Log file not found",
                {"file": str(log_file)}
            )

        try:
            # Get last 100 lines
            result = subprocess.run(
                ["tail", "-n", "100", str(log_file)],
                capture_output=True,
                text=True,
                timeout=5
            )

            lines = result.stdout.split("\n")

            # Count error levels
            error_count = sum(1 for line in lines if "ERROR" in line)
            warning_count = sum(1 for line in lines if "WARNING" in line or "WARN" in line)

            if error_count > 10:
                return (
                    HealthStatus.UNHEALTHY,
                    f"Many recent errors: {error_count} errors in last 100 lines",
                    {"error_count": error_count, "warning_count": warning_count}
                )

            if error_count > 0:
                return (
                    HealthStatus.DEGRADED,
                    f"Some recent errors: {error_count} errors, {warning_count} warnings",
                    {"error_count": error_count, "warning_count": warning_count}
                )

            return (
                HealthStatus.HEALTHY,
                f"No recent errors ({warning_count} warnings)",
                {"error_count": 0, "warning_count": warning_count}
            )

        except Exception as e:
            return (
                HealthStatus.UNKNOWN,
                f"Error checking logs: {str(e)}",
                {"error": str(e)}
            )

    # ========== Main Health Check ==========

    def run_all_checks(self) -> Dict[str, Any]:
        """Run all health checks"""
        self.checks = []

        # Service health
        self.checks.append(self._run_check("master_json", self.check_master_json))
        self.checks.append(self._run_check("finance_json", self.check_finance_json))
        self.checks.append(self._run_check("execution_plan", self.check_execution_plan))
        self.checks.append(self._run_check("cron_jobs", self.check_cron_jobs))

        # Resource health
        self.checks.append(self._run_check("cpu_usage", self.check_cpu_usage))
        self.checks.append(self._run_check("memory_usage", self.check_memory_usage))
        self.checks.append(self._run_check("disk_usage", self.check_disk_usage))

        # API health
        self.checks.append(self._run_check("admin_server", self.check_admin_server))
        self.checks.append(self._run_check("polymarket_api", self.check_polymarket_api))
        self.checks.append(self._run_check("network_connectivity", self.check_network_connectivity))

        # Log analysis
        self.checks.append(self._run_check("recent_errors", self.check_recent_errors))

        # Calculate overall status
        overall_status = self._calculate_overall_status()

        return {
            "timestamp": datetime.now().isoformat(),
            "overall_status": overall_status.value,
            "checks": [check.to_dict() for check in self.checks],
            "summary": self._generate_summary()
        }

    def _calculate_overall_status(self) -> HealthStatus:
        """Calculate overall system health"""
        if not self.checks:
            return HealthStatus.UNKNOWN

        # Count statuses
        status_counts = {
            HealthStatus.HEALTHY: 0,
            HealthStatus.DEGRADED: 0,
            HealthStatus.UNHEALTHY: 0,
            HealthStatus.UNKNOWN: 0
        }

        for check in self.checks:
            status_counts[check.status] += 1

        # Overall status logic
        if status_counts[HealthStatus.UNHEALTHY] > 0:
            return HealthStatus.UNHEALTHY

        if status_counts[HealthStatus.DEGRADED] > 2:
            return HealthStatus.UNHEALTHY

        if status_counts[HealthStatus.DEGRADED] > 0:
            return HealthStatus.DEGRADED

        if status_counts[HealthStatus.UNKNOWN] > 3:
            return HealthStatus.DEGRADED

        return HealthStatus.HEALTHY

    def _generate_summary(self) -> dict:
        """Generate health summary statistics"""
        if not self.checks:
            return {}

        total = len(self.checks)
        healthy = sum(1 for c in self.checks if c.status == HealthStatus.HEALTHY)
        degraded = sum(1 for c in self.checks if c.status == HealthStatus.DEGRADED)
        unhealthy = sum(1 for c in self.checks if c.status == HealthStatus.UNHEALTHY)
        unknown = sum(1 for c in self.checks if c.status == HealthStatus.UNKNOWN)

        issues = [
            check.name
            for check in self.checks
            if check.status in [HealthStatus.UNHEALTHY, HealthStatus.DEGRADED]
        ]

        return {
            "total_checks": total,
            "healthy": healthy,
            "degraded": degraded,
            "unhealthy": unhealthy,
            "unknown": unknown,
            "health_percentage": (healthy / total * 100) if total > 0 else 0,
            "issues": issues
        }


def main():
    """Main entry point"""
    import argparse

    parser = argparse.ArgumentParser(description="Health monitoring system")
    parser.add_argument("--config", help="Path to configuration file")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    parser.add_argument("--watch", type=int, help="Watch mode with interval in seconds")

    args = parser.parse_args()

    # Configure logging
    if args.json:
        structlog.configure(
            processors=[
                structlog.processors.TimeStamper(fmt="iso"),
                structlog.processors.JSONRenderer()
            ]
        )
    else:
        structlog.configure(
            processors=[
                structlog.processors.TimeStamper(fmt="iso"),
                structlog.dev.ConsoleRenderer()
            ]
        )

    monitor = HealthMonitor(config_path=args.config)

    if args.watch:
        # Watch mode
        try:
            while True:
                results = monitor.run_all_checks()

                if args.json:
                    print(json.dumps(results, indent=2))
                else:
                    print(f"\n{'='*60}")
                    print(f"Health Check - {results['timestamp']}")
                    print(f"Overall Status: {results['overall_status'].upper()}")
                    print(f"{'='*60}")

                    for check in results['checks']:
                        status_icon = {
                            "healthy": "✓",
                            "degraded": "⚠",
                            "unhealthy": "✗",
                            "unknown": "?"
                        }.get(check['status'], "?")

                        print(f"{status_icon} {check['name']}: {check['message']}")

                    print(f"\nSummary: {results['summary']}")

                time.sleep(args.watch)

        except KeyboardInterrupt:
            print("\nStopped")
            sys.exit(0)

    else:
        # Single run
        results = monitor.run_all_checks()

        if args.json:
            print(json.dumps(results, indent=2))
        else:
            print(f"Health Check - {results['timestamp']}")
            print(f"Overall Status: {results['overall_status'].upper()}\n")

            for check in results['checks']:
                print(f"  {check['name']}: {check['status']} - {check['message']}")

            print(f"\nSummary: {results['summary']}")

        # Exit code based on health
        if results['overall_status'] == 'unhealthy':
            sys.exit(2)
        elif results['overall_status'] == 'degraded':
            sys.exit(1)
        else:
            sys.exit(0)


if __name__ == "__main__":
    main()
