#!/usr/bin/env python3
"""Authenticated Telegram transport for the autonomous communication loop.

Commands remain supported for compatibility. Ordinary authenticated messages
are now durable autonomous requests instead of being silently discarded.
"""

import logging
import os
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(Path(__file__).parent.parent))

from human_loop import HumanLoop
from telegram_command_bot import TelegramCommandBot

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
ALLOWED_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
POLL_INTERVAL = 2
LOG_FILE = "/var/log/telegram-bot.log"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.FileHandler(LOG_FILE), logging.StreamHandler()],
)
logger = logging.getLogger(__name__)


class SimpleTelegramBot:
    """Long-poll Telegram and route authenticated messages to the system."""

    def __init__(self, token: str):
        self.token = token
        self.base_url = f"https://api.telegram.org/bot{token}"
        self.offset = 0
        self.command_bot = TelegramCommandBot()
        self.human_loop = HumanLoop(Path(__file__).parent.parent)
        try:
            import requests
            self.requests = requests
        except ImportError:
            logger.error("requests library not found")
            raise

    def get_updates(self, timeout=30):
        try:
            response = self.requests.get(
                f"{self.base_url}/getUpdates",
                params={"offset": self.offset, "timeout": timeout},
                timeout=timeout + 5,
            )
            response.raise_for_status()
            data = response.json()
            return data.get("result", []) if data.get("ok") else []
        except Exception as exc:
            logger.error("Error getting updates: %s", exc)
            return []

    def send_message(self, chat_id: int, text: str):
        try:
            response = self.requests.post(
                f"{self.base_url}/sendMessage",
                json={"chat_id": chat_id, "text": text, "parse_mode": "Markdown"},
                timeout=10,
            )
            response.raise_for_status()
            return True
        except Exception as exc:
            logger.error("Error sending message: %s", exc)
            return False

    def process_update(self, update):
        try:
            message = update.get("message")
            if not message:
                return

            chat_id = message.get("chat", {}).get("id")
            text = message.get("text", "").strip()
            username = message.get("from", {}).get("username", "unknown")

            # Authentication is mandatory. Never operate an unrestricted bot.
            if not ALLOWED_CHAT_ID:
                logger.error("TELEGRAM_CHAT_ID is not configured; refusing inbound message")
                return
            if str(chat_id) != str(ALLOWED_CHAT_ID):
                logger.warning("Ignoring message from unauthorized chat: %s", chat_id)
                return
            if not text:
                return

            logger.info("Received authenticated message from %s", username)
            if text.startswith("/"):
                response = self.command_bot.process_command(text)
            else:
                response = self.human_loop.receive(text, chat_id=str(chat_id), username=username)
            self.send_message(chat_id, response)
        except Exception as exc:
            logger.error("Error processing update: %s", exc)

    def run(self):
        logger.info("Telegram Bot Listener starting")
        if not ALLOWED_CHAT_ID:
            logger.error("No TELEGRAM_CHAT_ID configured; inbound communication is fail-closed")
            return 1

        while True:
            try:
                updates = self.get_updates()
                for update in updates:
                    self.process_update(update)
                    update_id = update.get("update_id")
                    if update_id is not None:
                        self.offset = update_id + 1
                if not updates:
                    time.sleep(POLL_INTERVAL)
            except KeyboardInterrupt:
                logger.info("Shutting down gracefully")
                return 0
            except Exception as exc:
                logger.error("Error in main loop: %s", exc)
                time.sleep(10)


def test_mode():
    print("Running in TEST MODE (no Telegram connection)\n")
    bot = TelegramCommandBot()
    for cmd in ["/status", "/metrics", "/health", "/agents", "/help"]:
        print("\n" + "=" * 60)
        print(f"Command: {cmd}")
        print("=" * 60)
        print(bot.process_command(cmd))


def main():
    if len(sys.argv) > 1 and sys.argv[1] == "--test":
        test_mode()
        return 0
    if not BOT_TOKEN:
        print("Error: TELEGRAM_BOT_TOKEN environment variable not set")
        return 1
    try:
        return SimpleTelegramBot(BOT_TOKEN).run()
    except Exception as exc:
        logger.error("Fatal error: %s", exc)
        return 1


if __name__ == "__main__":
    sys.exit(main())
