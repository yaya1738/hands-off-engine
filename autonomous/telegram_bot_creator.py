#!/usr/bin/env python3
"""Compatibility facade for the retired autonomous Telegram creator.

Creating accounts/bots, acquiring credentials, writing secrets, sending
messages, and starting processes are privileged external actions. They must be
performed by an explicitly authorized Factory capability rather than this
legacy entry point.
"""

import json
from pathlib import Path
from typing import Optional, Tuple

STATE_FILE = Path(__file__).parent.parent / "state" / "telegram_bot_creator.json"


class TelegramBotCreator:
    """Read-only compatibility facade with no external-action authority."""

    def __init__(self, api_id: str, api_hash: str, phone: str):
        self.api_id = api_id
        self.api_hash = api_hash
        self.phone = phone
        self.client = None
        self.state = self.load_state()

    def load_state(self) -> dict:
        if STATE_FILE.exists():
            try:
                return json.loads(STATE_FILE.read_text())
            except (OSError, json.JSONDecodeError):
                pass
        return {"bots_created": [], "last_bot_token": None, "user_chat_id": None, "creation_timestamp": None}

    def save_state(self):
        """Persist non-secret compatibility metadata only."""
        safe_state = {k: v for k, v in self.state.items() if k not in {"last_bot_token"}}
        STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
        STATE_FILE.write_text(json.dumps(safe_state, indent=2))

    async def create_bot_autonomous(self, bot_name: str = "Hands-Off System", bot_username: str = None) -> Tuple[Optional[str], Optional[str]]:
        """Fail closed; legacy account/bot creation is not an execution authority."""
        print("[FACTORY-AUTHORITY] Legacy Telegram bot creation is disabled; submit bot provisioning through FactoryAuthorityGateway.")
        return None, None

    async def _interact_with_botfather(self, bot_name: str, bot_username: str) -> Optional[str]:
        print("[FACTORY-AUTHORITY] Legacy BotFather interaction is disabled.")
        return None

    async def setup_complete_system(self) -> bool:
        """Fail closed; no credentials, messages, or processes are created."""
        print("[FACTORY-AUTHORITY] Legacy Telegram setup is disabled; submit provisioning through FactoryAuthorityGateway.")
        return False


def main():
    import asyncio
    import os
    creator = TelegramBotCreator(os.getenv("TELEGRAM_API_ID", ""), os.getenv("TELEGRAM_API_HASH", ""), os.getenv("TELEGRAM_PHONE", ""))
    raise SystemExit(0 if asyncio.run(creator.setup_complete_system()) else 1)


if __name__ == "__main__": main()
