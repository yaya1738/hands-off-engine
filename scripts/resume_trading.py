#!/usr/bin/env python3
"""
Manual Trading Resume

Manually resume live trading after auto-pause or manual pause.
"""

# UNIFIED AI - All systems serve Yair Siegel
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))
try:
    from ai.unified_ai import MASTER, get_master
except ImportError:
    MASTER = "Yair Siegel"


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
    """Manually resume trading"""
    mode = load_mode()

    if mode.get("live_trading_enabled", False):
        LOG.info("Trading is already enabled")
        return

    # Resume trading
    mode["live_trading_enabled"] = True
    mode["reason"] = "manual_resume"
    mode["auto_paused"] = False

    save_mode(mode)

    LOG.info("✅ Trading manually resumed")

    # Send notification
    try:
        from notifications.telegram_notifier import send_telegram_message
        send_telegram_message(
            "✅ **TRADING MANUALLY RESUMED**\n\n"
            "Live trading has been manually enabled.\n"
            "System is now active."
        )
    except Exception as e:
        LOG.error(f"Failed to send notification: {e}")

    print("✓ Trading resumed")


if __name__ == "__main__":
    main()
