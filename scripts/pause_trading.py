#!/usr/bin/env python3
"""
Manual Trading Pause

Manually pause live trading. This sets auto_paused=False to prevent
auto-resume from overriding the manual decision.
"""

import sys
import os
import logging

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from executor.trading_safeguards import load_mode, save_mode

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
LOG = logging.getLogger(__name__)


def main():
    """Manually pause trading"""
    mode = load_mode()

    if not mode.get("live_trading_enabled", False):
        LOG.info("Trading is already paused")
        return

    # Pause trading
    mode["live_trading_enabled"] = False
    mode["reason"] = "manual_pause"
    mode["auto_paused"] = False  # Mark as manual pause

    save_mode(mode)

    LOG.info("🛑 Trading manually paused")

    # Send notification
    try:
        from notifications.telegram_notifier import send_telegram_message
        send_telegram_message(
            "🛑 **TRADING MANUALLY PAUSED**\n\n"
            "Live trading has been manually disabled.\n"
            "Will not auto-resume until manually resumed."
        )
    except Exception as e:
        LOG.error(f"Failed to send notification: {e}")

    print("✓ Trading paused")


if __name__ == "__main__":
    main()
