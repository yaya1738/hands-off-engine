"""
Hardware Health Dashboard - Visual Status and Alerting

Terminal-based dashboard for hardware health monitoring.
Provides real-time visualization and alert management.

Features:
- Real-time health display
- Alert management
- Decision approval interface
- Upgrade recommendation viewer
- Historical analysis

Standard: Yair Siegel Master Level Operations
"""

import json
import time
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Dict, List, Optional, Any


def _utc_now() -> datetime:
    """Get current UTC time as timezone-aware datetime."""
    return datetime.now(timezone.utc)

from hardware.hardware_types import (
    HealthStatus,
    ComponentType,
    HardwareHealth,
    HardwareAlert,
    HardwareDecision,
    HardwareUpgradeRecommendation,
)
from hardware.hardware_collector import HardwareCollector
from hardware.hardware_analyzer import HardwareAnalyzer
from hardware.hardware_kernel import HardwareKernel
from hardware.hardware_decision_engine import HardwareDecisionEngine
from hardware.trading_protection import TradingProtectionManager
from hardware.hardware_audit import get_hardware_audit_logger


class HardwareDashboard:
    """
    Terminal-based hardware health dashboard.

    Provides comprehensive visualization and management
    of hardware health, alerts, and decisions.
    """

    # ANSI color codes
    COLORS = {
        "reset": "\033[0m",
        "bold": "\033[1m",
        "red": "\033[91m",
        "green": "\033[92m",
        "yellow": "\033[93m",
        "blue": "\033[94m",
        "magenta": "\033[95m",
        "cyan": "\033[96m",
        "white": "\033[97m",
        "bg_red": "\033[41m",
        "bg_green": "\033[42m",
        "bg_yellow": "\033[43m",
    }

    STATUS_COLORS = {
        HealthStatus.PRISTINE: "cyan",
        HealthStatus.OPTIMAL: "green",
        HealthStatus.HEALTHY: "green",
        HealthStatus.DEGRADED: "yellow",
        HealthStatus.WARNING: "yellow",
        HealthStatus.CRITICAL: "red",
        HealthStatus.FAILED: "red",
    }

    def __init__(self):
        """Initialize the dashboard."""
        self.collector = HardwareCollector()
        self.analyzer = HardwareAnalyzer()
        self.kernel = HardwareKernel()
        self.decision_engine = HardwareDecisionEngine(kernel=self.kernel)
        self.trading_protection = TradingProtectionManager()
        self.audit = get_hardware_audit_logger()

    def _color(self, text: str, color: str) -> str:
        """Apply color to text."""
        return f"{self.COLORS.get(color, '')}{text}{self.COLORS['reset']}"

    def _status_color(self, status: HealthStatus) -> str:
        """Get color for status."""
        return self.STATUS_COLORS.get(status, "white")

    def _format_status(self, status: HealthStatus) -> str:
        """Format status with color."""
        color = self._status_color(status)
        return self._color(status.value.upper(), color)

    def _progress_bar(self, value: float, max_val: float = 100, width: int = 20) -> str:
        """Create a progress bar."""
        percent = min(value / max_val, 1.0) if max_val > 0 else 0
        filled = int(width * percent)
        bar = "█" * filled + "░" * (width - filled)

        if percent >= 0.9:
            color = "red"
        elif percent >= 0.7:
            color = "yellow"
        else:
            color = "green"

        return self._color(bar, color)

    def clear_screen(self):
        """Clear the terminal screen."""
        print("\033[2J\033[H", end="")

    def show_header(self):
        """Show dashboard header."""
        timestamp = _utc_now().strftime("%Y-%m-%d %H:%M:%S UTC")
        print(self._color("=" * 70, "blue"))
        print(self._color(f"  HARDWARE HEALTH DASHBOARD - {timestamp}", "bold"))
        print(self._color("  Standard: Yair Siegel Master Level Operations", "cyan"))
        print(self._color("=" * 70, "blue"))

    def show_health_summary(self, health: HardwareHealth):
        """Show overall health summary."""
        print(f"\n{self._color('OVERALL HEALTH', 'bold')}")
        print("-" * 40)

        # Overall status
        status_str = self._format_status(health.overall_status)
        score_bar = self._progress_bar(health.overall_score)
        print(f"  Status: {status_str}")
        print(f"  Score:  {score_bar} {health.overall_score:.0f}/100")
        print(f"  Trend:  {health.degradation_trend}")
        print(f"  Trading Risk: {self._color(health.trading_impact_risk.upper(), 'yellow' if health.trading_impact_risk != 'none' else 'green')}")

        if health.time_to_critical_estimate:
            print(f"  ⚠️  Time to Critical: {health.time_to_critical_estimate}")

    def show_component_health(self, health: HardwareHealth):
        """Show component-level health."""
        print(f"\n{self._color('COMPONENT HEALTH', 'bold')}")
        print("-" * 70)
        print(f"  {'Component':<12} {'Status':<12} {'Score':<8} {'Bar':<22} {'Trend':<10}")
        print("-" * 70)

        components = [
            ("CPU", health.cpu_health),
            ("Memory", health.memory_health),
            ("Disk", health.disk_health),
            ("Network", health.network_health),
            ("Thermal", health.thermal_health),
        ]

        for name, comp in components:
            status = self._format_status(comp.status)
            bar = self._progress_bar(comp.score)
            trend = self._color(comp.trend, "green" if comp.trend == "improving" else "red" if comp.trend == "degrading" else "white")
            print(f"  {name:<12} {status:<22} {comp.score:>5.0f}   {bar} {trend}")

    def show_metrics_detail(self, health: HardwareHealth):
        """Show detailed metrics."""
        print(f"\n{self._color('DETAILED METRICS', 'bold')}")
        print("-" * 70)

        # CPU
        cpu = health.cpu_health.metrics_summary
        print(f"\n  {self._color('CPU:', 'cyan')}")
        print(f"    Usage: {cpu.get('usage_percent', 0):.1f}%  Load: {cpu.get('load_average', 0):.2f}  "
              f"I/O Wait: {cpu.get('iowait_percent', 0):.1f}%")

        # Memory
        mem = health.memory_health.metrics_summary
        print(f"\n  {self._color('Memory:', 'cyan')}")
        print(f"    Used: {mem.get('used_gb', 0):.2f}GB / {mem.get('total_gb', 0):.2f}GB  "
              f"Available: {mem.get('available_gb', 0):.2f}GB  "
              f"Swap: {mem.get('swap_percent', 0):.1f}%")

        # Disk
        disk = health.disk_health.metrics_summary
        print(f"\n  {self._color('Disk:', 'cyan')}")
        if disk.get('disks'):
            for d in disk.get('disks', [])[:3]:
                print(f"    {d['mount']}: {d['usage_percent']:.1f}% used ({d['available_gb']:.1f}GB free)")

        # Thermal
        thermal = health.thermal_health.metrics_summary
        print(f"\n  {self._color('Thermal:', 'cyan')}")
        print(f"    CPU: {thermal.get('cpu_temp', 0)}°C  "
              f"Throttling: {'Yes ⚠️' if thermal.get('throttling') else 'No ✓'}")

    def show_alerts(self, health: HardwareHealth):
        """Show active alerts."""
        print(f"\n{self._color('ACTIVE ALERTS', 'bold')} ({len(health.active_alerts)})")
        print("-" * 70)

        if not health.active_alerts:
            print(f"  {self._color('✓ No active alerts', 'green')}")
            return

        for alert in health.active_alerts:
            severity_color = "red" if alert.severity == HealthStatus.CRITICAL else "yellow"
            print(f"\n  [{self._color(alert.severity.value.upper(), severity_color)}] {alert.message}")
            print(f"    Component: {alert.component.value}  Metric: {alert.metric_name}")
            print(f"    Value: {alert.current_value:.2f}  Threshold: {alert.threshold_value:.2f}")

    def show_issues_and_recommendations(self, health: HardwareHealth):
        """Show issues and recommendations."""
        print(f"\n{self._color('ISSUES & RECOMMENDATIONS', 'bold')}")
        print("-" * 70)

        components = [
            ("CPU", health.cpu_health),
            ("Memory", health.memory_health),
            ("Disk", health.disk_health),
            ("Network", health.network_health),
            ("Thermal", health.thermal_health),
        ]

        has_issues = False
        for name, comp in components:
            if comp.issues:
                has_issues = True
                print(f"\n  {self._color(name + ':', 'yellow')}")
                for issue in comp.issues:
                    print(f"    ⚠️  {issue}")
                for rec in comp.recommendations:
                    print(f"    → {self._color(rec, 'cyan')}")

        if not has_issues:
            print(f"  {self._color('✓ No issues detected', 'green')}")

    def show_pending_decisions(self):
        """Show pending decisions awaiting approval."""
        pending = self.decision_engine.get_pending_decisions()

        print(f"\n{self._color('PENDING DECISIONS', 'bold')} ({len(pending)})")
        print("-" * 70)

        if not pending:
            print(f"  {self._color('✓ No pending decisions', 'green')}")
            return

        for i, decision in enumerate(pending, 1):
            confidence_color = "green" if decision.confidence.value in ["certain", "high"] else "yellow"
            print(f"\n  [{i}] {self._color(decision.decision_type.upper(), 'cyan')}: {decision.action}")
            print(f"      Reason: {decision.reason}")
            print(f"      Confidence: {self._color(decision.confidence.value, confidence_color)}")
            print(f"      ID: {decision.decision_id}")

    def show_kernel_summary(self):
        """Show kernel learning summary."""
        summary = self.kernel.get_kernel_summary()

        print(f"\n{self._color('LEARNING KERNEL', 'bold')}")
        print("-" * 70)
        print(f"  Baseline samples: {summary['baseline']['samples']}")
        print(f"  Anomalies recorded: {summary['anomalies_recorded']}")
        print(f"  Decisions recorded: {summary['decisions_recorded']}")
        print(f"  Decision success rate: {summary['decision_success_rate']:.1f}%")

        upgrades = summary['upgrades']
        if upgrades['total_upgrades'] > 0:
            print(f"\n  Upgrade History:")
            print(f"    Total upgrades: {upgrades['total_upgrades']}")
            print(f"    Success rate: {upgrades['success_rate']:.1f}%")
            print(f"    Net benefit: ${upgrades['net_benefit']:.2f}")

    def show_trading_protection_status(self, metrics, health):
        """Show trading protection status."""
        check = self.trading_protection.check_trading_health(metrics, health)
        status = self.trading_protection.get_protection_status()

        print(f"\n{self._color('TRADING PROTECTION', 'bold')}")
        print("-" * 70)

        status_color = "green" if check.status.value == "active" else "red"
        print(f"  Status: {self._color(check.status.value.upper(), status_color)}")
        print(f"  Processes Healthy: {'✓' if check.processes_healthy else '✗'}")
        print(f"  Resource Headroom: {'✓' if check.resource_headroom_ok else '✗'}")
        print(f"  Network Latency: {'✓' if check.network_latency_ok else '✗'}")

        if check.issues:
            print(f"\n  Issues:")
            for issue in check.issues[:3]:
                print(f"    ⚠️  {issue}")

        if status.get('active_maintenance_windows'):
            print(f"\n  {self._color('In Maintenance Window', 'yellow')}")

    def run_live_view(self, refresh_seconds: int = 5):
        """Run live dashboard view."""
        print("Starting live dashboard... Press Ctrl+C to exit\n")

        try:
            while True:
                # Collect and analyze
                metrics = self.collector.collect_all()
                health = self.analyzer.analyze(metrics)

                # Clear and redraw
                self.clear_screen()
                self.show_header()
                self.show_health_summary(health)
                self.show_component_health(health)
                self.show_alerts(health)
                self.show_trading_protection_status(metrics, health)

                print(f"\n{self._color(f'[Refreshing in {refresh_seconds}s... Press Ctrl+C to exit]', 'blue')}")

                time.sleep(refresh_seconds)

        except KeyboardInterrupt:
            print(f"\n\n{self._color('Dashboard stopped', 'cyan')}")

    def run_full_report(self):
        """Generate a full health report."""
        # Collect and analyze
        metrics = self.collector.collect_all()
        health = self.analyzer.analyze(metrics)

        # Show all sections
        self.show_header()
        self.show_health_summary(health)
        self.show_component_health(health)
        self.show_metrics_detail(health)
        self.show_alerts(health)
        self.show_issues_and_recommendations(health)
        self.show_pending_decisions()
        self.show_trading_protection_status(metrics, health)
        self.show_kernel_summary()

        print(f"\n{self._color('='*70, 'blue')}")
        print(f"Report generated at {_utc_now().isoformat()}")

    def approve_decision(self, decision_id: str) -> bool:
        """Approve a pending decision."""
        success = self.decision_engine.approve_decision(decision_id)
        if success:
            print(f"{self._color('✓ Decision approved and executed', 'green')}")
        else:
            print(f"{self._color('✗ Decision not found', 'red')}")
        return success

    def reject_decision(self, decision_id: str, reason: str = "") -> bool:
        """Reject a pending decision."""
        success = self.decision_engine.reject_decision(decision_id, reason)
        if success:
            print(f"{self._color('✓ Decision rejected', 'yellow')}")
        else:
            print(f"{self._color('✗ Decision not found', 'red')}")
        return success

    def show_upgrade_recommendations(self, metrics, health):
        """Show hardware upgrade recommendations."""
        print(f"\n{self._color('UPGRADE RECOMMENDATIONS', 'bold')}")
        print("-" * 70)

        for component in [ComponentType.MEMORY, ComponentType.DISK, ComponentType.CPU]:
            rec = self.decision_engine.generate_upgrade_recommendation(metrics, health, component)
            if rec:
                print(f"\n  {self._color(component.value.upper(), 'cyan')}")
                print(f"    Current:     {rec.current_spec}")
                print(f"    Recommended: {rec.recommended_spec}")
                print(f"    Reason:      {rec.reason}")
                print(f"    Urgency:     {rec.urgency.value}")
                print(f"    Confidence:  {rec.confidence.value}")
                if rec.expected_improvement:
                    print(f"    Expected:    {rec.expected_improvement}")

        print()


def main():
    """Main entry point for dashboard CLI."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Hardware Health Dashboard"
    )

    parser.add_argument(
        "--live",
        action="store_true",
        help="Run live dashboard view"
    )
    parser.add_argument(
        "--refresh",
        type=int,
        default=5,
        help="Refresh interval for live view (seconds)"
    )
    parser.add_argument(
        "--report",
        action="store_true",
        help="Generate full health report"
    )
    parser.add_argument(
        "--approve",
        metavar="DECISION_ID",
        help="Approve a pending decision"
    )
    parser.add_argument(
        "--reject",
        metavar="DECISION_ID",
        help="Reject a pending decision"
    )
    parser.add_argument(
        "--upgrades",
        action="store_true",
        help="Show upgrade recommendations"
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output as JSON"
    )

    args = parser.parse_args()
    dashboard = HardwareDashboard()

    if args.live:
        dashboard.run_live_view(args.refresh)
    elif args.approve:
        dashboard.approve_decision(args.approve)
    elif args.reject:
        dashboard.reject_decision(args.reject)
    elif args.upgrades:
        metrics = dashboard.collector.collect_all()
        health = dashboard.analyzer.analyze(metrics)
        dashboard.show_upgrade_recommendations(metrics, health)
    elif args.json:
        metrics = dashboard.collector.collect_all()
        health = dashboard.analyzer.analyze(metrics)
        from dataclasses import asdict
        result = {
            "timestamp": _utc_now().isoformat(),
            "overall_status": health.overall_status.value,
            "overall_score": health.overall_score,
            "components": {
                "cpu": asdict(health.cpu_health),
                "memory": asdict(health.memory_health),
                "disk": asdict(health.disk_health),
                "network": asdict(health.network_health),
                "thermal": asdict(health.thermal_health),
            },
            "alerts": [asdict(a) for a in health.active_alerts]
        }
        # Convert enums to strings
        def convert_enums(obj):
            if isinstance(obj, dict):
                return {k: convert_enums(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [convert_enums(i) for i in obj]
            elif hasattr(obj, 'value'):
                return obj.value
            return obj

        print(json.dumps(convert_enums(result), indent=2, default=str))
    else:
        dashboard.run_full_report()


if __name__ == "__main__":
    main()
