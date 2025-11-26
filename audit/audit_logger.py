"""
Audit Logger for Hands-Off Engine

Provides structured, immutable audit logging for all critical operations:
- Decisions (alpha, risk, bet sizing)
- Actions (trades, orders, state changes)
- Data fetches and transformations
- System state transitions

All audit events are logged with:
- Timestamp (ISO 8601 UTC)
- Event type
- Component/source
- Data payload
- Context (session, user, etc.)
"""

import json
import os
import time
from datetime import datetime, timezone
from typing import Dict, Any, Optional
from pathlib import Path


class AuditLogger:
    """Central audit logger for the Hands-Off Engine"""
    
    # Event types
    EVENT_DECISION = "decision"
    EVENT_ACTION = "action"
    EVENT_DATA_FETCH = "data_fetch"
    EVENT_STATE_CHANGE = "state_change"
    EVENT_RISK_ASSESSMENT = "risk_assessment"
    EVENT_ALPHA_CALCULATION = "alpha_calculation"
    EVENT_EDGE_DETECTION = "edge_detection"
    EVENT_ORDER = "order"
    EVENT_EXECUTION = "execution"
    EVENT_ERROR = "error"
    
    def __init__(self, log_dir: Optional[str] = None, component: str = "unknown"):
        """
        Initialize audit logger
        
        Args:
            log_dir: Directory for audit logs (defaults to ~/hands-off/audit or ./audit)
            component: Name of the component using this logger
        """
        self.component = component
        
        if log_dir is None:
            # Try ~/hands-off/audit first, fall back to ./logs/audit
            home_audit = os.path.expanduser("~/hands-off/audit")
            if os.path.exists(os.path.expanduser("~/hands-off")):
                log_dir = home_audit
            else:
                log_dir = os.path.join(os.path.dirname(__file__), "../logs/audit")
        
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)
        
        # Current date for log rotation
        self._current_date = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        self._log_file = self._get_log_file()
    
    def _get_log_file(self) -> Path:
        """Get the current log file path based on date"""
        return self.log_dir / f"audit_{self._current_date}.jsonl"
    
    def _ensure_log_file(self):
        """Ensure log file exists and check for date rotation"""
        current_date = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        if current_date != self._current_date:
            self._current_date = current_date
            self._log_file = self._get_log_file()
    
    def log(self, event_type: str, event_data: Dict[str, Any], 
            severity: str = "info", session_id: Optional[str] = None):
        """
        Log an audit event
        
        Args:
            event_type: Type of event (use EVENT_* constants)
            event_data: Dictionary containing event-specific data
            severity: Severity level (debug, info, warning, error, critical)
            session_id: Optional session/run identifier for grouping related events
        """
        self._ensure_log_file()
        
        timestamp = datetime.now(timezone.utc).isoformat()
        
        audit_entry = {
            "timestamp": timestamp,
            "timestamp_unix": time.time(),
            "event_type": event_type,
            "component": self.component,
            "severity": severity,
            "data": event_data,
        }
        
        if session_id:
            audit_entry["session_id"] = session_id
        
        # Write as JSON line
        try:
            with open(self._log_file, "a") as f:
                f.write(json.dumps(audit_entry) + "\n")
        except Exception as e:
            # Fallback: print to stderr if we can't write to file
            import sys
            print(f"[AUDIT ERROR] Failed to write audit log: {e}", file=sys.stderr)
            print(f"[AUDIT ENTRY] {json.dumps(audit_entry)}", file=sys.stderr)
    
    # Convenience methods for common event types
    
    def log_decision(self, decision_type: str, inputs: Dict[str, Any], 
                     outputs: Dict[str, Any], metadata: Optional[Dict[str, Any]] = None,
                     session_id: Optional[str] = None):
        """Log a decision event (alpha, risk, sizing, etc.)"""
        event_data = {
            "decision_type": decision_type,
            "inputs": inputs,
            "outputs": outputs,
        }
        if metadata:
            event_data["metadata"] = metadata
        
        self.log(self.EVENT_DECISION, event_data, session_id=session_id)
    
    def log_action(self, action_type: str, action_data: Dict[str, Any],
                   result: Optional[str] = None, session_id: Optional[str] = None):
        """Log an action event (trade, order, state change)"""
        event_data = {
            "action_type": action_type,
            "action": action_data,
        }
        if result:
            event_data["result"] = result
        
        self.log(self.EVENT_ACTION, event_data, session_id=session_id)
    
    def log_data_fetch(self, source: str, params: Dict[str, Any],
                       success: bool, record_count: Optional[int] = None,
                       error: Optional[str] = None, session_id: Optional[str] = None):
        """Log a data fetch event"""
        event_data = {
            "source": source,
            "params": params,
            "success": success,
        }
        if record_count is not None:
            event_data["record_count"] = record_count
        if error:
            event_data["error"] = error
        
        severity = "info" if success else "error"
        self.log(self.EVENT_DATA_FETCH, event_data, severity=severity, session_id=session_id)
    
    def log_edge_detection(self, market: str, p_fair: float, p_market: float,
                           edge: float, action: str, metadata: Optional[Dict[str, Any]] = None,
                           session_id: Optional[str] = None):
        """Log an edge detection event"""
        event_data = {
            "market": market,
            "p_fair": p_fair,
            "p_market": p_market,
            "edge": edge,
            "action": action,
        }
        if metadata:
            event_data["metadata"] = metadata
        
        self.log(self.EVENT_EDGE_DETECTION, event_data, session_id=session_id)
    
    def log_order(self, order_type: str, market: str, side: str,
                  size: float, price: Optional[float] = None,
                  dryrun: bool = True, order_id: Optional[str] = None,
                  session_id: Optional[str] = None):
        """Log an order event"""
        event_data = {
            "order_type": order_type,
            "market": market,
            "side": side,
            "size": size,
            "dryrun": dryrun,
        }
        if price is not None:
            event_data["price"] = price
        if order_id:
            event_data["order_id"] = order_id
        
        self.log(self.EVENT_ORDER, event_data, session_id=session_id)
    
    def log_state_change(self, state_type: str, previous_state: Any,
                        new_state: Any, reason: Optional[str] = None,
                        session_id: Optional[str] = None):
        """Log a state change event"""
        event_data = {
            "state_type": state_type,
            "previous": previous_state,
            "new": new_state,
        }
        if reason:
            event_data["reason"] = reason
        
        self.log(self.EVENT_STATE_CHANGE, event_data, session_id=session_id)
    
    def log_error(self, error_type: str, error_message: str,
                  stack_trace: Optional[str] = None, context: Optional[Dict[str, Any]] = None,
                  session_id: Optional[str] = None):
        """Log an error event"""
        event_data = {
            "error_type": error_type,
            "message": error_message,
        }
        if stack_trace:
            event_data["stack_trace"] = stack_trace
        if context:
            event_data["context"] = context
        
        self.log(self.EVENT_ERROR, event_data, severity="error", session_id=session_id)


# Singleton instance for easy access
_default_logger: Optional[AuditLogger] = None


def get_audit_logger(component: str = "unknown") -> AuditLogger:
    """Get or create the default audit logger instance"""
    global _default_logger
    if _default_logger is None:
        _default_logger = AuditLogger(component=component)
    return _default_logger


# Example usage
if __name__ == "__main__":
    # Test the audit logger
    logger = AuditLogger(component="test")
    
    # Log a decision
    logger.log_decision(
        decision_type="bet_sizing",
        inputs={"bankroll": 1000, "edge": 0.15, "kelly_fraction": 0.25},
        outputs={"bet_size": 37.5, "bet_fraction": 0.0375},
        metadata={"strategy": "kelly", "confidence": 0.8}
    )
    
    # Log an edge detection
    logger.log_edge_detection(
        market="btc_100k_eoy",
        p_fair=0.40,
        p_market=0.25,
        edge=0.15,
        action="BUY YES",
        metadata={"threshold": 0.05}
    )
    
    # Log an order
    logger.log_order(
        order_type="limit",
        market="btc_100k_eoy",
        side="YES",
        size=37.5,
        price=0.25,
        dryrun=True,
        order_id="test-order-123"
    )
    
    print(f"Audit logs written to: {logger.log_dir}")
