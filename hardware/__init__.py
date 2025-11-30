"""
Hardware Monitoring Infrastructure

Autonomous hardware monitoring, analysis, and self-upgrading system
for protecting live trading infrastructure.

This module provides complete autonomous hardware management:
- Real-time metrics collection and health analysis
- AI-driven decision making for hardware operations
- Trading system protection during hardware events
- Persistent learning from hardware patterns
- Upgrade recommendations and maintenance scheduling

Modules:
- hardware_types: Core data models and types
- hardware_collector: Metrics collection from system
- hardware_analyzer: Health analysis and anomaly detection
- hardware_decision_engine: Autonomous decision making
- hardware_kernel: Persistent learning and memory
- trading_protection: Live trading system protection
- hardware_audit: Audit logging integration
- autonomous_hardware_monitor: Continuous monitoring daemon
- hardware_dashboard: CLI dashboard and alerting

Standard: Yair Siegel Master Level Operations

Note: All datetime operations use timezone-aware UTC (datetime.now(timezone.utc))
for Python 3.12+ compatibility.

Note on _utc_now() pattern: Each submodule contains its own private _utc_now()
helper function rather than importing from __init__.py. This is intentional to
avoid circular imports, as __init__.py imports from the submodules.
"""

from datetime import datetime, timezone


def utc_now() -> datetime:
    """
    Get current UTC time as timezone-aware datetime.

    This replaces deprecated datetime.utcnow() for Python 3.12+ compatibility.

    Note: This is the public API. Submodules use private _utc_now() functions
    to avoid circular import issues.

    Returns:
        Current UTC time with timezone info
    """
    return datetime.now(timezone.utc)

from hardware.hardware_types import (
    HealthStatus,
    ComponentType,
    UpgradeUrgency,
    DecisionConfidence,
    HardwareMetrics,
    HardwareHealth,
    HardwareAlert,
    HardwareDecision,
    HardwareUpgradeRecommendation,
    TradingSystemProtection,
    DEFAULT_THRESHOLDS,
    create_hardware_decision,
    create_upgrade_recommendation,
    create_alert,
)

from hardware.hardware_collector import (
    HardwareCollector,
    collect_hardware_snapshot,
)

from hardware.hardware_analyzer import (
    HardwareAnalyzer,
    analyze_hardware_health,
)

from hardware.hardware_kernel import (
    HardwareKernel,
    get_hardware_kernel,
)

from hardware.hardware_decision_engine import (
    HardwareDecisionEngine,
    get_decision_engine,
)

from hardware.trading_protection import (
    TradingProtectionManager,
    TradingStatus,
    ProtectionAction,
    get_trading_protection,
    is_trading_safe,
    get_throttle_level,
)

from hardware.hardware_audit import (
    HardwareAuditLogger,
    get_hardware_audit_logger,
)

__all__ = [
    # Utilities
    'utc_now',

    # Types and Enums
    'HealthStatus',
    'ComponentType',
    'UpgradeUrgency',
    'DecisionConfidence',
    'TradingStatus',
    'ProtectionAction',

    # Data Models
    'HardwareMetrics',
    'HardwareHealth',
    'HardwareAlert',
    'HardwareDecision',
    'HardwareUpgradeRecommendation',
    'TradingSystemProtection',
    'DEFAULT_THRESHOLDS',

    # Factory Functions
    'create_hardware_decision',
    'create_upgrade_recommendation',
    'create_alert',

    # Collector
    'HardwareCollector',
    'collect_hardware_snapshot',

    # Analyzer
    'HardwareAnalyzer',
    'analyze_hardware_health',

    # Kernel
    'HardwareKernel',
    'get_hardware_kernel',

    # Decision Engine
    'HardwareDecisionEngine',
    'get_decision_engine',

    # Trading Protection
    'TradingProtectionManager',
    'get_trading_protection',
    'is_trading_safe',
    'get_throttle_level',

    # Audit
    'HardwareAuditLogger',
    'get_hardware_audit_logger',
]


def quick_health_check() -> dict:
    """
    Perform a quick hardware health check.

    Returns:
        Dictionary with health status and score
    """
    collector = HardwareCollector()
    analyzer = HardwareAnalyzer()

    metrics = collector.collect_all()
    health = analyzer.analyze(metrics)

    return {
        "status": health.overall_status.value,
        "score": health.overall_score,
        "trading_risk": health.trading_impact_risk,
        "alerts": len(health.active_alerts)
    }


def is_hardware_healthy() -> bool:
    """
    Quick check if hardware is healthy enough for trading.

    Returns:
        True if hardware is in acceptable state
    """
    check = quick_health_check()
    return check["status"] not in ["critical", "failed"] and check["score"] >= 50
