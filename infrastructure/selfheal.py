#!/usr/bin/env python3
"""
Self-healing controller for the hands-off engine.

Automatically detects and remediates common issues:
- Stale services (restart processes)
- Disk space issues (cleanup old files)
- Network connectivity problems
- State file corruption
- Resource exhaustion

Runs continuously and takes action without user intervention.
"""

import os
import sys
import time
import json
import subprocess
import signal
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Callable
import structlog

logger = structlog.get_logger(__name__)


class HealingAction:
    """Represents a self-healing action"""

    def __init__(
        self,
        name: str,
        check: Callable[[], bool],
        heal: Callable[[], bool],
        severity: str = "warning",
        cooldown: int = 300,  # 5 minutes
    ):
        """
        Args:
            name: Human-readable name
            check: Function that returns True if healing needed
            heal: Function that performs healing, returns True if successful
            severity: "info", "warning", "error", or "critical"
            cooldown: Minimum seconds between heal attempts
        """
        self.name = name
        self.check = check
        self.heal = heal
        self.severity = severity
        self.cooldown = cooldown
        self.last_heal_time: Optional[datetime] = None
        self.heal_count = 0
        self.heal_success_count = 0

    def should_heal(self) -> bool:
        """Check if healing is needed and cooldown has elapsed"""
        if not self.check():
            return False

        if self.last_heal_time is None:
            return True

        elapsed = (datetime.now() - self.last_heal_time).total_seconds()
        return elapsed >= self.cooldown

    def execute_heal(self) -> bool:
        """Execute healing action"""
        self.heal_count += 1
        self.last_heal_time = datetime.now()

        try:
            success = self.heal()
            if success:
                self.heal_success_count += 1

            logger.info(
                "healing_action_executed",
                action=self.name,
                success=success,
                severity=self.severity,
                total_heals=self.heal_count,
                success_rate=f"{self.heal_success_count}/{self.heal_count}"
            )

            return success

        except Exception as e:
            logger.error(
                "healing_action_failed",
                action=self.name,
                error=str(e),
                error_type=type(e).__name__
            )
            return False


class SelfHealController:
    """Main self-healing controller"""

    def __init__(self, config_path: Optional[str] = None):
        """
        Args:
            config_path: Path to configuration file
        """
        self.config = self._load_config(config_path)
        self.actions: List[HealingAction] = []
        self.running = False
        self.check_interval = self.config.get("check_interval", 60)  # 1 minute
        self.state_dir = Path(self.config.get("state_dir", "/home/user/hands-off-engine/state"))
        self.termux_state_dir = Path(self.config.get("termux_state_dir", "/home/user/hands-off-engine/termux-hands-off/state"))

        self._register_default_actions()

    def _load_config(self, config_path: Optional[str]) -> dict:
        """Load configuration from file"""
        if config_path and os.path.exists(config_path):
            try:
                with open(config_path) as f:
                    return json.load(f)
            except Exception as e:
                logger.warning("config_load_failed", error=str(e))

        # Default configuration
        return {
            "check_interval": 60,
            "state_dir": "/home/user/hands-off-engine/state",
            "termux_state_dir": "/home/user/hands-off-engine/termux-hands-off/state",
            "staleness_thresholds": {
                "master_json": 2700,  # 45 minutes
                "finance_json": 3600,  # 60 minutes
                "execution_plan": 1800,  # 30 minutes
            },
            "restart_commands": {
                "orchestrator": "systemctl restart hands-off-orchestrator || true",
                "executor": "systemctl restart hands-off-executor || true",
                "finance_watcher": "systemctl restart hands-off-finance-watcher || true",
            },
            "disk_cleanup": {
                "min_free_gb": 5,
                "cleanup_patterns": [
                    "/var/log/hands-off-engine/*.log.old",
                    "/tmp/hands-off-*",
                    "/home/user/hands-off-engine/state/*.bak.*",
                ],
                "max_backup_age_days": 30,
            },
            "max_consecutive_failures": 3,
            "emergency_pause_on_failures": True,
        }

    def _register_default_actions(self):
        """Register default healing actions"""

        # Action 1: Check and restart stale orchestrator
        self.register_action(
            name="restart_stale_orchestrator",
            check=lambda: self._is_file_stale(
                self.termux_state_dir / "master.json",
                self.config["staleness_thresholds"]["master_json"]
            ),
            heal=lambda: self._restart_service("orchestrator"),
            severity="error",
            cooldown=900  # 15 minutes
        )

        # Action 2: Check and restart stale finance watcher
        self.register_action(
            name="restart_stale_finance_watcher",
            check=lambda: self._is_file_stale(
                self.termux_state_dir / "finance.json",
                self.config["staleness_thresholds"]["finance_json"]
            ),
            heal=lambda: self._restart_service("finance_watcher"),
            severity="warning",
            cooldown=900
        )

        # Action 3: Check and restart stale executor
        self.register_action(
            name="restart_stale_executor",
            check=lambda: self._is_file_stale(
                Path("/home/user/hands-off-engine/executor/execution_plan.json"),
                self.config["staleness_thresholds"]["execution_plan"]
            ),
            heal=lambda: self._restart_service("executor"),
            severity="error",
            cooldown=1800  # 30 minutes
        )

        # Action 4: Clean up disk space
        self.register_action(
            name="cleanup_disk_space",
            check=lambda: self._is_disk_space_low(),
            heal=lambda: self._cleanup_old_files(),
            severity="warning",
            cooldown=3600  # 1 hour
        )

        # Action 5: Fix corrupted state files
        self.register_action(
            name="fix_corrupted_state",
            check=lambda: self._has_corrupted_state_files(),
            heal=lambda: self._restore_from_backup(),
            severity="error",
            cooldown=600  # 10 minutes
        )

        # Action 6: Clear stale locks
        self.register_action(
            name="clear_stale_locks",
            check=lambda: self._has_stale_locks(),
            heal=lambda: self._clear_locks(),
            severity="warning",
            cooldown=300  # 5 minutes
        )

    def register_action(
        self,
        name: str,
        check: Callable[[], bool],
        heal: Callable[[], bool],
        severity: str = "warning",
        cooldown: int = 300
    ):
        """Register a new healing action"""
        action = HealingAction(
            name=name,
            check=check,
            heal=heal,
            severity=severity,
            cooldown=cooldown
        )
        self.actions.append(action)

        logger.info(
            "healing_action_registered",
            action=name,
            severity=severity,
            cooldown=cooldown
        )

    def _is_file_stale(self, file_path: Path, max_age_seconds: int) -> bool:
        """Check if file hasn't been updated recently"""
        if not file_path.exists():
            logger.debug("file_not_found", file=str(file_path))
            return True

        try:
            mtime = file_path.stat().st_mtime
            age = time.time() - mtime

            if age > max_age_seconds:
                logger.warning(
                    "file_stale",
                    file=str(file_path),
                    age_seconds=int(age),
                    threshold_seconds=max_age_seconds
                )
                return True

            return False

        except Exception as e:
            logger.error("file_check_error", file=str(file_path), error=str(e))
            return False

    def _restart_service(self, service_name: str) -> bool:
        """Restart a service"""
        command = self.config["restart_commands"].get(service_name)

        if not command:
            logger.error("restart_command_not_found", service=service_name)
            return False

        try:
            logger.info("restarting_service", service=service_name, command=command)

            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=30
            )

            success = result.returncode == 0

            if success:
                logger.info(
                    "service_restarted",
                    service=service_name,
                    stdout=result.stdout[:200]
                )
            else:
                logger.error(
                    "service_restart_failed",
                    service=service_name,
                    returncode=result.returncode,
                    stderr=result.stderr[:200]
                )

            return success

        except subprocess.TimeoutExpired:
            logger.error("service_restart_timeout", service=service_name)
            return False
        except Exception as e:
            logger.error(
                "service_restart_error",
                service=service_name,
                error=str(e),
                error_type=type(e).__name__
            )
            return False

    def _is_disk_space_low(self) -> bool:
        """Check if disk space is running low"""
        try:
            stat = os.statvfs("/")
            free_gb = (stat.f_bavail * stat.f_frsize) / (1024**3)

            min_free = self.config["disk_cleanup"]["min_free_gb"]

            if free_gb < min_free:
                logger.warning(
                    "disk_space_low",
                    free_gb=f"{free_gb:.2f}",
                    threshold_gb=min_free
                )
                return True

            return False

        except Exception as e:
            logger.error("disk_check_error", error=str(e))
            return False

    def _cleanup_old_files(self) -> bool:
        """Clean up old log files and backups"""
        try:
            patterns = self.config["disk_cleanup"]["cleanup_patterns"]
            max_age_days = self.config["disk_cleanup"]["max_backup_age_days"]
            cutoff_time = time.time() - (max_age_days * 86400)

            deleted_count = 0
            freed_bytes = 0

            for pattern in patterns:
                try:
                    # Use find command for efficient file discovery
                    cmd = f"find {pattern} -type f -mtime +{max_age_days} 2>/dev/null"
                    result = subprocess.run(
                        cmd,
                        shell=True,
                        capture_output=True,
                        text=True,
                        timeout=30
                    )

                    for file_path in result.stdout.strip().split("\n"):
                        if file_path:
                            try:
                                size = os.path.getsize(file_path)
                                os.remove(file_path)
                                deleted_count += 1
                                freed_bytes += size
                            except Exception as e:
                                logger.debug("file_delete_error", file=file_path, error=str(e))

                except Exception as e:
                    logger.debug("cleanup_pattern_error", pattern=pattern, error=str(e))

            logger.info(
                "disk_cleanup_complete",
                deleted_files=deleted_count,
                freed_mb=f"{freed_bytes / (1024**2):.2f}"
            )

            return deleted_count > 0

        except Exception as e:
            logger.error("disk_cleanup_error", error=str(e))
            return False

    def _has_corrupted_state_files(self) -> bool:
        """Check for corrupted JSON state files"""
        critical_files = [
            self.termux_state_dir / "master.json",
            self.termux_state_dir / "finance.json",
            Path("/home/user/hands-off-engine/executor/execution_plan.json"),
        ]

        for file_path in critical_files:
            if not file_path.exists():
                continue

            try:
                with open(file_path) as f:
                    json.load(f)
            except json.JSONDecodeError:
                logger.error("corrupted_json_file", file=str(file_path))
                return True
            except Exception as e:
                logger.debug("file_check_error", file=str(file_path), error=str(e))

        return False

    def _restore_from_backup(self) -> bool:
        """Restore corrupted files from backups"""
        critical_files = [
            self.termux_state_dir / "master.json",
            self.termux_state_dir / "finance.json",
            Path("/home/user/hands-off-engine/executor/execution_plan.json"),
        ]

        restored_count = 0

        for file_path in critical_files:
            if not file_path.exists():
                continue

            try:
                # Test if file is valid JSON
                with open(file_path) as f:
                    json.load(f)
                continue  # File is valid, skip

            except json.JSONDecodeError:
                # Find most recent backup
                backup_pattern = f"{file_path}.bak.*"
                backups = sorted(file_path.parent.glob(f"{file_path.name}.bak.*"), reverse=True)

                for backup_path in backups:
                    try:
                        with open(backup_path) as f:
                            data = json.load(f)  # Validate backup

                        # Restore from backup
                        import shutil
                        shutil.copy2(backup_path, file_path)

                        logger.info(
                            "state_restored_from_backup",
                            file=str(file_path),
                            backup=str(backup_path)
                        )
                        restored_count += 1
                        break

                    except Exception as e:
                        logger.debug("backup_invalid", backup=str(backup_path), error=str(e))
                        continue

        return restored_count > 0

    def _has_stale_locks(self) -> bool:
        """Check for stale lock files"""
        lock_patterns = [
            "/tmp/hands-off-*.lock",
            "/var/lock/hands-off-*.lock",
        ]

        for pattern in lock_patterns:
            try:
                cmd = f"find {pattern} -type f -mmin +60 2>/dev/null"
                result = subprocess.run(
                    cmd,
                    shell=True,
                    capture_output=True,
                    text=True,
                    timeout=10
                )

                if result.stdout.strip():
                    logger.warning("stale_locks_found", pattern=pattern)
                    return True

            except Exception as e:
                logger.debug("lock_check_error", pattern=pattern, error=str(e))

        return False

    def _clear_locks(self) -> bool:
        """Clear stale lock files"""
        lock_patterns = [
            "/tmp/hands-off-*.lock",
            "/var/lock/hands-off-*.lock",
        ]

        cleared_count = 0

        for pattern in lock_patterns:
            try:
                cmd = f"find {pattern} -type f -mmin +60 -delete 2>/dev/null"
                result = subprocess.run(
                    cmd,
                    shell=True,
                    capture_output=True,
                    text=True,
                    timeout=10
                )

                if result.returncode == 0:
                    cleared_count += 1

            except Exception as e:
                logger.debug("lock_clear_error", pattern=pattern, error=str(e))

        logger.info("locks_cleared", patterns_processed=cleared_count)
        return cleared_count > 0

    def run_once(self) -> Dict[str, any]:
        """Run one iteration of health checks and healing"""
        results = {
            "timestamp": datetime.now().isoformat(),
            "checks_run": 0,
            "heals_attempted": 0,
            "heals_successful": 0,
            "actions": []
        }

        for action in self.actions:
            results["checks_run"] += 1

            if action.should_heal():
                results["heals_attempted"] += 1

                success = action.execute_heal()

                if success:
                    results["heals_successful"] += 1

                results["actions"].append({
                    "name": action.name,
                    "severity": action.severity,
                    "success": success,
                    "heal_count": action.heal_count,
                    "success_rate": f"{action.heal_success_count}/{action.heal_count}"
                })

        return results

    def run(self):
        """Run continuous self-healing loop"""
        self.running = True

        logger.info(
            "selfheal_controller_started",
            check_interval=self.check_interval,
            actions_registered=len(self.actions)
        )

        # Handle graceful shutdown
        def signal_handler(signum, frame):
            logger.info("shutdown_signal_received", signal=signum)
            self.running = False

        signal.signal(signal.SIGTERM, signal_handler)
        signal.signal(signal.SIGINT, signal_handler)

        consecutive_failures = 0

        while self.running:
            try:
                results = self.run_once()

                logger.info(
                    "selfheal_iteration_complete",
                    **results
                )

                # Reset failure counter on successful iteration
                consecutive_failures = 0

                # Wait for next iteration
                time.sleep(self.check_interval)

            except KeyboardInterrupt:
                logger.info("keyboard_interrupt_received")
                break

            except Exception as e:
                consecutive_failures += 1

                logger.error(
                    "selfheal_iteration_error",
                    error=str(e),
                    error_type=type(e).__name__,
                    consecutive_failures=consecutive_failures
                )

                # Emergency pause if too many failures
                if (consecutive_failures >= self.config["max_consecutive_failures"]
                    and self.config["emergency_pause_on_failures"]):

                    logger.critical(
                        "emergency_pause_triggered",
                        consecutive_failures=consecutive_failures,
                        threshold=self.config["max_consecutive_failures"]
                    )

                    # Try to notify user
                    try:
                        subprocess.run(
                            ["notify-send", "Hands-Off Engine: Emergency Pause",
                             f"Self-heal controller failed {consecutive_failures} times"],
                            timeout=5
                        )
                    except:
                        pass

                    # Pause for longer before retrying
                    time.sleep(self.check_interval * 5)

                else:
                    time.sleep(self.check_interval)

        logger.info("selfheal_controller_stopped")

    def get_status(self) -> dict:
        """Get controller status and action statistics"""
        return {
            "running": self.running,
            "check_interval": self.check_interval,
            "actions_registered": len(self.actions),
            "actions": [
                {
                    "name": action.name,
                    "severity": action.severity,
                    "heal_count": action.heal_count,
                    "success_count": action.heal_success_count,
                    "success_rate": f"{action.heal_success_count}/{action.heal_count}" if action.heal_count > 0 else "N/A",
                    "last_heal_time": action.last_heal_time.isoformat() if action.last_heal_time else None,
                    "cooldown": action.cooldown
                }
                for action in self.actions
            ]
        }


def main():
    """Main entry point"""
    import argparse

    parser = argparse.ArgumentParser(description="Self-healing controller")
    parser.add_argument("--config", help="Path to configuration file")
    parser.add_argument("--once", action="store_true", help="Run once and exit")
    parser.add_argument("--status", action="store_true", help="Show status and exit")
    parser.add_argument("--force", action="store_true", help="Force healing actions (ignore cooldowns)")
    parser.add_argument("--service", help="Specific service to heal")

    args = parser.parse_args()

    # Configure structured logging
    structlog.configure(
        processors=[
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.add_log_level,
            structlog.processors.JSONRenderer()
        ]
    )

    controller = SelfHealController(config_path=args.config)

    if args.status:
        status = controller.get_status()
        print(json.dumps(status, indent=2))
        sys.exit(0)

    if args.force and args.service:
        # Force heal specific service
        for action in controller.actions:
            if args.service in action.name:
                action.last_heal_time = None  # Reset cooldown
                success = action.execute_heal()
                print(f"Forced healing: {action.name} -> {'SUCCESS' if success else 'FAILED'}")
                sys.exit(0 if success else 1)

        print(f"Service '{args.service}' not found")
        sys.exit(1)

    if args.once:
        results = controller.run_once()
        print(json.dumps(results, indent=2))
    else:
        controller.run()


if __name__ == "__main__":
    main()
