"""
Audit logging system for Hands-Off Engine
Tracks all AI operations, costs, and outcomes
"""
from .audit_logger import AuditLogger, AuditEvent

# Compatibility export
def get_audit_logger(component: str = "unknown") -> AuditLogger:
    """
    Get an audit logger instance for a component.
    
    Note: The component parameter is retained for API compatibility but is not used
    in initialization. Component names are specified per-event via log_event().
    
    Args:
        component: Component name (ignored, kept for backward compatibility)
    
    Returns:
        AuditLogger instance with default log directory
    """
    # AuditLogger takes log_dir as first positional argument, not component
    # Component is specified per-event in log_event() calls
    return AuditLogger()

try:
    from .ledger import FinancialLedger, LedgerEntry
    __all__ = ["AuditLogger", "AuditEvent", "FinancialLedger", "LedgerEntry", "get_audit_logger"]
except ImportError:
    __all__ = ["AuditLogger", "AuditEvent", "get_audit_logger"]

