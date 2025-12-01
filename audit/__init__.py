"""
Audit logging system for Hands-Off Engine
Tracks all AI operations, costs, and outcomes
"""
from .audit_logger import AuditLogger, AuditEvent

# Compatibility export
def get_audit_logger(component: str = "unknown") -> AuditLogger:
    """Get an audit logger instance for a component."""
    return AuditLogger(component=component)

try:
    from .ledger import FinancialLedger, LedgerEntry
    __all__ = ["AuditLogger", "AuditEvent", "FinancialLedger", "LedgerEntry", "get_audit_logger"]
except ImportError:
    __all__ = ["AuditLogger", "AuditEvent", "get_audit_logger"]

