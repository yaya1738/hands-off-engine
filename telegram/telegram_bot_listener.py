#!/usr/bin/env python3
"""
Telegram Bot Listener - Simple polling-based command handler

Listens for commands from user via Telegram bot using polling.
Processes commands using telegram_command_bot.py logic.

Setup:
1. Get bot token from @BotFather on Telegram
2. Set environment variable: TELEGRAM_BOT_TOKEN
3. Set environment variable: TELEGRAM_CHAT_ID (your chat ID)
4. Run: python3 telegram_bot_listener.py

Or deploy as systemd service for 24/7 operation.
"""

import os
import sys
import time
import logging
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from telegram_command_bot import TelegramCommandBot

# Configuration
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
ALLOWED_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")  # Optional - restrict to specific user
POLL_INTERVAL = 2  # seconds
LOG_FILE = "/var/log/telegram-bot.log"

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class SimpleTelegramBot:
    """Simple polling-based Telegram bot using requests library."""

    def __init__(self, token: str):
        self.token = token
        self.base_url = f"https://api.telegram.org/bot{token}"
        self.offset = 0
        self.command_bot = TelegramCommandBot()

        # Check if requests is available
        try:
            import requests
            self.requests = requests
        except ImportError:
            logger.error("requests library not found. Install with: pip3 install requests")
            sys.exit(1)

    def get_updates(self, timeout=30):
        """Get updates from Telegram using long polling."""
        try:
            url = f"{self.base_url}/getUpdates"
            params = {
                "offset": self.offset,
                "timeout": timeout
            }

            response = self.requests.get(url, params=params, timeout=timeout + 5)
            response.raise_for_status()

            data = response.json()
            if not data.get("ok"):
                logger.error(f"Telegram API error: {data}")
                return []

            return data.get("result", [])

        except Exception as e:
            logger.error(f"Error getting updates: {e}")
            return []

    def send_message(self, chat_id: int, text: str):
        """Send message to Telegram chat."""
        try:
            url = f"{self.base_url}/sendMessage"
            data = {
                "chat_id": chat_id,
                "text": text,
                "parse_mode": "Markdown"
            }

            response = self.requests.post(url, json=data, timeout=10)
            response.raise_for_status()

            return True

        except Exception as e:
            logger.error(f"Error sending message: {e}")
            return False

    def process_update(self, update):
        """Process a single update from Telegram."""
        try:
            # Extract message
            message = update.get("message")
            if not message:
                return

            chat_id = message.get("chat", {}).get("id")
            text = message.get("text", "")
            username = message.get("from", {}).get("username", "unknown")

            # Check if chat is allowed (if ALLOWED_CHAT_ID is set)
            if ALLOWED_CHAT_ID and str(chat_id) != ALLOWED_CHAT_ID:
                logger.warning(f"Ignoring message from unauthorized chat: {chat_id}")
                return

            # Only process commands (start with /)
            if not text.startswith("/"):
                return

            logger.info(f"Received command from {username} (chat {chat_id}): {text}")

            # Process command using command bot
            response = self.command_bot.process_command(text)

            # Send response
            self.send_message(chat_id, response)
            logger.info(f"Sent response ({len(response)} chars)")

        except Exception as e:
            logger.error(f"Error processing update: {e}")

    def run(self):
        """Main loop - poll for updates and process commands."""
        logger.info("Telegram Bot Listener starting...")
        logger.info(f"Poll interval: {POLL_INTERVAL}s")

        if ALLOWED_CHAT_ID:
            logger.info(f"Restricted to chat ID: {ALLOWED_CHAT_ID}")
        else:
            logger.warning("No ALLOWED_CHAT_ID set - bot will respond to any user!")

        while True:
            try:
                # Get updates
                updates = self.get_updates()

                # Process each update
                for update in updates:
                    self.process_update(update)

                    # Update offset to mark update as processed
                    update_id = update.get("update_id")
                    if update_id:
                        self.offset = update_id + 1

                # Brief pause between polls (if no updates received)
                if not updates:
                    time.sleep(POLL_INTERVAL)

            except KeyboardInterrupt:
                logger.info("Shutting down gracefully...")
                break
            except Exception as e:
                logger.error(f"Error in main loop: {e}")
                time.sleep(10)  # Wait before retrying


def test_mode():
    """Test mode - simulate commands without actual Telegram connection."""
    print("Running in TEST MODE (no Telegram connection)\n")

    bot = TelegramCommandBot()

    test_commands = [
        "/status",
        "/metrics",
        "/health",
        "/agents",
        "/help"
    ]

    for cmd in test_commands:
        print(f"\n{'='*60}")
        print(f"Command: {cmd}")
        print(f"{'='*60}")
        response = bot.process_command(cmd)
        print(response)


def main():
    """Entry point."""
    import sys

    # Check for test mode
    if len(sys.argv) > 1 and sys.argv[1] == "--test":
        test_mode()
        return 0

    # Check for required environment variables
    if not BOT_TOKEN:
        print("Error: TELEGRAM_BOT_TOKEN environment variable not set")
        print("\nSetup instructions:")
        print("1. Create bot with @BotFather on Telegram")
        print("2. Get bot token")
        print("3. Set environment variable:")
        print("   export TELEGRAM_BOT_TOKEN='your-token-here'")
        print("\nOptionally set TELEGRAM_CHAT_ID to restrict to specific user")
        print("   export TELEGRAM_CHAT_ID='your-chat-id'")
        print("\nThen run: python3 telegram_bot_listener.py")
        print("\nOr test without Telegram: python3 telegram_bot_listener.py --test")
        return 1

    # Create and run bot
    try:
        bot = SimpleTelegramBot(BOT_TOKEN)
        bot.run()
        return 0
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
