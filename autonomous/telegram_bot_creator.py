#!/usr/bin/env python3
"""
Autonomous Telegram Bot Creator

Creates and configures Telegram bots automatically without manual intervention.

Uses Telegram Client API to:
1. Login to user's Telegram account
2. Message @BotFather programmatically
3. Create bot and capture token
4. Get user's chat ID
5. Store credentials securely
6. Activate messaging system

This enables complete autonomous setup - no manual steps required.
"""

import os
import time
import json
from pathlib import Path
from typing import Optional, Tuple
import asyncio

# Check for Telethon (Telegram client library)
try:
    from telethon import TelegramClient, events
    from telethon.tl.types import User
    TELETHON_AVAILABLE = True
except ImportError:
    TELETHON_AVAILABLE = False
    print("⚠️  Telethon not installed. Install with: pip install telethon")

# Telegram API credentials (get from https://my.telegram.org)
API_ID = os.getenv('TELEGRAM_API_ID', '')
API_HASH = os.getenv('TELEGRAM_API_HASH', '')
PHONE = os.getenv('TELEGRAM_PHONE', '')

STATE_FILE = Path(__file__).parent.parent / 'state' / 'telegram_bot_creator.json'


class TelegramBotCreator:
    """Autonomously create and configure Telegram bots."""

    def __init__(self, api_id: str, api_hash: str, phone: str):
        self.api_id = api_id
        self.api_hash = api_hash
        self.phone = phone
        self.client = None
        self.state = self.load_state()

    def load_state(self) -> dict:
        """Load creator state."""
        if STATE_FILE.exists():
            return json.loads(STATE_FILE.read_text())
        return {
            'bots_created': [],
            'last_bot_token': None,
            'user_chat_id': None,
            'creation_timestamp': None
        }

    def save_state(self):
        """Save creator state."""
        STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
        STATE_FILE.write_text(json.dumps(self.state, indent=2))

    async def create_bot_autonomous(
        self,
        bot_name: str = "Hands-Off System",
        bot_username: str = None
    ) -> Tuple[Optional[str], Optional[str]]:
        """
        Autonomously create a Telegram bot.

        Returns: (bot_token, user_chat_id) or (None, None) if failed
        """
        if not TELETHON_AVAILABLE:
            print("✗ Telethon library not available")
            return None, None

        if not all([self.api_id, self.api_hash, self.phone]):
            print("✗ Telegram API credentials not configured")
            print("  Get credentials from: https://my.telegram.org")
            print("  Set: TELEGRAM_API_ID, TELEGRAM_API_HASH, TELEGRAM_PHONE")
            return None, None

        try:
            # Create client
            self.client = TelegramClient(
                'handsoff_session',
                int(self.api_id),
                self.api_hash
            )

            print(f"Connecting to Telegram as {self.phone}...")
            await self.client.start(phone=self.phone)

            print("✓ Connected to Telegram")

            # Get user's chat ID
            me = await self.client.get_me()
            user_chat_id = str(me.id)
            self.state['user_chat_id'] = user_chat_id

            print(f"✓ Your chat ID: {user_chat_id}")

            # Generate unique bot username if not provided
            if not bot_username:
                import random
                suffix = ''.join(random.choices('0123456789', k=6))
                bot_username = f"handsoff_{suffix}_bot"

            print(f"\nCreating bot: {bot_name} (@{bot_username})")

            # Message BotFather
            bot_token = await self._interact_with_botfather(bot_name, bot_username)

            if bot_token:
                print(f"✓ Bot created successfully!")
                print(f"  Token: {bot_token[:20]}...")
                print(f"  Username: @{bot_username}")

                self.state['bots_created'].append({
                    'name': bot_name,
                    'username': bot_username,
                    'token': bot_token,
                    'created_at': time.time()
                })
                self.state['last_bot_token'] = bot_token
                self.save_state()

                return bot_token, user_chat_id

            return None, None

        except Exception as e:
            print(f"✗ Error creating bot: {e}")
            return None, None

        finally:
            if self.client:
                await self.client.disconnect()

    async def _interact_with_botfather(
        self,
        bot_name: str,
        bot_username: str
    ) -> Optional[str]:
        """
        Interact with @BotFather to create a bot.

        Sends commands and parses responses.
        """
        try:
            # Find BotFather
            botfather = await self.client.get_entity('BotFather')

            print("  → Messaging @BotFather...")

            # Send /newbot command
            await self.client.send_message(botfather, '/newbot')
            await asyncio.sleep(1)

            # Send bot name
            await self.client.send_message(botfather, bot_name)
            await asyncio.sleep(1)

            # Send bot username
            await self.client.send_message(botfather, bot_username)
            await asyncio.sleep(2)

            # Get messages from BotFather
            messages = await self.client.get_messages(botfather, limit=10)

            # Parse token from BotFather's response
            for msg in messages:
                if msg.text and 'token' in msg.text.lower():
                    # Extract token (format: 123456789:ABC-DEF1234ghIkl...)
                    import re
                    token_match = re.search(r'(\d+:[A-Za-z0-9_-]+)', msg.text)
                    if token_match:
                        return token_match.group(1)

            # Check if username was taken
            for msg in messages:
                if msg.text and 'already taken' in msg.text.lower():
                    print("  ✗ Username already taken, trying different one...")
                    return None

            print("  ✗ Could not extract bot token from BotFather")
            return None

        except Exception as e:
            print(f"  ✗ Error interacting with BotFather: {e}")
            return None

    async def setup_complete_system(self) -> bool:
        """
        Complete autonomous setup:
        1. Create bot
        2. Store credentials
        3. Activate messaging system
        """
        print("="*60)
        print("AUTONOMOUS TELEGRAM BOT CREATION")
        print("="*60)
        print()

        # Create bot
        bot_token, chat_id = await self.create_bot_autonomous()

        if not bot_token or not chat_id:
            print("\n✗ Bot creation failed")
            return False

        # Store credentials
        print("\nStoring credentials...")
        env_file = Path(__file__).parent.parent / '.env.handsoff_telegram'

        env_file.write_text(f'''TELEGRAM_BOT_TOKEN="{bot_token}"
TELEGRAM_CHAT_ID="{chat_id}"
''')

        print("✓ Credentials stored in .env.handsoff_telegram")

        # Test bot
        print("\nTesting bot...")
        from autonomous.telegram_notifier import TelegramNotifier

        notifier = TelegramNotifier()
        success = notifier.send_message("🤖 Autonomous bot creation successful!")

        if success:
            print("✓ Test message sent")
        else:
            print("⚠️  Test message failed (bot may need /start)")

        # Start messaging bridge
        print("\nStarting messaging bridge...")
        import subprocess

        subprocess.run(['pkill', '-f', 'messaging_bridge'], check=False)

        proc = subprocess.Popen(
            ['python3', 'autonomous/messaging_bridge.py', '--continuous'],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            cwd=Path(__file__).parent.parent
        )

        print(f"✓ Messaging bridge started (PID: {proc.pid})")

        print("\n" + "="*60)
        print("AUTONOMOUS SETUP COMPLETE")
        print("="*60)
        print(f"\nBot Token: {bot_token[:20]}...")
        print(f"Chat ID: {chat_id}")
        print(f"\nOpen Telegram and search for your bot to start it!")
        print("="*60)

        return True


def main():
    """Run autonomous bot creator."""
    import sys

    if '--help' in sys.argv:
        print("""
Autonomous Telegram Bot Creator

Usage:
  python3 autonomous/telegram_bot_creator.py [--setup]

Setup:
  1. Get API credentials from: https://my.telegram.org
     - Login with your phone number
     - Go to 'API development tools'
     - Create an application
     - Copy API ID and API Hash

  2. Set environment variables:
     export TELEGRAM_API_ID="your_api_id"
     export TELEGRAM_API_HASH="your_api_hash"
     export TELEGRAM_PHONE="+1234567890"

  3. Run:
     python3 autonomous/telegram_bot_creator.py --setup

The system will:
  - Login to your Telegram account
  - Message @BotFather automatically
  - Create a bot for you
  - Extract credentials
  - Activate messaging system

No manual steps required after initial API credentials.
        """)
        return

    # Load credentials from env or .env file
    env_file = Path(__file__).parent.parent / '.env.telegram_api'
    if env_file.exists():
        for line in env_file.read_text().splitlines():
            if line.strip() and not line.startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                os.environ[key.strip()] = value.strip().strip('"')

    api_id = os.getenv('TELEGRAM_API_ID', '')
    api_hash = os.getenv('TELEGRAM_API_HASH', '')
    phone = os.getenv('TELEGRAM_PHONE', '')

    if not all([api_id, api_hash, phone]):
        print("✗ Telegram API credentials not configured")
        print("\nSetup:")
        print("1. Get credentials: https://my.telegram.org")
        print("2. Create .env.telegram_api with:")
        print('   TELEGRAM_API_ID="your_id"')
        print('   TELEGRAM_API_HASH="your_hash"')
        print('   TELEGRAM_PHONE="+1234567890"')
        print("\n3. Run again with --setup")
        return

    creator = TelegramBotCreator(api_id, api_hash, phone)

    if '--setup' in sys.argv:
        asyncio.run(creator.setup_complete_system())
    else:
        print("Use --setup to create bot autonomously")
        print("Use --help for detailed instructions")


if __name__ == '__main__':
    main()
