"""
Audit logging system for Hands-Off Engine.
Tracks AI operations, costs, and outcomes.
"""

from pathlib import Path
from typing import Any, Dict, Optional

from .audit_logger import AuditLogger, AuditEvent
from .ledger import FinancialLedger, LedgerEntry


class ComponentAuditLogger:
    """Bind a component name to the shared append-only audit event logger."""

    def __init__(self, component: str, log_dir: Optional[str] = None):
        self.component = component
        self.logger = AuditLogger(
            log_dir=log_dir or str(Path(__file__).resolve().parent / "logs")
        )

    def log_action(
        self,
        action_type: str,
        action_data: Optional[Dict[str, Any]] = None,
        result: Optional[str] = None,
        error: Optional[str] = None,
        cost: Optional[float] = None,
        revenue: Optional[float] = None,
    ):
        return self.logger.log_event(
            component=self.component,
            action=action_type,
            metadata=action_data,
            outcome=result,
            error=error,
            cost=cost,
            revenue=revenue,
        )

    def log_event(
        self,
        action: str,
        metadata: Optional[Dict[str, Any]] = None,
        outcome: Optional[str] = None,
        error: Optional[str] = None,
        cost: Optional[float] = None,
        revenue: Optional[float] = None,
    ):
        return self.logger.log_event(
            component=self.component,
            action=action,
            metadata=metadata,
            outcome=outcome,
            error=error,
            cost=cost,
            revenue=revenue,
        )


def get_audit_logger(component: str = "general", log_dir: Optional[str] = None):
    """Return a component-bound logger compatible with legacy callers."""
    return ComponentAuditLogger(component=component, log_dir=log_dir)


__all__ = [
    "AuditLogger",
    "AuditEvent",
    "FinancialLedger",
    "LedgerEntry",
    "ComponentAuditLogger",
    "get_audit_logger",
]
