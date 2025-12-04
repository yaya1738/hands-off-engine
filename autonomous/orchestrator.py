"""
Unified Autonomous System - Complete Self-Managing Infrastructure

The master autonomous controller that combines:
- Hardware monitoring and health management
- Infrastructure provisioning and scaling
- Business decision-making integration
- Approval queue for risky decisions
- AI Nexus for intelligent analysis

This is the LIVE system that runs continuously and manages
everything without user intervention.

Standard: Yair Siegel Master Level Operations - Full Self-Control
"""

# UNIFIED AI - All systems serve Yair Siegel
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
try:
    from ai.unified_ai import MASTER, get_master
except ImportError:
    MASTER = "Yair Siegel"


import json
import signal
import sys
import time
import threading
import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import asdict

# Core systems
from hardware import (
    HardwareCollector,
    HardwareAnalyzer,
    HardwareKernel,
    HardwareDecisionEngine,
    TradingProtectionManager,
    HardwareAuditLogger,
    HealthStatus,
    is_hardware_healthy,
    quick_health_check,
)

from infrastructure import (
    AutoProvisioner,
    AutonomousInfraManager,
    CloudProvider,
    InstanceSize,
    InfrastructureAction,
    ServerRole,
    get_auto_provisioner,
)

# Business integration
sys.path.insert(0, str(Path(__file__).parent.parent))
from ai.approval_queue import ApprovalQueue, needs_approval, send_approval_notification

# INTEGRAFIX: Import ABCFC bridge for hierarchy-aware decisions
try:
    from integrafix.claude_abcfc_bridge import get_bridge as get_abcfc_bridge
    ABCFC_AVAILABLE = True
except ImportError:
    ABCFC_AVAILABLE = False


class UnifiedAutonomousSystem:
    """
    The unified autonomous system that manages everything.

    This is the LIVE production system that:
    - Monitors hardware health continuously
    - Provisions/upgrades infrastructure automatically
    - Integrates with approval queue for risky decisions
    - Logs everything for audit
    - Protects trading at all costs

    User intervention: NEVER required for normal operations
    """

    # Check intervals
    NORMAL_INTERVAL = 60          # 1 minute normally
    DEGRADED_INTERVAL = 30        # 30 seconds when degraded
    CRITICAL_INTERVAL = 15        # 15 seconds when critical

    # Auto-approval thresholds
    AUTO_APPROVE_COST_USD = 50.0  # Auto-approve if cost < $50
    AUTO_APPROVE_SCORE = 95       # Auto-approve if health score > 95

    def __init__(
        self,
        infrastructure_budget: float = 500.0,
        auto_provision: bool = True,
        auto_upgrade: bool = True,
        dry_run: bool = False,
        node_id: Optional[str] = None
    ):
        """
        Initialize the unified autonomous system.

        Args:
            infrastructure_budget: Monthly budget for infrastructure
            auto_provision: Enable auto-provisioning of new servers
            auto_upgrade: Enable auto-upgrading of servers
            dry_run: Don't actually provision (for testing)
            node_id: Unique node identifier
        """
        self.node_id = node_id or self._get_node_id()
        self.dry_run = dry_run
        self.infrastructure_budget = infrastructure_budget
        self.auto_provision = auto_provision
        self.auto_upgrade = auto_upgrade

        # Initialize hardware monitoring
        self.hw_collector = HardwareCollector(node_id=self.node_id)
        self.hw_analyzer = HardwareAnalyzer()
        self.hw_kernel = HardwareKernel(node_id=self.node_id)
        self.hw_decision_engine = HardwareDecisionEngine(
            kernel=self.hw_kernel,
            auto_execute_enabled=True
        )
        self.trading_protection = TradingProtectionManager()
        self.hw_audit = HardwareAuditLogger()

        # Initialize infrastructure management
        self.infra_provisioner = get_auto_provisioner(dry_run=dry_run)
        self.infra_provisioner.budget.monthly_limit = infrastructure_budget

        # Business integration
        self.approval_queue = ApprovalQueue()

        # State
        self.running = False
        self._stop_event = threading.Event()
        self.last_check: Optional[datetime] = None
        self.last_health: Optional[Dict] = None
        self.session_id = f"unified_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"

        # Statistics
        self.stats = {
            "checks": 0,
            "hw_decisions": 0,
            "infra_decisions": 0,
            "auto_upgrades": 0,
            "servers_provisioned": 0,
            "approvals_requested": 0,
            "trading_protections": 0,
            "start_time": None
        }

        # Logging
        self.log_path = Path("logs/unified_autonomous")
        self.log_path.mkdir(parents=True, exist_ok=True)

        # Signal handlers
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)

    def _get_node_id(self) -> str:
        """Get unique node identifier."""
        import socket
        return socket.gethostname()

    def _signal_handler(self, signum, frame):
        """Handle shutdown signals."""
        print(f"\n⚡ Received signal {signum}, shutting down gracefully...")
        self.stop()

    def start(self):
        """Start the unified autonomous system."""
        self.running = True
        self._stop_event.clear()
        self.stats["start_time"] = datetime.utcnow().isoformat()

        self._print_startup_banner()

        # Initial warmup
        self._warmup()

        # Main loop
        try:
            while self.running and not self._stop_event.is_set():
                try:
                    self._autonomous_cycle()
                except Exception as e:
                    self._log_error(f"Cycle error: {e}")
                    import traceback
                    traceback.print_exc()

                interval = self._get_check_interval()
                self._stop_event.wait(interval)

        except KeyboardInterrupt:
            pass
        finally:
            self.stop()

    def stop(self):
        """Stop the system gracefully."""
        if not self.running:
            return

        self.running = False
        self._stop_event.set()

        self._save_state()
        self._print_shutdown_summary()

    def _print_startup_banner(self):
        """Print startup banner."""
        print("\n" + "=" * 70)
        print("🚀 UNIFIED AUTONOMOUS SYSTEM - LIVE")
        print("=" * 70)
        print(f"   Node: {self.node_id}")
        print(f"   Session: {self.session_id}")
        print(f"   Infrastructure Budget: ${self.infrastructure_budget}/month")
        print(f"   Auto-Provision: {self.auto_provision}")
        print(f"   Auto-Upgrade: {self.auto_upgrade}")
        print(f"   Dry Run: {self.dry_run}")
        print(f"   Cloud Provider: {self.infra_provisioner.provider.value}")
        print("=" * 70)
        print("\n📍 The system is now managing ALL infrastructure autonomously.")
        print("   User intervention is NOT required.")
        print("\n   Press Ctrl+C to stop\n")

    def _print_shutdown_summary(self):
        """Print shutdown summary."""
        print("\n" + "=" * 70)
        print("📊 AUTONOMOUS SYSTEM STATISTICS")
        print("=" * 70)
        print(f"   Checks performed: {self.stats['checks']}")
        print(f"   Hardware decisions: {self.stats['hw_decisions']}")
        print(f"   Infrastructure decisions: {self.stats['infra_decisions']}")
        print(f"   Auto-upgrades executed: {self.stats['auto_upgrades']}")
        print(f"   Servers provisioned: {self.stats['servers_provisioned']}")
        print(f"   Approvals requested: {self.stats['approvals_requested']}")
        print(f"   Trading protections: {self.stats['trading_protections']}")
        print("=" * 70)

    def _warmup(self):
        """Warmup phase for baseline collection."""
        print("🔄 Warming up (collecting baseline)...")

        for i in range(3):
            metrics = self.hw_collector.collect_all()
            health = self.hw_analyzer.analyze(metrics)
            self.hw_kernel.learn_from_metrics(metrics, health)
            time.sleep(1)

        print("✓ Warmup complete\n")

    def _autonomous_cycle(self):
        """Execute one autonomous cycle."""
        self.stats["checks"] += 1
        self.last_check = datetime.utcnow()

        # ═══════════════════════════════════════════════════════════════
        # PHASE 1: Hardware Health Assessment
        # ═══════════════════════════════════════════════════════════════

        metrics = self.hw_collector.collect_all()
        health = self.hw_analyzer.analyze(metrics)
        self.last_health = {
            "status": health.overall_status.value,
            "score": health.overall_score,
            "trading_risk": health.trading_impact_risk
        }

        # Feed metrics to kernel for learning
        self.hw_kernel.learn_from_metrics(metrics, health)

        # Log to audit
        self.hw_audit.log_health_check(health, self.session_id)

        # ═══════════════════════════════════════════════════════════════
        # PHASE 2: Hardware Decision Making
        # ═══════════════════════════════════════════════════════════════

        hw_decisions = self.hw_decision_engine.analyze_and_decide(metrics, health)
        self.stats["hw_decisions"] += len(hw_decisions)

        for decision in hw_decisions:
            self._handle_hardware_decision(decision, health)

        # ═══════════════════════════════════════════════════════════════
        # PHASE 3: Trading Protection Check
        # ═══════════════════════════════════════════════════════════════

        trading_check = self.trading_protection.check_trading_health(metrics, health)

        if trading_check.status.value != "active":
            self.stats["trading_protections"] += 1

            # Execute protection if needed
            if trading_check.recommended_action.value != "none":
                self.trading_protection.execute_protection(
                    trading_check.recommended_action,
                    f"Autonomous protection: {trading_check.status.value}",
                    "unified_autonomous"
                )

        # ═══════════════════════════════════════════════════════════════
        # PHASE 3.5: Redundancy Check - Single Point of Failure Detection
        # ═══════════════════════════════════════════════════════════════

        self._check_redundancy_autonomous()

        # ═══════════════════════════════════════════════════════════════
        # PHASE 4: Infrastructure Scaling Decisions
        # ═══════════════════════════════════════════════════════════════

        infra_decisions = self._make_infrastructure_decisions(health)
        self.stats["infra_decisions"] += len(infra_decisions)

        # ═══════════════════════════════════════════════════════════════
        # PHASE 5: Execute Approved Actions from Queue
        # ═══════════════════════════════════════════════════════════════

        self._process_approved_actions()

        # ═══════════════════════════════════════════════════════════════
        # PHASE 6: Status Output
        # ═══════════════════════════════════════════════════════════════

        self._print_status(health, hw_decisions, infra_decisions, trading_check)

    def _handle_hardware_decision(self, decision, health):
        """Handle a hardware decision through the business process."""
        # Log the decision
        self.hw_audit.log_decision(decision, self.session_id)

        # Determine if this needs approval or can auto-execute
        if self._can_auto_approve_hw_decision(decision, health):
            # Auto-execute
            if not decision.executed:
                decision.executed = True
                decision.executed_at = datetime.utcnow()
                decision.auto_executed = True
                self.hw_kernel.record_decision(decision, True, "Auto-executed")
        else:
            # Queue for approval
            self._queue_for_approval(
                title=f"Hardware: {decision.action}",
                description=decision.reason,
                change_type="hardware_operation",
                risk_level="medium" if decision.confidence.value in ["high", "certain"] else "high",
                action_data={
                    "type": "hardware_decision",
                    "decision_id": decision.decision_id,
                    "action": decision.action,
                    "node_id": decision.node_id
                }
            )

    def _can_auto_approve_hw_decision(self, decision, health) -> bool:
        """Determine if a hardware decision can be auto-approved."""
        # Emergency decisions are always auto-approved
        if decision.decision_type == "emergency":
            return True

        # High confidence decisions for non-critical operations
        # Include alert_response to handle memory/cpu/disk alerts automatically
        if decision.confidence.value in ["certain", "high"]:
            if decision.decision_type in ["alert", "monitoring", "alert_response"]:
                return True

        # Auto-approve upgrade recommendations with high confidence
        # EXCEPT for self-upgrade (would kill this process)
        if decision.decision_type == "upgrade_recommendation":
            if decision.confidence.value in ["certain", "high"]:
                # SELF-PROTECTION: Don't auto-approve upgrades targeting self
                if decision.node_id == self.node_id:
                    return False  # Queue for manual approval
                return True

        # For infrastructure decisions, still allow auto-approval even during
        # high trading risk IF this is an upgrade that would FIX the issue
        # BUT NEVER auto-approve self-upgrades
        if health.trading_impact_risk in ["high", "critical"]:
            # SELF-PROTECTION: Never auto-approve self-upgrades regardless of risk
            if decision.node_id == self.node_id and decision.decision_type == "upgrade_recommendation":
                return False  # Queue for manual approval
            # Allow upgrades/fixes to proceed - they're meant to resolve the risk
            if decision.decision_type in ["emergency", "upgrade_recommendation", "alert_response"]:
                return True
            return False

        return decision.auto_executed

    def _make_infrastructure_decisions(self, health) -> List:
        """Make infrastructure decisions based on health."""
        decisions = []

        # INTEGRAFIX: Use ABCFC to validate infrastructure decisions against hierarchy
        abcfc_allows_spending = True
        if ABCFC_AVAILABLE:
            try:
                bridge = get_abcfc_bridge()
                result = bridge.evaluate_trading_decision(
                    decision="Infrastructure spending",
                    actions=[
                        {"name": "spend", "action_type": "buy", "size": 50},
                        {"name": "hold", "action_type": "hold"}
                    ]
                )
                recommended = result.get("recommended", {}).get("action", "hold")
                if recommended != "spend":
                    abcfc_allows_spending = False
                    # Still allow emergency actions, but block optional upgrades
            except Exception:
                pass  # On error, allow spending (fail-open for infra)

        # Check if we need to upgrade or provision
        if health.overall_status == HealthStatus.CRITICAL:
            # Critical - need more capacity
            decision = self._create_infra_decision(
                action="provision_emergency",
                reason=f"Critical health state ({health.overall_score})",
                auto_approve=True  # Emergency
            )
            if decision:
                decisions.append(decision)
                self._execute_infra_decision(decision)

        elif health.overall_status == HealthStatus.WARNING:
            # Warning - consider upgrade (INTEGRAFIX: check ABCFC first)
            if self.auto_upgrade and abcfc_allows_spending:
                decision = self._create_infra_decision(
                    action="upgrade_server",
                    reason=f"Warning health state ({health.overall_score})",
                    auto_approve=self._within_auto_approve_budget()
                )
                if decision:
                    decisions.append(decision)
                    if decision.get("auto_approve"):
                        self._execute_infra_decision(decision)
                    else:
                        self._queue_infra_for_approval(decision)
            elif not abcfc_allows_spending:
                # ABCFC blocked - log but don't spend
                pass

        elif health.overall_status == HealthStatus.DEGRADED:
            # Degraded - schedule upgrade (INTEGRAFIX: check ABCFC first)
            if abcfc_allows_spending:
                decision = self._create_infra_decision(
                    action="plan_upgrade",
                    reason=f"Degraded health ({health.overall_score})",
                    auto_approve=False
                )
                if decision:
                    decisions.append(decision)
                    self._queue_infra_for_approval(decision)

        # CRITICAL: Check for component-specific issues that warrant upgrade
        # even if overall status looks healthy (other components mask the problem)
        elif self._needs_resource_upgrade(health) and abcfc_allows_spending:
            # Component is struggling - upgrade to fix it (INTEGRAFIX: ABCFC gated)
            component, reason = self._get_struggling_component(health)
            if self.auto_upgrade:
                decision = self._create_infra_decision(
                    action="upgrade_server",
                    reason=f"{component} constraint: {reason}",
                    auto_approve=self._within_auto_approve_budget()
                )
                if decision:
                    decisions.append(decision)
                    if decision.get("auto_approve"):
                        self._execute_infra_decision(decision)
                    else:
                        self._queue_infra_for_approval(decision)

        return decisions

    def _needs_resource_upgrade(self, health) -> bool:
        """Check if any critical component needs more resources."""
        # Memory is critical for trading - if it's struggling, upgrade
        if health.memory_health.status in [HealthStatus.CRITICAL, HealthStatus.WARNING]:
            return True
        # High trading risk with resource constraints
        if health.trading_impact_risk in ["high", "critical"]:
            if health.memory_health.score < 50 or health.cpu_health.score < 50:
                return True
        return False

    def _get_struggling_component(self, health) -> Tuple[str, str]:
        """Identify which component is struggling and why."""
        if health.memory_health.status in [HealthStatus.CRITICAL, HealthStatus.WARNING]:
            return "Memory", f"score {health.memory_health.score:.0f}, status {health.memory_health.status.value}"
        if health.cpu_health.status in [HealthStatus.CRITICAL, HealthStatus.WARNING]:
            return "CPU", f"score {health.cpu_health.score:.0f}, status {health.cpu_health.status.value}"
        if health.disk_health.status in [HealthStatus.CRITICAL, HealthStatus.WARNING]:
            return "Disk", f"score {health.disk_health.score:.0f}, status {health.disk_health.status.value}"
        return "Resources", f"trading risk {health.trading_impact_risk}"

    def _create_infra_decision(
        self,
        action: str,
        reason: str,
        auto_approve: bool
    ) -> Optional[Dict]:
        """Create an infrastructure decision."""
        return {
            "id": f"infra_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
            "action": action,
            "reason": reason,
            "auto_approve": auto_approve,
            "timestamp": datetime.utcnow().isoformat(),
            "executed": False
        }

    def _execute_infra_decision(self, decision: Dict):
        """Execute an infrastructure decision."""
        action = decision.get("action")

        if self.dry_run:
            decision["executed"] = True
            decision["result"] = "DRY RUN"
            return

        if action == "provision_emergency":
            # Provision emergency server
            success, server, message = self.infra_provisioner.provision_new_server(
                role=ServerRole.TRADING_BACKUP,
                size=InstanceSize.MEDIUM
            )
            decision["executed"] = True
            decision["result"] = message
            if success:
                self.stats["servers_provisioned"] += 1

        elif action == "upgrade_server":
            # Get current server and upgrade
            # Refresh server list from cloud provider
            self.infra_provisioner.refresh_servers()
            servers = list(self.infra_provisioner.servers.values())

            # Find the current server (match by hostname)
            import socket
            hostname = socket.gethostname()
            current_server = None
            for server in servers:
                if server.name == hostname or hostname in server.name:
                    current_server = server
                    break

            if not current_server and servers:
                # Fallback to first active server
                current_server = servers[0]

            if current_server:
                current_size = current_server.instance_type
                next_size = self._get_next_instance_type(current_size)

                # SELF-PROTECTION: Never auto-resize the server we're running on
                # Resizing requires shutdown which kills this process
                if current_server.name == hostname or hostname in current_server.name:
                    decision["executed"] = False
                    decision["result"] = "SELF-PROTECTION: Cannot auto-resize self"
                    print(f"⚠️ SELF-PROTECTION: Skipping auto-resize of {hostname} (would kill this process)")
                    print(f"   To resize manually: doctl compute droplet-action resize {current_server.server_id} --size {next_size}")
                    return

                print(f"🔄 Upgrading server {current_server.name} from {current_size} to {next_size}")

                success, message = self.infra_provisioner.api.resize_server(
                    current_server.server_id,
                    next_size
                )
                decision["executed"] = True
                decision["result"] = message
                if success:
                    self.stats["auto_upgrades"] += 1
                    print(f"✅ Upgrade initiated: {message}")
                else:
                    print(f"❌ Upgrade failed: {message}")
            else:
                decision["executed"] = False
                decision["result"] = "No server found to upgrade"
                print("❌ No server found to upgrade")

    def _get_next_instance_type(self, current: str) -> str:
        """Get the next larger instance type."""
        upgrades = {
            "s-1vcpu-1gb": "s-1vcpu-2gb",
            "s-1vcpu-2gb": "s-2vcpu-4gb",
            "s-2vcpu-4gb": "s-4vcpu-8gb",
            "s-4vcpu-8gb": "s-8vcpu-16gb",
            "s-8vcpu-16gb": "s-16vcpu-32gb",
        }
        return upgrades.get(current, "s-4vcpu-8gb")

    def _queue_infra_for_approval(self, decision: Dict):
        """Queue infrastructure decision for approval."""
        self._queue_for_approval(
            title=f"Infrastructure: {decision['action']}",
            description=decision["reason"],
            change_type="infrastructure",
            risk_level="high" if "emergency" in decision["action"] else "medium",
            action_data={
                "type": "infrastructure_decision",
                "decision": decision
            }
        )

    def _check_redundancy_autonomous(self):
        """
        AUTONOMOUS DECISION: Check for single-point-of-failure and act.

        The system detects risk and provisions backup WITHOUT user intervention.
        This is what autonomous infrastructure management means.
        """
        if hasattr(self, '_redundancy_handled') and self._redundancy_handled:
            return

        try:
            config_path = Path("config/production_servers.json")
            if not config_path.exists():
                return

            with open(config_path) as f:
                config = json.load(f)

            servers = config.get("production_servers", [])
            policy = config.get("redundancy_policy", {})

            min_servers = policy.get("min_trading_servers", 2)
            require_failover = policy.get("require_failover", True)
            auto_provision = policy.get("auto_provision_backup", True)

            # Count critical trading servers
            critical_servers = [s for s in servers if s.get("critical", False)]

            if len(critical_servers) < min_servers and require_failover:
                # ══════════════════════════════════════════════════════════
                # AUTONOMOUS DECISION: Single Point of Failure Detected
                # ══════════════════════════════════════════════════════════
                print("\n" + "=" * 60)
                print("🚨 AUTONOMOUS DECISION: Single Point of Failure Detected")
                print("=" * 60)
                print(f"   Current trading servers: {len(critical_servers)}")
                print(f"   Existing: {[s['id'] for s in critical_servers]}")
                print(f"   Required minimum: {min_servers}")
                print(f"   Risk: Complete trading halt if primary fails")
                print()

                if auto_provision and self.auto_provision:
                    current_spend = self.infra_provisioner.get_current_spend()
                    budget_available = self.infrastructure_budget - current_spend

                    if budget_available >= 20:  # Min cost for backup
                        print("   DECISION: Provision failover server")
                        print("   Reason: Protect live trading from single point of failure")

                        if not self.dry_run:
                            success, server, message = self.infra_provisioner.provision_new_server(
                                role=ServerRole.TRADING_BACKUP,
                                size=InstanceSize.SMALL
                            )

                            if success:
                                self._redundancy_handled = True
                                self.stats["servers_provisioned"] = self.stats.get("servers_provisioned", 0) + 1
                                print(f"   ✓ Failover server provisioned: {message}")

                                # Register new server
                                self._register_provisioned_server(server, config_path, config)
                            else:
                                print(f"   ✗ Provisioning failed: {message}")
                                print("   Will retry next cycle")
                        else:
                            print("   [DRY RUN] Would provision failover server")
                            self._redundancy_handled = True
                    else:
                        print(f"   ⚠️  Budget insufficient (${budget_available:.2f} available)")
                        print("   Queuing for budget approval...")
                        self._queue_for_approval(
                            title="Infrastructure: Failover Server Required",
                            description="Single point of failure detected. Need backup server to protect trading.",
                            change_type="infrastructure_budget",
                            risk_level="high",
                            action_data={
                                "type": "provision_failover",
                                "reason": "single_point_of_failure",
                                "estimated_cost": 20.0
                            }
                        )
                else:
                    print("   Auto-provision disabled, queuing for approval...")

                print("=" * 60 + "\n")

        except Exception as e:
            print(f"   Redundancy check error: {e}")

    def _register_provisioned_server(self, server, config_path: Path, config: dict):
        """Register a newly provisioned server."""
        try:
            new_server = {
                "id": f"auto-{datetime.utcnow().strftime('%Y%m%d%H%M')}",
                "provider": self.infra_provisioner.provider.value,
                "ip": getattr(server, 'ip', 'pending'),
                "role": "trading_backup",
                "type": "auto_provisioned",
                "critical": True,
                "registered_at": datetime.utcnow().isoformat()
            }
            config["production_servers"].append(new_server)

            with open(config_path, 'w') as f:
                json.dump(config, f, indent=2)

            print(f"   ✓ Server registered: {new_server['id']}")
        except Exception as e:
            print(f"   Warning: Failed to register server: {e}")

    def _queue_for_approval(
        self,
        title: str,
        description: str,
        change_type: str,
        risk_level: str,
        action_data: Dict
    ):
        """Add an action to the approval queue with deduplication."""
        # Deduplication: check if similar item already pending
        pending = self.approval_queue.get_pending()
        for existing in pending:
            if existing.get("title") == title:
                # Already have this exact request pending, skip
                return

        change_id = self.approval_queue.add_change(
            title=title,
            description=description,
            change_type=change_type,
            files_affected=["autonomous_system"],
            proposed_action=action_data,
            risk_level=risk_level
        )

        self.stats["approvals_requested"] += 1

        # Send notification
        change = self.approval_queue.get_change(change_id)
        if change:
            send_approval_notification(change_id, change)

        self._log_event("approval_requested", {
            "change_id": change_id,
            "title": title,
            "risk_level": risk_level
        })

    def _process_approved_actions(self):
        """Process any approved actions from the queue."""
        queue = self.approval_queue._load_queue()

        for change in queue.get("approved", []):
            if change.get("executed"):
                continue

            action = change.get("proposed_action", {})
            action_type = action.get("type")

            if action_type == "infrastructure_decision":
                decision = action.get("decision", {})
                self._execute_infra_decision(decision)
                change["executed"] = True
                change["executed_at"] = datetime.utcnow().isoformat()

            elif action_type == "hardware_decision":
                # Hardware decisions are handled by the decision engine
                change["executed"] = True
                change["executed_at"] = datetime.utcnow().isoformat()

        # Save updated queue
        self.approval_queue._save_queue(queue)

    def _within_auto_approve_budget(self) -> bool:
        """Check if within auto-approve budget."""
        current_spend = self.infra_provisioner.get_current_spend()
        return current_spend + self.AUTO_APPROVE_COST_USD <= self.infrastructure_budget

    def _get_check_interval(self) -> int:
        """Get adaptive check interval."""
        if not self.last_health:
            return self.NORMAL_INTERVAL

        status = self.last_health.get("status", "healthy")

        if status == "critical":
            return self.CRITICAL_INTERVAL
        elif status in ["warning", "degraded"]:
            return self.DEGRADED_INTERVAL
        else:
            return self.NORMAL_INTERVAL

    def _print_status(self, health, hw_decisions, infra_decisions, trading_check):
        """Print status update."""
        timestamp = datetime.utcnow().strftime("%H:%M:%S")
        status = health.overall_status.value
        score = health.overall_score

        # Status indicator
        indicators = {
            "pristine": "✨",
            "optimal": "🟢",
            "healthy": "🟢",
            "degraded": "🟡",
            "warning": "🟠",
            "critical": "🔴",
        }
        indicator = indicators.get(status, "❓")

        # Trading status
        trading = trading_check.status.value
        trading_ind = "🟢" if trading == "active" else "🔴"

        # Spend
        spend = self.infra_provisioner.get_current_spend()

        print(f"[{timestamp}] {indicator} {status.upper()} ({score:.0f}) | "
              f"Trading: {trading_ind} | "
              f"Spend: ${spend:.0f}/{self.infrastructure_budget:.0f} | "
              f"HW:{len(hw_decisions)} Infra:{len(infra_decisions)}")

    def _log_event(self, event_type: str, data: Dict):
        """Log an event."""
        log_file = self.log_path / f"events_{datetime.utcnow().strftime('%Y-%m-%d')}.jsonl"
        with open(log_file, "a") as f:
            f.write(json.dumps({
                "timestamp": datetime.utcnow().isoformat(),
                "session_id": self.session_id,
                "event_type": event_type,
                "data": data
            }) + "\n")

    def _log_error(self, error: str):
        """Log an error."""
        self._log_event("error", {"error": error})
        print(f"❌ Error: {error}")

    def _save_state(self):
        """Save system state."""
        state_file = self.log_path / "state.json"
        state_file.write_text(json.dumps({
            "node_id": self.node_id,
            "session_id": self.session_id,
            "stats": self.stats,
            "last_check": self.last_check.isoformat() if self.last_check else None,
            "last_health": self.last_health
        }, indent=2, default=str))

    def get_status(self) -> Dict[str, Any]:
        """Get current system status."""
        return {
            "running": self.running,
            "node_id": self.node_id,
            "session_id": self.session_id,
            "last_check": self.last_check.isoformat() if self.last_check else None,
            "last_health": self.last_health,
            "stats": self.stats,
            "pending_approvals": len(self.approval_queue.get_pending()),
            "infrastructure": self.infra_provisioner.get_infrastructure_status()
        }


def start_live_system(
    budget: float = 500.0,
    auto_provision: bool = True,
    auto_upgrade: bool = True,
    dry_run: bool = False
):
    """
    Start the unified autonomous system.

    This is the main entry point for LIVE operation.

    Args:
        budget: Monthly infrastructure budget
        auto_provision: Enable auto-provisioning
        auto_upgrade: Enable auto-upgrading
        dry_run: Don't actually provision (testing)
    """
    system = UnifiedAutonomousSystem(
        infrastructure_budget=budget,
        auto_provision=auto_provision,
        auto_upgrade=auto_upgrade,
        dry_run=dry_run
    )
    system.start()


def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Unified Autonomous System - Complete Self-Managing Infrastructure"
    )

    parser.add_argument(
        "--budget",
        type=float,
        default=500.0,
        help="Monthly infrastructure budget in USD"
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
        "--dry-run",
        action="store_true",
        help="Don't actually provision (testing)"
    )
    parser.add_argument(
        "--status",
        action="store_true",
        help="Show status and exit"
    )

    args = parser.parse_args()

    if args.status:
        system = UnifiedAutonomousSystem(dry_run=True)
        status = system.get_status()
        print(json.dumps(status, indent=2, default=str))
    else:
        start_live_system(
            budget=args.budget,
            auto_provision=not args.no_provision,
            auto_upgrade=not args.no_upgrade,
            dry_run=args.dry_run
        )


if __name__ == "__main__":
    main()
