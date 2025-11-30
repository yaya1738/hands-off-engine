"""
Hardware Audit System - Complete Traceability for Hardware Operations

Integrates hardware monitoring with the audit system for complete
traceability of all hardware decisions, actions, and outcomes.

Features:
- Hardware-specific audit events
- Decision audit trail
- Alert logging
- Upgrade tracking
- Integration with main audit system

Standard: Yair Siegel Master Level Operations
"""

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import asdict


def _utc_now() -> datetime:
    """Get current UTC time as timezone-aware datetime."""
    return datetime.now(timezone.utc)

# Import existing audit system
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    from audit import get_audit_logger
    AUDIT_AVAILABLE = True
except ImportError:
    AUDIT_AVAILABLE = False

from hardware.hardware_types import (
    HealthStatus,
    ComponentType,
    HardwareMetrics,
    HardwareHealth,
    HardwareAlert,
    HardwareDecision,
    HardwareUpgradeRecommendation,
)


class HardwareAuditLogger:
    """
    Specialized audit logger for hardware operations.

    Provides hardware-specific logging methods that integrate
    with the main audit system.
    """

    # Hardware-specific event types
    EVENT_HEALTH_CHECK = "hardware_health_check"
    EVENT_ALERT = "hardware_alert"
    EVENT_DECISION = "hardware_decision"
    EVENT_UPGRADE = "hardware_upgrade"
    EVENT_PROTECTION = "hardware_protection"
    EVENT_MAINTENANCE = "hardware_maintenance"
    EVENT_ANOMALY = "hardware_anomaly"
    EVENT_METRIC = "hardware_metric"

    def __init__(self, component: str = "hardware"):
        """
        Initialize the hardware audit logger.

        Args:
            component: Component name for audit logs
        """
        self.component = component

        # Use main audit system if available
        if AUDIT_AVAILABLE:
            self._audit = get_audit_logger(component=component)
        else:
            self._audit = None

        # Fallback hardware-specific log
        self.log_path = Path("logs/hardware_audit")
        self.log_path.mkdir(parents=True, exist_ok=True)

    def _log_event(
        self,
        event_type: str,
        data: Dict[str, Any],
        severity: str = "info",
        session_id: Optional[str] = None
    ):
        """Log an event to both audit systems."""
        event = {
            "timestamp": _utc_now().isoformat(),
            "event_type": event_type,
            "component": self.component,
            "severity": severity,
            "session_id": session_id or self._generate_session_id(),
            "data": data
        }

        # Log to main audit system
        if self._audit:
            self._audit.log_action(
                action_type=event_type,
                action_data=data,
                session_id=session_id
            )

        # Also log to hardware-specific log
        log_file = self.log_path / f"hardware_{_utc_now().strftime('%Y-%m-%d')}.jsonl"
        with open(log_file, "a") as f:
            f.write(json.dumps(event, default=str) + "\n")

    def _generate_session_id(self) -> str:
        """Generate a session ID for audit logging."""
        return f"hw_{_utc_now().strftime('%Y%m%d_%H%M%S')}"

    def log_health_check(
        self,
        health: HardwareHealth,
        session_id: Optional[str] = None
    ):
        """
        Log a hardware health check.

        Args:
            health: Health assessment to log
            session_id: Optional session ID
        """
        data = {
            "node_id": health.node_id,
            "overall_status": health.overall_status.value,
            "overall_score": health.overall_score,
            "trading_risk": health.trading_impact_risk,
            "active_alerts": len(health.active_alerts),
            "degradation_trend": health.degradation_trend,
            "components": {
                "cpu": {"status": health.cpu_health.status.value, "score": health.cpu_health.score},
                "memory": {"status": health.memory_health.status.value, "score": health.memory_health.score},
                "disk": {"status": health.disk_health.status.value, "score": health.disk_health.score},
                "network": {"status": health.network_health.status.value, "score": health.network_health.score},
                "thermal": {"status": health.thermal_health.status.value, "score": health.thermal_health.score},
            }
        }

        severity = "info"
        if health.overall_status == HealthStatus.CRITICAL:
            severity = "critical"
        elif health.overall_status == HealthStatus.WARNING:
            severity = "warning"
        elif health.overall_status == HealthStatus.DEGRADED:
            severity = "warning"

        self._log_event(self.EVENT_HEALTH_CHECK, data, severity, session_id)

    def log_alert(
        self,
        alert: HardwareAlert,
        session_id: Optional[str] = None
    ):
        """
        Log a hardware alert.

        Args:
            alert: Alert to log
            session_id: Optional session ID
        """
        data = {
            "alert_id": alert.alert_id,
            "node_id": alert.node_id,
            "component": alert.component.value,
            "metric_name": alert.metric_name,
            "current_value": alert.current_value,
            "threshold_value": alert.threshold_value,
            "severity": alert.severity.value,
            "message": alert.message,
            "acknowledged": alert.acknowledged,
            "resolved": alert.resolved
        }

        severity = "warning"
        if alert.severity == HealthStatus.CRITICAL:
            severity = "critical"

        self._log_event(self.EVENT_ALERT, data, severity, session_id)

    def log_decision(
        self,
        decision: HardwareDecision,
        session_id: Optional[str] = None
    ):
        """
        Log a hardware decision.

        Args:
            decision: Decision to log
            session_id: Optional session ID
        """
        data = {
            "decision_id": decision.decision_id,
            "node_id": decision.node_id,
            "decision_type": decision.decision_type,
            "action": decision.action,
            "reason": decision.reason,
            "triggered_by": decision.triggered_by,
            "confidence": decision.confidence.value,
            "auto_executed": decision.auto_executed,
            "requires_approval": decision.requires_approval,
            "approval_status": decision.approval_status,
            "executed": decision.executed,
            "success": decision.success,
            "outcome": decision.outcome,
            "health_snapshot": decision.health_snapshot,
            "ai_reasoning": decision.ai_reasoning[:500] if decision.ai_reasoning else None
        }

        severity = "info"
        if decision.decision_type == "emergency":
            severity = "critical"
        elif decision.decision_type in ["alert", "alert_response"]:
            severity = "warning"

        self._log_event(self.EVENT_DECISION, data, severity, session_id)

    def log_upgrade_recommendation(
        self,
        recommendation: HardwareUpgradeRecommendation,
        session_id: Optional[str] = None
    ):
        """
        Log a hardware upgrade recommendation.

        Args:
            recommendation: Upgrade recommendation to log
            session_id: Optional session ID
        """
        data = {
            "recommendation_id": recommendation.recommendation_id,
            "node_id": recommendation.node_id,
            "component": recommendation.component.value,
            "current_spec": recommendation.current_spec,
            "recommended_spec": recommendation.recommended_spec,
            "reason": recommendation.reason,
            "urgency": recommendation.urgency.value,
            "confidence": recommendation.confidence.value,
            "status": recommendation.status,
            "expected_improvement": recommendation.expected_improvement,
            "trading_impact": recommendation.trading_impact,
            "estimated_cost": recommendation.estimated_cost,
            "supporting_data": recommendation.supporting_data
        }

        self._log_event(self.EVENT_UPGRADE, data, "info", session_id)

    def log_protection_event(
        self,
        action: str,
        reason: str,
        affected_systems: List[str],
        outcome: str,
        session_id: Optional[str] = None
    ):
        """
        Log a trading protection event.

        Args:
            action: Protection action taken
            reason: Reason for action
            affected_systems: Systems affected
            outcome: Action outcome
            session_id: Optional session ID
        """
        data = {
            "action": action,
            "reason": reason,
            "affected_systems": affected_systems,
            "outcome": outcome
        }

        severity = "warning"
        if action in ["emergency_halt", "graceful_shutdown"]:
            severity = "critical"

        self._log_event(self.EVENT_PROTECTION, data, severity, session_id)

    def log_maintenance_event(
        self,
        event_type: str,  # "scheduled", "started", "completed", "cancelled"
        description: str,
        window_id: Optional[str] = None,
        session_id: Optional[str] = None
    ):
        """
        Log a maintenance event.

        Args:
            event_type: Type of maintenance event
            description: Description of maintenance
            window_id: Maintenance window ID
            session_id: Optional session ID
        """
        data = {
            "maintenance_type": event_type,
            "description": description,
            "window_id": window_id
        }

        self._log_event(self.EVENT_MAINTENANCE, data, "info", session_id)

    def log_anomaly(
        self,
        component: str,
        metric: str,
        value: float,
        expected_range: str,
        description: str,
        session_id: Optional[str] = None
    ):
        """
        Log a detected anomaly.

        Args:
            component: Component with anomaly
            metric: Metric with anomaly
            value: Current value
            expected_range: Expected value range
            description: Anomaly description
            session_id: Optional session ID
        """
        data = {
            "component": component,
            "metric": metric,
            "current_value": value,
            "expected_range": expected_range,
            "description": description
        }

        self._log_event(self.EVENT_ANOMALY, data, "warning", session_id)

    def log_metrics_snapshot(
        self,
        metrics: HardwareMetrics,
        session_id: Optional[str] = None
    ):
        """
        Log a metrics snapshot for detailed analysis.

        Args:
            metrics: Hardware metrics snapshot
            session_id: Optional session ID
        """
        data = {
            "node_id": metrics.node_id,
            "hostname": metrics.hostname,
            "cpu": {
                "usage_percent": metrics.cpu.usage_percent,
                "load_average": metrics.cpu.load_average_1m,
                "iowait": metrics.cpu.iowait_percent,
                "cores": metrics.cpu.core_count
            },
            "memory": {
                "total_gb": metrics.memory.total_gb,
                "used_gb": metrics.memory.used_gb,
                "available_gb": metrics.memory.available_gb,
                "swap_percent": metrics.memory.swap_percent
            },
            "disks": [
                {
                    "mount": d.mount_point,
                    "usage_percent": d.usage_percent,
                    "available_gb": d.available_gb
                }
                for d in metrics.disks
            ],
            "thermal": {
                "cpu_temp": metrics.thermal.cpu_temp_celsius,
                "throttling": metrics.thermal.thermal_throttling
            },
            "trading_processes": len(metrics.trading_processes),
            "collection_time_ms": metrics.collection_duration_ms
        }

        self._log_event(self.EVENT_METRIC, data, "debug", session_id)

    def get_recent_events(
        self,
        event_type: Optional[str] = None,
        hours: int = 24,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Get recent audit events.

        Args:
            event_type: Filter by event type
            hours: Hours of history to retrieve
            limit: Maximum number of events

        Returns:
            List of audit events
        """
        events = []

        # Read from hardware audit log
        log_files = sorted(self.log_path.glob("hardware_*.jsonl"), reverse=True)

        for log_file in log_files[:7]:  # Last 7 days
            try:
                with open(log_file, "r") as f:
                    for line in f:
                        if line.strip():
                            event = json.loads(line)
                            if event_type is None or event.get("event_type") == event_type:
                                events.append(event)

                if len(events) >= limit:
                    break
            except:
                continue

        # Sort by timestamp descending
        events.sort(key=lambda e: e.get("timestamp", ""), reverse=True)

        return events[:limit]

    def get_decision_audit_trail(
        self,
        decision_id: str
    ) -> Optional[Dict[str, Any]]:
        """
        Get complete audit trail for a decision.

        Args:
            decision_id: Decision ID to look up

        Returns:
            Decision with full audit trail
        """
        events = self.get_recent_events(event_type=self.EVENT_DECISION)

        for event in events:
            if event.get("data", {}).get("decision_id") == decision_id:
                return event

        return None


# Singleton instance
_hardware_audit_instance: Optional[HardwareAuditLogger] = None


def get_hardware_audit_logger() -> HardwareAuditLogger:
    """Get the hardware audit logger singleton."""
    global _hardware_audit_instance
    if _hardware_audit_instance is None:
        _hardware_audit_instance = HardwareAuditLogger()
    return _hardware_audit_instance


if __name__ == "__main__":
    from hardware.hardware_collector import HardwareCollector
    from hardware.hardware_analyzer import HardwareAnalyzer

    print("Hardware Audit Logger Test")
    print("=" * 50)

    # Initialize
    collector = HardwareCollector()
    analyzer = HardwareAnalyzer()
    audit = get_hardware_audit_logger()

    # Collect and analyze
    print("Collecting metrics...")
    metrics = collector.collect_all()
    health = analyzer.analyze(metrics)

    # Log various events
    print("\nLogging events...")

    # Log health check
    audit.log_health_check(health)
    print("  ✓ Health check logged")

    # Log metrics snapshot
    audit.log_metrics_snapshot(metrics)
    print("  ✓ Metrics snapshot logged")

    # Log alerts
    for alert in health.active_alerts:
        audit.log_alert(alert)
    print(f"  ✓ {len(health.active_alerts)} alerts logged")

    # Get recent events
    print("\nRecent Events:")
    events = audit.get_recent_events(limit=5)
    for event in events:
        print(f"  [{event['event_type']}] {event['timestamp']}")

    print("\n✅ Hardware Audit Logger operational")
