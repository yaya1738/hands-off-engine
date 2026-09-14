#!/usr/bin/env python3
"""
Telegram Bridge — bidirectional Telegram ↔ system communication.

Reads bot token from ~/.codex/telegram-bridge.json (same file as AnyClaw).
Polls Telegram for incoming messages, routes them through CommHub.receive().
Sends outbound alerts from CommHub through the bot API.

Token file format:
    {"botToken": "123456:ABC...", "chatIds": [123456789]}

When no token is configured, the bridge is silent (no errors, no polling).
It silently starts and waits — the moment the token file appears, it works.

Usage:
    # As a long-lived daemon (started by bootstrap.py):
    python3 scripts/telegram_bridge.py

    # Send a one-shot message:
    python3 scripts/telegram_bridge.py send "ETH position up 5%"

    # Check connection:
    python3 scripts/telegram_bridge.py check
"""

import json
import os
import sys
import time
import logging
import urllib.request
import urllib.parse
from pathlib import Path
from datetime import datetime, timezone

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

logging.basicConfig(level=logging.INFO, format='[%(asctime)s] [%(levelname)s] [TelegramBridge] %(message)s')
log = logging.getLogger("TelegramBridge")

REPO_ROOT = Path.home() / "hands-off-engine"
TOKEN_FILE = Path.home() / ".codex" / "telegram-bridge.json"
STATE_DIR = REPO_ROOT / "state"
TELEGRAM_STATE = STATE_DIR / "telegram_state.json"
MAX_MESSAGE_LENGTH = 4000


def load_config():
    """Load bot token and chat IDs from config file."""
    if not TOKEN_FILE.exists():
        return None
    try:
        cfg = json.loads(TOKEN_FILE.read_text())
        token = cfg.get("botToken", "")
        chat_ids = cfg.get("chatIds", [])
        if token and chat_ids:
            return {"token": token, "chat_ids": chat_ids}
    except Exception:
        pass
    return None


def load_state():
    if TELEGRAM_STATE.exists():
        try:
            return json.loads(TELEGRAM_STATE.read_text())
        except Exception:
            pass
    return {"last_update_id": 0, "messages_sent": 0, "messages_received": 0}


def save_state(state):
    TELEGRAM_STATE.write_text(json.dumps(state, indent=2) + "\n")


class TelegramBridge:
    """Bidirectional Telegram ↔ system bridge."""

    def __init__(self):
        self.config = load_config()
        self.state = load_state()
        self.available = self.config is not None

    # ── outbound: system → Telegram ──

    def send(self, text, chat_id=None):
        """Send a message to Telegram."""
        if not self.available:
            log.warning("Telegram not configured — message not sent")
            return {"status": "not_configured", "text_preview": text[:80]}

        target_chat = chat_id or self.config["chat_ids"][0]

        # Split long messages
        chunks = [text[i:i+MAX_MESSAGE_LENGTH] for i in range(0, len(text), MAX_MESSAGE_LENGTH)]
        results = []
        for chunk in chunks:
            result = self._api_call("sendMessage", {
                "chat_id": target_chat,
                "text": chunk,
                "parse_mode": "Markdown",
            })
            results.append(result)
            self.state["messages_sent"] = self.state.get("messages_sent", 0) + 1

        save_state(self.state)
        return {"status": "sent", "chunks": len(chunks), "chat_id": target_chat}

    def send_alert(self, title, body, severity="normal"):
        """Send a formatted alert with emoji prefix."""
        emoji = {"critical": "🚨", "error": "⚠️", "warning": "⚡", "normal": "ℹ️"}.get(severity, "ℹ️")
        text = f"{emoji} *{title}*\n\n{body}"
        return self.send(text)

    # ── inbound: Telegram → system ──

    def poll_updates(self, timeout=30):
        """Long-poll for new Telegram messages."""
        if not self.available:
            return []

        params = {"offset": self.state.get("last_update_id", 0) + 1, "timeout": timeout}
        result = self._api_call("getUpdates", params)

        updates = result.get("result", [])
        messages = []
        for update in updates:
            self.state["last_update_id"] = update.get("update_id", self.state["last_update_id"])
            msg = update.get("message", {})
            if msg and "text" in msg:
                messages.append({
                    "update_id": update["update_id"],
                    "chat_id": msg["chat"]["id"],
                    "user_id": msg.get("from", {}).get("id"),
                    "username": msg.get("from", {}).get("username", ""),
                    "text": msg["text"],
                    "timestamp": msg.get("date"),
                })
                self.state["messages_received"] = self.state.get("messages_received", 0) + 1

        save_state(self.state)
        return messages

    def process_inbound(self, messages):
        """Route inbound Telegram messages through CommHub."""
        from scripts.comm_hub import CommHub
        hub = CommHub()

        for msg in messages:
            text = msg["text"].strip()

            # Parse command-style messages
            if text.startswith("/approve "):
                cmd_id = text.split(" ", 1)[1].strip()
                response = hub.receive("operator", "approve", {"command_id": cmd_id}, channel="telegram")
            elif text.startswith("/reject "):
                cmd_id = text.split(" ", 1)[1].strip()
                response = hub.receive("operator", "reject", {"command_id": cmd_id}, channel="telegram")
            elif text.startswith("/status"):
                response = hub.receive("operator", "status_query", {"query": "full"}, channel="telegram")
            elif text.startswith("/trade "):
                # Parse trade command: /trade buy ETH-USD 100
                parts = text.split(" ", 3)
                if len(parts) >= 3:
                    response = hub.receive("operator", "trade_command", {
                        "action": parts[1],
                        "params": {"market": parts[2], "amount": parts[3] if len(parts) > 3 else None},
                    }, channel="telegram")
                else:
                    response = {"error": "Usage: /trade <buy|sell> <market> [amount]"}
            elif text.startswith("/help"):
                response = self._help_response()
            else:
                response = hub.receive("operator", "inbound_from_operator", {"text": text}, channel="telegram")

            # Send response back
            reply = response.get("response", response.get("data", response.get("result", "")))
            if isinstance(reply, dict):
                reply = json.dumps(reply, indent=2)[:MAX_MESSAGE_LENGTH]
            elif reply:
                reply = str(reply)[:MAX_MESSAGE_LENGTH]
            else:
                reply = f"✅ Received: {text[:50]}"

            self.send(reply, chat_id=msg["chat_id"])
            log.info(f"Processed inbound from {msg.get('username', msg.get('chat_id'))}: {text[:60]}")

    def _help_response(self):
        return """🤖 *Hands-Off Engine Commands*

/status — System status
/trade <buy|sell> <market> [amount] — Execute trade (LIVE)
/approve <id> — Approve pending command
/reject <id> — Reject pending command
/help — This message"""

    # ── Telegram Bot API ──

    def _api_call(self, method, params=None):
        """Call Telegram Bot API."""
        if not self.config:
            return {}
        url = f"https://api.telegram.org/bot{self.config['token']}/{method}"
        try:
            data = json.dumps(params or {}).encode() if params else None
            req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
            with urllib.request.urlopen(req, timeout=30) as resp:
                return json.loads(resp.read())
        except Exception as e:
            log.error(f"Telegram API error ({method}): {e}")
            return {"ok": False, "error": str(e)}

    def check_connection(self):
        """Verify bot connection."""
        if not self.available:
            return {"status": "not_configured", "message": f"Token file not found: {TOKEN_FILE}"}
        result = self._api_call("getMe")
        if result.get("ok"):
            bot = result.get("result", {})
            return {"status": "connected", "bot": bot.get("username"), "id": bot.get("id")}
        return {"status": "error", "error": result.get("description", "unknown")}

    # ── daemon loop ──

    def run(self, poll_interval=5):
        """Run the bridge as a long-lived daemon."""
        if not self.available:
            log.info(f"Telegram not configured. Waiting for {TOKEN_FILE}...")
            while not self.available:
                time.sleep(30)
                self.config = load_config()
                self.available = self.config is not None
                if self.available:
                    log.info("Telegram config detected — starting bridge")
                    break
            log.info("Telegram config loaded")

        conn = self.check_connection()
        log.info(f"Connected to: @{conn.get('bot', '?')}")

        # Send startup notification
        self.send_alert("System Online", f"Telegram bridge connected at {datetime.now(timezone.utc).isoformat()}", "normal")

        while True:
            try:
                messages = self.poll_updates(timeout=poll_interval)
                if messages:
                    self.process_inbound(messages)
            except KeyboardInterrupt:
                log.info("Bridge shutting down")
                break
            except Exception as e:
                log.error(f"Bridge error: {e}")
                time.sleep(10)


# ── CLI ──

def cli():
    import argparse
    parser = argparse.ArgumentParser(description="Telegram Bridge")
    sub = parser.add_subparsers(dest="cmd")

    send_p = sub.add_parser("send", help="Send message to Telegram")
    send_p.add_argument("message", help="Message text")

    sub.add_parser("check", help="Check bot connection")
    sub.add_parser("poll", help="Poll for updates once")

    args = parser.parse_args()
    bridge = TelegramBridge()

    if args.cmd == "send":
        result = bridge.send(args.message)
        print(json.dumps(result, indent=2))
    elif args.cmd == "check":
        result = bridge.check_connection()
        print(json.dumps(result, indent=2))
    elif args.cmd == "poll":
        msgs = bridge.poll_updates(timeout=5)
        print(f"Messages: {len(msgs)}")
        for m in msgs:
            print(f"  [{m.get('username', '?')}]: {m['text'][:60]}")
    else:
        bridge.run()


if __name__ == "__main__":
    cli()
