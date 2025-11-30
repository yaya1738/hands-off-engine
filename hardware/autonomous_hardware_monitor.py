"""
Autonomous Hardware Monitor - Live Self-Monitoring Infrastructure

Autonomous monitoring system that continuously watches hardware health,
makes decisions, and protects trading systems without human intervention.

Features:
- Continuous health monitoring
- Autonomous decision making
- Trading protection integration
- Alert escalation
- Scheduled maintenance support
- Self-healing capabilities

Standard: Yair Siegel Master Level Operations
"""

import json
import time
import signal
import sys
import argparse
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import asdict
import threading


def _utc_now() -> datetime:
    """Get current UTC time as timezone-aware datetime."""
    return datetime.now(timezone.utc)

from hardware.hardware_types import (
    HealthStatus,
    ComponentType,
    HardwareMetrics,
    HardwareHealth,
    HardwareDecision,
)
from hardware.hardware_collector import HardwareCollector
from hardware.hardware_analyzer import HardwareAnalyzer
from hardware.hardware_kernel import HardwareKernel
from hardware.hardware_decision_engine import HardwareDecisionEngine
from hardware.trading_protection import TradingProtectionManager, TradingStatus
from hardware.hardware_audit import get_hardware_audit_logger


class AutonomousHardwareMonitor:
    """
    Autonomous hardware monitoring and management system.

    Runs continuously to monitor hardware health, make decisions,
    and protect trading systems.
    """

    # Monitoring intervals (seconds)
    DEFAULT_INTERVAL = 30
    ALERT_INTERVAL = 10      # Faster checks during alerts
    DEGRADED_INTERVAL = 15   # Faster checks when degraded
    PRISTINE_INTERVAL = 60   # Slower checks when pristine

    def __init__(
        self,
        node_id: Optional[str] = None,
        auto_execute: bool = False,
        trading_protection: bool = True,
        monitor_interval: int = DEFAULT_INTERVAL
    ):
        """
        Initialize the autonomous monitor.

        Args:
            node_id: Unique node identifier
            auto_execute: Enable auto-execution of decisions
            trading_protection: Enable trading protection
            monitor_interval: Base monitoring interval in seconds
        """
        self.node_id = node_id or self._get_node_id()
        self.monitor_interval = monitor_interval
        self.auto_execute = auto_execute
        self.trading_protection_enabled = trading_protection

        # Initialize components
        self.collector = HardwareCollector(node_id=self.node_id)
        self.analyzer = HardwareAnalyzer()
        self.kernel = HardwareKernel(node_id=self.node_id)
        self.decision_engine = HardwareDecisionEngine(
            kernel=self.kernel,
            auto_execute_enabled=auto_execute
        )
        self.trading_protection = TradingProtectionManager() if trading_protection else None
        self.audit = get_hardware_audit_logger()

        # State
        self.running = False
        self._stop_event = threading.Event()
        self.last_health: Optional[HardwareHealth] = None
        self.last_metrics: Optional[HardwareMetrics] = None
        self.consecutive_critical_count = 0
        self.session_id = f"hw_monitor_{_utc_now().strftime('%Y%m%d_%H%M%S')}"

        # Statistics
        self.stats = {
            "checks_performed": 0,
            "alerts_generated": 0,
            "decisions_made": 0,
            "protections_triggered": 0,
            "start_time": None,
            "last_check": None
        }

        # Register signal handlers
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)

    def _get_node_id(self) -> str:
        """Get unique node identifier."""
        import socket
        return socket.gethostname()

    def _signal_handler(self, signum, frame):
        """Handle shutdown signals gracefully."""
        print(f"\n⚡ Received signal {signum}, shutting down gracefully...")
        self.stop()

    def start(self):
        """Start the autonomous monitoring loop."""
        self.running = True
        self._stop_event.clear()
        self.stats["start_time"] = _utc_now().isoformat()

        print(f"🚀 Autonomous Hardware Monitor starting...")
        print(f"   Node: {self.node_id}")
        print(f"   Auto-execute: {self.auto_execute}")
        print(f"   Trading protection: {self.trading_protection_enabled}")
        print(f"   Base interval: {self.monitor_interval}s")
        print(f"   Session: {self.session_id}")
        print(f"\nPress Ctrl+C to stop\n")

        # Initial warmup collection
        self._warmup()

        # Main monitoring loop
        try:
            while self.running and not self._stop_event.is_set():
                try:
                    self._monitoring_cycle()
                except Exception as e:
                    print(f"❌ Error in monitoring cycle: {e}")
                    self.audit._log_event("monitor_error", {"error": str(e)}, "error")

                # Adaptive sleep interval
                interval = self._get_adaptive_interval()
                self._stop_event.wait(interval)

        except KeyboardInterrupt:
            pass
        finally:
            self.stop()

    def stop(self):
        """Stop the monitoring loop."""
        if not self.running:
            return

        self.running = False
        self._stop_event.set()

        # Log shutdown
        self.audit._log_event("monitor_stopped", {
            "session_id": self.session_id,
            "stats": self.stats
        }, "info")

        print(f"\n✅ Hardware Monitor stopped")
        print(f"   Checks performed: {self.stats['checks_performed']}")
        print(f"   Alerts generated: {self.stats['alerts_generated']}")
        print(f"   Decisions made: {self.stats['decisions_made']}")

    def _warmup(self):
        """Perform warmup collections for baseline establishment."""
        print("🔄 Warming up (collecting baseline)...")

        for i in range(3):
            metrics = self.collector.collect_all()
            health = self.analyzer.analyze(metrics)
            self.kernel.learn_from_metrics(metrics, health)
            time.sleep(1)

        print("✓ Warmup complete\n")

    def _monitoring_cycle(self):
        """Execute one monitoring cycle."""
        cycle_start = _utc_now()

        # Collect metrics
        metrics = self.collector.collect_all()
        self.last_metrics = metrics

        # Analyze health
        health = self.analyzer.analyze(metrics)
        self.last_health = health

        self.stats["checks_performed"] += 1
        self.stats["last_check"] = cycle_start.isoformat()

        # Log health check
        self.audit.log_health_check(health, self.session_id)

        # Handle based on status
        status_handlers = {
            HealthStatus.CRITICAL: self._handle_critical,
            HealthStatus.WARNING: self._handle_warning,
            HealthStatus.DEGRADED: self._handle_degraded,
            HealthStatus.HEALTHY: self._handle_healthy,
            HealthStatus.OPTIMAL: self._handle_optimal,
            HealthStatus.PRISTINE: self._handle_pristine,
        }

        handler = status_handlers.get(health.overall_status, self._handle_healthy)
        handler(metrics, health)

        # Trading protection check
        if self.trading_protection_enabled and self.trading_protection:
            self._check_trading_protection(metrics, health)

        # Generate and process decisions
        decisions = self.decision_engine.analyze_and_decide(metrics, health)
        self.stats["decisions_made"] += len(decisions)

        for decision in decisions:
            self.audit.log_decision(decision, self.session_id)

        # Log alerts
        for alert in health.active_alerts:
            self.audit.log_alert(alert, self.session_id)
        self.stats["alerts_generated"] += len(health.active_alerts)

        # Status output
        self._print_status(health, decisions)

    def _handle_critical(self, metrics: HardwareMetrics, health: HardwareHealth):
        """Handle critical health status."""
        self.consecutive_critical_count += 1

        print(f"\n🚨 CRITICAL: {health.overall_status.value} (score: {health.overall_score})")

        # Escalate if persistent
        if self.consecutive_critical_count >= 3:
            print(f"⚠️  Persistent critical state ({self.consecutive_critical_count} consecutive)")

            # Emergency trading protection
            if self.trading_protection_enabled and self.trading_protection:
                check = self.trading_protection.check_trading_health(metrics, health)
                if check.status != TradingStatus.ACTIVE:
                    self.trading_protection.execute_protection(
                        check.recommended_action,
                        "Persistent critical hardware state",
                        "autonomous_monitor"
                    )
                    self.stats["protections_triggered"] += 1

    def _handle_warning(self, metrics: HardwareMetrics, health: HardwareHealth):
        """Handle warning health status."""
        self.consecutive_critical_count = 0
        print(f"⚠️  WARNING: {health.overall_status.value} (score: {health.overall_score})")

    def _handle_degraded(self, metrics: HardwareMetrics, health: HardwareHealth):
        """Handle degraded health status."""
        self.consecutive_critical_count = 0
        print(f"📉 DEGRADED: {health.overall_status.value} (score: {health.overall_score})")

    def _handle_healthy(self, metrics: HardwareMetrics, health: HardwareHealth):
        """Handle healthy status."""
        self.consecutive_critical_count = 0
        # Normal operation, minimal output

    def _handle_optimal(self, metrics: HardwareMetrics, health: HardwareHealth):
        """Handle optimal status."""
        self.consecutive_critical_count = 0
        # Optimal operation

    def _handle_pristine(self, metrics: HardwareMetrics, health: HardwareHealth):
        """Handle pristine status."""
        self.consecutive_critical_count = 0
        # Pristine operation - can consider reducing monitoring frequency

    def _check_trading_protection(
        self,
        metrics: HardwareMetrics,
        health: HardwareHealth
    ):
        """Check and apply trading protection."""
        check = self.trading_protection.check_trading_health(metrics, health)

        if check.status != TradingStatus.ACTIVE:
            print(f"🛡️  Trading protection: {check.status.value}")

            if check.issues:
                for issue in check.issues[:3]:
                    print(f"     - {issue}")

    def _get_adaptive_interval(self) -> int:
        """Get adaptive monitoring interval based on health."""
        if not self.last_health:
            return self.monitor_interval

        status = self.last_health.overall_status

        if status == HealthStatus.CRITICAL:
            return self.ALERT_INTERVAL
        elif status in [HealthStatus.WARNING, HealthStatus.DEGRADED]:
            return self.DEGRADED_INTERVAL
        elif status == HealthStatus.PRISTINE:
            return self.PRISTINE_INTERVAL
        else:
            return self.monitor_interval

    def _print_status(
        self,
        health: HardwareHealth,
        decisions: List[HardwareDecision]
    ):
        """Print status line."""
        timestamp = _utc_now().strftime("%H:%M:%S")
        status_emoji = {
            HealthStatus.PRISTINE: "✨",
            HealthStatus.OPTIMAL: "🟢",
            HealthStatus.HEALTHY: "🟢",
            HealthStatus.DEGRADED: "🟡",
            HealthStatus.WARNING: "🟠",
            HealthStatus.CRITICAL: "🔴",
            HealthStatus.FAILED: "💀",
        }.get(health.overall_status, "❓")

        # Only print status for non-pristine states or every 10 checks
        if health.overall_status != HealthStatus.PRISTINE or self.stats["checks_performed"] % 10 == 0:
            print(f"[{timestamp}] {status_emoji} {health.overall_status.value} "
                  f"({health.overall_score:.0f}) | "
                  f"CPU:{health.cpu_health.score:.0f} "
                  f"MEM:{health.memory_health.score:.0f} "
                  f"DISK:{health.disk_health.score:.0f} | "
                  f"Alerts:{len(health.active_alerts)} "
                  f"Decisions:{len(decisions)}")

    def get_status(self) -> Dict[str, Any]:
        """Get current monitor status."""
        return {
            "running": self.running,
            "node_id": self.node_id,
            "session_id": self.session_id,
            "last_health": asdict(self.last_health) if self.last_health else None,
            "consecutive_critical": self.consecutive_critical_count,
            "stats": self.stats,
            "pending_decisions": [
                asdict(d) for d in self.decision_engine.get_pending_decisions()
            ]
        }

    def run_single_check(self) -> Dict[str, Any]:
        """Run a single health check without starting the loop."""
        metrics = self.collector.collect_all()
        health = self.analyzer.analyze(metrics)
        decisions = self.decision_engine.analyze_and_decide(metrics, health)

        # Trading protection check
        trading_check = None
        if self.trading_protection_enabled and self.trading_protection:
            trading_check = self.trading_protection.check_trading_health(metrics, health)

        return {
            "timestamp": _utc_now().isoformat(),
            "node_id": self.node_id,
            "health": {
                "overall_status": health.overall_status.value,
                "overall_score": health.overall_score,
                "trading_risk": health.trading_impact_risk,
                "alerts": len(health.active_alerts),
                "trend": health.degradation_trend
            },
            "components": {
                "cpu": {"status": health.cpu_health.status.value, "score": health.cpu_health.score},
                "memory": {"status": health.memory_health.status.value, "score": health.memory_health.score},
                "disk": {"status": health.disk_health.status.value, "score": health.disk_health.score},
                "network": {"status": health.network_health.status.value, "score": health.network_health.score},
                "thermal": {"status": health.thermal_health.status.value, "score": health.thermal_health.score},
            },
            "trading_protection": asdict(trading_check) if trading_check else None,
            "decisions": [
                {
                    "id": d.decision_id,
                    "type": d.decision_type,
                    "action": d.action,
                    "confidence": d.confidence.value,
                    "requires_approval": d.requires_approval
                }
                for d in decisions
            ]
        }


def create_hardware_monitoring_task() -> Dict[str, Any]:
    """
    Create an autonomous hardware monitoring task.

    Returns task configuration for the autonomous task queue.
    """
    return {
        "task_type": "hardware_monitoring",
        "task_id": f"hw_monitor_{_utc_now().strftime('%Y%m%d_%H%M%S')}",
        "description": "Autonomous hardware health monitoring and protection",
        "mode": "continuous",
        "config": {
            "monitor_interval": 30,
            "auto_execute": False,
            "trading_protection": True
        },
        "created_at": _utc_now().isoformat()
    }


def main():
    """Main entry point for autonomous hardware monitor."""
    parser = argparse.ArgumentParser(
        description="Autonomous Hardware Monitor - Live Trading Protection"
    )

    parser.add_argument(
        "--node-id",
        help="Node identifier",
        default=None
    )
    parser.add_argument(
        "--interval",
        type=int,
        help="Monitoring interval in seconds",
        default=30
    )
    parser.add_argument(
        "--auto-execute",
        action="store_true",
        help="Enable auto-execution of high-confidence decisions"
    )
    parser.add_argument(
        "--no-trading-protection",
        action="store_true",
        help="Disable trading protection"
    )
    parser.add_argument(
        "--single-check",
        action="store_true",
        help="Run a single check and exit"
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output results as JSON (for single check)"
    )

    args = parser.parse_args()

    # Create monitor
    monitor = AutonomousHardwareMonitor(
        node_id=args.node_id,
        auto_execute=args.auto_execute,
        trading_protection=not args.no_trading_protection,
        monitor_interval=args.interval
    )

    if args.single_check:
        # Single check mode
        result = monitor.run_single_check()

        if args.json:
            print(json.dumps(result, indent=2, default=str))
        else:
            print(f"\n{'='*60}")
            print(f"Hardware Health Check - {result['node_id']}")
            print(f"{'='*60}")
            print(f"Status: {result['health']['overall_status']} (score: {result['health']['overall_score']})")
            print(f"Trading Risk: {result['health']['trading_risk']}")
            print(f"Trend: {result['health']['trend']}")
            print(f"\nComponents:")
            for comp, data in result['components'].items():
                print(f"  {comp.upper():10} {data['status']:10} ({data['score']:.0f})")
            if result['decisions']:
                print(f"\nDecisions ({len(result['decisions'])}):")
                for d in result['decisions']:
                    print(f"  [{d['type']}] {d['action']} ({d['confidence']})")
            print(f"{'='*60}")
    else:
        # Continuous monitoring mode
        monitor.start()


if __name__ == "__main__":
    main()
