"""
Autonomous Infrastructure Provisioner - Self-Upgrading Hardware System

This is the core autonomous system that:
- Monitors infrastructure needs
- Makes scaling/upgrade decisions
- Actually provisions new hardware
- Migrates workloads automatically
- Manages the entire infrastructure lifecycle

The user should NEVER need to manually manage infrastructure.

Standard: Yair Siegel Master Level Operations - Full Self-Control
"""

import json
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import asdict
import os

from infrastructure.infra_types import (
    CloudProvider,
    InstanceSize,
    InfrastructureAction,
    ServerSpec,
    Server,
    ServerRole,
    ScalingDecision,
    InfrastructureBudget,
    ProvisioningRequest,
    ProvisioningStatus,
    MigrationPlan,
    DIGITALOCEAN_INSTANCES,
    create_scaling_decision,
    create_provisioning_request,
)
from infrastructure.cloud_providers import (
    CloudProviderAPI,
    get_cloud_provider,
    get_best_available_provider,
)

# Import hardware monitoring if available
try:
    from hardware import (
        HardwareCollector,
        HardwareAnalyzer,
        HardwareHealth,
        HealthStatus,
    )
    HARDWARE_MONITORING_AVAILABLE = True
except ImportError:
    HARDWARE_MONITORING_AVAILABLE = False


class AutoProvisioner:
    """
    Autonomous infrastructure provisioner.

    Makes all infrastructure decisions and executes them automatically.
    User intervention is only required for exceptional cases.
    """

    # Thresholds for autonomous scaling
    SCALE_UP_CPU_THRESHOLD = 80.0        # Scale up if CPU > 80%
    SCALE_UP_MEMORY_THRESHOLD = 85.0     # Scale up if memory > 85%
    SCALE_UP_DISK_THRESHOLD = 90.0       # Scale up if disk > 90%
    SCALE_DOWN_CPU_THRESHOLD = 20.0      # Scale down if CPU < 20%
    SCALE_DOWN_MEMORY_THRESHOLD = 30.0   # Scale down if memory < 30%

    # Auto-approval settings
    AUTO_APPROVE_COST_INCREASE = 50.0    # Auto-approve if monthly cost increase < $50
    AUTO_APPROVE_TRADING_CRITICAL = True # Always auto-approve if trading is at risk

    def __init__(
        self,
        provider: Optional[CloudProvider] = None,
        budget: Optional[InfrastructureBudget] = None,
        state_path: Optional[Path] = None,
        dry_run: bool = False
    ):
        """
        Initialize the auto-provisioner.

        Args:
            provider: Cloud provider to use (auto-detect if None)
            budget: Budget configuration
            state_path: Path for state storage
            dry_run: If True, don't actually provision (for testing)
        """
        # Get cloud provider
        if provider:
            self.api = get_cloud_provider(provider)
            self.provider = provider
        else:
            self.api, self.provider = get_best_available_provider()

        self.dry_run = dry_run
        self.state_path = state_path or Path("state/infrastructure")
        self.state_path.mkdir(parents=True, exist_ok=True)

        # Budget management
        self.budget = budget or InfrastructureBudget(
            monthly_limit=500.0,        # $500/month default
            auto_approve_hourly_increase=0.05,
            auto_approve_monthly_increase=50.0
        )

        # Load state
        self.servers: Dict[str, Server] = {}
        self.pending_decisions: List[ScalingDecision] = []
        self.executed_decisions: List[ScalingDecision] = []
        self._load_state()

        # Hardware monitoring
        if HARDWARE_MONITORING_AVAILABLE:
            self.collector = HardwareCollector()
            self.analyzer = HardwareAnalyzer()
        else:
            self.collector = None
            self.analyzer = None

    def _load_state(self):
        """Load persisted state."""
        state_file = self.state_path / "provisioner_state.json"
        if state_file.exists():
            try:
                data = json.loads(state_file.read_text())
                self.budget.current_spend = data.get("current_spend", 0)
                self.budget.trading_revenue_this_month = data.get("trading_revenue", 0)
            except:
                pass

    def _save_state(self):
        """Save state to disk."""
        state_file = self.state_path / "provisioner_state.json"
        state_file.write_text(json.dumps({
            "current_spend": self.budget.current_spend,
            "trading_revenue": self.budget.trading_revenue_this_month,
            "last_updated": datetime.utcnow().isoformat()
        }, indent=2))

    def refresh_servers(self) -> List[Server]:
        """Refresh the list of servers from the cloud provider."""
        self.servers = {s.server_id: s for s in self.api.list_servers()}
        return list(self.servers.values())

    def get_current_spend(self) -> float:
        """Calculate current monthly spend."""
        self.refresh_servers()
        return sum(s.monthly_cost for s in self.servers.values())

    def analyze_and_scale(self) -> List[ScalingDecision]:
        """
        Analyze current infrastructure and make scaling decisions.

        This is the main autonomous decision-making function.

        Returns:
            List of scaling decisions (some may be auto-executed)
        """
        decisions = []

        # Refresh server list
        self.refresh_servers()

        # Get current hardware health if available
        health = None
        if self.collector and self.analyzer:
            try:
                metrics = self.collector.collect_all()
                health = self.analyzer.analyze(metrics)
            except:
                pass

        # Check each server for scaling needs
        for server in self.servers.values():
            server_decisions = self._analyze_server(server, health)
            decisions.extend(server_decisions)

        # Check if we need more servers (horizontal scaling)
        horizontal_decisions = self._check_horizontal_scaling(health)
        decisions.extend(horizontal_decisions)

        # Check budget
        self._enforce_budget(decisions)

        # Auto-execute approved decisions
        for decision in decisions:
            if decision.auto_approved and not decision.requires_approval:
                self._execute_decision(decision)

        self.pending_decisions.extend(
            d for d in decisions if not d.executed and d.requires_approval
        )

        self._save_state()
        self._log_decisions(decisions)

        return decisions

    def _analyze_server(
        self,
        server: Server,
        health: Optional['HardwareHealth']
    ) -> List[ScalingDecision]:
        """Analyze a specific server for scaling needs."""
        decisions = []

        if not health:
            return decisions

        # Check CPU
        cpu_score = health.cpu_health.score
        if cpu_score < 30:  # Poor CPU health
            decision = self._create_upgrade_decision(
                server=server,
                reason=f"CPU health degraded ({cpu_score}%)",
                trigger_metrics={"cpu_score": cpu_score},
                upgrade_type="cpu"
            )
            if decision:
                decisions.append(decision)

        # Check Memory
        mem_score = health.memory_health.score
        if mem_score < 30:  # Poor memory health
            decision = self._create_upgrade_decision(
                server=server,
                reason=f"Memory health degraded ({mem_score}%)",
                trigger_metrics={"memory_score": mem_score},
                upgrade_type="memory"
            )
            if decision:
                decisions.append(decision)

        # Check Disk
        disk_score = health.disk_health.score
        if disk_score < 30:  # Poor disk health
            decision = self._create_upgrade_decision(
                server=server,
                reason=f"Disk health degraded ({disk_score}%)",
                trigger_metrics={"disk_score": disk_score},
                upgrade_type="disk"
            )
            if decision:
                decisions.append(decision)

        # Check for critical trading impact
        if health.trading_impact_risk in ["high", "critical"]:
            # Immediate upgrade needed
            decision = self._create_emergency_upgrade_decision(
                server=server,
                reason=f"Trading at risk: {health.trading_impact_risk}",
                trigger_metrics={"trading_risk": health.trading_impact_risk}
            )
            if decision:
                decision.auto_approved = self.AUTO_APPROVE_TRADING_CRITICAL
                decision.requires_approval = not self.AUTO_APPROVE_TRADING_CRITICAL
                decisions.append(decision)

        return decisions

    def _check_horizontal_scaling(
        self,
        health: Optional['HardwareHealth']
    ) -> List[ScalingDecision]:
        """Check if we need to add more servers."""
        decisions = []

        if not health:
            return decisions

        # If overall health is critical and we can't upgrade current server
        if health.overall_status == HealthStatus.CRITICAL:
            # Check if we have budget for new server
            current_spend = self.get_current_spend()
            if current_spend + 40 <= self.budget.monthly_limit:  # $40/month minimum
                decision = create_scaling_decision(
                    action=InfrastructureAction.PROVISION_SERVER,
                    reason="Critical health - need additional capacity",
                    trigger_metrics={"health_status": health.overall_status.value},
                    trading_impact="high"
                )
                decision.projected_monthly_cost = current_spend + 40
                decision.cost_change = 40
                decisions.append(decision)

        return decisions

    def _create_upgrade_decision(
        self,
        server: Server,
        reason: str,
        trigger_metrics: Dict[str, Any],
        upgrade_type: str
    ) -> Optional[ScalingDecision]:
        """Create an upgrade decision for a server."""
        # Find next size up
        current_size = self._get_instance_size(server.instance_type)
        next_size = self._get_next_size(current_size)

        if not next_size:
            return None  # Already at max size

        # Get new instance type
        new_instance_type = self._get_instance_type_for_size(next_size)
        if not new_instance_type:
            return None

        new_instance = DIGITALOCEAN_INSTANCES.get(new_instance_type)
        if not new_instance:
            return None

        # Calculate cost change
        cost_change = new_instance.monthly_cost - server.monthly_cost

        decision = create_scaling_decision(
            action=InfrastructureAction.UPGRADE_SERVER,
            reason=reason,
            trigger_metrics=trigger_metrics,
            trading_impact="low"
        )
        decision.target_server = server.server_id
        decision.new_instance_type = new_instance_type
        decision.new_spec = new_instance.spec
        decision.current_monthly_cost = server.monthly_cost
        decision.projected_monthly_cost = new_instance.monthly_cost
        decision.cost_change = cost_change

        # Auto-approve if cost increase is small
        if cost_change <= self.budget.auto_approve_monthly_increase:
            decision.auto_approved = True
            decision.requires_approval = False

        return decision

    def _create_emergency_upgrade_decision(
        self,
        server: Server,
        reason: str,
        trigger_metrics: Dict[str, Any]
    ) -> Optional[ScalingDecision]:
        """Create an emergency upgrade decision."""
        decision = self._create_upgrade_decision(
            server, reason, trigger_metrics, "emergency"
        )
        if decision:
            decision.trading_impact = "critical"
        return decision

    def _execute_decision(self, decision: ScalingDecision) -> bool:
        """Execute a scaling decision."""
        if self.dry_run:
            decision.executed = True
            decision.executed_at = datetime.utcnow()
            decision.execution_result = "DRY RUN - would have executed"
            return True

        success = False
        result = ""

        try:
            if decision.action == InfrastructureAction.UPGRADE_SERVER:
                success, result = self._execute_upgrade(decision)

            elif decision.action == InfrastructureAction.PROVISION_SERVER:
                success, result = self._execute_provision(decision)

            elif decision.action == InfrastructureAction.TERMINATE_SERVER:
                success, result = self._execute_terminate(decision)

            elif decision.action == InfrastructureAction.SCALE_HORIZONTALLY:
                success, result = self._execute_horizontal_scale(decision)

        except Exception as e:
            result = f"Error: {str(e)}"

        decision.executed = True
        decision.executed_at = datetime.utcnow()
        decision.execution_result = result
        decision.rollback_available = success

        self.executed_decisions.append(decision)

        # Update budget
        if success and decision.cost_change > 0:
            self.budget.current_spend += decision.cost_change

        return success

    def _execute_upgrade(self, decision: ScalingDecision) -> Tuple[bool, str]:
        """Execute a server upgrade."""
        if not decision.target_server or not decision.new_instance_type:
            return False, "Missing target server or new instance type"

        # Create snapshot first for rollback
        snapshot_name = f"pre-upgrade-{decision.target_server}-{datetime.utcnow().strftime('%Y%m%d%H%M')}"
        if hasattr(self.api, 'create_snapshot'):
            self.api.create_snapshot(decision.target_server, snapshot_name)

        # Resize the server
        success, message = self.api.resize_server(
            decision.target_server,
            decision.new_instance_type
        )

        if success:
            # Update local state
            if decision.target_server in self.servers:
                self.servers[decision.target_server].instance_type = decision.new_instance_type
                if decision.new_spec:
                    self.servers[decision.target_server].spec = decision.new_spec

        return success, message

    def _execute_provision(self, decision: ScalingDecision) -> Tuple[bool, str]:
        """Execute provisioning a new server."""
        # Determine instance type
        instance_type = decision.new_instance_type or "s-2vcpu-4gb"  # Default small

        request = create_provisioning_request(
            action=InfrastructureAction.PROVISION_SERVER,
            provider=self.provider,
            instance_type=instance_type,
            region="nyc1",  # Default region
            role=ServerRole.GENERAL,
            name=f"hands-off-{datetime.utcnow().strftime('%Y%m%d%H%M')}"
        )

        # Add trading setup script
        request.user_data = self._get_server_setup_script()

        success, server, message = self.api.create_server(request)

        if success and server:
            self.servers[server.server_id] = server

        return success, message

    def _execute_terminate(self, decision: ScalingDecision) -> Tuple[bool, str]:
        """Execute server termination."""
        if not decision.target_server:
            return False, "No target server specified"

        success, message = self.api.delete_server(decision.target_server)

        if success:
            if decision.target_server in self.servers:
                del self.servers[decision.target_server]

        return success, message

    def _execute_horizontal_scale(self, decision: ScalingDecision) -> Tuple[bool, str]:
        """Execute horizontal scaling (add more servers)."""
        return self._execute_provision(decision)

    def _get_server_setup_script(self) -> str:
        """Get cloud-init script for new servers."""
        return """#!/bin/bash
# Autonomous server setup for Hands-Off Engine
apt-get update
apt-get install -y python3 python3-pip git

# Clone and setup the engine
cd /opt
git clone https://github.com/user/hands-off-engine.git
cd hands-off-engine
pip3 install -r requirements.txt

# Start monitoring
python3 -m hardware.autonomous_hardware_monitor --auto-execute &

echo "Hands-Off Engine setup complete"
"""

    def _get_instance_size(self, instance_type: str) -> InstanceSize:
        """Get the size category of an instance type."""
        instance = DIGITALOCEAN_INSTANCES.get(instance_type)
        if instance:
            return instance.size
        return InstanceSize.SMALL

    def _get_next_size(self, current: InstanceSize) -> Optional[InstanceSize]:
        """Get the next size up."""
        size_order = [
            InstanceSize.NANO,
            InstanceSize.MICRO,
            InstanceSize.SMALL,
            InstanceSize.MEDIUM,
            InstanceSize.LARGE,
            InstanceSize.XLARGE,
            InstanceSize.XXLARGE,
        ]

        try:
            idx = size_order.index(current)
            if idx < len(size_order) - 1:
                return size_order[idx + 1]
        except ValueError:
            pass

        return None

    def _get_instance_type_for_size(self, size: InstanceSize) -> Optional[str]:
        """Get an instance type for a given size."""
        for type_id, instance in DIGITALOCEAN_INSTANCES.items():
            if instance.size == size:
                return type_id
        return None

    def _enforce_budget(self, decisions: List[ScalingDecision]):
        """Enforce budget limits on decisions."""
        current_spend = self.get_current_spend()

        for decision in decisions:
            projected = current_spend + decision.cost_change

            if projected > self.budget.monthly_limit:
                decision.requires_approval = True
                decision.auto_approved = False
                decision.execution_result = f"Exceeds budget (${projected:.2f} > ${self.budget.monthly_limit:.2f})"

    def _log_decisions(self, decisions: List[ScalingDecision]):
        """Log decisions to file."""
        log_file = self.state_path / f"decisions_{datetime.utcnow().strftime('%Y-%m-%d')}.jsonl"
        with open(log_file, "a") as f:
            for decision in decisions:
                f.write(json.dumps(asdict(decision), default=str) + "\n")

    def approve_decision(self, decision_id: str) -> bool:
        """Approve and execute a pending decision."""
        for decision in self.pending_decisions:
            if decision.decision_id == decision_id:
                decision.approved_by = "user"
                decision.approved_at = datetime.utcnow()
                decision.approval_status = "approved"
                decision.requires_approval = False

                success = self._execute_decision(decision)
                self.pending_decisions.remove(decision)

                return success

        return False

    def reject_decision(self, decision_id: str, reason: str = "") -> bool:
        """Reject a pending decision."""
        for decision in self.pending_decisions:
            if decision.decision_id == decision_id:
                decision.approval_status = "rejected"
                decision.execution_result = f"Rejected: {reason}"
                self.pending_decisions.remove(decision)
                return True

        return False

    def provision_new_server(
        self,
        role: ServerRole,
        size: InstanceSize = InstanceSize.SMALL,
        region: str = "nyc1"
    ) -> Tuple[bool, Optional[Server], str]:
        """
        Manually provision a new server.

        Args:
            role: Server role
            size: Instance size
            region: Cloud region

        Returns:
            (success, server, message)
        """
        instance_type = self._get_instance_type_for_size(size)
        if not instance_type:
            return False, None, f"No instance type for size {size}"

        request = create_provisioning_request(
            action=InfrastructureAction.PROVISION_SERVER,
            provider=self.provider,
            instance_type=instance_type,
            region=region,
            role=role,
            name=f"hands-off-{role.value}-{datetime.utcnow().strftime('%Y%m%d%H%M')}"
        )
        request.user_data = self._get_server_setup_script()

        if self.dry_run:
            return True, None, "DRY RUN - would provision"

        return self.api.create_server(request)

    def get_infrastructure_status(self) -> Dict[str, Any]:
        """Get current infrastructure status."""
        self.refresh_servers()

        return {
            "provider": self.provider.value,
            "dry_run": self.dry_run,
            "servers": {
                "count": len(self.servers),
                "list": [
                    {
                        "id": s.server_id,
                        "name": s.name,
                        "type": s.instance_type,
                        "status": s.status,
                        "ip": s.ip_address,
                        "monthly_cost": s.monthly_cost
                    }
                    for s in self.servers.values()
                ]
            },
            "budget": {
                "monthly_limit": self.budget.monthly_limit,
                "current_spend": self.get_current_spend(),
                "remaining": self.budget.monthly_limit - self.get_current_spend()
            },
            "pending_decisions": len(self.pending_decisions),
            "executed_decisions": len(self.executed_decisions)
        }


def get_auto_provisioner(dry_run: bool = False) -> AutoProvisioner:
    """Get the auto-provisioner instance."""
    return AutoProvisioner(dry_run=dry_run)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Autonomous Infrastructure Provisioner")
    parser.add_argument("--dry-run", action="store_true", help="Don't actually provision")
    parser.add_argument("--status", action="store_true", help="Show infrastructure status")
    parser.add_argument("--analyze", action="store_true", help="Analyze and make decisions")
    parser.add_argument("--provision", metavar="SIZE", help="Provision new server")

    args = parser.parse_args()

    provisioner = get_auto_provisioner(dry_run=args.dry_run)

    if args.status:
        status = provisioner.get_infrastructure_status()
        print(json.dumps(status, indent=2, default=str))

    elif args.analyze:
        print("Analyzing infrastructure...")
        decisions = provisioner.analyze_and_scale()
        print(f"\nDecisions: {len(decisions)}")
        for d in decisions:
            print(f"  [{d.action.value}] {d.reason}")
            print(f"    Cost change: ${d.cost_change:.2f}/month")
            print(f"    Auto-approved: {d.auto_approved}")
            print(f"    Executed: {d.executed}")

    elif args.provision:
        size = InstanceSize[args.provision.upper()]
        print(f"Provisioning {size.value} server...")
        success, server, message = provisioner.provision_new_server(
            role=ServerRole.GENERAL,
            size=size
        )
        print(f"Result: {message}")
        if server:
            print(f"Server ID: {server.server_id}")

    else:
        # Default: show status
        status = provisioner.get_infrastructure_status()
        print(f"Provider: {status['provider']}")
        print(f"Servers: {status['servers']['count']}")
        print(f"Budget: ${status['budget']['remaining']:.2f} remaining of ${status['budget']['monthly_limit']:.2f}")
