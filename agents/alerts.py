"""
Alert System for Hands-Off Engine

Sends alerts via Telegram for critical events:
- Critical errors
- Extended downtime
- Unusual activity
- Health check failures
"""

import json
import os
import sys
import requests
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, Optional, List
from enum import Enum

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from audit.audit_logger import AuditLogger


class AlertLevel(Enum):
    """Alert severity levels"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class AlertSystem:
    """Sends alerts via Telegram and logs to audit"""
    
    def __init__(
        self,
        bot_token: Optional[str] = None,
        chat_id: Optional[str] = None,
        audit_logger: Optional[AuditLogger] = None
    ):
        """
        Initialize alert system
        
        Args:
            bot_token: Telegram bot token (defaults to TELEGRAM_BOT_TOKEN env var)
            chat_id: Telegram chat ID (defaults to TELEGRAM_CHAT_ID env var)
            audit_logger: Optional audit logger instance
        """
        self.bot_token = bot_token or os.getenv("TELEGRAM_BOT_TOKEN")
        self.chat_id = chat_id or os.getenv("TELEGRAM_CHAT_ID")
        self.audit_logger = audit_logger or AuditLogger(component="alerts")
        
        # Alert rate limiting
        self.alert_history: Dict[str, datetime] = {}
        self.min_alert_interval_seconds = 300  # 5 minutes
        
    def send_alert(
        self,
        message: str,
        level: AlertLevel = AlertLevel.INFO,
        context: Optional[Dict[str, Any]] = None,
        dedupe_key: Optional[str] = None
    ) -> bool:
        """
        Send alert via Telegram and log to audit
        
        Args:
            message: Alert message
            level: Alert severity level
            context: Additional context data
            dedupe_key: Key for deduplication (prevents duplicate alerts)
            
        Returns:
            True if alert was sent successfully
        """
        # Check rate limiting
        if dedupe_key and self._is_rate_limited(dedupe_key):
            return False
        
        # Format message with level
        emoji = self._get_emoji_for_level(level)
        formatted_message = f"{emoji} {level.value.upper()}: {message}"
        
        # Add context if provided
        if context:
            formatted_message += f"\n\nContext:\n{json.dumps(context, indent=2)}"
        
        # Log to audit
        self.audit_logger.log(
            event_type="alert",
            event_data={
                "message": message,
                "level": level.value,
                "context": context or {},
                "dedupe_key": dedupe_key
            }
        )
        
        # Send to Telegram
        success = self._send_telegram_message(formatted_message)
        
        # Update rate limiting
        if dedupe_key and success:
            self.alert_history[dedupe_key] = datetime.now(timezone.utc)
        
        return success
    
    def alert_critical_error(self, error: str, context: Optional[Dict[str, Any]] = None):
        """Send critical error alert"""
        self.send_alert(
            f"CRITICAL ERROR: {error}",
            level=AlertLevel.CRITICAL,
            context=context,
            dedupe_key=f"critical_error_{error[:50]}"
        )
    
    def alert_downtime(self, service: str, duration_seconds: int):
        """Alert on extended downtime"""
        self.send_alert(
            f"Service '{service}' has been down for {duration_seconds}s",
            level=AlertLevel.ERROR,
            context={"service": service, "duration_seconds": duration_seconds},
            dedupe_key=f"downtime_{service}"
        )
    
    def alert_unusual_activity(self, description: str, metrics: Dict[str, Any]):
        """Alert on unusual activity"""
        self.send_alert(
            f"Unusual activity detected: {description}",
            level=AlertLevel.WARNING,
            context=metrics,
            dedupe_key=f"unusual_{description[:50]}"
        )
    
    def alert_health_check_failed(self, check_name: str, details: Dict[str, Any]):
        """Alert when health check fails"""
        self.send_alert(
            f"Health check failed: {check_name}",
            level=AlertLevel.ERROR,
            context=details,
            dedupe_key=f"health_check_{check_name}"
        )
    
    def alert_self_healing_action(self, action: str, target: str, success: bool):
        """Alert when self-healing action is taken"""
        level = AlertLevel.INFO if success else AlertLevel.WARNING
        status = "succeeded" if success else "failed"
        
        self.send_alert(
            f"Self-healing: {action} on '{target}' {status}",
            level=level,
            context={"action": action, "target": target, "success": success},
            dedupe_key=f"healing_{action}_{target}"
        )
    
    def _is_rate_limited(self, dedupe_key: str) -> bool:
        """Check if alert is rate limited"""
        if dedupe_key not in self.alert_history:
            return False
        
        last_sent = self.alert_history[dedupe_key]
        elapsed = (datetime.now(timezone.utc) - last_sent).total_seconds()
        
        return elapsed < self.min_alert_interval_seconds
    
    def _get_emoji_for_level(self, level: AlertLevel) -> str:
        """Get emoji for alert level"""
        emoji_map = {
            AlertLevel.INFO: "ℹ️",
            AlertLevel.WARNING: "⚠️",
            AlertLevel.ERROR: "❌",
            AlertLevel.CRITICAL: "🚨"
        }
        return emoji_map.get(level, "📢")
    
    def _send_telegram_message(self, message: str) -> bool:
        """
        Send message to Telegram
        
        Returns:
            True if message was sent successfully
        """
        if not self.bot_token or not self.chat_id:
            # Fallback to stderr if Telegram not configured
            print(f"[ALERT] {message}", file=sys.stderr)
            return False
        
        try:
            url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
            payload = {
                "chat_id": self.chat_id,
                "text": message,
                "parse_mode": "HTML"
            }
            
            response = requests.post(url, json=payload, timeout=10)
            response.raise_for_status()
            return True
            
        except Exception as e:
            print(f"Failed to send Telegram alert: {e}", file=sys.stderr)
            return False


# Singleton instance
_alert_system: Optional[AlertSystem] = None


def get_alert_system() -> AlertSystem:
    """Get or create singleton alert system instance"""
    global _alert_system
    if _alert_system is None:
        _alert_system = AlertSystem()
    return _alert_system


if __name__ == "__main__":
    # Simple test
    alerts = AlertSystem()
    alerts.send_alert("Test alert from alert system", level=AlertLevel.INFO)
    print("Alert system test complete")
