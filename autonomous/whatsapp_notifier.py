#!/usr/bin/env python3
"""
WhatsApp Notifier - System notifications via WhatsApp

Sends real-time updates about:
- Trading activity
- Bounty status
- System health
- Critical alerts

Uses Twilio API for reliable message delivery.
Alternative: whatsapp-web.js for direct WhatsApp Web access.
"""

import os
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional
import subprocess

# Load credentials
env_file = Path(__file__).parent.parent / ".env.handsoff_whatsapp"
if env_file.exists():
    for line in env_file.read_text().splitlines():
        if line.strip() and not line.startswith('#') and '=' in line:
            key, value = line.split('=', 1)
            os.environ[key.strip()] = value.strip().strip('"')

WHATSAPP_PHONE = os.getenv('WHATSAPP_PHONE', '')
TWILIO_ACCOUNT_SID = os.getenv('TWILIO_ACCOUNT_SID', '')
TWILIO_AUTH_TOKEN = os.getenv('TWILIO_AUTH_TOKEN', '')
TWILIO_WHATSAPP_NUMBER = os.getenv('TWILIO_WHATSAPP_NUMBER', '')

STATE_FILE = Path(__file__).parent.parent / 'state' / 'whatsapp_notifier.json'


class WhatsAppNotifier:
    """Send notifications via WhatsApp."""

    def __init__(self):
        self.phone = WHATSAPP_PHONE
        self.account_sid = TWILIO_ACCOUNT_SID
        self.auth_token = TWILIO_AUTH_TOKEN
        self.from_number = TWILIO_WHATSAPP_NUMBER
        self.load_state()

    def load_state(self):
        """Load notifier state."""
        if STATE_FILE.exists():
            self.state = json.loads(STATE_FILE.read_text())
        else:
            self.state = {
                'messages_sent': 0,
                'last_notification': None,
                'notifications': []
            }

    def save_state(self):
        """Save notifier state."""
        STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
        STATE_FILE.write_text(json.dumps(self.state, indent=2))

    def send_message(self, text: str) -> bool:
        """Send a message via WhatsApp using Twilio."""
        if not all([self.phone, self.account_sid, self.auth_token, self.from_number]):
            print("⚠️  WhatsApp credentials not configured")
            return False

        try:
            # Use Twilio API via curl (Python twilio library may not be installed)
            import requests

            url = f"https://api.twilio.com/2010-04-01/Accounts/{self.account_sid}/Messages.json"

            data = {
                'From': f'whatsapp:{self.from_number}',
                'To': f'whatsapp:{self.phone}',
                'Body': text
            }

            response = requests.post(
                url,
                data=data,
                auth=(self.account_sid, self.auth_token),
                timeout=10
            )

            if response.status_code == 201:
                self.state['messages_sent'] += 1
                self.state['last_notification'] = datetime.now(timezone.utc).isoformat()
                self.state['notifications'].append({
                    'timestamp': datetime.now(timezone.utc).isoformat(),
                    'text': text[:100]
                })
                self.save_state()
                print(f"✓ WhatsApp message sent")
                return True
            else:
                print(f"✗ Twilio API error: {response.status_code} - {response.text}")
                return False

        except ImportError:
            print("⚠️  requests library not available, install with: pip install requests")
            return False
        except Exception as e:
            print(f"✗ Failed to send WhatsApp message: {e}")
            return False


# Convenience functions
def notify(message: str) -> bool:
    """Send a notification to WhatsApp."""
    notifier = WhatsAppNotifier()
    return notifier.send_message(message)


def notify_trade(action: str, market: str, amount: float, outcome: str):
    """Notify about a trade."""
    message = f"""💰 Trade Executed

Action: {action}
Market: {market}
Amount: ${amount:.2f}
Outcome: {outcome}

Time: {datetime.now(timezone.utc).strftime('%H:%M UTC')}"""

    return notify(message)


def notify_bounty(pr_num: int, status: str, details: str):
    """Notify about bounty status."""
    message = f"""🎯 Bounty Update

PR #{pr_num}: {status}

{details}

Time: {datetime.now(timezone.utc).strftime('%H:%M UTC')}"""

    return notify(message)


def notify_critical(alert: str, details: str):
    """Send critical alert."""
    message = f"""🚨 CRITICAL ALERT

{alert}

{details}

Time: {datetime.now(timezone.utc).strftime('%H:%M UTC')}"""

    return notify(message)


def main():
    """Run WhatsApp notifier."""
    import sys

    notifier = WhatsAppNotifier()

    if len(sys.argv) > 1 and sys.argv[1] == '--test':
        # Test message
        success = notifier.send_message("🤖 WhatsApp notifier test successful!")
        print("✓ Test message sent" if success else "✗ Test failed")
    else:
        # Send startup notification
        notifier.send_message("""🚀 Hands-Off System Online

All systems operational.
You'll receive updates here automatically.""")


if __name__ == '__main__':
    main()
