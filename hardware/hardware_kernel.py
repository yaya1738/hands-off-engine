"""
Hardware Memory Kernel - Persistent Learning for Hardware Management

Stores and learns from hardware patterns, baselines, anomalies, and decisions.
Enables the system to improve hardware management over time.

Features:
- Baseline learning from normal operation
- Anomaly pattern detection and storage
- Decision outcome tracking
- Adaptive threshold adjustment
- Upgrade history and ROI tracking

Standard: Yair Siegel Master Level Operations
"""

import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field, asdict
import statistics

from hardware.hardware_types import (
    HealthStatus,
    ComponentType,
    HardwareMetrics,
    HardwareHealth,
    HardwareThreshold,
    HardwareDecision,
    HardwareUpgradeRecommendation,
    HardwareKernelState,
    DEFAULT_THRESHOLDS,
)


@dataclass
class BaselineMetrics:
    """Learned baseline metrics for normal operation."""
    cpu_usage_mean: float = 0.0
    cpu_usage_std: float = 0.0
    cpu_load_mean: float = 0.0
    cpu_load_std: float = 0.0
    memory_usage_mean: float = 0.0
    memory_usage_std: float = 0.0
    disk_usage_mean: Dict[str, float] = field(default_factory=dict)
    network_latency_mean: float = 0.0
    network_latency_std: float = 0.0
    cpu_temp_mean: float = 0.0
    cpu_temp_std: float = 0.0
    samples_collected: int = 0
    last_updated: str = ""


@dataclass
class AnomalyPattern:
    """Recorded anomaly pattern for future detection."""
    pattern_id: str
    component: str
    description: str
    signature: Dict[str, Any]
    first_seen: str
    occurrences: int = 1
    led_to_failure: bool = False
    remediation: Optional[str] = None


@dataclass
class DecisionOutcome:
    """Tracked outcome of a hardware decision."""
    decision_id: str
    decision_type: str
    action: str
    timestamp: str
    success: bool
    impact: str
    lessons_learned: List[str] = field(default_factory=list)


@dataclass
class UpgradeRecord:
    """Record of hardware upgrade."""
    upgrade_id: str
    component: str
    from_spec: str
    to_spec: str
    timestamp: str
    cost: Optional[float] = None
    roi_realized: Optional[float] = None
    performance_improvement: Optional[str] = None
    outcome: str = "pending"


class HardwareKernel:
    """
    Persistent memory and learning system for hardware management.

    Stores patterns, learns baselines, and tracks decision outcomes
    to improve autonomous hardware management over time.
    """

    def __init__(
        self,
        kernel_path: Optional[Path] = None,
        node_id: str = "default"
    ):
        """
        Initialize the hardware kernel.

        Args:
            kernel_path: Path to kernel storage directory
            node_id: Unique identifier for this node
        """
        self.kernel_path = kernel_path or Path("ai/memory/kernels/hardware")
        self.kernel_path.mkdir(parents=True, exist_ok=True)
        self.node_id = node_id

        # State files
        self.baseline_file = self.kernel_path / f"baseline_{node_id}.json"
        self.anomalies_file = self.kernel_path / f"anomalies_{node_id}.json"
        self.decisions_file = self.kernel_path / f"decisions_{node_id}.json"
        self.thresholds_file = self.kernel_path / f"thresholds_{node_id}.json"
        self.upgrades_file = self.kernel_path / f"upgrades_{node_id}.json"
        self.state_file = self.kernel_path / f"state_{node_id}.json"

        # In-memory state
        self.baseline = self._load_baseline()
        self.anomalies = self._load_anomalies()
        self.decisions = self._load_decisions()
        self.thresholds = self._load_thresholds()
        self.upgrades = self._load_upgrades()

        # Metric buffers for baseline learning
        self._cpu_usage_buffer: List[float] = []
        self._cpu_load_buffer: List[float] = []
        self._memory_usage_buffer: List[float] = []
        self._network_latency_buffer: List[float] = []
        self._cpu_temp_buffer: List[float] = []
        self._buffer_max_size = 1000

    def _load_json(self, file_path: Path, default: Any = None) -> Any:
        """Load JSON file with default fallback."""
        if file_path.exists():
            try:
                return json.loads(file_path.read_text())
            except:
                pass
        return default if default is not None else {}

    def _save_json(self, file_path: Path, data: Any):
        """Save data to JSON file."""
        file_path.write_text(json.dumps(data, indent=2, default=str))

    def _load_baseline(self) -> BaselineMetrics:
        """Load baseline metrics from storage."""
        data = self._load_json(self.baseline_file, {})
        return BaselineMetrics(**data) if data else BaselineMetrics()

    def _load_anomalies(self) -> List[AnomalyPattern]:
        """Load anomaly patterns from storage."""
        data = self._load_json(self.anomalies_file, [])
        return [AnomalyPattern(**a) for a in data]

    def _load_decisions(self) -> List[DecisionOutcome]:
        """Load decision outcomes from storage."""
        data = self._load_json(self.decisions_file, [])
        return [DecisionOutcome(**d) for d in data]

    def _load_thresholds(self) -> Dict[str, HardwareThreshold]:
        """Load adaptive thresholds from storage."""
        data = self._load_json(self.thresholds_file, {})
        thresholds = {}
        for key, t in data.items():
            thresholds[key] = HardwareThreshold(
                component=ComponentType(t["component"]),
                metric_name=t["metric_name"],
                warning_value=t["warning_value"],
                critical_value=t["critical_value"],
                pristine_max=t["pristine_max"],
                unit=t["unit"],
                comparison=t.get("comparison", "greater"),
                enabled=t.get("enabled", True),
                description=t.get("description", "")
            )
        return thresholds

    def _load_upgrades(self) -> List[UpgradeRecord]:
        """Load upgrade records from storage."""
        data = self._load_json(self.upgrades_file, [])
        return [UpgradeRecord(**u) for u in data]

    def _save_all(self):
        """Save all state to storage."""
        self._save_json(self.baseline_file, asdict(self.baseline))
        self._save_json(self.anomalies_file, [asdict(a) for a in self.anomalies])
        self._save_json(self.decisions_file, [asdict(d) for d in self.decisions])
        self._save_json(self.thresholds_file, {
            f"{t.component.value}_{t.metric_name}": {
                "component": t.component.value,
                "metric_name": t.metric_name,
                "warning_value": t.warning_value,
                "critical_value": t.critical_value,
                "pristine_max": t.pristine_max,
                "unit": t.unit,
                "comparison": t.comparison,
                "enabled": t.enabled,
                "description": t.description
            }
            for t in self.thresholds.values()
        })
        self._save_json(self.upgrades_file, [asdict(u) for u in self.upgrades])

    def learn_from_metrics(self, metrics: HardwareMetrics, health: HardwareHealth):
        """
        Learn from collected metrics and health assessment.

        Updates baselines, detects anomalies, and refines understanding.

        Args:
            metrics: Current hardware metrics
            health: Current health assessment
        """
        # Add to buffers for baseline learning
        self._cpu_usage_buffer.append(metrics.cpu.usage_percent)
        self._cpu_load_buffer.append(metrics.cpu.load_average_1m)
        usage_pct = (metrics.memory.used_gb / metrics.memory.total_gb * 100) if metrics.memory.total_gb > 0 else 0
        self._memory_usage_buffer.append(usage_pct)
        self._cpu_temp_buffer.append(metrics.thermal.cpu_temp_celsius)

        for net in metrics.networks:
            if net.latency_ms > 0:
                self._network_latency_buffer.append(net.latency_ms)

        # Trim buffers
        for buf in [self._cpu_usage_buffer, self._cpu_load_buffer,
                    self._memory_usage_buffer, self._network_latency_buffer,
                    self._cpu_temp_buffer]:
            while len(buf) > self._buffer_max_size:
                buf.pop(0)

        # Update baseline if we have enough samples
        if len(self._cpu_usage_buffer) >= 100:
            self._update_baseline()

        # Check for anomalies
        self._detect_anomalies(metrics, health)

        # Periodic save
        self._save_all()

    def _update_baseline(self):
        """Update baseline metrics from buffers."""
        if len(self._cpu_usage_buffer) >= 50:
            self.baseline.cpu_usage_mean = statistics.mean(self._cpu_usage_buffer)
            self.baseline.cpu_usage_std = statistics.stdev(self._cpu_usage_buffer) if len(self._cpu_usage_buffer) > 1 else 0

        if len(self._cpu_load_buffer) >= 50:
            self.baseline.cpu_load_mean = statistics.mean(self._cpu_load_buffer)
            self.baseline.cpu_load_std = statistics.stdev(self._cpu_load_buffer) if len(self._cpu_load_buffer) > 1 else 0

        if len(self._memory_usage_buffer) >= 50:
            self.baseline.memory_usage_mean = statistics.mean(self._memory_usage_buffer)
            self.baseline.memory_usage_std = statistics.stdev(self._memory_usage_buffer) if len(self._memory_usage_buffer) > 1 else 0

        if len(self._network_latency_buffer) >= 50:
            self.baseline.network_latency_mean = statistics.mean(self._network_latency_buffer)
            self.baseline.network_latency_std = statistics.stdev(self._network_latency_buffer) if len(self._network_latency_buffer) > 1 else 0

        if len(self._cpu_temp_buffer) >= 50:
            self.baseline.cpu_temp_mean = statistics.mean(self._cpu_temp_buffer)
            self.baseline.cpu_temp_std = statistics.stdev(self._cpu_temp_buffer) if len(self._cpu_temp_buffer) > 1 else 0

        self.baseline.samples_collected = len(self._cpu_usage_buffer)
        self.baseline.last_updated = datetime.utcnow().isoformat()

    def _detect_anomalies(self, metrics: HardwareMetrics, health: HardwareHealth):
        """Detect and record anomaly patterns."""
        anomalies_detected = []

        # CPU anomaly detection
        if self.baseline.cpu_usage_std > 0:
            z_score = (metrics.cpu.usage_percent - self.baseline.cpu_usage_mean) / self.baseline.cpu_usage_std
            if abs(z_score) > 3:
                anomalies_detected.append({
                    "component": "cpu",
                    "metric": "usage_percent",
                    "value": metrics.cpu.usage_percent,
                    "z_score": z_score,
                    "description": f"CPU usage anomaly: {metrics.cpu.usage_percent:.1f}% (z-score: {z_score:.2f})"
                })

        # Memory anomaly detection
        if self.baseline.memory_usage_std > 0:
            usage_pct = (metrics.memory.used_gb / metrics.memory.total_gb * 100) if metrics.memory.total_gb > 0 else 0
            z_score = (usage_pct - self.baseline.memory_usage_mean) / self.baseline.memory_usage_std
            if abs(z_score) > 3:
                anomalies_detected.append({
                    "component": "memory",
                    "metric": "usage_percent",
                    "value": usage_pct,
                    "z_score": z_score,
                    "description": f"Memory usage anomaly: {usage_pct:.1f}% (z-score: {z_score:.2f})"
                })

        # Temperature anomaly detection
        if self.baseline.cpu_temp_std > 0:
            z_score = (metrics.thermal.cpu_temp_celsius - self.baseline.cpu_temp_mean) / self.baseline.cpu_temp_std
            if abs(z_score) > 3:
                anomalies_detected.append({
                    "component": "thermal",
                    "metric": "cpu_temp",
                    "value": metrics.thermal.cpu_temp_celsius,
                    "z_score": z_score,
                    "description": f"Temperature anomaly: {metrics.thermal.cpu_temp_celsius}°C (z-score: {z_score:.2f})"
                })

        # Record anomalies
        for anomaly in anomalies_detected:
            self._record_anomaly(anomaly)

    def _record_anomaly(self, anomaly: Dict[str, Any]):
        """Record an anomaly pattern."""
        # Check if similar pattern exists
        for existing in self.anomalies:
            if (existing.component == anomaly["component"] and
                existing.signature.get("metric") == anomaly["metric"]):
                existing.occurrences += 1
                return

        # Create new pattern
        pattern = AnomalyPattern(
            pattern_id=f"anomaly_{len(self.anomalies) + 1}_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
            component=anomaly["component"],
            description=anomaly["description"],
            signature={
                "metric": anomaly["metric"],
                "value": anomaly["value"],
                "z_score": anomaly["z_score"]
            },
            first_seen=datetime.utcnow().isoformat()
        )
        self.anomalies.append(pattern)

        # Keep only recent anomalies
        if len(self.anomalies) > 100:
            self.anomalies = self.anomalies[-100:]

    def record_decision(self, decision: HardwareDecision, success: bool, impact: str = ""):
        """
        Record the outcome of a hardware decision.

        Args:
            decision: The decision that was made
            success: Whether the decision was successful
            impact: Description of the impact
        """
        outcome = DecisionOutcome(
            decision_id=decision.decision_id,
            decision_type=decision.decision_type,
            action=decision.action,
            timestamp=datetime.utcnow().isoformat(),
            success=success,
            impact=impact
        )
        self.decisions.append(outcome)

        # Keep only recent decisions
        if len(self.decisions) > 500:
            self.decisions = self.decisions[-500:]

        self._save_all()

    def record_upgrade(
        self,
        component: ComponentType,
        from_spec: str,
        to_spec: str,
        cost: Optional[float] = None
    ) -> str:
        """
        Record a hardware upgrade.

        Args:
            component: Component being upgraded
            from_spec: Previous specification
            to_spec: New specification
            cost: Cost of upgrade

        Returns:
            Upgrade record ID
        """
        upgrade = UpgradeRecord(
            upgrade_id=f"upgrade_{len(self.upgrades) + 1}_{datetime.utcnow().strftime('%Y%m%d')}",
            component=component.value,
            from_spec=from_spec,
            to_spec=to_spec,
            timestamp=datetime.utcnow().isoformat(),
            cost=cost
        )
        self.upgrades.append(upgrade)
        self._save_all()
        return upgrade.upgrade_id

    def update_upgrade_outcome(
        self,
        upgrade_id: str,
        outcome: str,
        performance_improvement: Optional[str] = None,
        roi_realized: Optional[float] = None
    ):
        """Update the outcome of an upgrade."""
        for upgrade in self.upgrades:
            if upgrade.upgrade_id == upgrade_id:
                upgrade.outcome = outcome
                upgrade.performance_improvement = performance_improvement
                upgrade.roi_realized = roi_realized
                self._save_all()
                return

    def get_adaptive_thresholds(self) -> Dict[str, HardwareThreshold]:
        """
        Get adaptive thresholds based on learned baselines.

        Returns thresholds adjusted for this specific system's patterns.
        """
        adaptive = {}

        # Start with defaults
        for threshold in DEFAULT_THRESHOLDS:
            key = f"{threshold.component.value}_{threshold.metric_name}"
            adaptive[key] = threshold

        # Adjust based on learned baseline
        if self.baseline.samples_collected >= 100:
            # CPU usage - adjust based on normal operation
            cpu_key = f"{ComponentType.CPU.value}_usage_percent"
            if cpu_key in adaptive and self.baseline.cpu_usage_mean > 0:
                normal_peak = self.baseline.cpu_usage_mean + (2 * self.baseline.cpu_usage_std)
                adaptive[cpu_key] = HardwareThreshold(
                    component=ComponentType.CPU,
                    metric_name="usage_percent",
                    warning_value=min(90, max(normal_peak + 10, 70)),
                    critical_value=min(95, max(normal_peak + 20, 85)),
                    pristine_max=min(60, max(normal_peak - 10, 40)),
                    unit="%",
                    description=f"Adaptive threshold based on baseline {self.baseline.cpu_usage_mean:.1f}%"
                )

            # Memory - adjust based on normal operation
            mem_key = f"{ComponentType.MEMORY.value}_usage_percent"
            if mem_key in adaptive and self.baseline.memory_usage_mean > 0:
                normal_peak = self.baseline.memory_usage_mean + (2 * self.baseline.memory_usage_std)
                adaptive[mem_key] = HardwareThreshold(
                    component=ComponentType.MEMORY,
                    metric_name="usage_percent",
                    warning_value=min(92, max(normal_peak + 8, 75)),
                    critical_value=min(97, max(normal_peak + 15, 90)),
                    pristine_max=min(70, max(normal_peak - 5, 50)),
                    unit="%",
                    description=f"Adaptive threshold based on baseline {self.baseline.memory_usage_mean:.1f}%"
                )

            # Temperature - adjust based on normal operation
            temp_key = f"{ComponentType.THERMAL.value}_cpu_temp_celsius"
            if temp_key in adaptive and self.baseline.cpu_temp_mean > 0:
                normal_peak = self.baseline.cpu_temp_mean + (2 * self.baseline.cpu_temp_std)
                adaptive[temp_key] = HardwareThreshold(
                    component=ComponentType.THERMAL,
                    metric_name="cpu_temp_celsius",
                    warning_value=min(85, max(normal_peak + 10, 65)),
                    critical_value=min(95, max(normal_peak + 20, 80)),
                    pristine_max=min(55, max(normal_peak - 5, 45)),
                    unit="°C",
                    description=f"Adaptive threshold based on baseline {self.baseline.cpu_temp_mean:.1f}°C"
                )

        self.thresholds = adaptive
        return adaptive

    def get_decision_success_rate(self, decision_type: Optional[str] = None) -> float:
        """
        Get success rate for past decisions.

        Args:
            decision_type: Filter by decision type (optional)

        Returns:
            Success rate as percentage
        """
        filtered = self.decisions
        if decision_type:
            filtered = [d for d in self.decisions if d.decision_type == decision_type]

        if not filtered:
            return 0.0

        successful = sum(1 for d in filtered if d.success)
        return (successful / len(filtered)) * 100

    def get_upgrade_roi(self) -> Dict[str, Any]:
        """
        Calculate ROI from upgrades.

        Returns:
            Summary of upgrade costs and returns
        """
        total_cost = sum(u.cost or 0 for u in self.upgrades)
        total_roi = sum(u.roi_realized or 0 for u in self.upgrades if u.roi_realized)
        successful = sum(1 for u in self.upgrades if u.outcome == "successful")

        return {
            "total_upgrades": len(self.upgrades),
            "successful_upgrades": successful,
            "total_cost": total_cost,
            "total_roi_realized": total_roi,
            "net_benefit": total_roi - total_cost,
            "success_rate": (successful / len(self.upgrades) * 100) if self.upgrades else 0
        }

    def get_anomaly_patterns(self, component: Optional[str] = None) -> List[AnomalyPattern]:
        """
        Get recorded anomaly patterns.

        Args:
            component: Filter by component (optional)

        Returns:
            List of anomaly patterns
        """
        if component:
            return [a for a in self.anomalies if a.component == component]
        return self.anomalies

    def get_kernel_summary(self) -> Dict[str, Any]:
        """Get a summary of the kernel state."""
        return {
            "node_id": self.node_id,
            "baseline": {
                "samples": self.baseline.samples_collected,
                "cpu_usage_mean": round(self.baseline.cpu_usage_mean, 1),
                "memory_usage_mean": round(self.baseline.memory_usage_mean, 1),
                "cpu_temp_mean": round(self.baseline.cpu_temp_mean, 1),
                "last_updated": self.baseline.last_updated
            },
            "anomalies_recorded": len(self.anomalies),
            "decisions_recorded": len(self.decisions),
            "decision_success_rate": round(self.get_decision_success_rate(), 1),
            "upgrades": self.get_upgrade_roi(),
            "adaptive_thresholds_active": len(self.thresholds)
        }

    def export_state(self) -> HardwareKernelState:
        """Export complete kernel state."""
        return HardwareKernelState(
            kernel_id=f"hardware_kernel_{self.node_id}",
            node_id=self.node_id,
            baseline_metrics=asdict(self.baseline),
            anomaly_patterns=[asdict(a) for a in self.anomalies],
            failure_predictions=[],  # Future: ML predictions
            adaptive_thresholds=self.thresholds,
            threshold_adjustments=[],  # Future: track adjustments
            successful_decisions=[d.decision_id for d in self.decisions if d.success],
            failed_decisions=[d.decision_id for d in self.decisions if not d.success],
            upgrade_history=[asdict(u) for u in self.upgrades],
            upgrade_outcomes={u.upgrade_id: u.outcome for u in self.upgrades},
            optimal_maintenance_windows=[],  # Future: learned maintenance windows
            last_updated=datetime.utcnow(),
            version="1.0.0"
        )


def get_hardware_kernel(node_id: str = "default") -> HardwareKernel:
    """
    Get a hardware kernel instance for a node.

    Args:
        node_id: Node identifier

    Returns:
        HardwareKernel instance
    """
    return HardwareKernel(node_id=node_id)


if __name__ == "__main__":
    # Test the hardware kernel
    kernel = HardwareKernel(node_id="test_node")

    print("Hardware Kernel Test")
    print("=" * 50)

    # Simulate learning from metrics
    from hardware.hardware_collector import HardwareCollector
    from hardware.hardware_analyzer import HardwareAnalyzer
    import time

    collector = HardwareCollector()
    analyzer = HardwareAnalyzer()

    print("Collecting metrics for baseline learning...")
    for i in range(5):
        metrics = collector.collect_all()
        health = analyzer.analyze(metrics)
        kernel.learn_from_metrics(metrics, health)
        print(f"  Sample {i+1}: CPU={metrics.cpu.usage_percent:.1f}%, Mem={metrics.memory.used_gb:.1f}GB")
        time.sleep(1)

    print("\nKernel Summary:")
    summary = kernel.get_kernel_summary()
    for key, value in summary.items():
        print(f"  {key}: {value}")

    # Test adaptive thresholds
    print("\nAdaptive Thresholds:")
    thresholds = kernel.get_adaptive_thresholds()
    for key, t in list(thresholds.items())[:3]:
        print(f"  {key}: warning={t.warning_value}, critical={t.critical_value}")

    print("\n✓ Hardware Kernel operational")
