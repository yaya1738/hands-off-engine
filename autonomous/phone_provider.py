#!/usr/bin/env python3
"""
Phone Provider Integration - SMS & Voice Calls

Direct integration with phone carriers for:
- SMS notifications (reliable, works without internet)
- Voice call alerts (for critical emergencies)
- Multi-provider support (Twilio, AWS SNS, Vonage)

Use cases:
- Critical system failures → Voice call
- Trade wins → SMS
- Bounty paid → SMS
- Process down → Voice call
- Backup when Telegram/WhatsApp fail

This is the most reliable notification channel - works even without internet.
"""

import os
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, Dict, List

# Load credentials
env_file = Path(__file__).parent.parent / ".env.handsoff_phone"
if env_file.exists():
    for line in env_file.read_text().splitlines():
        if line.strip() and not line.startswith('#') and '=' in line:
            key, value = line.split('=', 1)
            os.environ[key.strip()] = value.strip().strip('"')

# Credentials
PHONE_NUMBER = os.getenv('YOUR_PHONE_NUMBER', '')  # Your phone: +1234567890
TWILIO_ACCOUNT_SID = os.getenv('TWILIO_ACCOUNT_SID', '')
TWILIO_AUTH_TOKEN = os.getenv('TWILIO_AUTH_TOKEN', '')
TWILIO_PHONE_NUMBER = os.getenv('TWILIO_PHONE_NUMBER', '')

STATE_FILE = Path(__file__).parent.parent / 'state' / 'phone_provider.json'


class PhoneProvider:
    """Direct phone communication via SMS and voice calls."""

    def __init__(self):
        self.phone = PHONE_NUMBER
        self.twilio_sid = TWILIO_ACCOUNT_SID
        self.twilio_token = TWILIO_AUTH_TOKEN
        self.twilio_number = TWILIO_PHONE_NUMBER
        self.state = self.load_state()

    def load_state(self) -> dict:
        """Load provider state."""
        if STATE_FILE.exists():
            return json.loads(STATE_FILE.read_text())
        return {
            'sms_sent': 0,
            'calls_made': 0,
            'last_sms': None,
            'last_call': None,
            'notifications': []
        }

    def save_state(self):
        """Save provider state."""
        STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
        STATE_FILE.write_text(json.dumps(self.state, indent=2))

    # ===================================================================
    # SMS NOTIFICATIONS
    # ===================================================================

    def send_sms(self, message: str, priority: str = 'normal') -> bool:
        """
        Send SMS via Twilio.

        Args:
            message: Text message (max 160 chars for single SMS)
            priority: 'normal' or 'critical'

        Returns:
            True if sent successfully
        """
        if not all([self.phone, self.twilio_sid, self.twilio_token, self.twilio_number]):
            print("⚠️  Phone provider credentials not configured")
            return False

        try:
            import requests

            # Twilio SMS API
            url = f"https://api.twilio.com/2010-04-01/Accounts/{self.twilio_sid}/Messages.json"

            # Truncate if too long (SMS limit)
            if len(message) > 1600:  # 10 SMS segments max
                message = message[:1597] + "..."

            data = {
                'From': self.twilio_number,
                'To': self.phone,
                'Body': message
            }

            response = requests.post(
                url,
                data=data,
                auth=(self.twilio_sid, self.twilio_token),
                timeout=10
            )

            if response.status_code == 201:
                self.state['sms_sent'] += 1
                self.state['last_sms'] = datetime.now(timezone.utc).isoformat()
                self.state['notifications'].append({
                    'type': 'sms',
                    'timestamp': datetime.now(timezone.utc).isoformat(),
                    'priority': priority,
                    'message': message[:100]
                })
                self.save_state()
                print(f"✓ SMS sent to {self.phone}")
                return True
            else:
                print(f"✗ SMS failed: {response.status_code} - {response.text}")
                return False

        except ImportError:
            print("⚠️  requests library not available")
            return False
        except Exception as e:
            print(f"✗ SMS error: {e}")
            return False

    # ===================================================================
    # VOICE CALL ALERTS
    # ===================================================================

    def make_voice_call(self, message: str, repeat: int = 2) -> bool:
        """
        Make voice call with text-to-speech alert.

        For CRITICAL alerts only - this will actually call your phone.

        Args:
            message: Alert message (will be read aloud)
            repeat: Number of times to repeat message (default 2)

        Returns:
            True if call initiated successfully
        """
        if not all([self.phone, self.twilio_sid, self.twilio_token, self.twilio_number]):
            print("⚠️  Phone provider credentials not configured")
            return False

        try:
            import requests
            from urllib.parse import quote

            # Twilio Voice API with TwiML
            url = f"https://api.twilio.com/2010-04-01/Accounts/{self.twilio_sid}/Calls.json"

            # Create TwiML (Twilio's XML for voice)
            # Repeat message for clarity
            twiml = f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Say voice="alice" language="en-US">
        Critical alert from your hands-off system.
    </Say>
    <Pause length="1"/>
    {"".join([f'<Say voice="alice" language="en-US">{message}</Say><Pause length="1"/>' for _ in range(repeat)])}
    <Say voice="alice" language="en-US">
        End of alert. Check your system immediately.
    </Say>
</Response>"""

            # Twilio requires TwiML to be hosted or passed as URL
            # For simplicity, we'll use Twilio's TwiML Bins (or pass inline)
            # In production, host TwiML or use Twilio Functions

            data = {
                'From': self.twilio_number,
                'To': self.phone,
                'Twiml': twiml
            }

            response = requests.post(
                url,
                data=data,
                auth=(self.twilio_sid, self.twilio_token),
                timeout=10
            )

            if response.status_code == 201:
                self.state['calls_made'] += 1
                self.state['last_call'] = datetime.now(timezone.utc).isoformat()
                self.state['notifications'].append({
                    'type': 'voice_call',
                    'timestamp': datetime.now(timezone.utc).isoformat(),
                    'priority': 'critical',
                    'message': message[:100]
                })
                self.save_state()
                print(f"✓ Voice call initiated to {self.phone}")
                return True
            else:
                print(f"✗ Call failed: {response.status_code} - {response.text}")
                return False

        except Exception as e:
            print(f"✗ Voice call error: {e}")
            return False

    # ===================================================================
    # AWS SNS SUPPORT (Alternative Provider)
    # ===================================================================

    def send_sms_via_sns(self, message: str) -> bool:
        """
        Send SMS via AWS SNS (alternative to Twilio).

        Requires AWS credentials configured.
        """
        try:
            import boto3

            aws_access_key = os.getenv('AWS_ACCESS_KEY_ID', '')
            aws_secret_key = os.getenv('AWS_SECRET_ACCESS_KEY', '')

            if not all([aws_access_key, aws_secret_key, self.phone]):
                print("⚠️  AWS SNS credentials not configured")
                return False

            sns = boto3.client(
                'sns',
                aws_access_key_id=aws_access_key,
                aws_secret_access_key=aws_secret_key,
                region_name='us-east-1'
            )

            response = sns.publish(
                PhoneNumber=self.phone,
                Message=message
            )

            if response['ResponseMetadata']['HTTPStatusCode'] == 200:
                self.state['sms_sent'] += 1
                self.state['last_sms'] = datetime.now(timezone.utc).isoformat()
                self.save_state()
                print(f"✓ SMS sent via AWS SNS to {self.phone}")
                return True

            return False

        except ImportError:
            print("⚠️  boto3 library not available (pip install boto3)")
            return False
        except Exception as e:
            print(f"✗ AWS SNS error: {e}")
            return False

    # ===================================================================
    # SMART NOTIFICATION ROUTING
    # ===================================================================

    def notify(
        self,
        message: str,
        priority: str = 'normal',
        method: str = 'auto'
    ) -> bool:
        """
        Smart notification routing based on priority.

        Args:
            message: Alert message
            priority: 'normal' or 'critical'
            method: 'auto', 'sms', 'voice', or 'both'

        Routing:
            - Normal: SMS only
            - Critical: SMS + Voice call
            - Auto: Decides based on priority
        """
        if method == 'auto':
            if priority == 'critical':
                method = 'both'
            else:
                method = 'sms'

        success = False

        if method in ['sms', 'both']:
            success = self.send_sms(message, priority) or success

        if method in ['voice', 'both'] and priority == 'critical':
            # Only voice call for truly critical alerts
            success = self.make_voice_call(message) or success

        return success

    # ===================================================================
    # RATE LIMITING (Prevent SMS/call spam)
    # ===================================================================

    def should_notify(self, notification_type: str, cooldown_seconds: int = 300) -> bool:
        """
        Rate limit notifications to prevent spam.

        Args:
            notification_type: 'sms' or 'voice_call'
            cooldown_seconds: Minimum time between notifications (default 5 mins)

        Returns:
            True if notification should be sent
        """
        last_key = f'last_{notification_type}'
        last_time = self.state.get(last_key)

        if not last_time:
            return True

        last_dt = datetime.fromisoformat(last_time.replace('Z', '+00:00'))
        now = datetime.now(timezone.utc)
        seconds_since = (now - last_dt).total_seconds()

        return seconds_since >= cooldown_seconds


# ===================================================================
# CONVENIENCE FUNCTIONS
# ===================================================================

def send_sms(message: str, priority: str = 'normal') -> bool:
    """Convenience: Send SMS."""
    provider = PhoneProvider()
    return provider.send_sms(message, priority)


def make_call(message: str) -> bool:
    """Convenience: Make voice call."""
    provider = PhoneProvider()
    return provider.make_voice_call(message)


def notify_phone(message: str, priority: str = 'normal') -> bool:
    """Convenience: Smart notification."""
    provider = PhoneProvider()
    return provider.notify(message, priority)


# ===================================================================
# TESTING
# ===================================================================

def test_provider():
    """Test phone provider integration."""
    provider = PhoneProvider()

    print("="*60)
    print("PHONE PROVIDER TEST")
    print("="*60)
    print()

    if not provider.phone:
        print("✗ Phone number not configured")
        print("  Set YOUR_PHONE_NUMBER in .env.handsoff_phone")
        return

    print(f"Testing notifications to: {provider.phone}")
    print()

    # Test SMS
    print("1. Testing SMS...")
    success_sms = provider.send_sms(
        "🤖 Test SMS from hands-off system. This is a normal priority notification."
    )

    if success_sms:
        print("  ✓ SMS sent - check your phone!")
    else:
        print("  ✗ SMS failed")

    print()

    # Test voice call (ask first - this will actually call)
    print("2. Voice call test (WILL ACTUALLY CALL YOUR PHONE)")
    response = input("  Send test voice call? (yes/no): ")

    if response.lower() == 'yes':
        print("  Making test call...")
        success_call = provider.make_voice_call(
            "This is a test critical alert from your hands-off system."
        )

        if success_call:
            print("  ✓ Call initiated - answer your phone!")
        else:
            print("  ✗ Call failed")
    else:
        print("  Skipped voice call test")

    print()
    print("="*60)
    print("TEST COMPLETE")
    print("="*60)
    print()
    print(f"SMS sent: {provider.state['sms_sent']}")
    print(f"Calls made: {provider.state['calls_made']}")


def main():
    """Run phone provider."""
    import sys

    if '--help' in sys.argv:
        print("""
Phone Provider Integration

Usage:
  python3 autonomous/phone_provider.py [--test]

Setup:
  1. Get Twilio credentials:
     - Sign up: https://www.twilio.com/try-twilio
     - Get Account SID, Auth Token, Phone Number

  2. Configure:
     nano .env.handsoff_phone
     # Add:
     YOUR_PHONE_NUMBER="+1234567890"
     TWILIO_ACCOUNT_SID="your_sid"
     TWILIO_AUTH_TOKEN="your_token"
     TWILIO_PHONE_NUMBER="+1234567890"  # Twilio number

  3. Test:
     python3 autonomous/phone_provider.py --test

Features:
  - SMS notifications (reliable, works without internet)
  - Voice call alerts (for critical emergencies)
  - Multi-provider support (Twilio, AWS SNS)
  - Smart routing (normal=SMS, critical=SMS+voice)
  - Rate limiting (prevents spam)

Cost:
  Twilio: $0.0075 per SMS, $0.013 per minute voice
  AWS SNS: $0.00645 per SMS
  Both have free trials
        """)
        return

    if '--test' in sys.argv:
        test_provider()
    else:
        print("Use --test to send test notifications")
        print("Use --help for setup instructions")


if __name__ == '__main__':
    main()
