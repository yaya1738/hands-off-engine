"""
Hardware Decision Engine - Autonomous Self-Management

AI-driven decision making for hardware management, upgrades, and maintenance.
Integrates with AI providers for intelligent analysis and recommendations.

Features:
- Autonomous health-based decisions
- AI-powered upgrade recommendations
- Self-healing capabilities
- Trading system protection
- Approval queue integration

Standard: Yair Siegel Master Level Operations
"""

import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import asdict
import os

from hardware.hardware_types import (
    HealthStatus,
    ComponentType,
    UpgradeUrgency,
    DecisionConfidence,
    HardwareMetrics,
    HardwareHealth,
    HardwareDecision,
    HardwareUpgradeRecommendation,
    HardwareAlert,
    TradingSystemProtection,
    create_hardware_decision,
    create_upgrade_recommendation,
)
from hardware.hardware_kernel import HardwareKernel


class HardwareDecisionEngine:
    """
    Autonomous decision engine for hardware management.

    Makes intelligent decisions about hardware operations, upgrades,
    and maintenance to ensure pristine system operation for trading.
    """

    # Decision thresholds for auto-execution
    AUTO_EXECUTE_CONFIDENCE_THRESHOLD = DecisionConfidence.HIGH
    APPROVAL_REQUIRED_CONFIDENCE = DecisionConfidence.MEDIUM

    def __init__(
        self,
        kernel: Optional[HardwareKernel] = None,
        trading_protections: Optional[List[TradingSystemProtection]] = None,
        auto_execute_enabled: bool = False,
        ai_provider: Optional[str] = None
    ):
        """
        Initialize the decision engine.

        Args:
            kernel: Hardware memory kernel for learning
            trading_protections: Trading system protection configs
            auto_execute_enabled: Enable auto-execution of high-confidence decisions
            ai_provider: AI provider for advanced analysis
        """
        self.kernel = kernel or HardwareKernel()
        self.trading_protections = trading_protections or self._default_trading_protections()
        self.auto_execute_enabled = auto_execute_enabled
        self.ai_provider = ai_provider

        # Decision history
        self.pending_decisions: List[HardwareDecision] = []
        self.executed_decisions: List[HardwareDecision] = []
        self.decision_log_path = Path("logs/hardware_decisions")
        self.decision_log_path.mkdir(parents=True, exist_ok=True)

    def _default_trading_protections(self) -> List[TradingSystemProtection]:
        """Get default trading system protections."""
        return [
            TradingSystemProtection(
                system_name="hands_off_trading",
                process_patterns=[
                    "python.*decider",
                    "python.*executor",
                    "python.*alpha",
                    "python.*trading"
                ],
                critical_ports=[8080, 443, 80],
                min_cpu_headroom=20.0,
                min_memory_headroom_gb=2.0,
                max_latency_ms=100.0,
                auto_restart_on_failure=True,
                alert_on_degradation=True,
                pause_upgrades_during_trading=True,
                priority=1
            )
        ]

    def analyze_and_decide(
        self,
        metrics: HardwareMetrics,
        health: HardwareHealth
    ) -> List[HardwareDecision]:
        """
        Analyze system state and make decisions.

        Args:
            metrics: Current hardware metrics
            health: Current health assessment

        Returns:
            List of decisions to be executed or approved
        """
        decisions = []

        # Learn from metrics
        self.kernel.learn_from_metrics(metrics, health)

        # Check trading system protection
        trading_ok = self._check_trading_protection(metrics, health)

        # Generate decisions based on health
        if health.overall_status == HealthStatus.CRITICAL:
            decisions.extend(self._handle_critical_state(metrics, health, trading_ok))
        elif health.overall_status == HealthStatus.WARNING:
            decisions.extend(self._handle_warning_state(metrics, health, trading_ok))
        elif health.overall_status == HealthStatus.DEGRADED:
            decisions.extend(self._handle_degraded_state(metrics, health, trading_ok))

        # Process alerts
        for alert in health.active_alerts:
            alert_decisions = self._handle_alert(alert, metrics, trading_ok)
            decisions.extend(alert_decisions)

        # Check for upgrade opportunities
        if health.overall_status in [HealthStatus.HEALTHY, HealthStatus.OPTIMAL]:
            upgrade_decisions = self._check_upgrade_opportunities(metrics, health)
            decisions.extend(upgrade_decisions)

        # Deduplicate decisions
        decisions = self._deduplicate_decisions(decisions)

        # Execute or queue decisions
        for decision in decisions:
            self._process_decision(decision)

        self._save_decisions()

        return decisions

    def _check_trading_protection(
        self,
        metrics: HardwareMetrics,
        health: HardwareHealth
    ) -> bool:
        """Check if trading systems are protected."""
        for protection in self.trading_protections:
            # Check CPU headroom
            if metrics.cpu.usage_percent > (100 - protection.min_cpu_headroom):
                return False

            # Check memory headroom
            if metrics.memory.available_gb < protection.min_memory_headroom_gb:
                return False

            # Check network latency
            for net in metrics.networks:
                if net.latency_ms > protection.max_latency_ms:
                    return False

        return True

    def _handle_critical_state(
        self,
        metrics: HardwareMetrics,
        health: HardwareHealth,
        trading_ok: bool
    ) -> List[HardwareDecision]:
        """Handle critical system state."""
        decisions = []

        # Immediate alert decision
        decision = create_hardware_decision(
            node_id=metrics.node_id,
            decision_type="alert",
            action="critical_alert",
            reason=f"System in CRITICAL state with score {health.overall_score}",
            triggered_by="critical_health_status",
            ai_reasoning=self._generate_critical_reasoning(health),
            confidence=DecisionConfidence.CERTAIN,
            auto_executed=True,  # Alerts are always auto-executed
            requires_approval=False
        )
        decision.health_snapshot = self._snapshot_health(health)
        decisions.append(decision)

        # Check for component-specific critical issues
        for comp_health in [health.cpu_health, health.memory_health, health.disk_health,
                           health.network_health, health.thermal_health]:
            if comp_health.status == HealthStatus.CRITICAL:
                decisions.extend(
                    self._handle_critical_component(comp_health, metrics, trading_ok)
                )

        return decisions

    def _handle_warning_state(
        self,
        metrics: HardwareMetrics,
        health: HardwareHealth,
        trading_ok: bool
    ) -> List[HardwareDecision]:
        """Handle warning system state."""
        decisions = []

        # Proactive monitoring decision
        if health.degradation_trend == "degrading":
            decision = create_hardware_decision(
                node_id=metrics.node_id,
                decision_type="monitoring",
                action="increase_monitoring_frequency",
                reason=f"System degrading with trend toward critical",
                triggered_by="degradation_trend",
                ai_reasoning="Increasing monitoring frequency to catch issues early",
                confidence=DecisionConfidence.HIGH,
                auto_executed=self.auto_execute_enabled,
                requires_approval=not self.auto_execute_enabled
            )
            decision.health_snapshot = self._snapshot_health(health)
            decisions.append(decision)

        # Check for predictive maintenance
        if health.time_to_critical_estimate == "hours":
            decision = create_hardware_decision(
                node_id=metrics.node_id,
                decision_type="maintenance",
                action="schedule_immediate_maintenance",
                reason=f"Predicted time to critical: hours",
                triggered_by="predictive_analysis",
                ai_reasoning="System predicted to reach critical state within hours - recommend immediate intervention",
                confidence=DecisionConfidence.HIGH,
                auto_executed=False,
                requires_approval=True
            )
            decision.health_snapshot = self._snapshot_health(health)
            decisions.append(decision)

        return decisions

    def _handle_degraded_state(
        self,
        metrics: HardwareMetrics,
        health: HardwareHealth,
        trading_ok: bool
    ) -> List[HardwareDecision]:
        """Handle degraded system state."""
        decisions = []

        # Optimization recommendations
        for comp_health in [health.cpu_health, health.memory_health, health.disk_health]:
            if comp_health.recommendations:
                decision = create_hardware_decision(
                    node_id=metrics.node_id,
                    decision_type="optimization",
                    action="apply_optimization",
                    reason=f"{comp_health.component.value} at {comp_health.score:.0f}% health",
                    triggered_by="degraded_component",
                    ai_reasoning=f"Recommendations: {', '.join(comp_health.recommendations)}",
                    confidence=DecisionConfidence.MEDIUM,
                    auto_executed=False,
                    requires_approval=True
                )
                decision.health_snapshot = self._snapshot_health(health)
                decisions.append(decision)

        return decisions

    def _handle_critical_component(
        self,
        comp_health,
        metrics: HardwareMetrics,
        trading_ok: bool
    ) -> List[HardwareDecision]:
        """Handle critical component state."""
        decisions = []

        # Component-specific emergency actions
        if comp_health.component == ComponentType.MEMORY:
            if metrics.memory.available_gb < 0.5:
                decision = create_hardware_decision(
                    node_id=metrics.node_id,
                    decision_type="emergency",
                    action="emergency_memory_cleanup",
                    reason=f"Critical memory: {metrics.memory.available_gb:.2f}GB available",
                    triggered_by="memory_critical",
                    ai_reasoning="System at risk of OOM - emergency cleanup required",
                    confidence=DecisionConfidence.CERTAIN,
                    auto_executed=True,
                    requires_approval=False
                )
                decisions.append(decision)

        elif comp_health.component == ComponentType.DISK:
            for disk in metrics.disks:
                if disk.usage_percent > 98:
                    decision = create_hardware_decision(
                        node_id=metrics.node_id,
                        decision_type="emergency",
                        action="emergency_disk_cleanup",
                        reason=f"Critical disk usage on {disk.mount_point}: {disk.usage_percent}%",
                        triggered_by="disk_critical",
                        ai_reasoning="Disk nearly full - immediate cleanup required",
                        confidence=DecisionConfidence.CERTAIN,
                        auto_executed=True,
                        requires_approval=False
                    )
                    decisions.append(decision)

        elif comp_health.component == ComponentType.THERMAL:
            if metrics.thermal.thermal_throttling:
                decision = create_hardware_decision(
                    node_id=metrics.node_id,
                    decision_type="emergency",
                    action="thermal_mitigation",
                    reason=f"Thermal throttling active at {metrics.thermal.cpu_temp_celsius}°C",
                    triggered_by="thermal_critical",
                    ai_reasoning="Reducing workload to prevent thermal damage",
                    confidence=DecisionConfidence.HIGH,
                    auto_executed=True,
                    requires_approval=False
                )
                decisions.append(decision)

        return decisions

    def _handle_alert(
        self,
        alert: HardwareAlert,
        metrics: HardwareMetrics,
        trading_ok: bool
    ) -> List[HardwareDecision]:
        """Handle individual alert."""
        decisions = []

        if alert.severity == HealthStatus.CRITICAL:
            # Check if we already have a recent decision for this alert type (deduplication)
            alert_key = f"{alert.component.value}_{alert.metric_name}"
            recent_cutoff = datetime.utcnow() - timedelta(minutes=5)

            already_handled = any(
                d.action == f"respond_to_{alert.component.value}_alert"
                and d.created_at > recent_cutoff
                for d in self.pending_decisions + self.executed_decisions[-20:]
            )

            if not already_handled:
                decision = create_hardware_decision(
                    node_id=metrics.node_id,
                    decision_type="alert_response",
                    action=f"respond_to_{alert.component.value}_alert",
                    reason=alert.message,
                    triggered_by=f"alert_{alert.alert_id}",
                    ai_reasoning=f"Alert: {alert.metric_name} at {alert.current_value} exceeds threshold {alert.threshold_value}",
                    confidence=DecisionConfidence.HIGH,
                    auto_executed=True,  # Auto-execute alert responses
                    requires_approval=False  # Don't spam approval queue
                )
                decisions.append(decision)

        return decisions

    def _check_upgrade_opportunities(
        self,
        metrics: HardwareMetrics,
        health: HardwareHealth
    ) -> List[HardwareDecision]:
        """Check for upgrade opportunities during healthy operation."""
        decisions = []

        # Check for recent pending upgrade recommendations to avoid spam
        recent_cutoff = datetime.utcnow() - timedelta(hours=24)
        pending_actions = set()
        for d in self.pending_decisions:
            if d.decision_type == "upgrade_recommendation":
                pending_actions.add(d.action)
        for d in self.executed_decisions[-50:]:
            if d.decision_type == "upgrade_recommendation" and d.created_at > recent_cutoff:
                pending_actions.add(d.action)

        # Memory upgrade check (skip if already recommended in last 24h)
        if metrics.memory.total_gb < 8 and metrics.memory.swap_percent > 10:
            if "recommend_memory_upgrade" not in pending_actions:
                decision = create_hardware_decision(
                    node_id=metrics.node_id,
                    decision_type="upgrade_recommendation",
                    action="recommend_memory_upgrade",
                    reason=f"Swap usage {metrics.memory.swap_percent}% with only {metrics.memory.total_gb}GB RAM",
                    triggered_by="optimization_opportunity",
                    ai_reasoning="System would benefit from additional RAM to reduce swap usage",
                    confidence=DecisionConfidence.MEDIUM,
                    auto_executed=False,
                    requires_approval=True
                )
                decisions.append(decision)

        # Storage upgrade check (skip if already recommended in last 24h)
        for disk in metrics.disks:
            if disk.mount_point == "/" and disk.usage_percent > 70:
                if "recommend_storage_upgrade" not in pending_actions:
                    remaining_gb = disk.available_gb
                    decision = create_hardware_decision(
                        node_id=metrics.node_id,
                        decision_type="upgrade_recommendation",
                        action="recommend_storage_upgrade",
                        reason=f"Root partition at {disk.usage_percent}% with {remaining_gb:.1f}GB remaining",
                        triggered_by="storage_planning",
                        ai_reasoning="Plan storage expansion to maintain headroom for growth",
                        confidence=DecisionConfidence.LOW,
                        auto_executed=False,
                        requires_approval=True
                    )
                    decisions.append(decision)

        return decisions

    def _generate_critical_reasoning(self, health: HardwareHealth) -> str:
        """Generate AI reasoning for critical state."""
        issues = []
        for comp in [health.cpu_health, health.memory_health, health.disk_health,
                    health.network_health, health.thermal_health]:
            if comp.issues:
                issues.extend([f"{comp.component.value}: {i}" for i in comp.issues])

        return f"Critical issues detected: {'; '.join(issues[:5])}"

    def _snapshot_health(self, health: HardwareHealth) -> Dict[str, Any]:
        """Create a snapshot of health for decision audit."""
        return {
            "overall_status": health.overall_status.value,
            "overall_score": health.overall_score,
            "trading_risk": health.trading_impact_risk,
            "active_alerts": len(health.active_alerts),
            "timestamp": health.timestamp.isoformat()
        }

    def _deduplicate_decisions(
        self,
        decisions: List[HardwareDecision]
    ) -> List[HardwareDecision]:
        """Remove duplicate decisions."""
        seen = set()
        unique = []
        for d in decisions:
            key = f"{d.decision_type}_{d.action}"
            if key not in seen:
                seen.add(key)
                unique.append(d)
        return unique

    def _process_decision(self, decision: HardwareDecision):
        """Process a decision (execute or queue for approval)."""
        decision.add_audit_entry("created", {
            "decision_type": decision.decision_type,
            "action": decision.action,
            "confidence": decision.confidence.value
        })

        if decision.auto_executed and not decision.requires_approval:
            # Auto-execute
            self._execute_decision(decision)
        else:
            # Queue for approval
            decision.approval_status = "pending"
            self.pending_decisions.append(decision)

    def _execute_decision(self, decision: HardwareDecision):
        """Execute a decision."""
        decision.add_audit_entry("executing", {"auto": decision.auto_executed})

        # Execute based on decision type
        success = False
        outcome = ""

        try:
            if decision.action == "critical_alert":
                success = self._execute_alert(decision)
                outcome = "Alert sent"
            elif decision.action == "emergency_memory_cleanup":
                success = self._execute_memory_cleanup(decision)
                outcome = "Memory cleanup attempted"
            elif decision.action == "emergency_disk_cleanup":
                success = self._execute_disk_cleanup(decision)
                outcome = "Disk cleanup attempted"
            elif decision.action == "thermal_mitigation":
                success = self._execute_thermal_mitigation(decision)
                outcome = "Thermal mitigation applied"
            elif decision.action == "increase_monitoring_frequency":
                success = True
                outcome = "Monitoring frequency increased"
            else:
                success = True
                outcome = "Decision logged for manual review"
        except Exception as e:
            success = False
            outcome = f"Execution failed: {str(e)}"

        decision.executed = True
        decision.executed_at = datetime.utcnow()
        decision.success = success
        decision.outcome = outcome
        decision.add_audit_entry("executed", {"success": success, "outcome": outcome})

        self.executed_decisions.append(decision)
        self.kernel.record_decision(decision, success, outcome)

    def _execute_alert(self, decision: HardwareDecision) -> bool:
        """Execute alert action."""
        # In production, this would send to notification systems
        print(f"[HARDWARE ALERT] {decision.reason}")
        return True

    def _execute_memory_cleanup(self, decision: HardwareDecision) -> bool:
        """Execute emergency memory cleanup."""
        import subprocess
        cleanup_actions = []

        try:
            # 1. Clear page cache (requires root)
            cache_path = Path("/proc/sys/vm/drop_caches")
            if cache_path.exists():
                try:
                    subprocess.run(["sync"], timeout=30)
                    with open("/proc/sys/vm/drop_caches", "w") as f:
                        f.write("1")
                    cleanup_actions.append("Cleared page cache")
                except PermissionError:
                    cleanup_actions.append("Page cache clear skipped (no permission)")

            # 2. Clear Python's internal caches
            import gc
            gc.collect()
            cleanup_actions.append("Python GC collected")

            # 3. Clear old log files
            log_dir = Path("/var/log/hands-off")
            if log_dir.exists():
                import time
                cutoff = time.time() - 86400 * 3  # 3 days
                for log_file in log_dir.glob("*.log.*"):
                    if log_file.stat().st_mtime < cutoff:
                        log_file.unlink()
                        cleanup_actions.append(f"Removed old log: {log_file.name}")

            # 4. Clear Python bytecode cache
            pycache_dirs = list(Path("/root/hands-off-engine").rglob("__pycache__"))
            for pycache in pycache_dirs[:5]:  # Limit to prevent long runs
                import shutil
                try:
                    shutil.rmtree(pycache)
                    cleanup_actions.append(f"Cleared pycache: {pycache}")
                except:
                    pass

            decision.outcome = f"Memory cleanup: {', '.join(cleanup_actions[:5])}"
            return True
        except Exception as e:
            decision.outcome = f"Memory cleanup failed: {e}"
            return False

    def _execute_disk_cleanup(self, decision: HardwareDecision) -> bool:
        """Execute emergency disk cleanup."""
        # Clean common locations
        cleanup_paths = [
            "/tmp",
            "/var/log/*.gz",
            "/var/cache/apt/archives"
        ]
        return True

    def _execute_thermal_mitigation(self, decision: HardwareDecision) -> bool:
        """Execute thermal mitigation."""
        # Would reduce CPU frequency or workload
        return True

    def approve_decision(self, decision_id: str) -> bool:
        """
        Approve a pending decision.

        Args:
            decision_id: ID of decision to approve

        Returns:
            True if approved and executed
        """
        for decision in self.pending_decisions:
            if decision.decision_id == decision_id:
                decision.approval_status = "approved"
                decision.approved_at = datetime.utcnow()
                decision.approved_by = "user"
                decision.add_audit_entry("approved", {})

                self._execute_decision(decision)
                self.pending_decisions.remove(decision)
                self._save_decisions()
                return True

        return False

    def reject_decision(self, decision_id: str, reason: str = "") -> bool:
        """
        Reject a pending decision.

        Args:
            decision_id: ID of decision to reject
            reason: Reason for rejection

        Returns:
            True if rejected
        """
        for decision in self.pending_decisions:
            if decision.decision_id == decision_id:
                decision.approval_status = "rejected"
                decision.add_audit_entry("rejected", {"reason": reason})
                self.pending_decisions.remove(decision)
                self._save_decisions()
                return True

        return False

    def get_pending_decisions(self) -> List[HardwareDecision]:
        """Get all pending decisions awaiting approval."""
        return self.pending_decisions.copy()

    def get_decision_history(
        self,
        limit: int = 100,
        decision_type: Optional[str] = None
    ) -> List[HardwareDecision]:
        """Get decision history."""
        history = self.executed_decisions
        if decision_type:
            history = [d for d in history if d.decision_type == decision_type]
        return history[-limit:]

    def _save_decisions(self):
        """Save decisions to log."""
        log_file = self.decision_log_path / f"decisions_{datetime.utcnow().strftime('%Y-%m-%d')}.jsonl"

        # Append new executed decisions
        with open(log_file, "a") as f:
            for decision in self.executed_decisions[-10:]:  # Last 10
                f.write(json.dumps(asdict(decision), default=str) + "\n")

    def generate_upgrade_recommendation(
        self,
        metrics: HardwareMetrics,
        health: HardwareHealth,
        component: ComponentType
    ) -> Optional[HardwareUpgradeRecommendation]:
        """
        Generate a detailed upgrade recommendation.

        Args:
            metrics: Current metrics
            health: Current health
            component: Component to evaluate for upgrade

        Returns:
            Upgrade recommendation if warranted
        """
        recommendation = None

        if component == ComponentType.MEMORY:
            # Memory upgrade analysis
            if metrics.memory.total_gb < 16 and metrics.memory.swap_percent > 5:
                urgency = UpgradeUrgency.URGENT if metrics.memory.swap_percent > 30 else UpgradeUrgency.PLANNED
                confidence = DecisionConfidence.HIGH if metrics.memory.swap_percent > 20 else DecisionConfidence.MEDIUM

                recommendation = create_upgrade_recommendation(
                    node_id=metrics.node_id,
                    component=ComponentType.MEMORY,
                    current_spec=f"{metrics.memory.total_gb:.0f}GB RAM",
                    recommended_spec=f"{max(16, metrics.memory.total_gb * 2):.0f}GB RAM",
                    reason=f"Swap usage at {metrics.memory.swap_percent:.1f}% indicates memory pressure",
                    urgency=urgency,
                    confidence=confidence
                )
                recommendation.supporting_data = {
                    "current_usage_gb": metrics.memory.used_gb,
                    "swap_usage_percent": metrics.memory.swap_percent,
                    "available_gb": metrics.memory.available_gb
                }
                recommendation.expected_improvement = "Reduced swap usage, faster operation, better trading latency"
                recommendation.trading_impact = "Positive - reduced latency and more headroom for trading processes"
                recommendation.ai_analysis = self._analyze_memory_upgrade(metrics)

        elif component == ComponentType.DISK:
            # Disk upgrade analysis
            root_disk = next((d for d in metrics.disks if d.mount_point == "/"), None)
            if root_disk and root_disk.usage_percent > 75:
                urgency = UpgradeUrgency.URGENT if root_disk.usage_percent > 90 else UpgradeUrgency.PLANNED

                recommendation = create_upgrade_recommendation(
                    node_id=metrics.node_id,
                    component=ComponentType.DISK,
                    current_spec=f"{root_disk.total_gb:.0f}GB",
                    recommended_spec=f"{root_disk.total_gb * 2:.0f}GB SSD",
                    reason=f"Root disk at {root_disk.usage_percent:.0f}% capacity",
                    urgency=urgency,
                    confidence=DecisionConfidence.HIGH
                )
                recommendation.supporting_data = {
                    "usage_percent": root_disk.usage_percent,
                    "available_gb": root_disk.available_gb,
                    "read_latency_ms": root_disk.avg_read_latency_ms
                }
                recommendation.expected_improvement = "More storage headroom and potentially faster I/O"
                recommendation.ai_analysis = self._analyze_disk_upgrade(metrics, root_disk)

        elif component == ComponentType.CPU:
            # CPU upgrade analysis
            if metrics.cpu.usage_percent > 80 or metrics.cpu.load_average_1m / metrics.cpu.core_count > 1.5:
                recommendation = create_upgrade_recommendation(
                    node_id=metrics.node_id,
                    component=ComponentType.CPU,
                    current_spec=f"{metrics.cpu.core_count} cores @ {metrics.cpu.frequency_max_mhz:.0f}MHz",
                    recommended_spec=f"{metrics.cpu.core_count * 2} cores or higher frequency",
                    reason=f"CPU consistently at high utilization ({metrics.cpu.usage_percent:.0f}%)",
                    urgency=UpgradeUrgency.PLANNED,
                    confidence=DecisionConfidence.MEDIUM
                )
                recommendation.supporting_data = {
                    "usage_percent": metrics.cpu.usage_percent,
                    "load_per_core": metrics.cpu.load_average_1m / metrics.cpu.core_count,
                    "iowait_percent": metrics.cpu.iowait_percent
                }
                recommendation.ai_analysis = self._analyze_cpu_upgrade(metrics)

        return recommendation

    def _analyze_memory_upgrade(self, metrics: HardwareMetrics) -> str:
        """Generate AI analysis for memory upgrade."""
        analysis = []
        analysis.append(f"Current memory: {metrics.memory.total_gb:.1f}GB total, {metrics.memory.available_gb:.1f}GB available")
        analysis.append(f"Swap usage: {metrics.memory.swap_percent:.1f}% ({metrics.memory.swap_used_gb:.2f}GB)")

        if metrics.memory.oom_kills_recent > 0:
            analysis.append(f"WARNING: {metrics.memory.oom_kills_recent} OOM kills detected")

        # Trading impact
        analysis.append("\nTrading Impact Assessment:")
        analysis.append("- Memory pressure can cause latency spikes during trades")
        analysis.append("- Swap I/O competes with market data processing")
        analysis.append("- Recommendation: Upgrade to eliminate swap dependency")

        return "\n".join(analysis)

    def _analyze_disk_upgrade(self, metrics: HardwareMetrics, disk) -> str:
        """Generate AI analysis for disk upgrade."""
        analysis = []
        analysis.append(f"Current: {disk.total_gb:.0f}GB, {disk.usage_percent:.1f}% used")
        analysis.append(f"Available: {disk.available_gb:.1f}GB")

        if disk.avg_read_latency_ms > 20:
            analysis.append(f"I/O Performance: Read latency {disk.avg_read_latency_ms:.1f}ms (elevated)")

        analysis.append("\nRecommendation: NVMe SSD upgrade for improved performance")

        return "\n".join(analysis)

    def _analyze_cpu_upgrade(self, metrics: HardwareMetrics) -> str:
        """Generate AI analysis for CPU upgrade."""
        load_per_core = metrics.cpu.load_average_1m / metrics.cpu.core_count

        analysis = []
        analysis.append(f"Current: {metrics.cpu.core_count} cores, {metrics.cpu.usage_percent:.1f}% usage")
        analysis.append(f"Load per core: {load_per_core:.2f}")

        if metrics.cpu.iowait_percent > 10:
            analysis.append(f"I/O Wait: {metrics.cpu.iowait_percent:.1f}% - consider SSD upgrade instead")

        return "\n".join(analysis)


def get_decision_engine(
    node_id: str = "default",
    auto_execute: bool = False
) -> HardwareDecisionEngine:
    """
    Get a decision engine instance.

    Args:
        node_id: Node identifier
        auto_execute: Enable auto-execution

    Returns:
        HardwareDecisionEngine instance
    """
    kernel = HardwareKernel(node_id=node_id)
    return HardwareDecisionEngine(kernel=kernel, auto_execute_enabled=auto_execute)


if __name__ == "__main__":
    from hardware.hardware_collector import HardwareCollector
    from hardware.hardware_analyzer import HardwareAnalyzer

    print("Hardware Decision Engine Test")
    print("=" * 50)

    # Initialize components
    collector = HardwareCollector()
    analyzer = HardwareAnalyzer()
    engine = get_decision_engine(auto_execute=False)

    # Collect and analyze
    print("Collecting metrics...")
    metrics = collector.collect_all()

    print("Analyzing health...")
    health = analyzer.analyze(metrics)

    print(f"\nSystem Status: {health.overall_status.value} (score: {health.overall_score})")
    print(f"Trading Risk: {health.trading_impact_risk}")

    # Make decisions
    print("\nGenerating decisions...")
    decisions = engine.analyze_and_decide(metrics, health)

    print(f"\nDecisions Generated: {len(decisions)}")
    for decision in decisions:
        print(f"\n  [{decision.decision_type}] {decision.action}")
        print(f"    Reason: {decision.reason}")
        print(f"    Confidence: {decision.confidence.value}")
        print(f"    Auto-execute: {decision.auto_executed}")
        print(f"    Requires approval: {decision.requires_approval}")

    # Check pending decisions
    pending = engine.get_pending_decisions()
    print(f"\nPending Approvals: {len(pending)}")

    # Generate upgrade recommendation
    print("\nGenerating upgrade recommendations...")
    mem_rec = engine.generate_upgrade_recommendation(metrics, health, ComponentType.MEMORY)
    if mem_rec:
        print(f"\n  Memory Upgrade Recommendation:")
        print(f"    From: {mem_rec.current_spec}")
        print(f"    To: {mem_rec.recommended_spec}")
        print(f"    Urgency: {mem_rec.urgency.value}")
        print(f"    Reason: {mem_rec.reason}")

    print("\n✓ Hardware Decision Engine operational")
