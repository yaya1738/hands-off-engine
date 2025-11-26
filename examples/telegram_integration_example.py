#!/usr/bin/env python3
"""
Integration Example: Telegram Notifications with Audit System

Demonstrates how to integrate the Telegram notification system
with the existing audit trail and state management.

This example shows:
1. Sending notifications when trades are executed
2. Logging notifications to audit trail
3. Detecting edge opportunities and alerting
4. Error notification integration
"""

import json
import sys
from datetime import datetime
from pathlib import Path

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from telegram.notifications import (
    NotificationSystem,
    send_edge_alert,
    send_trade_confirmation,
    send_error_notification,
    send_daily_summary
)

REPO_ROOT = Path(__file__).parent.parent
STATE_DIR = REPO_ROOT / "state"
LOGS_DIR = REPO_ROOT / "logs"


def log_to_audit(event_type: str, data: dict):
    """Log event to audit trail."""
    audit_file = LOGS_DIR / f"audit_{datetime.now().strftime('%Y%m%d')}.jsonl"
    
    audit_entry = {
        "timestamp": datetime.now().isoformat(),
        "event_type": event_type,
        "data": data
    }
    
    with open(audit_file, 'a') as f:
        f.write(json.dumps(audit_entry) + '\n')
    
    print(f"✓ Logged to audit: {event_type}")


def example_trade_execution_notification():
    """Example: Send notification when a trade is executed."""
    print("\n=== Example 1: Trade Execution Notification ===\n")
    
    trade_info = {
        'market': 'Will Bitcoin hit $100k by EOY 2025?',
        'side': 'YES',
        'size': 75.50,
        'price': 0.6234,
        'edge': 0.087,
        'confidence': 0.82,
        'mode': 'DRYRUN',
        'order_id': 'order_12345'
    }
    
    notifier = NotificationSystem()
    success = notifier.send_trade_confirmation(trade_info)
    
    if success:
        log_to_audit('trade_notification_sent', {
            'market': trade_info['market'],
            'size': trade_info['size'],
            'mode': trade_info['mode']
        })
    
    print(f"Trade notification sent: {success}")


def example_edge_detection_notification():
    """Example: Detect new opportunities and send alert."""
    print("\n=== Example 2: Edge Detection Alert ===\n")
    
    opportunities = [
        {'market': 'Will Republicans win House in 2024?', 'edge': 0.095, 'confidence': 0.88},
        {'market': 'Will Fed cut rates in December?', 'edge': 0.065, 'confidence': 0.75},
        {'market': 'Will Apple reach $200 by EOY?', 'edge': 0.058, 'confidence': 0.71}
    ]
    
    quality_opps = [o for o in opportunities if o['edge'] > 0.05 and o['confidence'] > 0.70]
    
    if quality_opps:
        success = send_edge_alert(quality_opps)
        
        if success:
            log_to_audit('edge_alert_sent', {
                'count': len(quality_opps),
                'avg_edge': sum(o['edge'] for o in quality_opps) / len(quality_opps)
            })
        
        print(f"Edge alert sent: {success} ({len(quality_opps)} opportunities)")


def main():
    """Run all integration examples."""
    print("=" * 70)
    print("Telegram Notification Integration Examples")
    print("=" * 70)
    
    LOGS_DIR.mkdir(exist_ok=True)
    
    example_trade_execution_notification()
    example_edge_detection_notification()
    
    print("\n" + "=" * 70)
    print("All examples completed!")
    print("=" * 70)


if __name__ == "__main__":
    main()
