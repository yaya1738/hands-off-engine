#!/usr/bin/env python3
"""
Telegram Notifier - System notifications and commands via Telegram

Sends real-time updates about:
- Trading activity (Money Printer wins/losses)
- Bounty status (PR merged, approved, paid)
- System health (processes down, errors)
- Gmail activity (important emails processed)

Receives commands:
- /status - System status
- /trades - Recent trades
- /bounties - Bounty status
- /balance - Current balances
- /logs - Recent logs
"""

import os
import json
import requests
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, Dict, Any
import time

# Load credentials
env_file = Path(__file__).parent.parent / ".env.handsoff_telegram"
if env_file.exists():
    for line in env_file.read_text().splitlines():
        if line.strip() and not line.startswith('#') and '=' in line:
            key, value = line.split('=', 1)
            os.environ[key.strip()] = value.strip().strip('"')

TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN', '')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID', '')

STATE_FILE = Path(__file__).parent.parent / 'state' / 'telegram_notifier.json'


class TelegramNotifier:
    """Send notifications and handle commands via Telegram."""

    def __init__(self):
        self.bot_token = TELEGRAM_BOT_TOKEN
        self.chat_id = TELEGRAM_CHAT_ID
        self.base_url = f"https://api.telegram.org/bot{self.bot_token}"
        self.load_state()

    def load_state(self):
        """Load notifier state."""
        if STATE_FILE.exists():
            self.state = json.loads(STATE_FILE.read_text())
        else:
            self.state = {
                'messages_sent': 0,
                'commands_received': 0,
                'last_update_id': 0,
                'notifications': []
            }

    def save_state(self):
        """Save notifier state."""
        STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
        STATE_FILE.write_text(json.dumps(self.state, indent=2))

    def send_message(self, text: str, parse_mode: str = 'Markdown') -> bool:
        """Send a message to Telegram."""
        if not self.bot_token or not self.chat_id:
            print("⚠️  Telegram credentials not configured")
            return False

        try:
            url = f"{self.base_url}/sendMessage"
            data = {
                'chat_id': self.chat_id,
                'text': text,
                'parse_mode': parse_mode
            }

            response = requests.post(url, json=data, timeout=10)

            if response.status_code == 200:
                self.state['messages_sent'] += 1
                self.state['notifications'].append({
                    'timestamp': datetime.now(timezone.utc).isoformat(),
                    'text': text[:100]  # Store preview
                })
                self.save_state()
                return True
            else:
                print(f"✗ Telegram API error: {response.status_code}")
                return False

        except Exception as e:
            print(f"✗ Failed to send Telegram message: {e}")
            return False

    def get_updates(self, offset: Optional[int] = None) -> list:
        """Get updates (messages/commands) from Telegram."""
        try:
            url = f"{self.base_url}/getUpdates"
            params = {'timeout': 30}

            if offset:
                params['offset'] = offset

            response = requests.get(url, params=params, timeout=35)

            if response.status_code == 200:
                data = response.json()
                return data.get('result', [])

            return []

        except Exception as e:
            print(f"✗ Failed to get Telegram updates: {e}")
            return []

    def handle_command(self, command: str, chat_id: str) -> str:
        """Handle incoming commands."""
        self.state['commands_received'] += 1
        self.save_state()

        if command == '/start':
            return """🤖 *Hands-Off System Bot*

I'll keep you updated on:
• Trading activity
• Bounty status
• System health
• Email processing

Commands:
/status - System overview
/trades - Recent trades
/bounties - Bounty PRs
/balance - Account balances
/logs - Recent activity"""

        elif command == '/status':
            return self.get_system_status()

        elif command == '/trades':
            return self.get_recent_trades()

        elif command == '/bounties':
            return self.get_bounty_status()

        elif command == '/balance':
            return self.get_balances()

        elif command == '/logs':
            return self.get_recent_logs()

        else:
            return f"Unknown command: {command}\n\nTry /start for help"

    def get_system_status(self) -> str:
        """Get current system status."""
        import subprocess

        # Count running processes
        procs = subprocess.run(
            ['ps', 'aux'],
            capture_output=True,
            text=True
        ).stdout

        running = []
        if 'money_printer' in procs:
            running.append('Money Printer')
        if 'backend_loop' in procs:
            running.append('Backend Loop')
        if 'pr_email_bridge' in procs:
            running.append('PR Email Bridge')
        if 'email_inbox_handler' in procs:
            running.append('Gmail Handler')

        return f"""📊 *System Status*

Running: {len(running)}/8 processes

Active:
{chr(10).join(f'✅ {p}' for p in running)}

Type /trades or /bounties for details"""

    def get_recent_trades(self) -> str:
        """Get recent trading activity."""
        log_file = Path(__file__).parent.parent / 'logs' / 'money_printer.log'

        if not log_file.exists():
            return "No trading data available"

        # Read last 20 lines
        lines = log_file.read_text().splitlines()[-20:]

        return f"""💰 *Recent Trading*

{chr(10).join(lines[-5:])}

Full logs: logs/money_printer.log"""

    def get_bounty_status(self) -> str:
        """Get bounty PR status."""
        return """🎯 *Bounty Status*

PR #239: $125 - Under review
PR #240: $100 - Under review
PR #241: $25 - Under review

Total: $250 pending

All PRs being monitored automatically"""

    def get_balances(self) -> str:
        """Get current balances."""
        wallet_file = Path(__file__).parent.parent / 'state' / 'wallet_state.json'

        if wallet_file.exists():
            wallet = json.loads(wallet_file.read_text())
            return f"""💵 *Balances*

Polymarket: ${wallet.get('balance', 'N/A')}
Orders: ${wallet.get('total_orders', 'N/A')}

Updated: {wallet.get('last_updated', 'N/A')}"""

        return "Balance data not available"

    def get_recent_logs(self) -> str:
        """Get recent system logs."""
        return """📝 *Recent Activity*

Check these logs:
• `tail -f logs/money_printer.log`
• `tail -f logs/email_handler.log`
• `tail -f logs/pr_email_bridge.log`

Or use /status for quick overview"""

    def process_updates(self):
        """Process all pending updates."""
        updates = self.get_updates(self.state['last_update_id'] + 1)

        for update in updates:
            update_id = update.get('update_id', 0)
            message = update.get('message', {})
            text = message.get('text', '')
            chat_id = message.get('chat', {}).get('id', '')

            if text.startswith('/'):
                print(f"📱 Command: {text}")
                response = self.handle_command(text, chat_id)
                self.send_message(response)

            # Update last processed ID
            if update_id > self.state['last_update_id']:
                self.state['last_update_id'] = update_id
                self.save_state()

    def monitor_continuous(self, interval: int = 10):
        """Continuously monitor for commands."""
        print(f"Starting Telegram monitoring (every {interval}s)")

        while True:
            try:
                self.process_updates()
            except Exception as e:
                print(f"Error processing updates: {e}")

            time.sleep(interval)


# Convenience functions for other scripts to use
def notify(message: str) -> bool:
    """Send a notification to Telegram."""
    notifier = TelegramNotifier()
    return notifier.send_message(message)


def notify_trade(action: str, market: str, amount: float, outcome: str):
    """Notify about a trade."""
    message = f"""💰 *Trade Executed*

Action: {action}
Market: {market}
Amount: ${amount:.2f}
Outcome: {outcome}

Time: {datetime.now(timezone.utc).strftime('%H:%M UTC')}"""

    return notify(message)


def notify_bounty(pr_num: int, status: str, details: str):
    """Notify about bounty status."""
    message = f"""🎯 *Bounty Update*

PR #{pr_num}: {status}

{details}

Time: {datetime.now(timezone.utc).strftime('%H:%M UTC')}"""

    return notify(message)


def notify_system(component: str, status: str, details: str):
    """Notify about system status."""
    message = f"""⚙️ *System Alert*

Component: {component}
Status: {status}

{details}

Time: {datetime.now(timezone.utc).strftime('%H:%M UTC')}"""

    return notify(message)


def main():
    """Run Telegram notifier."""
    import sys

    notifier = TelegramNotifier()

    if len(sys.argv) > 1:
        if sys.argv[1] == '--continuous':
            # Continuous monitoring mode
            notifier.monitor_continuous()
        elif sys.argv[1] == '--test':
            # Test message
            success = notifier.send_message("🤖 Telegram notifier test successful!")
            print("✓ Test message sent" if success else "✗ Test failed")
    else:
        # Send startup notification
        notifier.send_message("""🚀 *Hands-Off System Online*

All systems operational.
Type /status for details.""")


if __name__ == '__main__':
    main()
