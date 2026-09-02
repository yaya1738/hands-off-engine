#!/usr/bin/env python3
"""Self-healing controller with fail-closed mutation boundaries.

Health detection remains available. Remediation that changes services, files,
or locks is recorded as a governed request instead of being executed here.
FactoryAuthorityGateway is the sole execution authority.
"""

import json
import os
import signal
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

import structlog

logger = structlog.get_logger(__name__)


class HealingAction:
    """Represents an observable healing condition and governed remediation."""

    def __init__(
        self,
        name: str,
        check: Callable[[], bool],
        heal: Callable[[], bool],
        severity: str = "warning",
        cooldown: int = 300,
    ):
        self.name = name
        self.check = check
        self.heal = heal
        self.severity = severity
        self.cooldown = cooldown
        self.last_heal_time: Optional[datetime] = None
        self.heal_count = 0
        self.heal_success_count = 0

    def should_heal(self) -> bool:
        if not self.check():
            return False
        if self.last_heal_time is None:
            return True
        return (datetime.now() - self.last_heal_time).total_seconds() >= self.cooldown

    def execute_heal(self) -> bool:
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
                success_rate=f"{self.heal_success_count}/{self.heal_count}",
            )
            return success
        except Exception as exc:
            logger.error(
                "healing_action_failed",
                action=self.name,
                error=str(exc),
                error_type=type(exc).__name__,
            )
            return False


class SelfHealController:
    """Health observer; remediation is delegated to FactoryAuthorityGateway."""

    def __init__(self, config_path: Optional[str] = None):
        self.config = self._load_config(config_path)
        self.actions: List[HealingAction] = []
        self.running = False
        self.check_interval = self.config.get("check_interval", 60)
        self.state_dir = Path(self.config.get("state_dir", "/home/user/hands-off-engine/state"))
        self.termux_state_dir = Path(
            self.config.get("termux_state_dir", "/home/user/hands-off-engine/termux-hands-off/state")
        )
        self._register_default_actions()

    def _load_config(self, config_path: Optional[str]) -> dict:
        if config_path and os.path.exists(config_path):
            try:
                with open(config_path, encoding="utf-8") as handle:
                    return json.load(handle)
            except Exception as exc:
                logger.warning("config_load_failed", error=str(exc))

        return {
            "check_interval": 60,
            "state_dir": "/home/user/hands-off-engine/state",
            "termux_state_dir": "/home/user/hands-off-engine/termux-hands-off/state",
            "staleness_thresholds": {
                "master_json": 2700,
                "finance_json": 3600,
                "execution_plan": 1800,
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
        self.register_action(
            "restart_stale_orchestrator",
            lambda: self._is_file_stale(self.termux_state_dir / "master.json", self.config["staleness_thresholds"]["master_json"]),
            lambda: self._request_governed_healing("restart_stale_orchestrator", "orchestrator"),
            "error", 900,
        )
        self.register_action(
            "restart_stale_finance_watcher",
            lambda: self._is_file_stale(self.termux_state_dir / "finance.json", self.config["staleness_thresholds"]["finance_json"]),
            lambda: self._request_governed_healing("restart_stale_finance_watcher", "finance_watcher"),
            "warning", 900,
        )
        self.register_action(
            "restart_stale_executor",
            lambda: self._is_file_stale(Path("/home/user/hands-off-engine/executor/execution_plan.json"), self.config["staleness_thresholds"]["execution_plan"]),
            lambda: self._request_governed_healing("restart_stale_executor", "executor"),
            "error", 1800,
        )
        self.register_action(
            "cleanup_disk_space",
            self._is_disk_space_low,
            lambda: self._request_governed_healing("cleanup_disk_space", "disk_cleanup"),
            "warning", 3600,
        )
        self.register_action(
            "fix_corrupted_state",
            self._has_corrupted_state_files,
            lambda: self._request_governed_healing("fix_corrupted_state", "restore_state_backup"),
            "error", 600,
        )
        self.register_action(
            "clear_stale_locks",
            self._has_stale_locks,
            lambda: self._request_governed_healing("clear_stale_locks", "clear_locks"),
            "warning", 300,
        )

    def register_action(
        self,
        name: str,
        check: Callable[[], bool],
        heal: Callable[[], bool],
        severity: str = "warning",
        cooldown: int = 300,
    ):
        self.actions.append(HealingAction(name, check, heal, severity, cooldown))
        logger.info("healing_action_registered", action=name, severity=severity, cooldown=cooldown)

    def _is_file_stale(self, file_path: Path, max_age_seconds: int) -> bool:
        if not file_path.exists():
            logger.debug("file_not_found", file=str(file_path))
            return True
        try:
            age = time.time() - file_path.stat().st_mtime
            if age > max_age_seconds:
                logger.warning("file_stale", file=str(file_path), age_seconds=int(age), threshold_seconds=max_age_seconds)
                return True
            return False
        except Exception as exc:
            logger.error("file_check_error", file=str(file_path), error=str(exc))
            return False

    def _request_governed_healing(self, action: str, target: str) -> bool:
        """Record a remediation request; never execute it from this legacy controller."""
        logger.warning(
            "selfheal_mutation_blocked",
            action=action,
            target=target,
            authority="FactoryAuthorityGateway",
            status="blocked",
        )
        return False

    def _restart_service(self, service_name: str) -> bool:
        """Legacy compatibility entrypoint; service mutation is forbidden here."""
        return self._request_governed_healing("restart_service", service_name)

    def _is_disk_space_low(self) -> bool:
        try:
            stat = os.statvfs("/")
            free_gb = (stat.f_bavail * stat.f_frsize) / (1024 ** 3)
            threshold = self.config["disk_cleanup"]["min_free_gb"]
            if free_gb < threshold:
                logger.warning("disk_space_low", free_gb=f"{free_gb:.2f}", threshold_gb=threshold)
                return True
            return False
        except Exception as exc:
            logger.error("disk_check_error", error=str(exc))
            return False

    def _cleanup_old_files(self) -> bool:
        """Legacy compatibility entrypoint; file deletion is forbidden here."""
        return self._request_governed_healing("cleanup_old_files", "configured_cleanup_patterns")

    def _has_corrupted_state_files(self) -> bool:
        critical_files = [
            self.termux_state_dir / "master.json",
            self.termux_state_dir / "finance.json",
            Path("/home/user/hands-off-engine/executor/execution_plan.json"),
        ]
        for file_path in critical_files:
            if not file_path.exists():
                continue
            try:
                with open(file_path, encoding="utf-8") as handle:
                    json.load(handle)
            except json.JSONDecodeError:
                logger.error("corrupted_json_file", file=str(file_path))
                return True
            except Exception as exc:
                logger.debug("file_check_error", file=str(file_path), error=str(exc))
        return False

    def _restore_from_backup(self) -> bool:
        """Legacy compatibility entrypoint; backup restoration is forbidden here."""
        return self._request_governed_healing("restore_from_backup", "critical_state_files")

    def _has_stale_locks(self) -> bool:
        """Detect stale locks without invoking an external command."""
        patterns = ("/tmp/hands-off-*.lock", "/var/lock/hands-off-*.lock")
        cutoff = time.time() - 3600
        for pattern in patterns:
            parent = Path(pattern).parent
            name_pattern = Path(pattern).name
            try:
                for lock_path in parent.glob(name_pattern):
                    if lock_path.is_file() and lock_path.stat().st_mtime < cutoff:
                        logger.warning("stale_lock_found", file=str(lock_path))
                        return True
            except Exception as exc:
                logger.debug("lock_check_error", pattern=pattern, error=str(exc))
        return False

    def _clear_locks(self) -> bool:
        """Legacy compatibility entrypoint; lock deletion is forbidden here."""
        return self._request_governed_healing("clear_locks", "stale_lock_files")

    def run_once(self) -> Dict[str, Any]:
        results: Dict[str, Any] = {
            "timestamp": datetime.now().isoformat(),
            "checks_run": 0,
            "heals_attempted": 0,
            "heals_successful": 0,
            "actions": [],
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
                    "success_rate": f"{action.heal_success_count}/{action.heal_count}",
                })
        return results

    def run(self):
        self.running = True
        logger.info("selfheal_controller_started", check_interval=self.check_interval, actions_registered=len(self.actions))

        def signal_handler(signum, _frame):
            logger.info("shutdown_signal_received", signal=signum)
            self.running = False

        signal.signal(signal.SIGTERM, signal_handler)
        signal.signal(signal.SIGINT, signal_handler)
        consecutive_failures = 0

        while self.running:
            try:
                results = self.run_once()
                logger.info("selfheal_iteration_complete", **results)
                consecutive_failures = 0
                time.sleep(self.check_interval)
            except KeyboardInterrupt:
                break
            except Exception as exc:
                consecutive_failures += 1
                logger.error("selfheal_iteration_error", error=str(exc), error_type=type(exc).__name__, consecutive_failures=consecutive_failures)
                if consecutive_failures >= self.config["max_consecutive_failures"] and self.config["emergency_pause_on_failures"]:
                    logger.critical("emergency_pause_triggered", consecutive_failures=consecutive_failures)
                    time.sleep(self.check_interval * 5)
                else:
                    time.sleep(self.check_interval)
        logger.info("selfheal_controller_stopped")

    def get_status(self) -> dict:
        return {
            "running": self.running,
            "check_interval": self.check_interval,
            "actions_registered": len(self.actions),
            "authority": "FactoryAuthorityGateway",
            "mutation_mode": "fail_closed",
            "actions": [
                {
                    "name": action.name,
                    "severity": action.severity,
                    "heal_count": action.heal_count,
                    "success_count": action.heal_success_count,
                    "success_rate": f"{action.heal_success_count}/{action.heal_count}" if action.heal_count else "N/A",
                    "last_heal_time": action.last_heal_time.isoformat() if action.last_heal_time else None,
                    "cooldown": action.cooldown,
                }
                for action in self.actions
            ],
        }


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Self-healing controller")
    parser.add_argument("--config", help="Path to configuration file")
    parser.add_argument("--once", action="store_true", help="Run once and exit")
    parser.add_argument("--status", action="store_true", help="Show status and exit")
    parser.add_argument("--force", action="store_true", help="Deprecated; remediation remains governed")
    parser.add_argument("--service", help="Specific service to evaluate")
    args = parser.parse_args()

    controller = SelfHealController(config_path=args.config)
    if args.status:
        print(json.dumps(controller.get_status(), indent=2))
        return
    if args.force and args.service:
        for action in controller.actions:
            if args.service in action.name:
                action.last_heal_time = None
                success = action.execute_heal()
                print(f"Governed healing request: {action.name} -> {'ACCEPTED' if success else 'BLOCKED'}")
                return
        print(f"Service '{args.service}' not found")
        return
    if args.once:
        print(json.dumps(controller.run_once(), indent=2))
    else:
        controller.run()


if __name__ == "__main__":
    main()
