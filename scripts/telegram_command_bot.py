#!/usr/bin/env python3
"""
Telegram Command Bot - Autonomous Control Interface
=====================================================

Provides a Telegram bot interface for controlling and monitoring
the hands-off-engine without requiring CLI access.

Commands:
  /status - Get system status
  /health - Run health check
  /metrics - View performance metrics
  /approve_pr <num> - Approve and merge PR
  /reject_pr <num> - Reject PR
  /approve <id> - Approve queued change
  /reject <id> - Reject queued change
  /pause - Pause trading
  /resume - Resume trading
  /phase - View current phase
  /help - Show available commands

Runs continuously, polling for new messages.
"""

# UNIFIED AI - All systems serve Yair Siegel
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))
try:
    from ai.unified_ai import MASTER, get_master
except ImportError:
    MASTER = "Yair Siegel"


import os
import json
import time
import subprocess
import requests
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, List

REPO_ROOT = Path(__file__).parent.parent
STATE_DIR = REPO_ROOT / "state"
CONFIG_DIR = REPO_ROOT / "config"
LOGS_DIR = REPO_ROOT / "logs"

# Telegram config
BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN', '8214203655:AAGkAamvjQq0b7T7lmaTPDd-yYY_hvo_xvA')
AUTHORIZED_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID', '8327766663')

# Track last processed update
LAST_UPDATE_FILE = STATE_DIR / "telegram_last_update.json"


class TelegramCommandBot:
    """Handles Telegram commands for autonomous control."""

    def __init__(self):
        self.token = BOT_TOKEN
        self.authorized_chat = AUTHORIZED_CHAT_ID
        self.base_url = f"https://api.telegram.org/bot{self.token}"
        self.last_update_id = self.load_last_update_id()

    def load_last_update_id(self) -> int:
        """Load last processed update ID."""
        if LAST_UPDATE_FILE.exists():
            with open(LAST_UPDATE_FILE) as f:
                data = json.load(f)
                return data.get("last_update_id", 0)
        return 0

    def save_last_update_id(self, update_id: int):
        """Save last processed update ID."""
        with open(LAST_UPDATE_FILE, 'w') as f:
            json.dump({"last_update_id": update_id, "saved_at": datetime.utcnow().isoformat()}, f)
        self.last_update_id = update_id

    def send_message(self, text: str, parse_mode: str = "HTML"):
        """Send a message to the authorized chat."""
        try:
            response = requests.post(
                f"{self.base_url}/sendMessage",
                json={
                    "chat_id": self.authorized_chat,
                    "text": text,
                    "parse_mode": parse_mode
                },
                timeout=10
            )
            return response.ok
        except Exception as e:
            print(f"Send message error: {e}")
            return False

    def get_updates(self) -> List[Dict]:
        """Get new updates from Telegram."""
        try:
            response = requests.get(
                f"{self.base_url}/getUpdates",
                params={
                    "offset": self.last_update_id + 1,
                    "timeout": 30
                },
                timeout=35
            )

            if response.ok:
                data = response.json()
                return data.get("result", [])
            return []
        except Exception as e:
            print(f"Get updates error: {e}")
            return []

    def process_command(self, message: Dict):
        """Process a command message."""
        chat_id = str(message.get("chat", {}).get("id", ""))
        text = message.get("text", "").strip()

        # Security: only process from authorized chat
        if chat_id != self.authorized_chat:
            print(f"Unauthorized message from chat {chat_id}")
            return

        if not text.startswith("/"):
            return

        # Parse command and args
        parts = text.split()
        command = parts[0].lower().split('@')[0]  # Handle @botname suffix
        args = parts[1:] if len(parts) > 1 else []

        print(f"Processing command: {command} {args}")

        # Route to handler
        handlers = {
            "/status": self.cmd_status,
            "/health": self.cmd_health,
            "/metrics": self.cmd_metrics,
            "/approve_pr": self.cmd_approve_pr,
            "/reject_pr": self.cmd_reject_pr,
            "/approve": self.cmd_approve,
            "/reject": self.cmd_reject,
            "/pause": self.cmd_pause,
            "/resume": self.cmd_resume,
            "/phase": self.cmd_phase,
            "/help": self.cmd_help,
            "/start": self.cmd_help,
        }

        handler = handlers.get(command)
        if handler:
            try:
                handler(args)
            except Exception as e:
                self.send_message(f"❌ Error: {e}")
        else:
            self.send_message(f"Unknown command: {command}\nUse /help for available commands")

    def cmd_status(self, args):
        """Get system status."""
        status_parts = []

        # Trading mode
        mode_file = STATE_DIR / "trading_mode.json"
        if mode_file.exists():
            with open(mode_file) as f:
                mode = json.load(f)
            paused = mode.get("paused", False)
            phase = mode.get("phase", "unknown")
            status_parts.append(f"<b>Trading:</b> {'⏸ Paused' if paused else '✅ Active'}")
            status_parts.append(f"<b>Phase:</b> {phase}")
        else:
            status_parts.append("<b>Trading:</b> ❓ Unknown")

        # Hard limits
        limits_file = CONFIG_DIR / "hard_limits.json"
        if limits_file.exists():
            with open(limits_file) as f:
                limits = json.load(f)
            max_pos = limits.get("max_position_usd", "?")
            status_parts.append(f"<b>Max Position:</b> ${max_pos}")

        # Recent activity
        perf_log = LOGS_DIR / "trading_performance.jsonl"
        if perf_log.exists():
            with open(perf_log) as f:
                lines = f.readlines()
            status_parts.append(f"<b>Total Trades:</b> {len(lines)}")

        self.send_message("📊 <b>System Status</b>\n\n" + "\n".join(status_parts))

    def cmd_health(self, args):
        """Run health check."""
        self.send_message("🔍 Running health check...")

        try:
            result = subprocess.run(
                [str(REPO_ROOT / "scripts" / "healthcheck.sh")],
                capture_output=True,
                text=True,
                timeout=30
            )

            if result.returncode == 0:
                self.send_message(f"✅ <b>Health Check Passed</b>\n\n<pre>{result.stdout[:1000]}</pre>")
            else:
                self.send_message(f"⚠️ <b>Health Check Issues</b>\n\n<pre>{result.stdout[:1000]}</pre>")

        except Exception as e:
            self.send_message(f"❌ Health check failed: {e}")

    def cmd_metrics(self, args):
        """View performance metrics."""
        perf_log = LOGS_DIR / "trading_performance.jsonl"

        if not perf_log.exists():
            self.send_message("📈 No trading data yet")
            return

        trades = []
        with open(perf_log) as f:
            for line in f:
                try:
                    trades.append(json.loads(line))
                except:
                    continue

        if not trades:
            self.send_message("📈 No trades recorded")
            return

        # Calculate metrics
        total = len(trades)
        wins = sum(1 for t in trades if t.get("pnl", 0) > 0)
        losses = sum(1 for t in trades if t.get("pnl", 0) < 0)
        total_pnl = sum(t.get("pnl", 0) for t in trades)
        win_rate = wins / total if total > 0 else 0

        msg = f'''📈 <b>Performance Metrics</b>

<b>Trades:</b> {total}
<b>Wins:</b> {wins} | <b>Losses:</b> {losses}
<b>Win Rate:</b> {win_rate:.1%}
<b>Total P&L:</b> ${total_pnl:.2f}
'''
        self.send_message(msg)

    def cmd_approve_pr(self, args):
        """Approve and merge a PR."""
        if not args:
            self.send_message("Usage: /approve_pr <pr_number>")
            return

        try:
            pr_num = int(args[0])
        except ValueError:
            self.send_message("Invalid PR number")
            return

        self.send_message(f"🔄 Merging PR #{pr_num}...")

        try:
            result = subprocess.run(
                ["gh", "pr", "merge", str(pr_num), "--squash"],
                capture_output=True,
                text=True,
                timeout=60,
                cwd=str(REPO_ROOT)
            )

            if result.returncode == 0:
                self.send_message(f"✅ PR #{pr_num} merged successfully")
            else:
                self.send_message(f"❌ Failed to merge PR #{pr_num}\n{result.stderr[:500]}")

        except Exception as e:
            self.send_message(f"❌ Error merging PR: {e}")

    def cmd_reject_pr(self, args):
        """Close a PR without merging."""
        if not args:
            self.send_message("Usage: /reject_pr <pr_number>")
            return

        try:
            pr_num = int(args[0])
        except ValueError:
            self.send_message("Invalid PR number")
            return

        try:
            result = subprocess.run(
                ["gh", "pr", "close", str(pr_num)],
                capture_output=True,
                text=True,
                timeout=30,
                cwd=str(REPO_ROOT)
            )

            if result.returncode == 0:
                self.send_message(f"🚫 PR #{pr_num} closed")
            else:
                self.send_message(f"❌ Failed to close PR #{pr_num}")

        except Exception as e:
            self.send_message(f"❌ Error closing PR: {e}")

    def cmd_approve(self, args):
        """Approve a queued change."""
        if not args:
            self.send_message("Usage: /approve <change_id>")
            return

        change_id = args[0]

        queue_file = STATE_DIR / "approval_queue.json"
        if not queue_file.exists():
            self.send_message("No pending approvals")
            return

        with open(queue_file) as f:
            queue = json.load(f)

        pending = queue.get("pending", [])
        found = None

        for i, item in enumerate(pending):
            if item.get("id") == change_id:
                found = (i, item)
                break

        if not found:
            self.send_message(f"Change {change_id} not found in queue")
            return

        idx, item = found

        # Move to approved
        pending.pop(idx)
        approved = queue.get("approved", [])
        item["approved_at"] = datetime.utcnow().isoformat() + "Z"
        item["approved_by"] = "telegram"
        approved.append(item)

        queue["pending"] = pending
        queue["approved"] = approved

        with open(queue_file, 'w') as f:
            json.dump(queue, f, indent=2)

        self.send_message(f"✅ Approved: {item.get('description', change_id)}")

    def cmd_reject(self, args):
        """Reject a queued change."""
        if not args:
            self.send_message("Usage: /reject <change_id>")
            return

        change_id = args[0]

        queue_file = STATE_DIR / "approval_queue.json"
        if not queue_file.exists():
            self.send_message("No pending approvals")
            return

        with open(queue_file) as f:
            queue = json.load(f)

        pending = queue.get("pending", [])
        found = None

        for i, item in enumerate(pending):
            if item.get("id") == change_id:
                found = (i, item)
                break

        if not found:
            self.send_message(f"Change {change_id} not found in queue")
            return

        idx, item = found
        pending.pop(idx)
        queue["pending"] = pending

        with open(queue_file, 'w') as f:
            json.dump(queue, f, indent=2)

        self.send_message(f"🚫 Rejected: {item.get('description', change_id)}")

    def cmd_pause(self, args):
        """Pause trading."""
        mode_file = STATE_DIR / "trading_mode.json"

        mode = {}
        if mode_file.exists():
            with open(mode_file) as f:
                mode = json.load(f)

        mode["paused"] = True
        mode["paused_at"] = datetime.utcnow().isoformat() + "Z"
        mode["paused_by"] = "telegram"

        with open(mode_file, 'w') as f:
            json.dump(mode, f, indent=2)

        self.send_message("⏸ <b>Trading Paused</b>\n\nUse /resume to restart")

    def cmd_resume(self, args):
        """Resume trading."""
        mode_file = STATE_DIR / "trading_mode.json"

        mode = {}
        if mode_file.exists():
            with open(mode_file) as f:
                mode = json.load(f)

        mode["paused"] = False
        mode["resumed_at"] = datetime.utcnow().isoformat() + "Z"

        with open(mode_file, 'w') as f:
            json.dump(mode, f, indent=2)

        self.send_message("▶️ <b>Trading Resumed</b>")

    def cmd_phase(self, args):
        """View current deployment phase."""
        mode_file = STATE_DIR / "trading_mode.json"

        if not mode_file.exists():
            self.send_message("Phase: baby_mode (default)")
            return

        with open(mode_file) as f:
            mode = json.load(f)

        phase = mode.get("phase", "baby_mode")
        started = mode.get("phase_started", "unknown")

        from autonomous_phase_manager import PHASES
        config = PHASES.get(phase, {})

        msg = f'''📊 <b>Current Phase: {phase}</b>

<b>Started:</b> {started}
<b>Max Position:</b> ${config.get('max_position_usd', '?')}

<b>Next Phase Requirements:</b>
• Min trades: {config.get('min_trades', 'N/A')}
• Min days: {config.get('min_days', 'N/A')}
• Win rate: {config.get('required_win_rate', 0):.0%}
• Max drawdown: {config.get('max_drawdown', 0):.0%}
'''
        self.send_message(msg)

    def cmd_help(self, args):
        """Show available commands."""
        msg = '''🤖 <b>Hands-Off Engine Commands</b>

<b>Status & Monitoring:</b>
/status - System status
/health - Run health check
/metrics - Performance metrics
/phase - Current deployment phase

<b>Trading Control:</b>
/pause - Pause trading
/resume - Resume trading

<b>Approvals:</b>
/approve_pr &lt;num&gt; - Merge PR
/reject_pr &lt;num&gt; - Close PR
/approve &lt;id&gt; - Approve change
/reject &lt;id&gt; - Reject change

<b>System:</b>
/help - This message
'''
        self.send_message(msg)

    def run(self):
        """Main loop: poll for updates and process commands."""
        print("=" * 60)
        print("TELEGRAM COMMAND BOT")
        print(f"Authorized chat: {self.authorized_chat}")
        print("=" * 60)

        self.send_message("🤖 <b>Bot Online</b>\n\nUse /help for commands")

        while True:
            try:
                updates = self.get_updates()

                for update in updates:
                    update_id = update.get("update_id", 0)

                    if "message" in update:
                        self.process_command(update["message"])

                    # Save progress
                    self.save_last_update_id(update_id)

                time.sleep(1)

            except KeyboardInterrupt:
                print("\nShutting down...")
                self.send_message("🔴 Bot going offline")
                break

            except Exception as e:
                print(f"Error in main loop: {e}")
                time.sleep(5)


def main():
    bot = TelegramCommandBot()
    bot.run()


if __name__ == '__main__':
    main()
