#!/usr/bin/env python3
"""
Handoff Health Monitoring Script
=================================

Monitors handoff system health and alerts on issues:
- Stale handoffs (pending too long)
- Failed handoffs above threshold
- Low completion rates
- Agent availability issues

Integrates with self-healing agent and Telegram notifications.
"""

import json
import sys
from pathlib import Path
from datetime import datetime, timezone

# Add parent directory to path
BASE_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(BASE_DIR))

from ai.coordination.handoff_manager import HandoffManager


class HandoffHealthMonitor:
    """Monitor handoff system health"""
    
    def __init__(self):
        self.manager = HandoffManager()
        self.alerts = []
        
        # Thresholds
        self.max_pending_time_minutes = 120  # 2 hours
        self.min_completion_rate = 0.70  # 70%
        self.max_failed_rate = 0.15  # 15%
        self.max_timeout_rate = 0.10  # 10%
    
    def check_health(self) -> dict:
        """
        Run all health checks
        
        Returns:
            dict with health status and alerts
        """
        self.alerts = []
        
        # Check for stale handoffs
        self._check_stale_handoffs()
        
        # Check for timeouts
        timed_out = self.manager.check_timeouts()
        if timed_out:
            self.alerts.append({
                "severity": "warning",
                "type": "timeout",
                "message": f"Found {len(timed_out)} timed out handoffs",
                "handoffs": [h["id"] for h in timed_out]
            })
        
        # Get and analyze metrics
        metrics = self.manager.get_metrics()
        self._check_metrics(metrics)
        
        # Determine overall status
        severity_levels = [a["severity"] for a in self.alerts]
        if "critical" in severity_levels:
            status = "critical"
        elif "warning" in severity_levels:
            status = "warning"
        else:
            status = "ok"
        
        return {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "status": status,
            "metrics": metrics,
            "alerts": self.alerts,
            "alert_count": len(self.alerts)
        }
    
    def _check_stale_handoffs(self):
        """Check for handoffs pending too long"""
        pending = self.manager.get_pending_handoffs()
        now = datetime.now(timezone.utc)
        
        stale = []
        for handoff in pending:
            created = datetime.fromisoformat(handoff["created_at"].replace('Z', '+00:00'))
            age_minutes = (now - created).total_seconds() / 60
            
            if age_minutes > self.max_pending_time_minutes:
                stale.append({
                    "id": handoff["id"],
                    "to_agent": handoff["to_agent"],
                    "age_minutes": round(age_minutes, 1),
                    "description": handoff["task"]["description"]
                })
        
        if stale:
            self.alerts.append({
                "severity": "warning" if len(stale) < 3 else "critical",
                "type": "stale_handoffs",
                "message": f"Found {len(stale)} stale handoffs (pending > {self.max_pending_time_minutes}min)",
                "handoffs": stale
            })
    
    def _check_metrics(self, metrics: dict):
        """Check metrics against thresholds"""
        total = metrics.get("total_handoffs", 0)
        if total < 5:
            # Not enough data for meaningful alerts
            return
        
        # Check completion rate
        completion_rate = metrics.get("completion_rate", 0)
        if completion_rate < self.min_completion_rate:
            self.alerts.append({
                "severity": "warning",
                "type": "low_completion_rate",
                "message": f"Completion rate is {completion_rate:.1%} (threshold: {self.min_completion_rate:.1%})",
                "current": completion_rate,
                "threshold": self.min_completion_rate
            })
        
        # Check failed rate
        by_status = metrics.get("by_status", {})
        failed = by_status.get("failed", 0)
        failed_rate = failed / total if total > 0 else 0
        
        if failed_rate > self.max_failed_rate:
            self.alerts.append({
                "severity": "warning",
                "type": "high_failure_rate",
                "message": f"Failure rate is {failed_rate:.1%} (threshold: {self.max_failed_rate:.1%})",
                "current": failed_rate,
                "threshold": self.max_failed_rate,
                "failed_count": failed
            })
        
        # Check timeout rate
        timeout = by_status.get("timeout", 0)
        timeout_rate = timeout / total if total > 0 else 0
        
        if timeout_rate > self.max_timeout_rate:
            self.alerts.append({
                "severity": "warning",
                "type": "high_timeout_rate",
                "message": f"Timeout rate is {timeout_rate:.1%} (threshold: {self.max_timeout_rate:.1%})",
                "current": timeout_rate,
                "threshold": self.max_timeout_rate,
                "timeout_count": timeout
            })
        
        # Check agent-specific issues
        by_agent = metrics.get("by_agent", {})
        for agent, stats in by_agent.items():
            agent_total = stats.get("total", 0)
            if agent_total < 3:
                continue
            
            agent_failed = stats.get("failed", 0)
            agent_failed_rate = agent_failed / agent_total if agent_total > 0 else 0
            
            if agent_failed_rate > self.max_failed_rate * 1.5:  # 1.5x threshold for individual agents
                self.alerts.append({
                    "severity": "warning",
                    "type": "agent_high_failure",
                    "message": f"Agent {agent} has {agent_failed_rate:.1%} failure rate",
                    "agent": agent,
                    "current": agent_failed_rate,
                    "failed_count": agent_failed,
                    "total_count": agent_total
                })
    
    def format_report(self, health: dict) -> str:
        """Format health report for human consumption"""
        lines = []
        lines.append("=" * 60)
        lines.append("HANDOFF SYSTEM HEALTH REPORT")
        lines.append("=" * 60)
        lines.append(f"Timestamp: {health['timestamp']}")
        lines.append(f"Status: {health['status'].upper()}")
        lines.append("")
        
        # Metrics summary
        metrics = health["metrics"]
        lines.append("METRICS:")
        lines.append(f"  Total Handoffs: {metrics['total_handoffs']}")
        lines.append(f"  Completion Rate: {metrics['completion_rate']:.1%}")
        lines.append(f"  Avg Duration: {metrics['average_duration_minutes']:.1f} minutes")
        lines.append("")
        
        # Status breakdown
        lines.append("BY STATUS:")
        for status, count in metrics["by_status"].items():
            if count > 0:
                lines.append(f"  {status}: {count}")
        lines.append("")
        
        # Agent breakdown
        lines.append("BY AGENT:")
        for agent, stats in metrics["by_agent"].items():
            lines.append(f"  {agent}:")
            lines.append(f"    Total: {stats['total']}")
            lines.append(f"    Completed: {stats['completed']}")
            lines.append(f"    Failed: {stats['failed']}")
            lines.append(f"    Pending: {stats['pending']}")
        lines.append("")
        
        # Alerts
        if health["alerts"]:
            lines.append(f"ALERTS ({health['alert_count']}):")
            for alert in health["alerts"]:
                severity_icon = "🔴" if alert["severity"] == "critical" else "⚠️"
                lines.append(f"  {severity_icon} [{alert['severity'].upper()}] {alert['message']}")
        else:
            lines.append("✅ No alerts")
        
        lines.append("=" * 60)
        
        return "\n".join(lines)


def main():
    """Main entry point"""
    monitor = HandoffHealthMonitor()
    health = monitor.check_health()
    
    # Output JSON for machine consumption
    if "--json" in sys.argv:
        print(json.dumps(health, indent=2))
    else:
        # Output formatted report
        report = monitor.format_report(health)
        print(report)
    
    # Exit code based on status
    if health["status"] == "critical":
        sys.exit(2)
    elif health["status"] == "warning":
        sys.exit(1)
    else:
        sys.exit(0)


if __name__ == "__main__":
    main()
