"""
Audit package for Hands-Off Engine

Provides comprehensive audit logging for all critical operations
"""

from .audit_logger import AuditLogger, get_audit_logger

__all__ = ['AuditLogger', 'get_audit_logger']
