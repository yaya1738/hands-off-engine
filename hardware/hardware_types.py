"""
Hardware Monitoring Types - Autonomous Hardware Management Infrastructure

This module defines all types for the autonomous hardware monitoring system.
Designed to protect live trading systems and ensure pristine hardware operation.

Architecture:
- HardwareMetrics: Raw hardware sensor data
- HardwareHealth: Aggregated health assessment
- HardwareThreshold: Configurable alert thresholds
- HardwareUpgradeRecommendation: AI-driven upgrade suggestions
- HardwareDecision: Self-decision output with audit trail

Standard: Yair Siegel Master Level Operations
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Any
from uuid import uuid4


class HealthStatus(Enum):
    """Hardware health status levels - pristine to critical."""
    PRISTINE = "pristine"      # Operating at peak performance
    OPTIMAL = "optimal"        # Excellent, minor optimizations possible
    HEALTHY = "healthy"        # Good, within normal parameters
    DEGRADED = "degraded"      # Below optimal, attention needed
    WARNING = "warning"        # Approaching critical thresholds
    CRITICAL = "critical"      # Immediate action required
    FAILED = "failed"          # Component failure detected


class ComponentType(Enum):
    """Hardware component types for monitoring."""
    CPU = "cpu"
    MEMORY = "memory"
    DISK = "disk"
    NETWORK = "network"
    GPU = "gpu"
    THERMAL = "thermal"
    POWER = "power"
    SYSTEM = "system"


class UpgradeUrgency(Enum):
    """Urgency levels for hardware upgrades."""
    IMMEDIATE = "immediate"    # Within hours - trading at risk
    URGENT = "urgent"          # Within 24h - degraded performance
    PLANNED = "planned"        # Within week - optimization opportunity
    SCHEDULED = "scheduled"    # Next maintenance window
    OPTIONAL = "optional"      # Nice to have, no urgency


class DecisionConfidence(Enum):
    """Confidence levels for autonomous decisions."""
    CERTAIN = "certain"        # 95%+ confidence, auto-execute
    HIGH = "high"              # 80-95%, auto with notification
    MEDIUM = "medium"          # 60-80%, requires approval
    LOW = "low"                # 40-60%, human decision needed
    UNCERTAIN = "uncertain"    # <40%, gather more data


@dataclass
class CPUMetrics:
    """CPU performance metrics."""
    usage_percent: float                    # Current CPU utilization
    load_average_1m: float                  # 1-minute load average
    load_average_5m: float                  # 5-minute load average
    load_average_15m: float                 # 15-minute load average
    core_count: int                         # Number of CPU cores
    frequency_mhz: float                    # Current frequency
    frequency_max_mhz: float                # Maximum frequency
    context_switches_per_sec: float         # Context switch rate
    interrupts_per_sec: float               # Interrupt rate
    iowait_percent: float                   # I/O wait percentage
    steal_percent: float                    # CPU steal (VM overhead)
    per_core_usage: List[float] = field(default_factory=list)


@dataclass
class MemoryMetrics:
    """Memory performance metrics."""
    total_gb: float                         # Total RAM
    used_gb: float                          # Used RAM
    available_gb: float                     # Available RAM
    cached_gb: float                        # Cached memory
    buffers_gb: float                       # Buffer memory
    swap_total_gb: float                    # Total swap
    swap_used_gb: float                     # Used swap
    swap_percent: float                     # Swap utilization
    memory_pressure: float                  # Memory pressure score
    page_faults_per_sec: float              # Page fault rate
    oom_kills_recent: int                   # Recent OOM kills


@dataclass
class DiskMetrics:
    """Disk performance metrics."""
    mount_point: str                        # Mount point path
    total_gb: float                         # Total capacity
    used_gb: float                          # Used space
    available_gb: float                     # Available space
    usage_percent: float                    # Usage percentage
    read_iops: float                        # Read operations/sec
    write_iops: float                       # Write operations/sec
    read_throughput_mbps: float             # Read throughput
    write_throughput_mbps: float            # Write throughput
    avg_read_latency_ms: float              # Average read latency
    avg_write_latency_ms: float             # Average write latency
    queue_depth: float                      # I/O queue depth
    disk_health_smart: Optional[str] = None # SMART status


@dataclass
class NetworkMetrics:
    """Network performance metrics."""
    interface: str                          # Network interface
    rx_bytes_per_sec: float                 # Receive rate
    tx_bytes_per_sec: float                 # Transmit rate
    rx_packets_per_sec: float               # Receive packets
    tx_packets_per_sec: float               # Transmit packets
    rx_errors_per_sec: float                # Receive errors
    tx_errors_per_sec: float                # Transmit errors
    rx_drops_per_sec: float                 # Receive drops
    tx_drops_per_sec: float                 # Transmit drops
    latency_ms: float                       # Network latency
    connection_count: int                   # Active connections
    tcp_retransmits_per_sec: float          # TCP retransmit rate


@dataclass
class ThermalMetrics:
    """Thermal monitoring metrics."""
    cpu_temp_celsius: float                 # CPU temperature
    gpu_temp_celsius: Optional[float]       # GPU temperature
    system_temp_celsius: float              # System temperature
    fan_speed_rpm: Optional[float]          # Fan speed
    thermal_throttling: bool                # Throttling active
    thermal_zone_temps: Dict[str, float] = field(default_factory=dict)


@dataclass
class PowerMetrics:
    """Power management metrics."""
    power_consumption_watts: Optional[float]  # Current power draw
    battery_percent: Optional[float]          # Battery level
    battery_status: Optional[str]             # Charging/discharging
    on_battery_power: bool                    # Running on battery
    uptime_seconds: float                     # System uptime
    last_reboot: datetime                     # Last reboot time


@dataclass
class ProcessMetrics:
    """Process-level metrics for trading systems."""
    process_name: str                       # Process identifier
    pid: int                                # Process ID
    cpu_percent: float                      # CPU usage
    memory_percent: float                   # Memory usage
    memory_rss_mb: float                    # Resident set size
    memory_vms_mb: float                    # Virtual memory size
    open_files: int                         # Open file handles
    open_connections: int                   # Network connections
    threads: int                            # Thread count
    status: str                             # Process status
    uptime_seconds: float                   # Process uptime


@dataclass
class HardwareMetrics:
    """Complete hardware metrics snapshot."""
    timestamp: datetime
    node_id: str                            # Unique node identifier
    hostname: str                           # System hostname

    # Core metrics
    cpu: CPUMetrics
    memory: MemoryMetrics
    disks: List[DiskMetrics]
    networks: List[NetworkMetrics]
    thermal: ThermalMetrics
    power: PowerMetrics

    # Trading system processes
    trading_processes: List[ProcessMetrics] = field(default_factory=list)

    # Collection metadata
    collection_duration_ms: float = 0.0
    collector_version: str = "1.0.0"


@dataclass
class HardwareThreshold:
    """Configurable threshold for hardware alerts."""
    component: ComponentType
    metric_name: str
    warning_value: float
    critical_value: float
    pristine_max: float                     # Maximum for pristine status
    unit: str                               # Unit of measurement
    comparison: str = "greater"             # "greater" or "less"
    enabled: bool = True
    description: str = ""


@dataclass
class HardwareAlert:
    """Hardware alert generated from threshold breach."""
    alert_id: str
    timestamp: datetime
    component: ComponentType
    metric_name: str
    current_value: float
    threshold_value: float
    severity: HealthStatus
    message: str
    node_id: str
    acknowledged: bool = False
    resolved: bool = False
    resolved_at: Optional[datetime] = None


@dataclass
class ComponentHealth:
    """Health assessment for a single component."""
    component: ComponentType
    status: HealthStatus
    score: float                            # 0-100 health score
    metrics_summary: Dict[str, Any]
    issues: List[str]
    recommendations: List[str]
    trend: str                              # "improving", "stable", "degrading"
    last_updated: datetime


@dataclass
class HardwareHealth:
    """Complete hardware health assessment."""
    timestamp: datetime
    node_id: str
    overall_status: HealthStatus
    overall_score: float                    # 0-100 composite score

    # Per-component health
    cpu_health: ComponentHealth
    memory_health: ComponentHealth
    disk_health: ComponentHealth
    network_health: ComponentHealth
    thermal_health: ComponentHealth

    # Trading system protection
    trading_systems_healthy: bool
    trading_impact_risk: str                # "none", "low", "medium", "high", "critical"

    # Aggregate analysis
    active_alerts: List[HardwareAlert]
    degradation_trend: str                  # Overall trend
    time_to_critical_estimate: Optional[str]  # Predicted time to critical


@dataclass
class HardwareUpgradeRecommendation:
    """AI-driven hardware upgrade recommendation."""
    recommendation_id: str
    timestamp: datetime
    node_id: str

    # What to upgrade
    component: ComponentType
    current_spec: str                       # Current hardware spec
    recommended_spec: str                   # Recommended upgrade

    # Why to upgrade
    reason: str                             # Primary reason
    supporting_data: Dict[str, Any]         # Evidence from metrics
    expected_improvement: str               # Expected benefit
    trading_impact: str                     # Impact on trading systems

    # When to upgrade
    urgency: UpgradeUrgency
    recommended_window: str                 # Recommended time window
    estimated_downtime: str                 # Expected downtime

    # Cost-benefit
    estimated_cost: Optional[float]         # Estimated cost
    roi_projection: Optional[str]           # ROI projection

    # Confidence
    confidence: DecisionConfidence
    ai_analysis: str                        # AI reasoning

    # Status
    status: str = "proposed"                # proposed, approved, rejected, implemented
    approved_by: Optional[str] = None
    approved_at: Optional[datetime] = None


@dataclass
class HardwareDecision:
    """Autonomous hardware decision with full audit trail."""
    decision_id: str
    timestamp: datetime
    node_id: str

    # Decision details
    decision_type: str                      # "alert", "threshold_adjust", "restart", "upgrade"
    action: str                             # Specific action taken
    reason: str                             # Why this decision

    # Context
    triggered_by: str                       # What triggered this decision
    health_snapshot: Dict[str, Any]         # Health at decision time

    # AI analysis
    ai_provider: str                        # Which AI made decision
    ai_reasoning: str                       # Full reasoning chain
    confidence: DecisionConfidence

    # Execution
    auto_executed: bool                     # Was it auto-executed?
    requires_approval: bool                 # Does it need human approval?
    approval_status: str = "pending"        # pending, approved, rejected

    # Outcome
    executed: bool = False
    executed_at: Optional[datetime] = None
    outcome: Optional[str] = None
    success: Optional[bool] = None

    # Audit
    audit_trail: List[Dict[str, Any]] = field(default_factory=list)

    def add_audit_entry(self, action: str, details: Dict[str, Any]):
        """Add entry to audit trail."""
        self.audit_trail.append({
            "timestamp": datetime.utcnow().isoformat(),
            "action": action,
            "details": details
        })


@dataclass
class TradingSystemProtection:
    """Protection configuration for live trading systems."""
    system_name: str                        # Trading system identifier
    process_patterns: List[str]             # Process name patterns to monitor
    critical_ports: List[int]               # Ports that must be available
    min_cpu_headroom: float                 # Minimum CPU available %
    min_memory_headroom_gb: float           # Minimum memory available
    max_latency_ms: float                   # Maximum acceptable latency

    # Protection actions
    auto_restart_on_failure: bool = True
    alert_on_degradation: bool = True
    pause_upgrades_during_trading: bool = True

    # Trading hours (UTC)
    active_trading_hours: List[Dict[str, int]] = field(default_factory=list)

    # Priority
    priority: int = 1                       # 1 = highest priority


@dataclass
class HardwareKernelState:
    """State for hardware memory kernel - persistent learning."""
    kernel_id: str
    node_id: str

    # Historical patterns
    baseline_metrics: Dict[str, Any]        # Normal operating baseline
    anomaly_patterns: List[Dict[str, Any]]  # Known anomaly signatures
    failure_predictions: List[Dict[str, Any]]  # Predicted failure patterns

    # Learned thresholds
    adaptive_thresholds: Dict[str, HardwareThreshold]
    threshold_adjustments: List[Dict[str, Any]]  # History of adjustments

    # Decision history
    successful_decisions: List[str]         # Decisions that worked
    failed_decisions: List[str]             # Decisions that didn't work

    # Upgrade history
    upgrade_history: List[Dict[str, Any]]
    upgrade_outcomes: Dict[str, str]        # upgrade_id -> outcome

    # Maintenance windows
    optimal_maintenance_windows: List[Dict[str, Any]]

    # Last updated
    last_updated: datetime
    version: str = "1.0.0"


# Factory functions for creating instances with defaults
def create_hardware_decision(
    node_id: str,
    decision_type: str,
    action: str,
    reason: str,
    triggered_by: str,
    ai_provider: str = "autonomous",
    ai_reasoning: str = "",
    confidence: DecisionConfidence = DecisionConfidence.MEDIUM,
    auto_executed: bool = False,
    requires_approval: bool = True
) -> HardwareDecision:
    """Create a new hardware decision with proper defaults."""
    return HardwareDecision(
        decision_id=f"hw_dec_{uuid4().hex[:12]}",
        timestamp=datetime.utcnow(),
        node_id=node_id,
        decision_type=decision_type,
        action=action,
        reason=reason,
        triggered_by=triggered_by,
        health_snapshot={},
        ai_provider=ai_provider,
        ai_reasoning=ai_reasoning,
        confidence=confidence,
        auto_executed=auto_executed,
        requires_approval=requires_approval
    )


def create_upgrade_recommendation(
    node_id: str,
    component: ComponentType,
    current_spec: str,
    recommended_spec: str,
    reason: str,
    urgency: UpgradeUrgency,
    confidence: DecisionConfidence
) -> HardwareUpgradeRecommendation:
    """Create a new upgrade recommendation."""
    return HardwareUpgradeRecommendation(
        recommendation_id=f"hw_upg_{uuid4().hex[:12]}",
        timestamp=datetime.utcnow(),
        node_id=node_id,
        component=component,
        current_spec=current_spec,
        recommended_spec=recommended_spec,
        reason=reason,
        supporting_data={},
        expected_improvement="",
        trading_impact="",
        urgency=urgency,
        recommended_window="",
        estimated_downtime="",
        confidence=confidence,
        ai_analysis=""
    )


def create_alert(
    node_id: str,
    component: ComponentType,
    metric_name: str,
    current_value: float,
    threshold_value: float,
    severity: HealthStatus,
    message: str
) -> HardwareAlert:
    """Create a new hardware alert."""
    return HardwareAlert(
        alert_id=f"hw_alert_{uuid4().hex[:12]}",
        timestamp=datetime.utcnow(),
        component=component,
        metric_name=metric_name,
        current_value=current_value,
        threshold_value=threshold_value,
        severity=severity,
        message=message,
        node_id=node_id
    )


# Default thresholds for pristine operation
DEFAULT_THRESHOLDS: List[HardwareThreshold] = [
    # CPU thresholds
    HardwareThreshold(ComponentType.CPU, "usage_percent", 70.0, 90.0, 50.0, "%", "greater", True, "CPU utilization"),
    HardwareThreshold(ComponentType.CPU, "load_average_1m", 2.0, 4.0, 1.0, "load", "greater", True, "1-minute load average"),
    HardwareThreshold(ComponentType.CPU, "iowait_percent", 10.0, 25.0, 5.0, "%", "greater", True, "I/O wait percentage"),

    # Memory thresholds
    HardwareThreshold(ComponentType.MEMORY, "usage_percent", 75.0, 90.0, 60.0, "%", "greater", True, "Memory utilization"),
    HardwareThreshold(ComponentType.MEMORY, "swap_percent", 20.0, 50.0, 5.0, "%", "greater", True, "Swap utilization"),
    HardwareThreshold(ComponentType.MEMORY, "available_gb", 2.0, 1.0, 4.0, "GB", "less", True, "Available memory"),

    # Disk thresholds
    HardwareThreshold(ComponentType.DISK, "usage_percent", 80.0, 95.0, 60.0, "%", "greater", True, "Disk utilization"),
    HardwareThreshold(ComponentType.DISK, "avg_read_latency_ms", 20.0, 50.0, 10.0, "ms", "greater", True, "Disk read latency"),
    HardwareThreshold(ComponentType.DISK, "avg_write_latency_ms", 30.0, 75.0, 15.0, "ms", "greater", True, "Disk write latency"),

    # Network thresholds
    HardwareThreshold(ComponentType.NETWORK, "latency_ms", 50.0, 100.0, 20.0, "ms", "greater", True, "Network latency"),
    HardwareThreshold(ComponentType.NETWORK, "rx_errors_per_sec", 10.0, 50.0, 1.0, "/sec", "greater", True, "Network receive errors"),
    HardwareThreshold(ComponentType.NETWORK, "tcp_retransmits_per_sec", 5.0, 20.0, 1.0, "/sec", "greater", True, "TCP retransmits"),

    # Thermal thresholds
    HardwareThreshold(ComponentType.THERMAL, "cpu_temp_celsius", 70.0, 85.0, 55.0, "°C", "greater", True, "CPU temperature"),
    HardwareThreshold(ComponentType.THERMAL, "system_temp_celsius", 60.0, 75.0, 45.0, "°C", "greater", True, "System temperature"),
]
