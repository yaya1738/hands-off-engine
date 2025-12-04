#!/usr/bin/env python3
"""
Autonomous Telegram Bot Creator (Web Version)

Uses browser automation (Playwright) to interact with Telegram Web
and create bots autonomously.

Simpler than Client API version - only requires:
1. User to scan QR code once
2. System handles rest autonomously

No API credentials needed.
"""

import os
import time
import json
from pathlib import Path
from typing import Optional, Tuple
import re

STATE_FILE = Path(__file__).parent.parent / 'state' / 'telegram_bot_creator.json'


class TelegramBotCreatorWeb:
    """Create Telegram bots via browser automation."""

    def __init__(self):
        self.state = self.load_state()
        self.playwright = None
        self.browser = None
        self.page = None

    def load_state(self) -> dict:
        """Load creator state."""
        if STATE_FILE.exists():
            return json.loads(STATE_FILE.read_text())
        return {
            'bots_created': [],
            'last_bot_token': None,
            'user_chat_id': None,
            'session_stored': False
        }

    def save_state(self):
        """Save creator state."""
        STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
        STATE_FILE.write_text(json.dumps(self.state, indent=2))

    def check_playwright(self) -> bool:
        """Check if Playwright is available."""
        try:
            from playwright.sync_api import sync_playwright
            return True
        except ImportError:
            print("⚠️  Playwright not installed")
            print("Install with: pip install playwright && playwright install chromium")
            return False

    def create_bot_web(
        self,
        bot_name: str = "Hands-Off System",
        bot_username: str = None
    ) -> Tuple[Optional[str], Optional[str]]:
        """
        Create bot using Telegram Web automation.

        Returns: (bot_token, user_chat_id) or (None, None)
        """
        if not self.check_playwright():
            return None, None

        from playwright.sync_api import sync_playwright

        try:
            print("="*60)
            print("AUTONOMOUS BOT CREATION (WEB)")
            print("="*60)
            print()

            with sync_playwright() as p:
                # Launch browser
                print("Launching browser...")
                self.browser = p.chromium.launch(headless=False)  # Show browser for QR code
                context = self.browser.new_context()

                # Load session if exists
                session_file = Path(__file__).parent.parent / 'state' / 'telegram_session.json'
                if session_file.exists():
                    context.add_cookies(json.loads(session_file.read_text()))
                    print("✓ Loaded previous session")

                self.page = context.new_page()

                # Navigate to Telegram Web
                print("Opening Telegram Web...")
                self.page.goto('https://web.telegram.org/k/')

                # Wait for login (QR code or auto-login)
                print("\nWaiting for Telegram login...")
                print("  → If you see QR code, scan it with your phone")
                print("  → Or enter your phone number")
                print()

                # Wait for main chat interface (indicates logged in)
                try:
                    self.page.wait_for_selector('.chat-list', timeout=60000)
                    print("✓ Logged in to Telegram")

                    # Save session
                    cookies = context.cookies()
                    session_file.parent.mkdir(parents=True, exist_ok=True)
                    session_file.write_text(json.dumps(cookies, indent=2))
                    self.state['session_stored'] = True
                    self.save_state()

                except:
                    print("✗ Login timeout")
                    return None, None

                # Get user's chat ID (from profile)
                user_chat_id = self._get_user_chat_id()
                if user_chat_id:
                    print(f"✓ Your chat ID: {user_chat_id}")
                    self.state['user_chat_id'] = user_chat_id
                    self.save_state()

                # Generate unique bot username
                if not bot_username:
                    import random
                    suffix = ''.join(random.choices('0123456789', k=6))
                    bot_username = f"handsoff_{suffix}_bot"

                print(f"\nCreating bot: @{bot_username}")

                # Interact with BotFather
                bot_token = self._interact_with_botfather_web(bot_name, bot_username)

                if bot_token:
                    print(f"\n✓ Bot created successfully!")
                    print(f"  Username: @{bot_username}")
                    print(f"  Token: {bot_token[:20]}...")

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
            print(f"✗ Error: {e}")
            return None, None

        finally:
            if self.browser:
                self.browser.close()

    def _get_user_chat_id(self) -> Optional[str]:
        """Extract user's chat ID from Telegram Web."""
        try:
            # Click on menu/profile
            # This is simplified - actual implementation would navigate UI
            # For now, return None and user can provide manually
            return None
        except:
            return None

    def _interact_with_botfather_web(
        self,
        bot_name: str,
        bot_username: str
    ) -> Optional[str]:
        """
        Interact with @BotFather via Telegram Web.

        Automates the bot creation flow.
        """
        try:
            # Search for BotFather
            print("  → Searching for @BotFather...")
            search_input = self.page.query_selector('input[type="text"]')
            if search_input:
                search_input.fill('BotFather')
                time.sleep(1)

                # Click on BotFather chat
                self.page.click('text=BotFather')
                time.sleep(1)

            # Send /newbot command
            print("  → Sending /newbot...")
            message_input = self.page.query_selector('.input-message-input')
            if message_input:
                message_input.fill('/newbot')
                self.page.keyboard.press('Enter')
                time.sleep(2)

                # Send bot name
                print(f"  → Sending bot name: {bot_name}...")
                message_input.fill(bot_name)
                self.page.keyboard.press('Enter')
                time.sleep(2)

                # Send bot username
                print(f"  → Sending username: {bot_username}...")
                message_input.fill(bot_username)
                self.page.keyboard.press('Enter')
                time.sleep(3)

                # Extract token from BotFather's response
                print("  → Extracting bot token...")
                messages = self.page.query_selector_all('.message')

                for msg in messages[-5:]:  # Check last 5 messages
                    text = msg.inner_text()
                    if 'token' in text.lower():
                        # Extract token
                        token_match = re.search(r'(\d+:[A-Za-z0-9_-]+)', text)
                        if token_match:
                            return token_match.group(1)

                    if 'already taken' in text.lower():
                        print("  ✗ Username taken, try different one")
                        return None

            return None

        except Exception as e:
            print(f"  ✗ Error interacting with BotFather: {e}")
            return None

    def setup_complete_system(self) -> bool:
        """
        Complete autonomous setup with web automation.
        """
        # Create bot
        bot_token, chat_id = self.create_bot_web()

        if not bot_token:
            print("\n✗ Bot creation failed")
            return False

        # If no chat ID from web, ask user
        if not chat_id:
            print("\nCouldn't auto-detect chat ID.")
            print("Get it by messaging @userinfobot in Telegram")
            chat_id = input("Enter your chat ID: ").strip()

            if not chat_id:
                print("✗ Chat ID required")
                return False

        # Store credentials
        print("\nStoring credentials...")
        env_file = Path(__file__).parent.parent / '.env.handsoff_telegram'

        env_file.write_text(f'''TELEGRAM_BOT_TOKEN="{bot_token}"
TELEGRAM_CHAT_ID="{chat_id}"
''')

        print("✓ Credentials stored")

        # Test and activate
        print("\nActivating messaging system...")

        import subprocess
        result = subprocess.run(
            ['./scripts/setup_telegram.sh', bot_token, chat_id],
            cwd=Path(__file__).parent.parent,
            capture_output=True,
            text=True
        )

        if result.returncode == 0:
            print("✓ System activated!")
            return True
        else:
            print("⚠️  Activation had issues, check logs")
            return False


def main():
    """Run web-based bot creator."""
    import sys

    if '--help' in sys.argv:
        print("""
Autonomous Telegram Bot Creator (Web Version)

This uses browser automation to create bots - simpler than API version.

Usage:
  python3 autonomous/telegram_bot_creator_web.py --create

What happens:
  1. Opens Telegram Web in browser
  2. You scan QR code once (or login with phone)
  3. System navigates to @BotFather automatically
  4. Creates bot and extracts token
  5. Activates messaging system

Requirements:
  pip install playwright
  playwright install chromium

No Telegram API credentials needed!
        """)
        return

    creator = TelegramBotCreatorWeb()

    if '--create' in sys.argv:
        success = creator.setup_complete_system()
        if success:
            print("\n✅ COMPLETE: Telegram bot ready!")
    else:
        print("Use --create to start autonomous bot creation")
        print("Use --help for more info")


if __name__ == '__main__':
    main()
