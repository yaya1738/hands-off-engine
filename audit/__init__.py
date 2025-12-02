"""
Audit logging system for Hands-Off Engine
Tracks all AI operations, costs, and outcomes
"""
from .audit_logger import AuditLogger, AuditEvent

# Compatibility export
def get_audit_logger(component: str = "unknown") -> AuditLogger:
    """Get an audit logger instance for a component."""
    # AuditLogger takes log_dir as first positional argument, not component
    # For compatibility, we use the default log_dir
    return AuditLogger()

try:
    from .ledger import FinancialLedger, LedgerEntry
    __all__ = ["AuditLogger", "AuditEvent", "FinancialLedger", "LedgerEntry", "get_audit_logger"]
except ImportError:
    __all__ = ["AuditLogger", "AuditEvent", "get_audit_logger"]

