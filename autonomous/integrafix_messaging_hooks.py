#!/usr/bin/env python3
"""
INTEGRAFIX Messaging Hooks

Patches existing INTEGRAFIX components to add messaging notifications
without modifying original files.

This is the glue layer that wires messaging into the live system.
"""

import sys
import json
from pathlib import Path
from datetime import datetime, timezone

# Add integrafix to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from integrafix.messaging_integration import (
    notify_trade,
    notify_trade_execution,
    notify_trade_win,
    notify_pr_status,
    notify_process_down,
    notify_process_restart,
    notify
)


class MessagingHooks:
    """Hooks that wire into INTEGRAFIX components."""

    @staticmethod
    def hook_money_printer():
        """
        Hook Money Printer to send trade notifications.

        Monitors money_printer.log and sends notifications for significant trades.
        """
        log_file = Path(__file__).parent.parent / 'logs' / 'money_printer.log'

        if not log_file.exists():
            return

        # Read last 20 lines
        lines = log_file.read_text().splitlines()[-20:]

        for line in lines:
            # Look for execution lines
            if 'EXECUTED' in line and 'already_notified' not in line:
                # Parse trade details (simplified)
                if '$' in line:
                    # Extract and notify
                    notify(
                        f"💰 Money Printer: {line[-150:]}",
                        priority='normal',
                        channel='telegram'
                    )

                    # Mark as notified (append to line in memory, not file)
                    # In production, track in state file

    @staticmethod
    def hook_pr_email_bridge():
        """
        Hook PR Email Bridge to send bounty notifications.

        Watches for PR status changes and notifies.
        """
        state_file = Path(__file__).parent.parent / 'state' / 'pr_email_bridge.json'

        if not state_file.exists():
            return

        data = json.loads(state_file.read_text())

        # Check for recent PR activity
        for pr_data in data.get('monitored_prs', []):
            pr_num = pr_data.get('number')
            status = pr_data.get('state')
            last_notified = pr_data.get('last_notified_status')

            # If status changed, notify
            if status != last_notified and status in ['merged', 'approved']:
                notify_pr_status(
                    pr_num,
                    status.upper(),
                    f"PR #{pr_num} {status}!"
                )

                # Update state (in production)
                pr_data['last_notified_status'] = status

    @staticmethod
    def hook_self_healer():
        """
        Hook Self Healer to send process failure notifications.

        Monitors for process restarts and sends alerts.
        """
        state_file = Path(__file__).parent.parent / 'state' / 'self_healer.json'

        if not state_file.exists():
            return

        data = json.loads(state_file.read_text())

        # Check for recent restarts
        recent_restarts = data.get('recent_restarts', [])

        for restart in recent_restarts[-5:]:  # Last 5
            if not restart.get('notified'):
                notify_process_restart(
                    restart.get('process', 'Unknown'),
                    restart.get('new_pid', 0)
                )

                # Mark as notified
                restart['notified'] = True

        # Save state
        state_file.write_text(json.dumps(data, indent=2))

    @staticmethod
    def hook_email_handler():
        """
        Hook Email Handler to send processing summaries.

        Notifies about email batches processed.
        """
        state_file = Path(__file__).parent.parent / 'state' / 'email_handler.json'

        if not state_file.exists():
            return

        data = json.loads(state_file.read_text())

        emails_processed = data.get('emails_processed', 0)
        last_notified_count = data.get('last_notified_count', 0)

        # If significant batch processed (100+), notify
        if emails_processed - last_notified_count >= 100:
            bounty_count = len([a for a in data.get('actions_taken', [])
                               if a.get('action_taken') != 'monitored'])

            notify(
                f"📧 Email Update\n\nProcessed: {emails_processed - last_notified_count} emails\nBounty-related: {bounty_count}\n\nInbox staying clean!",
                priority='normal',
                channel='telegram'
            )

            data['last_notified_count'] = emails_processed
            state_file.write_text(json.dumps(data, indent=2))

    @staticmethod
    def run_all_hooks():
        """Run all messaging hooks."""
        try:
            MessagingHooks.hook_money_printer()
        except Exception as e:
            print(f"Money Printer hook error: {e}")

        try:
            MessagingHooks.hook_pr_email_bridge()
        except Exception as e:
            print(f"PR Email Bridge hook error: {e}")

        try:
            MessagingHooks.hook_self_healer()
        except Exception as e:
            print(f"Self Healer hook error: {e}")

        try:
            MessagingHooks.hook_email_handler()
        except Exception as e:
            print(f"Email Handler hook error: {e}")


def continuous_monitoring(interval: int = 60):
    """
    Continuously run hooks to check for events to notify.

    This runs in parallel with messaging_bridge.
    """
    import time

    print("Starting INTEGRAFIX messaging hooks...")
    print("Monitoring all components for notification events")
    print()

    while True:
        try:
            MessagingHooks.run_all_hooks()
        except Exception as e:
            print(f"Error in hooks: {e}")

        time.sleep(interval)


def main():
    """Run messaging hooks."""
    import sys

    if '--continuous' in sys.argv:
        continuous_monitoring()
    elif '--test' in sys.argv:
        print("Running test hooks...")
        MessagingHooks.run_all_hooks()
        print("✓ Hooks executed")
    else:
        print("Usage:")
        print("  --continuous   Run hooks continuously")
        print("  --test         Run hooks once")


if __name__ == '__main__':
    main()
