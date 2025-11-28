"""
Autonomous Infrastructure Manager - Complete Self-Managing Infrastructure

The master controller for autonomous infrastructure management.
Runs continuously to ensure infrastructure is always optimal for trading.

Features:
- Continuous infrastructure monitoring
- Automatic scaling decisions
- Self-healing and recovery
- Budget-aware provisioning
- Zero user intervention required

The user should NEVER need to:
- Buy cloud servers manually
- Upgrade instance capabilities
- Purchase hardware
- Manage infrastructure scaling

Standard: Yair Siegel Master Level Operations - Full Self-Control
"""

import json
import signal
import sys
import time
import threading
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import asdict

from infrastructure.infra_types import (
    CloudProvider,
    InstanceSize,
    InfrastructureAction,
    ServerRole,
    ScalingDecision,
    InfrastructureBudget,
)
from infrastructure.cloud_providers import get_best_available_provider
from infrastructure.auto_provisioner import AutoProvisioner, get_auto_provisioner

# Import hardware monitoring
try:
    from hardware import (
        HardwareCollector,
        HardwareAnalyzer,
        HardwareHealth,
        HealthStatus,
        is_hardware_healthy,
        quick_health_check,
    )
    HARDWARE_AVAILABLE = True
except ImportError:
    HARDWARE_AVAILABLE = False


class AutonomousInfraManager:
    """
    Autonomous infrastructure management system.

    Continuously monitors and manages infrastructure without user intervention.
    Handles all scaling, provisioning, and maintenance automatically.
    """

    # Check intervals (seconds)
    NORMAL_CHECK_INTERVAL = 300      # 5 minutes normally
    DEGRADED_CHECK_INTERVAL = 60     # 1 minute when degraded
    CRITICAL_CHECK_INTERVAL = 30     # 30 seconds when critical

    def __init__(
        self,
        budget_monthly: float = 500.0,
        auto_provision: bool = True,
        auto_upgrade: bool = True,
        auto_scale: bool = True,
        dry_run: bool = False
    ):
        """
        Initialize the infrastructure manager.

        Args:
            budget_monthly: Maximum monthly infrastructure spend
            auto_provision: Automatically provision new servers when needed
            auto_upgrade: Automatically upgrade servers when needed
            auto_scale: Automatically scale horizontally when needed
            dry_run: Don't actually provision (for testing)
        """
        self.budget = InfrastructureBudget(
            monthly_limit=budget_monthly,
            auto_approve_hourly_increase=0.10,
            auto_approve_monthly_increase=min(50.0, budget_monthly * 0.1)
        )

        self.auto_provision = auto_provision
        self.auto_upgrade = auto_upgrade
        self.auto_scale = auto_scale
        self.dry_run = dry_run

        # Initialize provisioner
        self.provisioner = AutoProvisioner(
            budget=self.budget,
            dry_run=dry_run
        )

        # State
        self.running = False
        self._stop_event = threading.Event()
        self.last_check: Optional[datetime] = None
        self.last_health: Optional[Dict] = None
        self.consecutive_critical = 0

        # Statistics
        self.stats = {
            "checks": 0,
            "upgrades_executed": 0,
            "servers_provisioned": 0,
            "total_cost_saved": 0.0,
            "downtime_prevented_minutes": 0,
            "start_time": None
        }

        # Log path
        self.log_path = Path("logs/infrastructure")
        self.log_path.mkdir(parents=True, exist_ok=True)

        # Production servers config
        self.prod_servers_config = Path("config/production_servers.json")
        self.redundancy_checked = False
        self.redundancy_action_taken = False

        # Signal handlers
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)

    def _signal_handler(self, signum, frame):
        """Handle shutdown signals."""
        print(f"\n⚡ Received signal {signum}, shutting down...")
        self.stop()

    def start(self):
        """Start the autonomous infrastructure manager."""
        self.running = True
        self._stop_event.clear()
        self.stats["start_time"] = datetime.utcnow().isoformat()

        print("=" * 60)
        print("🚀 AUTONOMOUS INFRASTRUCTURE MANAGER")
        print("=" * 60)
        print(f"   Budget: ${self.budget.monthly_limit:.2f}/month")
        print(f"   Auto-provision: {self.auto_provision}")
        print(f"   Auto-upgrade: {self.auto_upgrade}")
        print(f"   Auto-scale: {self.auto_scale}")
        print(f"   Dry run: {self.dry_run}")
        print(f"   Provider: {self.provisioner.provider.value}")
        print("=" * 60)
        print("\nThe system will now manage all infrastructure autonomously.")
        print("User intervention is NOT required.")
        print("\nPress Ctrl+C to stop\n")

        # Initial check
        self._check_and_act()

        # Main loop
        try:
            while self.running and not self._stop_event.is_set():
                interval = self._get_check_interval()
                self._stop_event.wait(interval)

                if self.running:
                    self._check_and_act()

        except KeyboardInterrupt:
            pass
        finally:
            self.stop()

    def stop(self):
        """Stop the manager."""
        if not self.running:
            return

        self.running = False
        self._stop_event.set()

        # Save final state
        self._save_stats()

        print("\n" + "=" * 60)
        print("📊 INFRASTRUCTURE MANAGER STATISTICS")
        print("=" * 60)
        print(f"   Total checks: {self.stats['checks']}")
        print(f"   Upgrades executed: {self.stats['upgrades_executed']}")
        print(f"   Servers provisioned: {self.stats['servers_provisioned']}")
        print(f"   Downtime prevented: ~{self.stats['downtime_prevented_minutes']} minutes")
        print("=" * 60)

    def _check_and_act(self):
        """Perform one check cycle and take action if needed."""
        self.stats["checks"] += 1
        self.last_check = datetime.utcnow()

        try:
            # Get hardware health
            if HARDWARE_AVAILABLE:
                self.last_health = quick_health_check()
            else:
                self.last_health = {"status": "unknown", "score": 50}

            # CHECK REDUNDANCY - Single point of failure detection
            self._check_redundancy_and_act()

            # Analyze and make decisions
            decisions = self.provisioner.analyze_and_scale()

            # Handle decisions based on autonomy settings
            for decision in decisions:
                self._handle_decision(decision)

            # Check for critical situations
            self._check_critical_situations()

            # Print status
            self._print_status(decisions)

        except Exception as e:
            self._log_error(f"Check cycle error: {e}")

    def _handle_decision(self, decision: ScalingDecision):
        """Handle a scaling decision based on autonomy settings."""
        # Determine if we should auto-execute
        should_execute = False

        if decision.action == InfrastructureAction.UPGRADE_SERVER:
            should_execute = self.auto_upgrade

        elif decision.action == InfrastructureAction.PROVISION_SERVER:
            should_execute = self.auto_provision

        elif decision.action == InfrastructureAction.SCALE_HORIZONTALLY:
            should_execute = self.auto_scale

        elif decision.action == InfrastructureAction.TERMINATE_SERVER:
            # Be more careful with terminations
            should_execute = self.auto_scale and decision.cost_change < 0

        # Execute if appropriate
        if should_execute and not decision.executed:
            # Check budget
            if self._within_budget(decision):
                if not self.dry_run:
                    success = self.provisioner._execute_decision(decision)
                    if success:
                        self._update_stats(decision)
                        self._log_action(decision)
                else:
                    decision.execution_result = "DRY RUN"

    def _within_budget(self, decision: ScalingDecision) -> bool:
        """Check if decision is within budget."""
        current_spend = self.provisioner.get_current_spend()
        projected = current_spend + decision.cost_change

        # Allow if within limit
        if projected <= self.budget.monthly_limit:
            return True

        # Allow emergency situations even if over budget
        if decision.trading_impact in ["high", "critical"]:
            # Use emergency reserve
            if projected <= self.budget.monthly_limit + self.budget.reserved_for_emergency:
                return True

        return False

    def _check_redundancy_and_act(self):
        """
        Check for single-point-of-failure risk and automatically provision backup.

        This is a core autonomous decision - the system detects risk and acts
        WITHOUT requiring user intervention.
        """
        if self.redundancy_action_taken:
            return  # Already handled

        try:
            if not self.prod_servers_config.exists():
                return

            with open(self.prod_servers_config) as f:
                config = json.load(f)

            servers = config.get("production_servers", [])
            policy = config.get("redundancy_policy", {})

            min_servers = policy.get("min_trading_servers", 2)
            require_failover = policy.get("require_failover", True)
            auto_provision = policy.get("auto_provision_backup", True)

            # Count critical trading servers
            critical_servers = [s for s in servers if s.get("critical", False)]

            if len(critical_servers) < min_servers and require_failover:
                # SINGLE POINT OF FAILURE DETECTED
                print("\n" + "=" * 60)
                print("🚨 AUTONOMOUS DECISION: Single Point of Failure Detected")
                print("=" * 60)
                print(f"   Current trading servers: {len(critical_servers)}")
                print(f"   Required minimum: {min_servers}")
                print(f"   Risk: Complete trading halt if primary fails")
                print()

                if auto_provision and self.auto_provision:
                    # Check budget before provisioning
                    if self._within_budget_for_emergency():
                        print("   DECISION: Provision failover server")
                        print("   Reason: Protect live trading from hardware failure")

                        if not self.dry_run:
                            # Provision backup server
                            success, server, message = self.provisioner.provision_new_server(
                                role=ServerRole.TRADING_BACKUP,
                                size=InstanceSize.MEDIUM
                            )

                            if success:
                                self.stats["servers_provisioned"] += 1
                                self.redundancy_action_taken = True
                                print(f"   ✓ Failover server provisioned: {message}")

                                # Update config with new server
                                self._register_new_server(server)
                            else:
                                print(f"   ✗ Provisioning failed: {message}")
                                print("   Will retry on next cycle")
                        else:
                            print("   [DRY RUN] Would provision failover server")
                            self.redundancy_action_taken = True
                    else:
                        print("   ⚠️  Insufficient budget for failover")
                        print("   Adding to approval queue for budget increase")
                        self._request_budget_increase_for_redundancy()
                else:
                    print("   Auto-provision disabled - logging for review")

                print("=" * 60 + "\n")
                self.redundancy_checked = True

        except Exception as e:
            self._log_error(f"Redundancy check error: {e}")

    def _register_new_server(self, server):
        """Register a newly provisioned server in config."""
        try:
            with open(self.prod_servers_config) as f:
                config = json.load(f)

            config["production_servers"].append({
                "id": server.id if hasattr(server, 'id') else f"auto-{datetime.utcnow().strftime('%Y%m%d%H%M')}",
                "provider": self.provisioner.provider.value,
                "ip": server.ip if hasattr(server, 'ip') else "pending",
                "role": "trading_backup",
                "type": "auto_provisioned",
                "critical": True,
                "registered_at": datetime.utcnow().isoformat()
            })

            with open(self.prod_servers_config, 'w') as f:
                json.dump(config, f, indent=2)

        except Exception as e:
            self._log_error(f"Failed to register server: {e}")

    def _request_budget_increase_for_redundancy(self):
        """Request budget increase through approval queue for redundancy."""
        try:
            approval_queue_path = Path("ai/approval_queue.json")
            if approval_queue_path.exists():
                with open(approval_queue_path) as f:
                    queue = json.load(f)
            else:
                queue = {"pending_requests": []}

            queue["pending_requests"].append({
                "id": f"redundancy-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
                "type": "infrastructure_budget_increase",
                "priority": "high",
                "reason": "Single point of failure - need failover server",
                "requested_increase": 50.0,
                "timestamp": datetime.utcnow().isoformat(),
                "auto_generated": True
            })

            with open(approval_queue_path, 'w') as f:
                json.dump(queue, f, indent=2)

        except Exception as e:
            self._log_error(f"Failed to request budget increase: {e}")

    def _check_critical_situations(self):
        """Check for and handle critical situations."""
        if not self.last_health:
            return

        status = self.last_health.get("status", "unknown")

        if status == "critical":
            self.consecutive_critical += 1

            if self.consecutive_critical >= 3:
                # Persistent critical - take emergency action
                self._handle_emergency()
        else:
            self.consecutive_critical = 0

    def _handle_emergency(self):
        """Handle emergency situations."""
        print("\n🚨 EMERGENCY: Persistent critical hardware state!")

        if not self.auto_provision:
            print("   Auto-provision disabled - manual intervention required")
            return

        # Try to provision emergency capacity
        if self._within_budget_for_emergency():
            print("   Provisioning emergency server...")
            success, server, message = self.provisioner.provision_new_server(
                role=ServerRole.TRADING_BACKUP,
                size=InstanceSize.MEDIUM
            )

            if success:
                self.stats["servers_provisioned"] += 1
                self.stats["downtime_prevented_minutes"] += 30
                print(f"   ✓ Emergency server provisioned: {message}")
            else:
                print(f"   ✗ Failed to provision: {message}")

    def _within_budget_for_emergency(self) -> bool:
        """Check if we have budget for emergency provisioning."""
        current = self.provisioner.get_current_spend()
        return current + 40 <= self.budget.monthly_limit + self.budget.reserved_for_emergency

    def _update_stats(self, decision: ScalingDecision):
        """Update statistics after a decision."""
        if decision.action == InfrastructureAction.UPGRADE_SERVER:
            self.stats["upgrades_executed"] += 1
            self.stats["downtime_prevented_minutes"] += 10

        elif decision.action == InfrastructureAction.PROVISION_SERVER:
            self.stats["servers_provisioned"] += 1

        elif decision.action == InfrastructureAction.TERMINATE_SERVER:
            if decision.cost_change < 0:
                self.stats["total_cost_saved"] += abs(decision.cost_change)

    def _get_check_interval(self) -> int:
        """Get adaptive check interval based on health."""
        if not self.last_health:
            return self.NORMAL_CHECK_INTERVAL

        status = self.last_health.get("status", "healthy")

        if status == "critical":
            return self.CRITICAL_CHECK_INTERVAL
        elif status in ["warning", "degraded"]:
            return self.DEGRADED_CHECK_INTERVAL
        else:
            return self.NORMAL_CHECK_INTERVAL

    def _print_status(self, decisions: List[ScalingDecision]):
        """Print status update."""
        timestamp = datetime.utcnow().strftime("%H:%M:%S")
        status = self.last_health.get("status", "unknown") if self.last_health else "unknown"
        score = self.last_health.get("score", 0) if self.last_health else 0

        # Status indicator
        if status == "pristine":
            indicator = "✨"
        elif status in ["optimal", "healthy"]:
            indicator = "🟢"
        elif status == "degraded":
            indicator = "🟡"
        elif status == "warning":
            indicator = "🟠"
        elif status == "critical":
            indicator = "🔴"
        else:
            indicator = "❓"

        spend = self.provisioner.get_current_spend()
        servers = len(self.provisioner.servers)

        print(f"[{timestamp}] {indicator} {status.upper()} ({score:.0f}) | "
              f"Servers: {servers} | Spend: ${spend:.2f}/{self.budget.monthly_limit:.2f} | "
              f"Decisions: {len(decisions)}")

        for d in decisions:
            if d.executed:
                print(f"  └─ {d.action.value}: {d.execution_result}")

    def _log_action(self, decision: ScalingDecision):
        """Log an action to file."""
        log_file = self.log_path / f"actions_{datetime.utcnow().strftime('%Y-%m-%d')}.jsonl"
        with open(log_file, "a") as f:
            f.write(json.dumps({
                "timestamp": datetime.utcnow().isoformat(),
                "action": decision.action.value,
                "reason": decision.reason,
                "cost_change": decision.cost_change,
                "result": decision.execution_result
            }) + "\n")

    def _log_error(self, error: str):
        """Log an error."""
        log_file = self.log_path / "errors.log"
        with open(log_file, "a") as f:
            f.write(f"[{datetime.utcnow().isoformat()}] {error}\n")

    def _save_stats(self):
        """Save statistics to file."""
        stats_file = self.log_path / "stats.json"
        stats_file.write_text(json.dumps(self.stats, indent=2, default=str))

    def run_single_check(self) -> Dict[str, Any]:
        """Run a single infrastructure check and return results."""
        # Get current status
        status = self.provisioner.get_infrastructure_status()

        # Get hardware health
        if HARDWARE_AVAILABLE:
            health = quick_health_check()
        else:
            health = {"status": "unknown", "score": 50}

        # Analyze
        decisions = self.provisioner.analyze_and_scale()

        return {
            "timestamp": datetime.utcnow().isoformat(),
            "infrastructure": status,
            "hardware_health": health,
            "decisions": [
                {
                    "action": d.action.value,
                    "reason": d.reason,
                    "cost_change": d.cost_change,
                    "auto_approved": d.auto_approved,
                    "executed": d.executed
                }
                for d in decisions
            ]
        }

    def get_status(self) -> Dict[str, Any]:
        """Get current manager status."""
        return {
            "running": self.running,
            "last_check": self.last_check.isoformat() if self.last_check else None,
            "last_health": self.last_health,
            "consecutive_critical": self.consecutive_critical,
            "stats": self.stats,
            "budget": {
                "limit": self.budget.monthly_limit,
                "current": self.provisioner.get_current_spend(),
                "remaining": self.budget.monthly_limit - self.provisioner.get_current_spend()
            },
            "settings": {
                "auto_provision": self.auto_provision,
                "auto_upgrade": self.auto_upgrade,
                "auto_scale": self.auto_scale,
                "dry_run": self.dry_run
            }
        }


def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Autonomous Infrastructure Manager - Zero User Intervention Required"
    )

    parser.add_argument(
        "--budget",
        type=float,
        default=500.0,
        help="Monthly budget limit in USD"
    )
    parser.add_argument(
        "--no-provision",
        action="store_true",
        help="Disable auto-provisioning"
    )
    parser.add_argument(
        "--no-upgrade",
        action="store_true",
        help="Disable auto-upgrading"
    )
    parser.add_argument(
        "--no-scale",
        action="store_true",
        help="Disable auto-scaling"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Don't actually provision (testing mode)"
    )
    parser.add_argument(
        "--single-check",
        action="store_true",
        help="Run single check and exit"
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output as JSON"
    )

    args = parser.parse_args()

    manager = AutonomousInfraManager(
        budget_monthly=args.budget,
        auto_provision=not args.no_provision,
        auto_upgrade=not args.no_upgrade,
        auto_scale=not args.no_scale,
        dry_run=args.dry_run
    )

    if args.single_check:
        result = manager.run_single_check()
        if args.json:
            print(json.dumps(result, indent=2, default=str))
        else:
            print(f"Infrastructure Status: {result['infrastructure']['servers']['count']} servers")
            print(f"Hardware Health: {result['hardware_health']['status']} ({result['hardware_health']['score']})")
            print(f"Budget: ${result['infrastructure']['budget']['current']:.2f} / ${result['infrastructure']['budget']['monthly_limit']:.2f}")
            print(f"Decisions: {len(result['decisions'])}")
            for d in result['decisions']:
                print(f"  - {d['action']}: {d['reason']}")
    else:
        manager.start()


if __name__ == "__main__":
    main()
