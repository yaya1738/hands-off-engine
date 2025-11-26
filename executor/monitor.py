"""
Execution Monitor for Hands-Off Engine

This module monitors order execution:
- Track pending orders
- Timeout handling
- Failed execution recovery
- Execution quality metrics
"""

import json
import sys
import os
import time
from typing import Optional, Dict, List
from datetime import datetime, timezone, timedelta
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from audit import get_audit_logger


class ExecutionMonitor:
    """
    Monitor tracks pending orders and execution quality.
    """
    
    # Monitoring parameters
    ORDER_TIMEOUT_SECONDS = 60  # Timeout for pending orders
    ALERT_SLIPPAGE_THRESHOLD_BPS = 50  # Alert if slippage exceeds 50 bps
    ALERT_FAILURE_RATE_THRESHOLD = 0.20  # Alert if >20% orders fail
    
    def __init__(self, state_dir: Optional[Path] = None):
        """
        Initialize execution monitor.
        
        Args:
            state_dir: Directory for state files (defaults to ../state)
        """
        if state_dir is None:
            state_dir = Path(__file__).parent.parent / "state"
        
        self.state_dir = state_dir
        self.pending_file = state_dir / "execution" / "pending.json"
        self.history_file = state_dir / "execution" / "history.jsonl"
        self.metrics_file = state_dir / "execution" / "metrics.json"
        
        self.audit = get_audit_logger(component="executor.monitor")
    
    def _load_pending_orders(self) -> List[Dict]:
        """Load pending orders from state file"""
        if not self.pending_file.exists():
            return []
        
        with open(self.pending_file, 'r') as f:
            data = json.load(f)
        
        return data.get("orders", [])
    
    def _load_metrics(self) -> Dict:
        """Load execution metrics from state file"""
        if not self.metrics_file.exists():
            return {
                "total_orders": 0,
                "successful_fills": 0,
                "failed_orders": 0,
                "total_slippage_bps": 0.0,
                "avg_execution_time_ms": 0.0
            }
        
        with open(self.metrics_file, 'r') as f:
            return json.load(f)
    
    def _load_recent_history(self, hours: int = 24) -> List[Dict]:
        """
        Load recent execution history.
        
        Args:
            hours: Number of hours to look back
            
        Returns:
            List of execution history entries
        """
        if not self.history_file.exists():
            return []
        
        cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)
        recent_entries = []
        
        with open(self.history_file, 'r') as f:
            for line in f:
                try:
                    entry = json.loads(line)
                    entry_time = datetime.fromisoformat(entry.get("timestamp", "").replace("Z", "+00:00"))
                    
                    if entry_time >= cutoff:
                        recent_entries.append(entry)
                except (json.JSONDecodeError, ValueError):
                    continue
        
        return recent_entries
    
    def check_timeouts(self) -> List[Dict]:
        """
        Check for timed out pending orders.
        
        Returns:
            List of timed out orders
        """
        pending = self._load_pending_orders()
        timed_out = []
        now = datetime.now(timezone.utc)
        
        for order in pending:
            try:
                created_at = datetime.fromisoformat(order.get("created_at", "").replace("Z", "+00:00"))
                age_seconds = (now - created_at).total_seconds()
                
                if age_seconds > self.ORDER_TIMEOUT_SECONDS:
                    timed_out.append({
                        "order_id": order.get("order_id"),
                        "market_id": order.get("market_id"),
                        "age_seconds": age_seconds,
                        "order": order
                    })
            except (ValueError, TypeError):
                continue
        
        if timed_out:
            self.audit.log_action(
                action_type="timeout_check",
                action_data={
                    "timed_out_count": len(timed_out),
                    "orders": [t["order_id"] for t in timed_out]
                },
                result="timeouts_found"
            )
        
        return timed_out
    
    def handle_timeout(self, order_info: Dict) -> Dict:
        """
        Handle timed out order.
        
        Args:
            order_info: Order info from check_timeouts
            
        Returns:
            Recovery action taken
        """
        order = order_info["order"]
        order_id = order.get("order_id")
        
        # Log timeout
        self.audit.log_action(
            action_type="order_timeout",
            action_data={
                "order_id": order_id,
                "market_id": order.get("market_id"),
                "age_seconds": order_info["age_seconds"]
            },
            result="cancelled"
        )
        
        # Return recovery action
        return {
            "order_id": order_id,
            "action": "cancelled",
            "reason": "timeout",
            "age_seconds": order_info["age_seconds"]
        }
    
    def check_execution_quality(self) -> Dict:
        """
        Check execution quality metrics and identify issues.
        
        Returns:
            Dict with quality metrics and alerts
        """
        metrics = self._load_metrics()
        recent_history = self._load_recent_history(hours=24)
        
        alerts = []
        
        # Check failure rate
        total_orders = metrics.get("total_orders", 0)
        failed_orders = metrics.get("failed_orders", 0)
        
        if total_orders > 0:
            failure_rate = failed_orders / total_orders
            
            if failure_rate > self.ALERT_FAILURE_RATE_THRESHOLD:
                alerts.append({
                    "type": "high_failure_rate",
                    "severity": "warning",
                    "message": f"Failure rate {failure_rate:.1%} exceeds threshold {self.ALERT_FAILURE_RATE_THRESHOLD:.1%}",
                    "value": failure_rate
                })
        
        # Check slippage
        avg_slippage = metrics.get("total_slippage_bps", 0.0)
        
        if avg_slippage > self.ALERT_SLIPPAGE_THRESHOLD_BPS:
            alerts.append({
                "type": "high_slippage",
                "severity": "warning",
                "message": f"Avg slippage {avg_slippage:.2f} bps exceeds threshold {self.ALERT_SLIPPAGE_THRESHOLD_BPS} bps",
                "value": avg_slippage
            })
        
        # Check recent execution times
        if recent_history:
            recent_times = [
                entry.get("result", {}).get("execution_time_ms", 0)
                for entry in recent_history
                if entry.get("result", {}).get("success", False)
            ]
            
            if recent_times:
                avg_recent_time = sum(recent_times) / len(recent_times)
                
                if avg_recent_time > 5000:  # 5 seconds
                    alerts.append({
                        "type": "slow_execution",
                        "severity": "info",
                        "message": f"Recent avg execution time {avg_recent_time:.0f} ms is high",
                        "value": avg_recent_time
                    })
        
        quality_report = {
            "metrics": metrics,
            "recent_executions": len(recent_history),
            "alerts": alerts,
            "status": "ok" if not alerts else "warning"
        }
        
        if alerts:
            self.audit.log_action(
                action_type="quality_check",
                action_data={
                    "alerts_count": len(alerts),
                    "alerts": alerts
                },
                result="alerts_found"
            )
        
        return quality_report
    
    def get_pending_summary(self) -> Dict:
        """
        Get summary of pending orders.
        
        Returns:
            Summary of pending orders
        """
        pending = self._load_pending_orders()
        now = datetime.now(timezone.utc)
        
        summary = {
            "total_pending": len(pending),
            "total_amount": 0.0,
            "oldest_age_seconds": 0.0,
            "markets": {}
        }
        
        for order in pending:
            amount = order.get("amount", 0.0)
            market_id = order.get("market_id", "unknown")
            
            summary["total_amount"] += amount
            
            # Track by market
            if market_id not in summary["markets"]:
                summary["markets"][market_id] = {
                    "market_name": order.get("market_name", "Unknown"),
                    "order_count": 0,
                    "total_amount": 0.0
                }
            
            summary["markets"][market_id]["order_count"] += 1
            summary["markets"][market_id]["total_amount"] += amount
            
            # Check age
            try:
                created_at = datetime.fromisoformat(order.get("created_at", "").replace("Z", "+00:00"))
                age_seconds = (now - created_at).total_seconds()
                summary["oldest_age_seconds"] = max(summary["oldest_age_seconds"], age_seconds)
            except (ValueError, TypeError):
                continue
        
        return summary
    
    def recover_failed_execution(self, order_id: str) -> Dict:
        """
        Attempt to recover from failed execution.
        
        Args:
            order_id: Order ID to recover
            
        Returns:
            Recovery result
        """
        # Load recent history to find the failed execution
        recent_history = self._load_recent_history(hours=24)
        
        failed_execution = None
        for entry in recent_history:
            if entry.get("order", {}).get("order_id") == order_id:
                if not entry.get("result", {}).get("success", True):
                    failed_execution = entry
                    break
        
        if not failed_execution:
            return {
                "success": False,
                "message": f"No failed execution found for order {order_id}"
            }
        
        # Log recovery attempt
        self.audit.log_action(
            action_type="execution_recovery",
            action_data={
                "order_id": order_id,
                "original_error": failed_execution.get("result", {}).get("message", "unknown")
            },
            result="recovery_attempted"
        )
        
        # Return recovery info (actual retry would happen in engine)
        return {
            "success": True,
            "message": "Recovery logged, requires manual retry",
            "failed_execution": failed_execution
        }
    
    def monitor_loop(self, iterations: int = 1) -> Dict:
        """
        Run monitoring loop to check all conditions.
        
        Args:
            iterations: Number of monitoring iterations to run
            
        Returns:
            Summary of monitoring run
        """
        summary = {
            "iterations": iterations,
            "timeouts_found": 0,
            "alerts_generated": 0,
            "pending_orders": 0
        }
        
        for i in range(iterations):
            # Check timeouts
            timeouts = self.check_timeouts()
            summary["timeouts_found"] += len(timeouts)
            
            # Handle timeouts
            for timeout_info in timeouts:
                self.handle_timeout(timeout_info)
            
            # Check execution quality
            quality = self.check_execution_quality()
            summary["alerts_generated"] += len(quality.get("alerts", []))
            
            # Get pending summary
            pending = self.get_pending_summary()
            summary["pending_orders"] = pending["total_pending"]
            
            # Sleep between iterations (if more than one)
            if i < iterations - 1:
                time.sleep(1)
        
        return summary


# Example usage
if __name__ == "__main__":
    monitor = ExecutionMonitor()
    
    # Check timeouts
    timeouts = monitor.check_timeouts()
    print(f"\nTimeouts found: {len(timeouts)}")
    
    # Check execution quality
    quality = monitor.check_execution_quality()
    print(f"\nExecution Quality: {quality['status']}")
    print(f"Alerts: {len(quality['alerts'])}")
    for alert in quality['alerts']:
        print(f"  - {alert['type']}: {alert['message']}")
    
    # Get pending summary
    pending = monitor.get_pending_summary()
    print(f"\nPending Orders: {pending['total_pending']}")
    print(f"Total Amount: ${pending['total_amount']:.2f}")
    
    # Show metrics
    metrics = quality['metrics']
    print(f"\nExecution Metrics:")
    print(f"  Total orders: {metrics['total_orders']}")
    print(f"  Successful: {metrics['successful_fills']}")
    print(f"  Failed: {metrics['failed_orders']}")
    if metrics['total_orders'] > 0:
        success_rate = metrics['successful_fills'] / metrics['total_orders']
        print(f"  Success rate: {success_rate:.1%}")
