"""
Hardware Analyzer - Health Assessment and Anomaly Detection

Analyzes hardware metrics to determine system health, detect anomalies,
and predict potential failures before they impact trading systems.

Features:
- Component-level health scoring
- Trend analysis and degradation detection
- Anomaly detection with ML-ready patterns
- Trading system impact assessment
- Predictive failure analysis

Standard: Yair Siegel Master Level Operations
"""

import math
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field


def _utc_now() -> datetime:
    """Get current UTC time as timezone-aware datetime."""
    return datetime.now(timezone.utc)

from hardware.hardware_types import (
    HealthStatus,
    ComponentType,
    HardwareMetrics,
    HardwareHealth,
    HardwareThreshold,
    HardwareAlert,
    ComponentHealth,
    CPUMetrics,
    MemoryMetrics,
    DiskMetrics,
    NetworkMetrics,
    ThermalMetrics,
    DEFAULT_THRESHOLDS,
    create_alert,
)


@dataclass
class MetricHistory:
    """Historical metrics for trend analysis."""
    component: ComponentType
    metric_name: str
    values: List[Tuple[datetime, float]] = field(default_factory=list)
    max_history_hours: int = 24

    def add(self, timestamp: datetime, value: float):
        """Add a value to history."""
        self.values.append((timestamp, value))
        # Prune old values
        cutoff = _utc_now() - timedelta(hours=self.max_history_hours)
        self.values = [(ts, v) for ts, v in self.values if ts > cutoff]

    def get_trend(self) -> str:
        """Calculate trend over recent history."""
        if len(self.values) < 3:
            return "stable"

        recent = self.values[-10:]  # Last 10 data points
        if len(recent) < 3:
            return "stable"

        # Simple linear regression
        n = len(recent)
        x_sum = sum(i for i in range(n))
        y_sum = sum(v for _, v in recent)
        xy_sum = sum(i * v for i, (_, v) in enumerate(recent))
        x2_sum = sum(i * i for i in range(n))

        denominator = n * x2_sum - x_sum * x_sum
        if denominator == 0:
            return "stable"

        slope = (n * xy_sum - x_sum * y_sum) / denominator

        # Normalize slope relative to average value
        avg_value = y_sum / n
        if avg_value == 0:
            return "stable"

        normalized_slope = slope / avg_value

        if normalized_slope > 0.05:
            return "degrading" if self._higher_is_worse() else "improving"
        elif normalized_slope < -0.05:
            return "improving" if self._higher_is_worse() else "degrading"
        return "stable"

    def _higher_is_worse(self) -> bool:
        """Determine if higher values are worse for this metric."""
        # Most metrics: higher is worse
        worse_when_higher = [
            "usage_percent", "load_average", "latency", "temp",
            "errors", "drops", "swap", "iowait", "steal"
        ]
        return any(w in self.metric_name.lower() for w in worse_when_higher)


class HardwareAnalyzer:
    """
    Analyzes hardware metrics for health, anomalies, and predictions.

    Provides comprehensive health assessment for autonomous decision-making.
    """

    def __init__(
        self,
        thresholds: Optional[List[HardwareThreshold]] = None,
        history_hours: int = 24
    ):
        """
        Initialize the hardware analyzer.

        Args:
            thresholds: Custom thresholds (uses defaults if None)
            history_hours: Hours of history to retain
        """
        self.thresholds = {
            (t.component, t.metric_name): t
            for t in (thresholds or DEFAULT_THRESHOLDS)
        }
        self.history_hours = history_hours
        self.metric_history: Dict[str, MetricHistory] = {}
        self._baseline: Optional[HardwareMetrics] = None

    def analyze(self, metrics: HardwareMetrics) -> HardwareHealth:
        """
        Perform comprehensive health analysis.

        Args:
            metrics: Current hardware metrics

        Returns:
            Complete HardwareHealth assessment
        """
        # Update history
        self._update_history(metrics)

        # Analyze each component
        cpu_health = self._analyze_cpu(metrics.cpu, metrics.node_id)
        memory_health = self._analyze_memory(metrics.memory, metrics.node_id)
        disk_health = self._analyze_disks(metrics.disks, metrics.node_id)
        network_health = self._analyze_networks(metrics.networks, metrics.node_id)
        thermal_health = self._analyze_thermal(metrics.thermal, metrics.node_id)

        # Aggregate alerts
        all_alerts = self._check_all_thresholds(metrics)

        # Calculate overall health
        component_healths = [cpu_health, memory_health, disk_health, network_health, thermal_health]
        overall_score = sum(h.score for h in component_healths) / len(component_healths)
        overall_status = self._score_to_status(overall_score)

        # Trading system assessment
        trading_healthy = self._assess_trading_health(metrics)
        trading_risk = self._calculate_trading_risk(component_healths, all_alerts)

        # Overall trend
        trends = [h.trend for h in component_healths]
        if trends.count("degrading") > len(trends) // 2:
            overall_trend = "degrading"
        elif trends.count("improving") > len(trends) // 2:
            overall_trend = "improving"
        else:
            overall_trend = "stable"

        # Time to critical estimate
        time_to_critical = self._estimate_time_to_critical(component_healths)

        return HardwareHealth(
            timestamp=metrics.timestamp,
            node_id=metrics.node_id,
            overall_status=overall_status,
            overall_score=round(overall_score, 1),
            cpu_health=cpu_health,
            memory_health=memory_health,
            disk_health=disk_health,
            network_health=network_health,
            thermal_health=thermal_health,
            trading_systems_healthy=trading_healthy,
            trading_impact_risk=trading_risk,
            active_alerts=all_alerts,
            degradation_trend=overall_trend,
            time_to_critical_estimate=time_to_critical
        )

    def _update_history(self, metrics: HardwareMetrics):
        """Update metric history for trend analysis."""
        timestamp = metrics.timestamp

        # CPU history
        self._add_to_history(ComponentType.CPU, "usage_percent", timestamp, metrics.cpu.usage_percent)
        self._add_to_history(ComponentType.CPU, "load_average_1m", timestamp, metrics.cpu.load_average_1m)
        self._add_to_history(ComponentType.CPU, "iowait_percent", timestamp, metrics.cpu.iowait_percent)

        # Memory history
        usage_pct = (metrics.memory.used_gb / metrics.memory.total_gb * 100) if metrics.memory.total_gb > 0 else 0
        self._add_to_history(ComponentType.MEMORY, "usage_percent", timestamp, usage_pct)
        self._add_to_history(ComponentType.MEMORY, "swap_percent", timestamp, metrics.memory.swap_percent)

        # Disk history
        for disk in metrics.disks:
            key = f"disk_{disk.mount_point}"
            self._add_to_history(ComponentType.DISK, f"{key}_usage_percent", timestamp, disk.usage_percent)

        # Thermal history
        self._add_to_history(ComponentType.THERMAL, "cpu_temp_celsius", timestamp, metrics.thermal.cpu_temp_celsius)

        # Network history
        for net in metrics.networks:
            self._add_to_history(ComponentType.NETWORK, f"{net.interface}_latency_ms", timestamp, net.latency_ms)

    def _add_to_history(self, component: ComponentType, metric: str, timestamp: datetime, value: float):
        """Add a metric to history."""
        key = f"{component.value}_{metric}"
        if key not in self.metric_history:
            self.metric_history[key] = MetricHistory(component, metric, max_history_hours=self.history_hours)
        self.metric_history[key].add(timestamp, value)

    def _get_trend(self, component: ComponentType, metric: str) -> str:
        """Get trend for a specific metric."""
        key = f"{component.value}_{metric}"
        if key in self.metric_history:
            return self.metric_history[key].get_trend()
        return "stable"

    def _analyze_cpu(self, cpu: CPUMetrics, node_id: str) -> ComponentHealth:
        """Analyze CPU health."""
        issues = []
        recommendations = []
        score = 100.0

        # Usage analysis
        if cpu.usage_percent > 90:
            issues.append(f"CPU usage critical at {cpu.usage_percent:.1f}%")
            score -= 40
        elif cpu.usage_percent > 70:
            issues.append(f"CPU usage elevated at {cpu.usage_percent:.1f}%")
            score -= 20
        elif cpu.usage_percent > 50:
            score -= 5

        # Load average analysis (relative to cores)
        load_per_core = cpu.load_average_1m / cpu.core_count if cpu.core_count > 0 else 0
        if load_per_core > 2.0:
            issues.append(f"Load average critical: {cpu.load_average_1m:.2f} ({load_per_core:.2f}x cores)")
            recommendations.append("Consider scaling or optimizing workload")
            score -= 30
        elif load_per_core > 1.0:
            issues.append(f"Load average elevated: {cpu.load_average_1m:.2f}")
            score -= 15

        # I/O wait
        if cpu.iowait_percent > 25:
            issues.append(f"High I/O wait: {cpu.iowait_percent:.1f}%")
            recommendations.append("Check disk performance, consider SSD upgrade")
            score -= 25
        elif cpu.iowait_percent > 10:
            score -= 10

        # Steal (VM overhead)
        if cpu.steal_percent > 10:
            issues.append(f"CPU steal detected: {cpu.steal_percent:.1f}%")
            recommendations.append("VM host may be oversubscribed")
            score -= 20

        # Frequency throttling
        if cpu.frequency_max_mhz > 0 and cpu.frequency_mhz < cpu.frequency_max_mhz * 0.7:
            issues.append("CPU frequency throttled")
            recommendations.append("Check thermal conditions")
            score -= 15

        # Pristine bonus
        if cpu.usage_percent < 30 and load_per_core < 0.5 and cpu.iowait_percent < 5:
            score = min(100, score + 10)

        score = max(0, min(100, score))
        status = self._score_to_status(score)
        trend = self._get_trend(ComponentType.CPU, "usage_percent")

        return ComponentHealth(
            component=ComponentType.CPU,
            status=status,
            score=score,
            metrics_summary={
                "usage_percent": cpu.usage_percent,
                "load_average": cpu.load_average_1m,
                "load_per_core": round(load_per_core, 2),
                "iowait_percent": cpu.iowait_percent,
                "frequency_mhz": cpu.frequency_mhz,
                "core_count": cpu.core_count
            },
            issues=issues,
            recommendations=recommendations,
            trend=trend,
            last_updated=_utc_now()
        )

    def _analyze_memory(self, memory: MemoryMetrics, node_id: str) -> ComponentHealth:
        """Analyze memory health."""
        issues = []
        recommendations = []
        score = 100.0

        # Usage analysis
        usage_percent = (memory.used_gb / memory.total_gb * 100) if memory.total_gb > 0 else 0

        # PRIMARY CHECK: Available memory in absolute terms
        # This is the most important metric - low available memory = OOM risk
        if memory.available_gb < 0.3:
            issues.append(f"CRITICAL: Only {memory.available_gb:.2f}GB available - OOM imminent")
            recommendations.append("URGENT: System will crash without intervention")
            score -= 70
        elif memory.available_gb < 0.5:
            issues.append(f"CRITICAL: Only {memory.available_gb:.2f}GB available")
            recommendations.append("Immediate attention required - high OOM risk")
            score -= 55
        elif memory.available_gb < 1.0:
            issues.append(f"Low available memory: {memory.available_gb:.2f}GB")
            recommendations.append("System at risk - consider upgrade")
            score -= 40
        elif memory.available_gb < 2.0:
            issues.append(f"Limited available memory: {memory.available_gb:.2f}GB")
            score -= 20

        # SECONDARY: Percentage-based check (less important than absolute)
        if usage_percent > 95:
            issues.append(f"Memory usage at {usage_percent:.1f}%")
            score -= 25
        elif usage_percent > 85:
            issues.append(f"Memory usage elevated at {usage_percent:.1f}%")
            score -= 15
        elif usage_percent > 75:
            score -= 5

        # Swap usage - indicates memory pressure
        if memory.swap_percent > 50:
            issues.append(f"High swap usage: {memory.swap_percent:.1f}%")
            recommendations.append("System is memory constrained")
            score -= 30
        elif memory.swap_percent > 20:
            issues.append(f"Swap in use: {memory.swap_percent:.1f}%")
            score -= 15

        # OOM kills - critical indicator
        if memory.oom_kills_recent > 0:
            issues.append(f"Recent OOM kills detected: {memory.oom_kills_recent}")
            recommendations.append("Critical: processes being killed due to memory")
            score -= 40

        # Pristine bonus - only if truly healthy
        if usage_percent < 60 and memory.swap_percent < 5 and memory.available_gb > 4.0:
            score = min(100, score + 10)

        score = max(0, min(100, score))
        status = self._score_to_status(score)
        trend = self._get_trend(ComponentType.MEMORY, "usage_percent")

        return ComponentHealth(
            component=ComponentType.MEMORY,
            status=status,
            score=score,
            metrics_summary={
                "total_gb": memory.total_gb,
                "used_gb": memory.used_gb,
                "available_gb": memory.available_gb,
                "usage_percent": round(usage_percent, 1),
                "swap_percent": memory.swap_percent,
                "oom_kills": memory.oom_kills_recent
            },
            issues=issues,
            recommendations=recommendations,
            trend=trend,
            last_updated=_utc_now()
        )

    def _analyze_disks(self, disks: List[DiskMetrics], node_id: str) -> ComponentHealth:
        """Analyze disk health."""
        issues = []
        recommendations = []
        score = 100.0

        if not disks:
            return ComponentHealth(
                component=ComponentType.DISK,
                status=HealthStatus.HEALTHY,
                score=80.0,
                metrics_summary={"disk_count": 0},
                issues=["No disk metrics available"],
                recommendations=[],
                trend="stable",
                last_updated=_utc_now()
            )

        worst_score = 100.0

        for disk in disks:
            disk_score = 100.0

            # Usage analysis
            if disk.usage_percent > 95:
                issues.append(f"{disk.mount_point}: Critical usage {disk.usage_percent:.1f}%")
                recommendations.append(f"Urgent: Clean up {disk.mount_point} or expand storage")
                disk_score -= 50
            elif disk.usage_percent > 85:
                issues.append(f"{disk.mount_point}: High usage {disk.usage_percent:.1f}%")
                recommendations.append(f"Plan storage expansion for {disk.mount_point}")
                disk_score -= 25
            elif disk.usage_percent > 75:
                disk_score -= 10

            # Latency analysis
            if disk.avg_read_latency_ms > 50 or disk.avg_write_latency_ms > 75:
                issues.append(f"{disk.mount_point}: High latency (read: {disk.avg_read_latency_ms:.1f}ms, write: {disk.avg_write_latency_ms:.1f}ms)")
                recommendations.append("Consider SSD upgrade or check disk health")
                disk_score -= 20

            # Available space absolute check
            if disk.available_gb < 10 and disk.mount_point == "/":
                issues.append(f"Root partition low: {disk.available_gb:.1f}GB available")
                disk_score -= 30

            # SMART status
            if disk.disk_health_smart and disk.disk_health_smart.lower() != "ok":
                issues.append(f"{disk.mount_point}: SMART status: {disk.disk_health_smart}")
                recommendations.append("Disk may be failing - backup and replace")
                disk_score -= 40

            worst_score = min(worst_score, disk_score)

        score = worst_score
        score = max(0, min(100, score))
        status = self._score_to_status(score)

        # Get trend from root disk
        root_disk = next((d for d in disks if d.mount_point == "/"), disks[0] if disks else None)
        trend = "stable"
        if root_disk:
            key = f"disk_{root_disk.mount_point}_usage_percent"
            trend = self._get_trend(ComponentType.DISK, key)

        return ComponentHealth(
            component=ComponentType.DISK,
            status=status,
            score=score,
            metrics_summary={
                "disk_count": len(disks),
                "disks": [
                    {
                        "mount": d.mount_point,
                        "usage_percent": d.usage_percent,
                        "available_gb": d.available_gb
                    }
                    for d in disks
                ]
            },
            issues=issues,
            recommendations=recommendations,
            trend=trend,
            last_updated=_utc_now()
        )

    def _analyze_networks(self, networks: List[NetworkMetrics], node_id: str) -> ComponentHealth:
        """Analyze network health."""
        issues = []
        recommendations = []
        score = 100.0

        if not networks:
            return ComponentHealth(
                component=ComponentType.NETWORK,
                status=HealthStatus.HEALTHY,
                score=80.0,
                metrics_summary={"interface_count": 0},
                issues=["No network metrics available"],
                recommendations=[],
                trend="stable",
                last_updated=_utc_now()
            )

        for net in networks:
            # Latency analysis (critical for trading)
            if net.latency_ms > 100:
                issues.append(f"{net.interface}: Critical latency {net.latency_ms:.1f}ms")
                recommendations.append("High latency may impact trading - check network path")
                score -= 30
            elif net.latency_ms > 50:
                issues.append(f"{net.interface}: Elevated latency {net.latency_ms:.1f}ms")
                score -= 15

            # Error rates
            if net.rx_errors_per_sec > 50 or net.tx_errors_per_sec > 50:
                issues.append(f"{net.interface}: High error rate")
                recommendations.append("Check network hardware and cables")
                score -= 25
            elif net.rx_errors_per_sec > 10 or net.tx_errors_per_sec > 10:
                score -= 10

            # Drop rates
            if net.rx_drops_per_sec > 50 or net.tx_drops_per_sec > 50:
                issues.append(f"{net.interface}: Packet drops detected")
                score -= 20

            # TCP retransmits (reliability concern)
            if net.tcp_retransmits_per_sec > 20:
                issues.append(f"{net.interface}: High TCP retransmits")
                recommendations.append("Network congestion or quality issues")
                score -= 15

        score = max(0, min(100, score))
        status = self._score_to_status(score)

        trend = "stable"
        if networks:
            key = f"{networks[0].interface}_latency_ms"
            trend = self._get_trend(ComponentType.NETWORK, key)

        return ComponentHealth(
            component=ComponentType.NETWORK,
            status=status,
            score=score,
            metrics_summary={
                "interface_count": len(networks),
                "interfaces": [
                    {
                        "name": n.interface,
                        "latency_ms": n.latency_ms,
                        "rx_mbps": n.rx_bytes_per_sec / 1024 / 1024,
                        "tx_mbps": n.tx_bytes_per_sec / 1024 / 1024
                    }
                    for n in networks
                ]
            },
            issues=issues,
            recommendations=recommendations,
            trend=trend,
            last_updated=_utc_now()
        )

    def _analyze_thermal(self, thermal: ThermalMetrics, node_id: str) -> ComponentHealth:
        """Analyze thermal health."""
        issues = []
        recommendations = []
        score = 100.0

        # CPU temperature
        if thermal.cpu_temp_celsius > 85:
            issues.append(f"CPU temperature critical: {thermal.cpu_temp_celsius}°C")
            recommendations.append("Check cooling - may cause throttling or damage")
            score -= 40
        elif thermal.cpu_temp_celsius > 70:
            issues.append(f"CPU temperature elevated: {thermal.cpu_temp_celsius}°C")
            recommendations.append("Consider improving cooling")
            score -= 20
        elif thermal.cpu_temp_celsius > 60:
            score -= 5

        # GPU temperature
        if thermal.gpu_temp_celsius:
            if thermal.gpu_temp_celsius > 90:
                issues.append(f"GPU temperature critical: {thermal.gpu_temp_celsius}°C")
                score -= 35
            elif thermal.gpu_temp_celsius > 80:
                issues.append(f"GPU temperature elevated: {thermal.gpu_temp_celsius}°C")
                score -= 15

        # Throttling
        if thermal.thermal_throttling:
            issues.append("Thermal throttling active")
            recommendations.append("Performance degraded due to heat")
            score -= 25

        # System temperature
        if thermal.system_temp_celsius > 75:
            issues.append(f"System temperature high: {thermal.system_temp_celsius}°C")
            score -= 20
        elif thermal.system_temp_celsius > 60:
            score -= 10

        # Pristine bonus for cool operation
        if thermal.cpu_temp_celsius < 50 and not thermal.thermal_throttling:
            score = min(100, score + 10)

        score = max(0, min(100, score))
        status = self._score_to_status(score)
        trend = self._get_trend(ComponentType.THERMAL, "cpu_temp_celsius")

        return ComponentHealth(
            component=ComponentType.THERMAL,
            status=status,
            score=score,
            metrics_summary={
                "cpu_temp": thermal.cpu_temp_celsius,
                "gpu_temp": thermal.gpu_temp_celsius,
                "system_temp": thermal.system_temp_celsius,
                "throttling": thermal.thermal_throttling,
                "fan_rpm": thermal.fan_speed_rpm
            },
            issues=issues,
            recommendations=recommendations,
            trend=trend,
            last_updated=_utc_now()
        )

    def _check_all_thresholds(self, metrics: HardwareMetrics) -> List[HardwareAlert]:
        """Check all thresholds and generate alerts."""
        alerts = []

        # CPU thresholds
        cpu_checks = [
            (ComponentType.CPU, "usage_percent", metrics.cpu.usage_percent),
            (ComponentType.CPU, "load_average_1m", metrics.cpu.load_average_1m),
            (ComponentType.CPU, "iowait_percent", metrics.cpu.iowait_percent),
        ]

        # Memory thresholds
        usage_pct = (metrics.memory.used_gb / metrics.memory.total_gb * 100) if metrics.memory.total_gb > 0 else 0
        mem_checks = [
            (ComponentType.MEMORY, "usage_percent", usage_pct),
            (ComponentType.MEMORY, "swap_percent", metrics.memory.swap_percent),
            (ComponentType.MEMORY, "available_gb", metrics.memory.available_gb),
        ]

        # Disk thresholds
        disk_checks = []
        for disk in metrics.disks:
            disk_checks.append((ComponentType.DISK, "usage_percent", disk.usage_percent))

        # Network thresholds
        net_checks = []
        for net in metrics.networks:
            net_checks.append((ComponentType.NETWORK, "latency_ms", net.latency_ms))
            net_checks.append((ComponentType.NETWORK, "rx_errors_per_sec", net.rx_errors_per_sec))

        # Thermal thresholds
        thermal_checks = [
            (ComponentType.THERMAL, "cpu_temp_celsius", metrics.thermal.cpu_temp_celsius),
            (ComponentType.THERMAL, "system_temp_celsius", metrics.thermal.system_temp_celsius),
        ]

        all_checks = cpu_checks + mem_checks + disk_checks + net_checks + thermal_checks

        for component, metric_name, value in all_checks:
            threshold_key = (component, metric_name)
            if threshold_key in self.thresholds:
                threshold = self.thresholds[threshold_key]
                if not threshold.enabled:
                    continue

                breached = False
                severity = HealthStatus.HEALTHY

                if threshold.comparison == "greater":
                    if value >= threshold.critical_value:
                        breached = True
                        severity = HealthStatus.CRITICAL
                    elif value >= threshold.warning_value:
                        breached = True
                        severity = HealthStatus.WARNING
                else:  # less
                    if value <= threshold.critical_value:
                        breached = True
                        severity = HealthStatus.CRITICAL
                    elif value <= threshold.warning_value:
                        breached = True
                        severity = HealthStatus.WARNING

                if breached:
                    alert = create_alert(
                        node_id=metrics.node_id,
                        component=component,
                        metric_name=metric_name,
                        current_value=value,
                        threshold_value=threshold.critical_value if severity == HealthStatus.CRITICAL else threshold.warning_value,
                        severity=severity,
                        message=f"{component.value.upper()} {metric_name} at {value:.1f}{threshold.unit} (threshold: {threshold.warning_value}{threshold.unit})"
                    )
                    alerts.append(alert)

        return alerts

    def _score_to_status(self, score: float) -> HealthStatus:
        """Convert health score to status."""
        if score >= 95:
            return HealthStatus.PRISTINE
        elif score >= 85:
            return HealthStatus.OPTIMAL
        elif score >= 70:
            return HealthStatus.HEALTHY
        elif score >= 50:
            return HealthStatus.DEGRADED
        elif score >= 25:
            return HealthStatus.WARNING
        elif score > 0:
            return HealthStatus.CRITICAL
        else:
            return HealthStatus.FAILED

    def _assess_trading_health(self, metrics: HardwareMetrics) -> bool:
        """Assess if trading systems can operate safely."""
        # Check for critical issues that would impact trading
        critical_conditions = [
            metrics.cpu.usage_percent > 95,
            metrics.memory.available_gb < 0.5,
            metrics.thermal.thermal_throttling,
            any(d.usage_percent > 98 for d in metrics.disks),
            any(n.latency_ms > 500 for n in metrics.networks),
        ]
        return not any(critical_conditions)

    def _calculate_trading_risk(
        self,
        component_healths: List[ComponentHealth],
        alerts: List[HardwareAlert]
    ) -> str:
        """Calculate risk level for trading operations."""
        critical_count = sum(1 for a in alerts if a.severity == HealthStatus.CRITICAL)
        warning_count = sum(1 for a in alerts if a.severity == HealthStatus.WARNING)
        min_score = min(h.score for h in component_healths)

        if critical_count >= 2 or min_score < 25:
            return "critical"
        elif critical_count >= 1 or min_score < 50:
            return "high"
        elif warning_count >= 3 or min_score < 70:
            return "medium"
        elif warning_count >= 1 or min_score < 85:
            return "low"
        else:
            return "none"

    def _estimate_time_to_critical(
        self,
        component_healths: List[ComponentHealth]
    ) -> Optional[str]:
        """Estimate time until system becomes critical."""
        degrading = [h for h in component_healths if h.trend == "degrading"]

        if not degrading:
            return None

        # Find component closest to critical
        worst = min(degrading, key=lambda h: h.score)

        if worst.score < 50:
            return "hours"
        elif worst.score < 70:
            return "days"
        else:
            return "weeks"


def analyze_hardware_health(
    metrics: HardwareMetrics,
    custom_thresholds: Optional[List[HardwareThreshold]] = None
) -> HardwareHealth:
    """
    Convenience function for one-shot health analysis.

    Args:
        metrics: Hardware metrics to analyze
        custom_thresholds: Optional custom thresholds

    Returns:
        Complete health assessment
    """
    analyzer = HardwareAnalyzer(thresholds=custom_thresholds)
    return analyzer.analyze(metrics)


if __name__ == "__main__":
    # Test with collected metrics
    from hardware.hardware_collector import HardwareCollector
    import time

    print("Collecting metrics...")
    collector = HardwareCollector()
    analyzer = HardwareAnalyzer()

    # First collection
    metrics1 = collector.collect_all()
    health1 = analyzer.analyze(metrics1)

    print(f"\n=== Hardware Health Report ===")
    print(f"Node: {health1.node_id}")
    print(f"Overall: {health1.overall_status.value.upper()} (score: {health1.overall_score}/100)")
    print(f"Trading Risk: {health1.trading_impact_risk}")

    print(f"\n--- Component Health ---")
    for comp in [health1.cpu_health, health1.memory_health, health1.disk_health,
                 health1.network_health, health1.thermal_health]:
        print(f"  {comp.component.value.upper()}: {comp.status.value} ({comp.score:.0f}) [{comp.trend}]")
        for issue in comp.issues:
            print(f"    ⚠ {issue}")
        for rec in comp.recommendations:
            print(f"    → {rec}")

    if health1.active_alerts:
        print(f"\n--- Active Alerts ({len(health1.active_alerts)}) ---")
        for alert in health1.active_alerts:
            print(f"  [{alert.severity.value}] {alert.message}")

    # Second collection for trend data
    time.sleep(3)
    metrics2 = collector.collect_all()
    health2 = analyzer.analyze(metrics2)

    print(f"\n--- Trends ---")
    print(f"Overall trend: {health2.degradation_trend}")
    if health2.time_to_critical_estimate:
        print(f"Time to critical: {health2.time_to_critical_estimate}")
