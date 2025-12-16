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

try:
    from autonomous.phone_provider import PhoneProvider
    PHONE_AVAILABLE = True
except:
    PHONE_AVAILABLE = False
    print("⚠️  Phone provider not available")

try:
    from autonomous.sms_provider_manager import SMSProviderManager
    SMS_MULTI_PROVIDER_AVAILABLE = True
except:
    SMS_MULTI_PROVIDER_AVAILABLE = False
    print("⚠️  Multi-provider SMS manager not available")

STATE_FILE = Path(__file__).parent.parent / 'state' / 'messaging_bridge.json'


class MessagingBridge:
    """Unified messaging system for all notifications."""

    def __init__(self):
        self.telegram = TelegramNotifier() if TELEGRAM_AVAILABLE else None
        self.whatsapp = WhatsAppNotifier() if WHATSAPP_AVAILABLE else None
        self.phone = PhoneProvider() if PHONE_AVAILABLE else None  # For voice calls only
        self.sms = SMSProviderManager() if SMS_MULTI_PROVIDER_AVAILABLE else None  # Multi-provider SMS
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
        Send notification via appropriate channel with robust failover.

        Args:
            message: Message to send
            priority: 'critical' or 'normal'
            channel: 'telegram', 'whatsapp', 'both', or 'all'

        Routing (with multi-provider cellular failover):
            Critical Priority:
                1. WhatsApp (instant app notification)
                2. Multi-Provider SMS (Twilio → AWS SNS → Vonage → Plivo → TextBelt)
                3. Voice Call (if SMS fails - ultimate failover via Twilio)
                4. Telegram (last resort)

            Normal Priority:
                1. Telegram (convenient, non-urgent)
                2. Multi-Provider SMS (automatic failover across 5 providers)
                3. WhatsApp (last resort)
        """
        success = False

        if priority == 'critical':
            # Critical → Multi-channel with cellular failover for robustness

            # Try WhatsApp first (instant if app is open)
            if channel in ['whatsapp', 'both', 'all'] and self.whatsapp:
                if self.whatsapp.send_message(message):
                    self.state['whatsapp_sent'] += 1
                    success = True

            # Multi-Provider SMS failover - most robust (works without internet)
            # Tries: Twilio → AWS SNS → Vonage → Plivo → TextBelt
            if not success and self.sms:
                sms_success, provider = self.sms.send_sms(to_number=self._get_phone_number(), message=message, priority='critical')
                if sms_success:
                    self.state['sms_sent'] = self.state.get('sms_sent', 0) + 1
                    self.state[f'sms_via_{provider}'] = self.state.get(f'sms_via_{provider}', 0) + 1
                    success = True

            # Voice call - ultimate failover for TRUE emergencies
            if not success and self.phone and channel == 'all':
                if self.phone.make_voice_call(message):
                    self.state['calls_made'] = self.state.get('calls_made', 0) + 1
                    success = True

            # Telegram last resort
            if not success and self.telegram:
                if self.telegram.send_message(f"🚨 {message}"):
                    self.state['telegram_sent'] += 1
                    success = True

        else:
            # Normal → Telegram preferred, SMS failover

            # Try Telegram first (convenient for regular updates)
            if channel in ['telegram', 'both', 'all'] and self.telegram:
                if self.telegram.send_message(message):
                    self.state['telegram_sent'] += 1
                    success = True

            # Multi-Provider SMS failover if Telegram unavailable
            # Automatically tries all providers until one succeeds
            if not success and self.sms:
                sms_success, provider = self.sms.send_sms(to_number=self._get_phone_number(), message=message, priority='normal')
                if sms_success:
                    self.state['sms_sent'] = self.state.get('sms_sent', 0) + 1
                    self.state[f'sms_via_{provider}'] = self.state.get(f'sms_via_{provider}', 0) + 1
                    success = True

            # WhatsApp last resort
            if not success and channel in ['both', 'all'] and self.whatsapp:
                if self.whatsapp.send_message(message):
                    self.state['whatsapp_sent'] += 1
                    success = True

        if success:
            self.state['total_notifications'] += 1
            self.save_state()

        return success

    def _get_phone_number(self) -> str:
        """Get phone number from configuration."""
        # Try multi-provider config first
        env_file = Path(__file__).parent.parent / '.env.sms_providers'
        if env_file.exists():
            for line in env_file.read_text().splitlines():
                if line.startswith('YOUR_PHONE_NUMBER='):
                    return line.split('=')[1].strip().strip('"')

        # Fall back to legacy config
        env_file = Path(__file__).parent.parent / '.env.handsoff_phone'
        if env_file.exists():
            for line in env_file.read_text().splitlines():
                if line.startswith('YOUR_PHONE_NUMBER='):
                    return line.split('=')[1].strip().strip('"')

        return ''

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

        if self.sms:
            available_providers = [p for p in self.sms.providers if self.sms._is_provider_available(p)]
            print(f"Multi-Provider SMS: ✓ ({len(available_providers)} providers)")
            for p in available_providers:
                print(f"  • {p['name']} (${p.get('cost_per_sms', 0):.4f}/SMS)")
        else:
            print(f"Multi-Provider SMS: ✗")

        print(f"Voice Calls: {'✓' if self.phone else '✗'}")
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
