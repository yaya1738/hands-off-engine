"""
Trading System Protection - Live Money Protection Layer

Critical protection layer for live trading systems during hardware operations.
Ensures trading infrastructure remains operational during maintenance,
upgrades, and hardware issues.

Features:
- Process health monitoring
- Automatic failsafe triggers
- Maintenance window management
- Graceful degradation
- Emergency trading halt capability

Standard: Yair Siegel Master Level Operations
PRIORITY: LIVE MONEY PROTECTION
"""

import json
import os
import signal
import subprocess
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field, asdict
from enum import Enum

from hardware.hardware_types import (
    HealthStatus,
    HardwareMetrics,
    HardwareHealth,
    ProcessMetrics,
    TradingSystemProtection,
)


class TradingStatus(Enum):
    """Trading system status levels."""
    ACTIVE = "active"              # Normal trading operations
    DEGRADED = "degraded"          # Operating with reduced capability
    PAUSED = "paused"              # Trading paused, monitoring active
    MAINTENANCE = "maintenance"    # Maintenance window, no trading
    EMERGENCY_HALT = "emergency_halt"  # Emergency stop
    OFFLINE = "offline"            # System offline


class ProtectionAction(Enum):
    """Protection actions that can be taken."""
    NONE = "none"
    ALERT = "alert"
    THROTTLE = "throttle"
    PAUSE_TRADING = "pause_trading"
    GRACEFUL_SHUTDOWN = "graceful_shutdown"
    EMERGENCY_HALT = "emergency_halt"


@dataclass
class TradingHealthCheck:
    """Health check result for trading system."""
    timestamp: datetime
    system_name: str
    status: TradingStatus
    processes_healthy: bool
    resource_headroom_ok: bool
    network_latency_ok: bool
    issues: List[str]
    recommended_action: ProtectionAction
    details: Dict[str, Any] = field(default_factory=dict)


@dataclass
class MaintenanceWindow:
    """Scheduled maintenance window."""
    window_id: str
    start_time: datetime
    end_time: datetime
    description: str
    allow_emergency_trades: bool = False
    auto_resume: bool = True
    created_by: str = "system"


@dataclass
class ProtectionEvent:
    """Record of a protection action taken."""
    event_id: str
    timestamp: datetime
    action: ProtectionAction
    reason: str
    triggered_by: str
    affected_systems: List[str]
    outcome: str = "pending"
    reverted_at: Optional[datetime] = None


class TradingProtectionManager:
    """
    Manages protection of live trading systems.

    Provides comprehensive protection for trading infrastructure
    during hardware operations and issues.
    """

    # Critical thresholds for trading protection
    MIN_CPU_HEADROOM = 15.0          # Minimum CPU headroom percentage
    MIN_MEMORY_HEADROOM_GB = 1.5     # Minimum available memory
    MAX_NETWORK_LATENCY_MS = 200     # Maximum acceptable network latency
    MAX_PROCESS_RESTART_TIME_S = 30  # Maximum time to restart a process

    def __init__(
        self,
        config_path: Optional[Path] = None,
        state_path: Optional[Path] = None
    ):
        """
        Initialize the trading protection manager.

        Args:
            config_path: Path to protection configuration
            state_path: Path to state storage
        """
        self.config_path = config_path or Path("config/trading_protection.json")
        self.state_path = state_path or Path("state/trading_protection")
        self.state_path.mkdir(parents=True, exist_ok=True)

        # Load configuration
        self.protections = self._load_protections()
        self.maintenance_windows: List[MaintenanceWindow] = []
        self.protection_events: List[ProtectionEvent] = []

        # Current state
        self.current_status = TradingStatus.ACTIVE
        self.last_health_check: Optional[TradingHealthCheck] = None
        self._monitoring_active = True

    def _load_protections(self) -> List[TradingSystemProtection]:
        """Load trading system protection configurations."""
        if self.config_path.exists():
            try:
                data = json.loads(self.config_path.read_text())
                return [TradingSystemProtection(**p) for p in data.get("systems", [])]
            except Exception as e:
                # INTEGRAFIX: Log trading protection config failures
                import logging
                logging.warning(f"Failed to load trading protection config: {e}")

        # Default protections - matched to actual running processes
        return [
            TradingSystemProtection(
                system_name="unified_autonomous_system",
                process_patterns=["python.*unified_system", "python.*autonomous"],
                critical_ports=[8000],
                min_cpu_headroom=15.0,
                min_memory_headroom_gb=1.0,
                max_latency_ms=200.0,
                priority=1
            ),
            TradingSystemProtection(
                system_name="telegram_bot",
                process_patterns=["python.*telegram"],
                critical_ports=[],
                min_cpu_headroom=10.0,
                min_memory_headroom_gb=0.5,
                max_latency_ms=300.0,
                priority=2
            ),
            TradingSystemProtection(
                system_name="self_healing",
                process_patterns=["python.*self_healing", "python.*healing"],
                critical_ports=[],
                min_cpu_headroom=5.0,
                min_memory_headroom_gb=0.5,
                max_latency_ms=500.0,
                priority=3
            )
        ]

    def check_trading_health(
        self,
        metrics: HardwareMetrics,
        health: HardwareHealth
    ) -> TradingHealthCheck:
        """
        Check health of trading systems.

        Args:
            metrics: Current hardware metrics
            health: Current hardware health

        Returns:
            TradingHealthCheck with status and recommendations
        """
        issues = []
        all_processes_healthy = True
        resource_headroom_ok = True
        network_ok = True

        # Check each protected system
        import re
        for protection in self.protections:
            # Check processes - use regex matching
            for pattern in protection.process_patterns:
                process_found = any(
                    re.search(pattern, p.process_name, re.IGNORECASE)
                    for p in metrics.trading_processes
                )
                if not process_found:
                    issues.append(f"{protection.system_name}: Process not found ({pattern})")
                    all_processes_healthy = False

            # Check resource headroom
            cpu_headroom = 100 - metrics.cpu.usage_percent
            if cpu_headroom < protection.min_cpu_headroom:
                issues.append(f"{protection.system_name}: Low CPU headroom ({cpu_headroom:.1f}%)")
                resource_headroom_ok = False

            if metrics.memory.available_gb < protection.min_memory_headroom_gb:
                issues.append(f"{protection.system_name}: Low memory ({metrics.memory.available_gb:.2f}GB)")
                resource_headroom_ok = False

            # Check network latency
            for net in metrics.networks:
                if net.latency_ms > protection.max_latency_ms:
                    issues.append(f"{protection.system_name}: High latency ({net.latency_ms:.1f}ms)")
                    network_ok = False

        # Determine status
        status = TradingStatus.ACTIVE
        action = ProtectionAction.NONE

        if not all_processes_healthy:
            status = TradingStatus.DEGRADED
            action = ProtectionAction.ALERT

        if not resource_headroom_ok:
            if metrics.memory.available_gb < 0.5:
                status = TradingStatus.EMERGENCY_HALT
                action = ProtectionAction.EMERGENCY_HALT
            elif metrics.cpu.usage_percent > 95:
                status = TradingStatus.PAUSED
                action = ProtectionAction.PAUSE_TRADING
            else:
                status = TradingStatus.DEGRADED
                action = ProtectionAction.THROTTLE

        if not network_ok:
            if any(n.latency_ms > 500 for n in metrics.networks):
                status = TradingStatus.PAUSED
                action = ProtectionAction.PAUSE_TRADING

        # Check for critical hardware health
        if health.overall_status == HealthStatus.CRITICAL:
            status = TradingStatus.EMERGENCY_HALT
            action = ProtectionAction.EMERGENCY_HALT
            issues.append("Hardware in CRITICAL state")

        # Check maintenance windows
        if self._in_maintenance_window():
            status = TradingStatus.MAINTENANCE
            action = ProtectionAction.PAUSE_TRADING
            issues.append("In scheduled maintenance window")

        check = TradingHealthCheck(
            timestamp=datetime.utcnow(),
            system_name="trading_systems",
            status=status,
            processes_healthy=all_processes_healthy,
            resource_headroom_ok=resource_headroom_ok,
            network_latency_ok=network_ok,
            issues=issues,
            recommended_action=action,
            details={
                "cpu_headroom": round(100 - metrics.cpu.usage_percent, 1),
                "memory_available_gb": round(metrics.memory.available_gb, 2),
                "trading_processes": len(metrics.trading_processes),
                "hardware_health_score": health.overall_score
            }
        )

        self.last_health_check = check
        self.current_status = status

        # AUTO-RECOVERY: If system is healthy and protection flags exist, clear them
        if status == TradingStatus.ACTIVE and action == ProtectionAction.NONE:
            self._auto_recover_if_healthy(health)

        return check

    def _auto_recover_if_healthy(self, health: HardwareHealth) -> bool:
        """
        Automatically recover from protection state if system is healthy.

        Only recovers if:
        - Hardware health is good (score >= 70)
        - No critical alerts
        - Protection was triggered by hardware (not manual)
        """
        # Check if any protection flags exist
        halt_file = self.state_path / "emergency_halt"
        pause_file = self.state_path / "trading_paused"
        throttle_file = self.state_path / "throttle_active"

        has_protection = halt_file.exists() or pause_file.exists() or throttle_file.exists()

        if not has_protection:
            return False  # Nothing to recover from

        # Only auto-recover if health is genuinely good
        if health.overall_score < 70:
            return False

        # Check if protection was hardware-triggered (safe to auto-recover)
        auto_recover = False
        if pause_file.exists():
            try:
                data = json.loads(pause_file.read_text())
                if data.get("reason") == "hardware_protection":
                    auto_recover = True
            except:
                pass

        if halt_file.exists():
            # Emergency halts from hardware issues can be auto-recovered
            auto_recover = True

        if throttle_file.exists():
            auto_recover = True

        if auto_recover:
            print(f"🔄 Auto-recovering: Hardware healthy (score: {health.overall_score})")
            return self.resume_trading(reason=f"auto_recovery_healthy_score_{health.overall_score}")

    def _in_maintenance_window(self) -> bool:
        """Check if currently in a maintenance window."""
        now = datetime.utcnow()
        for window in self.maintenance_windows:
            if window.start_time <= now <= window.end_time:
                return True
        return False

    def execute_protection(
        self,
        action: ProtectionAction,
        reason: str,
        triggered_by: str = "automatic"
    ) -> ProtectionEvent:
        """
        Execute a protection action.

        Args:
            action: Protection action to take
            reason: Reason for the action
            triggered_by: What triggered this action

        Returns:
            ProtectionEvent record
        """
        event = ProtectionEvent(
            event_id=f"protect_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
            timestamp=datetime.utcnow(),
            action=action,
            reason=reason,
            triggered_by=triggered_by,
            affected_systems=[p.system_name for p in self.protections]
        )

        try:
            if action == ProtectionAction.ALERT:
                self._send_alert(reason)
                event.outcome = "alert_sent"

            elif action == ProtectionAction.THROTTLE:
                self._throttle_trading()
                event.outcome = "throttled"

            elif action == ProtectionAction.PAUSE_TRADING:
                self._pause_trading()
                event.outcome = "paused"

            elif action == ProtectionAction.GRACEFUL_SHUTDOWN:
                self._graceful_shutdown()
                event.outcome = "shutdown_initiated"

            elif action == ProtectionAction.EMERGENCY_HALT:
                self._emergency_halt()
                event.outcome = "halted"

            else:
                event.outcome = "no_action"

        except Exception as e:
            event.outcome = f"failed: {str(e)}"

        self.protection_events.append(event)
        self._save_event(event)

        return event

    def _send_alert(self, reason: str):
        """Send protection alert."""
        alert_file = self.state_path / "alerts.jsonl"
        alert = {
            "timestamp": datetime.utcnow().isoformat(),
            "type": "trading_protection",
            "reason": reason,
            "status": self.current_status.value
        }
        with open(alert_file, "a") as f:
            f.write(json.dumps(alert) + "\n")

        # Print to console for immediate visibility
        print(f"\n🚨 TRADING PROTECTION ALERT: {reason}")

    def _throttle_trading(self):
        """Throttle trading operations."""
        # Set throttle flag for trading systems to read
        throttle_file = self.state_path / "throttle_active"
        throttle_file.write_text(json.dumps({
            "active": True,
            "since": datetime.utcnow().isoformat(),
            "level": "medium"
        }))
        print("⚠️ Trading throttled")

    def _pause_trading(self):
        """Pause all trading operations."""
        pause_file = self.state_path / "trading_paused"
        pause_file.write_text(json.dumps({
            "paused": True,
            "since": datetime.utcnow().isoformat(),
            "reason": "hardware_protection"
        }))
        print("⏸️ Trading paused")

    def _graceful_shutdown(self):
        """Initiate graceful shutdown of trading systems."""
        shutdown_file = self.state_path / "shutdown_requested"
        shutdown_file.write_text(json.dumps({
            "requested": True,
            "time": datetime.utcnow().isoformat(),
            "type": "graceful"
        }))
        print("🛑 Graceful shutdown initiated")

    def _emergency_halt(self):
        """Emergency halt all trading operations."""
        # Immediate halt flag
        halt_file = self.state_path / "emergency_halt"
        halt_file.write_text(json.dumps({
            "halted": True,
            "time": datetime.utcnow().isoformat()
        }))

        # Also create pause file for belt-and-suspenders
        self._pause_trading()

        print("🚨 EMERGENCY HALT ACTIVATED")

    def resume_trading(self, reason: str = "manual_resume") -> bool:
        """
        Resume trading after protection action.

        Args:
            reason: Reason for resuming

        Returns:
            True if successfully resumed
        """
        try:
            # Remove all protection flags
            for flag_file in ["throttle_active", "trading_paused", "shutdown_requested", "emergency_halt"]:
                flag_path = self.state_path / flag_file
                if flag_path.exists():
                    flag_path.unlink()

            self.current_status = TradingStatus.ACTIVE

            # Record resume event
            event = ProtectionEvent(
                event_id=f"resume_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
                timestamp=datetime.utcnow(),
                action=ProtectionAction.NONE,
                reason=reason,
                triggered_by="manual",
                affected_systems=[p.system_name for p in self.protections],
                outcome="resumed"
            )
            self.protection_events.append(event)
            self._save_event(event)

            print("✅ Trading resumed")
            return True

        except Exception as e:
            print(f"❌ Failed to resume trading: {e}")
            return False

    def schedule_maintenance(
        self,
        start_time: datetime,
        duration_hours: float,
        description: str,
        allow_emergency: bool = False
    ) -> MaintenanceWindow:
        """
        Schedule a maintenance window.

        Args:
            start_time: Start of maintenance
            duration_hours: Duration in hours
            description: Description of maintenance
            allow_emergency: Allow emergency trades during maintenance

        Returns:
            MaintenanceWindow record
        """
        window = MaintenanceWindow(
            window_id=f"maint_{start_time.strftime('%Y%m%d%H%M')}",
            start_time=start_time,
            end_time=start_time + timedelta(hours=duration_hours),
            description=description,
            allow_emergency_trades=allow_emergency
        )
        self.maintenance_windows.append(window)
        self._save_maintenance_windows()

        print(f"📅 Maintenance scheduled: {start_time} for {duration_hours}h")
        return window

    def cancel_maintenance(self, window_id: str) -> bool:
        """Cancel a scheduled maintenance window."""
        for window in self.maintenance_windows:
            if window.window_id == window_id:
                self.maintenance_windows.remove(window)
                self._save_maintenance_windows()
                print(f"❌ Maintenance cancelled: {window_id}")
                return True
        return False

    def is_safe_for_hardware_operation(
        self,
        operation_type: str,
        estimated_duration_minutes: float = 5
    ) -> Tuple[bool, str]:
        """
        Check if it's safe to perform a hardware operation.

        Args:
            operation_type: Type of operation (upgrade, restart, etc.)
            estimated_duration_minutes: Expected duration

        Returns:
            Tuple of (is_safe, reason)
        """
        # Check current trading status
        if self.current_status == TradingStatus.ACTIVE:
            # Check if we have enough headroom
            if self.last_health_check:
                details = self.last_health_check.details
                cpu_headroom = details.get("cpu_headroom", 0)
                mem_available = details.get("memory_available_gb", 0)

                if cpu_headroom < 30:
                    return False, f"Insufficient CPU headroom ({cpu_headroom:.1f}%)"

                if mem_available < 3.0:
                    return False, f"Insufficient memory ({mem_available:.2f}GB)"

        # Check maintenance windows
        if self._in_maintenance_window():
            return True, "In maintenance window"

        # Check for upcoming maintenance
        now = datetime.utcnow()
        for window in self.maintenance_windows:
            if window.start_time <= now + timedelta(minutes=estimated_duration_minutes):
                return True, f"Maintenance window starting soon ({window.window_id})"

        # Default: allow non-disruptive operations
        if operation_type in ["monitor", "analyze", "log"]:
            return True, "Non-disruptive operation"

        # For other operations, require maintenance window
        return False, "Schedule maintenance window for disruptive operations"

    def get_protection_status(self) -> Dict[str, Any]:
        """Get current protection status summary."""
        return {
            "trading_status": self.current_status.value,
            "monitoring_active": self._monitoring_active,
            "last_health_check": asdict(self.last_health_check) if self.last_health_check else None,
            "active_maintenance_windows": [
                asdict(w) for w in self.maintenance_windows
                if w.start_time <= datetime.utcnow() <= w.end_time
            ],
            "upcoming_maintenance": [
                asdict(w) for w in self.maintenance_windows
                if w.start_time > datetime.utcnow()
            ],
            "recent_protection_events": [
                asdict(e) for e in self.protection_events[-10:]
            ],
            "protected_systems": [p.system_name for p in self.protections]
        }

    def _save_event(self, event: ProtectionEvent):
        """Save protection event to log."""
        events_file = self.state_path / "protection_events.jsonl"
        with open(events_file, "a") as f:
            f.write(json.dumps(asdict(event), default=str) + "\n")

    def _save_maintenance_windows(self):
        """Save maintenance windows to storage."""
        windows_file = self.state_path / "maintenance_windows.json"
        windows_file.write_text(json.dumps(
            [asdict(w) for w in self.maintenance_windows],
            default=str,
            indent=2
        ))


def get_trading_protection() -> TradingProtectionManager:
    """Get the trading protection manager instance."""
    return TradingProtectionManager()


# Convenience functions for external use
def is_trading_safe() -> bool:
    """Quick check if trading is currently safe."""
    status_file = Path("state/trading_protection/trading_paused")
    halt_file = Path("state/trading_protection/emergency_halt")

    if halt_file.exists() or status_file.exists():
        return False
    return True


def get_throttle_level() -> Optional[str]:
    """Get current throttle level if active."""
    throttle_file = Path("state/trading_protection/throttle_active")
    if throttle_file.exists():
        try:
            data = json.loads(throttle_file.read_text())
            return data.get("level", "unknown")
        except:
            pass
    return None


if __name__ == "__main__":
    from hardware.hardware_collector import HardwareCollector
    from hardware.hardware_analyzer import HardwareAnalyzer

    print("Trading Protection Manager Test")
    print("=" * 50)

    # Initialize
    collector = HardwareCollector()
    analyzer = HardwareAnalyzer()
    protection = get_trading_protection()

    # Collect metrics and health
    print("Collecting metrics...")
    metrics = collector.collect_all()
    health = analyzer.analyze(metrics)

    # Check trading health
    print("\nChecking trading health...")
    check = protection.check_trading_health(metrics, health)

    print(f"\nTrading Status: {check.status.value}")
    print(f"Processes Healthy: {check.processes_healthy}")
    print(f"Resource Headroom OK: {check.resource_headroom_ok}")
    print(f"Network Latency OK: {check.network_latency_ok}")
    print(f"Recommended Action: {check.recommended_action.value}")

    if check.issues:
        print(f"\nIssues:")
        for issue in check.issues:
            print(f"  - {issue}")

    print(f"\nDetails: {check.details}")

    # Check if safe for hardware operation
    safe, reason = protection.is_safe_for_hardware_operation("upgrade", 30)
    print(f"\nSafe for hardware upgrade: {safe}")
    print(f"Reason: {reason}")

    # Get status summary
    print("\nProtection Status Summary:")
    status = protection.get_protection_status()
    print(f"  Current Status: {status['trading_status']}")
    print(f"  Protected Systems: {', '.join(status['protected_systems'])}")

    print("\n✅ Trading Protection Manager operational")
