#!/usr/bin/env python3
"""
Unified Messaging Bridge - Coordinates Telegram and WhatsApp notifications

Routes messages to the appropriate channel based on priority:
- Critical alerts → WhatsApp (immediate attention needed)
- Regular updates → Telegram (convenient, non-urgent)
- System commands → Telegram (interactive)

Monitors system events and sends appropriate notifications.
"""

import json
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, Dict, Any
import subprocess

# Import notifiers
try:
    from autonomous.telegram_notifier import TelegramNotifier, notify as telegram_notify
    TELEGRAM_AVAILABLE = True
except:
    TELEGRAM_AVAILABLE = False
    print("⚠️  Telegram notifier not available")

try:
    from autonomous.whatsapp_notifier import WhatsAppNotifier, notify as whatsapp_notify
    WHATSAPP_AVAILABLE = True
except:
    WHATSAPP_AVAILABLE = False
    print("⚠️  WhatsApp notifier not available")

STATE_FILE = Path(__file__).parent.parent / 'state' / 'messaging_bridge.json'


class MessagingBridge:
    """Unified messaging system for all notifications."""

    def __init__(self):
        self.telegram = TelegramNotifier() if TELEGRAM_AVAILABLE else None
        self.whatsapp = WhatsAppNotifier() if WHATSAPP_AVAILABLE else None
        self.load_state()

    def load_state(self):
        """Load bridge state."""
        if STATE_FILE.exists():
            self.state = json.loads(STATE_FILE.read_text())
        else:
            self.state = {
                'total_notifications': 0,
                'telegram_sent': 0,
                'whatsapp_sent': 0,
                'last_check': None,
                'monitored_events': []
            }

    def save_state(self):
        """Save bridge state."""
        STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
        STATE_FILE.write_text(json.dumps(self.state, indent=2))

    def notify(self, message: str, priority: str = 'normal', channel: str = 'both') -> bool:
        """
        Send notification via appropriate channel.

        Args:
            message: Message to send
            priority: 'critical' or 'normal'
            channel: 'telegram', 'whatsapp', or 'both'
        """
        success = False

        if priority == 'critical':
            # Critical → WhatsApp first, fallback to Telegram
            if channel in ['whatsapp', 'both'] and self.whatsapp:
                if self.whatsapp.send_message(message):
                    self.state['whatsapp_sent'] += 1
                    success = True

            if not success and self.telegram:
                if self.telegram.send_message(f"🚨 {message}"):
                    self.state['telegram_sent'] += 1
                    success = True

        else:
            # Normal → Telegram first, fallback to WhatsApp
            if channel in ['telegram', 'both'] and self.telegram:
                if self.telegram.send_message(message):
                    self.state['telegram_sent'] += 1
                    success = True

            if not success and channel == 'both' and self.whatsapp:
                if self.whatsapp.send_message(message):
                    self.state['whatsapp_sent'] += 1
                    success = True

        if success:
            self.state['total_notifications'] += 1
            self.save_state()

        return success

    def monitor_system_events(self):
        """Monitor system for events worth notifying about."""
        # Check money printer logs for significant trades
        self.check_money_printer()

        # Check bounty status
        self.check_bounties()

        # Check system health
        self.check_system_health()

        # Check email handler
        self.check_email_handler()

        self.state['last_check'] = datetime.now(timezone.utc).isoformat()
        self.save_state()

    def check_money_printer(self):
        """Check for significant trading events."""
        log_file = Path(__file__).parent.parent / 'logs' / 'money_printer.log'

        if not log_file.exists():
            return

        # Check for wins > $10
        try:
            recent_lines = log_file.read_text().splitlines()[-50:]

            for line in recent_lines:
                if 'WIN' in line and '$' in line:
                    # Parse amount (simplified)
                    if 'already_notified' not in line:  # Avoid duplicate notifications
                        self.notify(f"💰 Money Printer: {line[-100:]}", priority='normal')
        except:
            pass

    def check_bounties(self):
        """Check for bounty status updates."""
        # Check GitHub API for PR status changes
        # This is a simplified version - full implementation would track state changes

        try:
            result = subprocess.run(
                ['gh', 'pr', 'list', '--repo', 'cortexlinux/cortex', '--state', 'all',
                 '--author', '@me', '--json', 'number,state,title'],
                capture_output=True,
                text=True,
                timeout=10
            )

            if result.returncode == 0:
                prs = json.loads(result.stdout)

                for pr in prs:
                    pr_num = pr['number']
                    state = pr['state']

                    # Check if state changed (simplified)
                    if state == 'MERGED' and pr_num not in self.state.get('merged_prs', []):
                        self.notify(
                            f"🎉 PR #{pr_num} MERGED!\n\n{pr['title']}\n\nBounty is claimable!",
                            priority='critical'
                        )

                        if 'merged_prs' not in self.state:
                            self.state['merged_prs'] = []
                        self.state['merged_prs'].append(pr_num)
                        self.save_state()

        except:
            pass

    def check_system_health(self):
        """Check if any critical processes are down."""
        result = subprocess.run(['ps', 'aux'], capture_output=True, text=True)
        procs = result.stdout

        critical_processes = [
            ('money_printer', 'Money Printer'),
            ('backend_loop', 'Backend Loop'),
            ('self_healer', 'Self Healer'),
        ]

        for proc_name, display_name in critical_processes:
            if proc_name not in procs:
                # Process is down
                if f'down_{proc_name}' not in self.state.get('alerted_downs', []):
                    self.notify(
                        f"⚠️ {display_name} is DOWN\n\nProcess: {proc_name}\n\nCheck immediately!",
                        priority='critical'
                    )

                    if 'alerted_downs' not in self.state:
                        self.state['alerted_downs'] = []
                    self.state['alerted_downs'].append(f'down_{proc_name}')
                    self.save_state()

    def check_email_handler(self):
        """Check email handler stats."""
        email_state_file = Path(__file__).parent.parent / 'state' / 'email_handler.json'

        if email_state_file.exists():
            email_state = json.loads(email_state_file.read_text())

            # Notify if significant email processing happened
            emails_processed = email_state.get('emails_processed', 0)

            if emails_processed > self.state.get('last_email_count', 0) + 50:
                self.notify(
                    f"📧 Email Update\n\nProcessed: {emails_processed} total\n\nInbox being cleaned!",
                    priority='normal'
                )

                self.state['last_email_count'] = emails_processed
                self.save_state()

    def continuous_monitoring(self, interval: int = 300):
        """Continuously monitor and send notifications."""
        print(f"Starting messaging bridge (checking every {interval}s)")
        print(f"Telegram: {'✓' if self.telegram else '✗'}")
        print(f"WhatsApp: {'✓' if self.whatsapp else '✗'}")
        print()

        # Send startup notification
        self.notify("🚀 *Messaging Bridge Active*\n\nMonitoring all systems for updates.")

        while True:
            try:
                # Process Telegram commands if available
                if self.telegram:
                    self.telegram.process_updates()

                # Monitor system events
                self.monitor_system_events()

            except Exception as e:
                print(f"Error in monitoring loop: {e}")

            time.sleep(interval)


def main():
    """Run messaging bridge."""
    import sys

    bridge = MessagingBridge()

    if len(sys.argv) > 1:
        if sys.argv[1] == '--continuous':
            bridge.continuous_monitoring()
        elif sys.argv[1] == '--test':
            print("Sending test notifications...")

            if bridge.telegram:
                bridge.notify("✓ Telegram test", channel='telegram')
                print("✓ Telegram sent")

            if bridge.whatsapp:
                bridge.notify("✓ WhatsApp test", channel='whatsapp')
                print("✓ WhatsApp sent")

            if not bridge.telegram and not bridge.whatsapp:
                print("✗ No messaging channels configured")

    else:
        print("Usage:")
        print("  --continuous    Start monitoring loop")
        print("  --test          Send test messages")


if __name__ == '__main__':
    main()
