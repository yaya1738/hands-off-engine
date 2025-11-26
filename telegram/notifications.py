#!/usr/bin/env python3
"""
Telegram Notification System

Implements proactive notifications for zero-touch operation:
- Edge detection alerts (new opportunities)
- Daily summary reports (morning briefing)
- Error/warning notifications
- Trade execution confirmations (DRYRUN mode)

Integrates with:
- Audit system for logging
- State files for data
- AI Nexus for AI-powered summaries
"""

import json
import os
import sys
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional
import hashlib

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

# Configuration
REPO_ROOT = Path(__file__).parent.parent
STATE_DIR = REPO_ROOT / "state"
LOGS_DIR = REPO_ROOT / "logs"
NOTIFICATION_STATE_FILE = STATE_DIR / "notification_state.json"

# Configurable thresholds
MIN_CONFIDENCE_THRESHOLD = 0.7  # Minimum confidence for opportunities
MIN_EDGE_THRESHOLD = 0.05  # Minimum edge (5%)

# Telegram config
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")


class NotificationSystem:
    """Manages Telegram notifications for system events."""

    def __init__(self):
        """Initialize notification system."""
        self.state_file = NOTIFICATION_STATE_FILE
        self.state_file.parent.mkdir(parents=True, exist_ok=True)
        self._load_state()

    def _load_state(self):
        """Load notification state from disk."""
        if self.state_file.exists():
            with open(self.state_file) as f:
                self.state = json.load(f)
        else:
            self.state = {
                'last_daily_summary': None,
                'last_edge_alert': None,
                'sent_notifications': [],
                'notification_settings': {
                    'edge_alerts': True,
                    'daily_summary': True,
                    'error_notifications': True,
                    'trade_confirmations': True,
                    'daily_summary_hour': 8  # 8 AM
                }
            }
            self._save_state()

    def _save_state(self):
        """Save notification state to disk."""
        with open(self.state_file, 'w') as f:
            json.dump(self.state, f, indent=2)

    def _record_notification(self, notification_type: str, data: Dict):
        """Record that a notification was sent."""
        self.state['sent_notifications'].append({
            'type': notification_type,
            'timestamp': datetime.now().isoformat(),
            'data': data
        })
        
        # Keep only last 100 notifications
        if len(self.state['sent_notifications']) > 100:
            self.state['sent_notifications'] = self.state['sent_notifications'][-100:]
        
        self._save_state()

    def send_telegram_message(self, message: str, parse_mode: str = "Markdown") -> bool:
        """
        Send message to Telegram.
        
        Args:
            message: Message text to send
            parse_mode: "Markdown" or "HTML"
            
        Returns:
            True if sent successfully, False otherwise
        """
        if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
            # Fallback: log to console
            logger.info(f"Telegram notification (no config):\n{message}")
            return False

        try:
            import requests
            
            url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
            data = {
                "chat_id": TELEGRAM_CHAT_ID,
                "text": message,
                "parse_mode": parse_mode
            }
            
            response = requests.post(url, json=data, timeout=10)
            response.raise_for_status()
            
            logger.info(f"Telegram notification sent to chat {TELEGRAM_CHAT_ID}")
            return True

        except Exception as e:
            logger.error(f"Error sending Telegram message: {e}")
            return False

    def send_edge_alert(self, opportunities: List[Dict]) -> bool:
        """
        Send alert about new market opportunities.
        
        Args:
            opportunities: List of opportunity dicts with market info
            
        Returns:
            True if sent successfully
        """
        if not self.state['notification_settings']['edge_alerts']:
            return False

        try:
            # Build message
            message_parts = []
            message_parts.append("🎯 *New Market Opportunities Detected*\n")
            message_parts.append(f"Found {len(opportunities)} opportunities:\n")

            for i, opp in enumerate(opportunities[:3], 1):  # Show top 3
                market = opp.get('market', 'Unknown')
                edge = opp.get('edge', 0) * 100
                confidence = opp.get('confidence', 0) * 100
                
                edge_emoji = "🟢" if edge > 5 else "🟡"
                message_parts.append(f"{i}. {edge_emoji} *{market}*")
                message_parts.append(f"   Edge: {edge:.1f}% | Confidence: {confidence:.0f}%\n")

            if len(opportunities) > 3:
                message_parts.append(f"_... and {len(opportunities) - 3} more_\n")

            message_parts.append("Send `/markets` for full details")

            message = "\n".join(message_parts)
            
            # Send notification
            if self.send_telegram_message(message):
                self.state['last_edge_alert'] = datetime.now().isoformat()
                self._record_notification('edge_alert', {
                    'count': len(opportunities)
                })
                return True

        except Exception as e:
            logger.error(f"Error sending edge alert: {e}")

        return False

    def send_daily_summary(self) -> bool:
        """
        Send daily morning briefing with system status.
        
        Includes:
        - System health
        - Performance metrics (24h)
        - Current positions
        - Top opportunities
        - Action items
        
        Returns:
            True if sent successfully
        """
        if not self.state['notification_settings']['daily_summary']:
            return False

        # Check if already sent today
        last_summary = self.state.get('last_daily_summary')
        if last_summary:
            last_time = datetime.fromisoformat(last_summary)
            if last_time.date() == datetime.now().date():
                return False  # Already sent today

        try:
            message_parts = []
            message_parts.append("☀️ *Morning Briefing*")
            message_parts.append(f"_{datetime.now().strftime('%A, %B %d, %Y')}_\n")

            # System status
            message_parts.append("*System Status:*")
            health = self._get_system_health()
            message_parts.append(f"• Health: {health}")
            
            mode = os.getenv('TRADING_MODE', 'DRYRUN')
            mode_emoji = "🟢" if mode == "DRYRUN" else "🔴"
            message_parts.append(f"• Mode: {mode_emoji} {mode}\n")

            # 24h Performance
            metrics = self._get_24h_metrics()
            if metrics:
                message_parts.append("*24h Performance:*")
                message_parts.append(f"• Runs: {metrics.get('runs', 0)}")
                message_parts.append(f"• Orders Planned: {metrics.get('orders', 0)}")
                message_parts.append(f"• Total Size: ${metrics.get('size', 0):.2f}\n")

            # Current opportunities
            opportunities = self._get_current_opportunities()
            if opportunities:
                message_parts.append(f"*Current Opportunities:* {len(opportunities)}")
                for opp in opportunities[:2]:  # Top 2
                    market = opp.get('market', 'Unknown')[:30]  # Truncate
                    edge = opp.get('edge', 0) * 100
                    message_parts.append(f"• {market} ({edge:.1f}% edge)")
                message_parts.append("")

            # Action items
            action_items = self._get_action_items()
            if action_items:
                message_parts.append("*Action Items:*")
                for item in action_items[:3]:
                    message_parts.append(f"• {item}")
                message_parts.append("")

            message_parts.append("_Send /status for detailed view_")

            message = "\n".join(message_parts)

            # Send notification
            if self.send_telegram_message(message):
                self.state['last_daily_summary'] = datetime.now().isoformat()
                self._record_notification('daily_summary', {})
                return True

        except Exception as e:
            logger.error(f"Error sending daily summary: {e}")

        return False

    def send_error_notification(self, error_type: str, error_message: str, context: Optional[Dict] = None) -> bool:
        """
        Send notification about system error or warning.
        
        Args:
            error_type: Type of error (e.g., "data_fetch", "execution", "health_check")
            error_message: Human-readable error description
            context: Additional context data
            
        Returns:
            True if sent successfully
        """
        if not self.state['notification_settings']['error_notifications']:
            return False

        try:
            # Build message
            message_parts = []
            
            # Use appropriate emoji based on severity
            if "critical" in error_type.lower() or "fatal" in error_type.lower():
                emoji = "🚨"
                severity = "CRITICAL"
            elif "warning" in error_type.lower():
                emoji = "⚠️"
                severity = "WARNING"
            else:
                emoji = "❌"
                severity = "ERROR"

            message_parts.append(f"{emoji} *{severity}: {error_type}*\n")
            message_parts.append(f"{error_message}\n")

            if context:
                message_parts.append("*Context:*")
                for key, value in list(context.items())[:5]:  # Max 5 items
                    message_parts.append(f"• {key}: {value}")
                message_parts.append("")

            message_parts.append(f"_Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}_")
            message_parts.append("_Self-healing agent will attempt recovery_")

            message = "\n".join(message_parts)

            # Send notification
            if self.send_telegram_message(message):
                self._record_notification('error', {
                    'type': error_type,
                    'message': error_message
                })
                return True

        except Exception as e:
            logger.error(f"Error sending error notification: {e}")

        return False

    def send_trade_confirmation(self, trade_info: Dict) -> bool:
        """
        Send confirmation of trade execution (DRYRUN or LIVE).
        
        Args:
            trade_info: Dict with trade details (market, side, size, price, etc.)
            
        Returns:
            True if sent successfully
        """
        if not self.state['notification_settings']['trade_confirmations']:
            return False

        try:
            # Build message
            message_parts = []
            
            mode = trade_info.get('mode', 'DRYRUN')
            if mode == 'DRYRUN':
                message_parts.append("🧪 *Trade Executed (DRYRUN)*\n")
            else:
                message_parts.append("💰 *Trade Executed (LIVE)*\n")

            market = trade_info.get('market', 'Unknown')
            side = trade_info.get('side', 'Unknown')
            size = trade_info.get('size', 0)
            price = trade_info.get('price', 0)
            
            message_parts.append(f"*Market:* {market}")
            message_parts.append(f"*Side:* {side}")
            message_parts.append(f"*Size:* ${size:.2f}")
            message_parts.append(f"*Price:* {price:.4f}\n")

            # Additional info
            edge = trade_info.get('edge')
            if edge:
                message_parts.append(f"*Expected Edge:* {edge * 100:.1f}%")

            confidence = trade_info.get('confidence')
            if confidence:
                message_parts.append(f"*Confidence:* {confidence * 100:.0f}%\n")

            message_parts.append(f"_Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}_")
            
            if mode == 'DRYRUN':
                message_parts.append("_No real money involved_")

            message = "\n".join(message_parts)

            # Send notification
            if self.send_telegram_message(message):
                self._record_notification('trade_confirmation', {
                    'market': market,
                    'size': size,
                    'mode': mode
                })
                return True

        except Exception as e:
            logger.error(f"Error sending trade confirmation: {e}")

        return False

    def check_and_send_daily_summary(self) -> bool:
        """
        Check if daily summary should be sent and send it.
        
        Should be called periodically (e.g., every hour).
        
        Returns:
            True if summary was sent
        """
        # Check if it's time for daily summary
        now = datetime.now()
        target_hour = self.state['notification_settings']['daily_summary_hour']
        
        # Only send if current hour matches target and not sent today
        if now.hour != target_hour:
            return False

        return self.send_daily_summary()

    # Helper methods

    def _get_system_health(self) -> str:
        """Get current system health status."""
        try:
            # Check critical state files
            critical_files = [
                STATE_DIR / "knowledge.json",
                STATE_DIR / "polymarket-model.json",
            ]
            
            for file_path in critical_files:
                if not file_path.exists():
                    return "⚠️ Issues detected"
            
            return "✅ Healthy"
        except Exception:
            return "❌ Unknown"

    def _get_24h_metrics(self) -> Optional[Dict]:
        """Get 24h performance metrics."""
        try:
            metrics_path = STATE_DIR / "performance_metrics.jsonl"
            if not metrics_path.exists():
                return None

            with open(metrics_path) as f:
                lines = f.readlines()

            # Get last 24h
            cutoff = datetime.now() - timedelta(hours=24)
            recent_metrics = []

            for line in lines:
                metric = json.loads(line)
                ts = datetime.fromisoformat(metric["timestamp"].replace("+00:00", ""))
                if ts >= cutoff:
                    recent_metrics.append(metric)

            if not recent_metrics:
                return None

            # Calculate summary
            total_runs = len(recent_metrics)
            total_orders = sum(m.get("execution_plan", {}).get("total_orders", 0) for m in recent_metrics)
            total_size = sum(m.get("execution_plan", {}).get("total_size_usd", 0) for m in recent_metrics)

            return {
                'runs': total_runs,
                'orders': total_orders,
                'size': total_size
            }

        except Exception:
            return None

    def _get_current_opportunities(self) -> List[Dict]:
        """Get current market opportunities."""
        try:
            model_path = STATE_DIR / "polymarket-model.json"
            if not model_path.exists():
                return []

            with open(model_path) as f:
                model_data = json.load(f)

            # Extract opportunities (simplified)
            markets = model_data.get('markets', [])
            opportunities = []

            for market in markets:
                edge = market.get('edge', 0)
                confidence = market.get('confidence', 0)

                if edge > MIN_EDGE_THRESHOLD and confidence > MIN_CONFIDENCE_THRESHOLD:
                    opportunities.append({
                        'market': market.get('title', 'Unknown'),
                        'edge': edge,
                        'confidence': confidence
                    })

            opportunities.sort(key=lambda x: x['edge'], reverse=True)
            return opportunities

        except Exception:
            return []

    def _get_action_items(self) -> List[str]:
        """Get pending action items for user."""
        action_items = []

        try:
            # Check for pending approvals
            approval_file = STATE_DIR / "approval_queue.json"
            if approval_file.exists():
                with open(approval_file) as f:
                    queue = json.load(f)
                pending = queue.get('pending', [])
                if pending:
                    action_items.append(f"{len(pending)} pending approval(s)")

            # Check for system errors
            error_count = self._count_recent_errors()
            if error_count > 0:
                action_items.append(f"{error_count} error(s) in last 24h")

            # Check data freshness
            model_path = STATE_DIR / "polymarket-model.json"
            if model_path.exists():
                mtime = datetime.fromtimestamp(model_path.stat().st_mtime)
                age = datetime.now() - mtime
                if age > timedelta(hours=6):
                    action_items.append(f"Market data {age.seconds // 3600}h old")

        except Exception:
            pass

        return action_items

    def _count_recent_errors(self) -> int:
        """Count errors in last 24 hours."""
        try:
            log_files = list(LOGS_DIR.glob("*.txt"))
            error_count = 0

            for log_file in log_files:
                try:
                    mtime = datetime.fromtimestamp(log_file.stat().st_mtime)
                    if datetime.now() - mtime > timedelta(hours=24):
                        continue

                    with open(log_file) as f:
                        for line in f:
                            if 'error' in line.lower() or 'failed' in line.lower():
                                error_count += 1
                except Exception:
                    continue

            return error_count

        except Exception:
            return 0


# Convenience functions for easy import

def send_edge_alert(opportunities: List[Dict]) -> bool:
    """Send edge detection alert."""
    notifier = NotificationSystem()
    return notifier.send_edge_alert(opportunities)


def send_daily_summary() -> bool:
    """Send daily summary."""
    notifier = NotificationSystem()
    return notifier.send_daily_summary()


def send_error_notification(error_type: str, error_message: str, context: Optional[Dict] = None) -> bool:
    """Send error notification."""
    notifier = NotificationSystem()
    return notifier.send_error_notification(error_type, error_message, context)


def send_trade_confirmation(trade_info: Dict) -> bool:
    """Send trade confirmation."""
    notifier = NotificationSystem()
    return notifier.send_trade_confirmation(trade_info)


def check_and_send_daily_summary() -> bool:
    """Check and send daily summary if needed."""
    notifier = NotificationSystem()
    return notifier.check_and_send_daily_summary()


if __name__ == "__main__":
    # Test notifications
    print("Testing Telegram Notification System\n")
    
    notifier = NotificationSystem()
    
    # Test edge alert
    print("1. Testing edge alert...")
    test_opportunities = [
        {'market': 'Test Market 1', 'edge': 0.08, 'confidence': 0.85},
        {'market': 'Test Market 2', 'edge': 0.06, 'confidence': 0.75},
    ]
    notifier.send_edge_alert(test_opportunities)
    
    # Test error notification
    print("2. Testing error notification...")
    notifier.send_error_notification(
        'data_fetch',
        'Failed to fetch market data',
        {'source': 'polymarket_api', 'attempt': 3}
    )
    
    # Test trade confirmation
    print("3. Testing trade confirmation...")
    notifier.send_trade_confirmation({
        'market': 'Test Market',
        'side': 'YES',
        'size': 50.0,
        'price': 0.65,
        'edge': 0.08,
        'confidence': 0.85,
        'mode': 'DRYRUN'
    })
    
    print("\nNotifications sent (or logged if no Telegram config)")
