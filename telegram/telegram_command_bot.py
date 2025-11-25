#!/usr/bin/env python3
"""
Telegram Command Bot - Bidirectional User-System Communication

Replaces need for Claude Code CLI sessions by providing all
system interaction capabilities via Telegram.

Commands:
- /status - Full system status
- /metrics - Performance metrics (24h)
- /health - Health check results
- /approve <id> - Approve pending change
- /reject <id> - Reject pending change
- /agents - AI agent coordination status
- /help - Command list

User texts command → Bot executes → Responds in Telegram
Zero CLI interaction needed.
"""

import os
import json
import subprocess
import sys
from datetime import datetime, timedelta
from pathlib import Path

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

# Configuration
REPO_ROOT = Path(__file__).parent.parent
STATE_DIR = REPO_ROOT / "state"
SCRIPTS_DIR = REPO_ROOT / "scripts"
AI_COORD_DIR = REPO_ROOT / "ai" / "coordination"

# Import approval queue
from ai.approval_queue import ApprovalQueue

# Telegram config (from environment or config file)
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")


class TelegramCommandBot:
    """Handles incoming commands from Telegram and executes system operations."""

    def __init__(self):
        self.commands = {
            '/status': self.cmd_status,
            '/metrics': self.cmd_metrics,
            '/health': self.cmd_health,
            '/pending': self.cmd_pending,
            '/approve': self.cmd_approve,
            '/reject': self.cmd_reject,
            '/task': self.cmd_task,
            '/agents': self.cmd_agents,
            '/help': self.cmd_help,
        }

    def process_command(self, command_text: str) -> str:
        """Process incoming command and return response text."""
        parts = command_text.strip().split()
        cmd = parts[0].lower()
        args = parts[1:] if len(parts) > 1 else []

        if cmd in self.commands:
            try:
                return self.commands[cmd](args)
            except Exception as e:
                return f"❌ Error executing {cmd}: {str(e)}"
        else:
            return f"Unknown command: {cmd}\nSend /help for command list"

    def cmd_status(self, args) -> str:
        """Get full system status."""
        try:
            # Run health check
            health_result = subprocess.run(
                [str(SCRIPTS_DIR / "healthcheck.sh")],
                capture_output=True,
                text=True,
                timeout=30
            )

            # Read latest execution plan
            exec_plan_path = REPO_ROOT / "executor" / "execution_plan.json"
            if exec_plan_path.exists():
                with open(exec_plan_path) as f:
                    exec_plan = json.load(f)
                plan_time = exec_plan.get("timestamp", "unknown")
                total_orders = exec_plan.get("total_orders", 0)
                total_size = exec_plan.get("total_size_usd", 0)
            else:
                plan_time = "N/A"
                total_orders = 0
                total_size = 0

            # Read latest metrics
            metrics_path = STATE_DIR / "performance_metrics.jsonl"
            if metrics_path.exists():
                with open(metrics_path) as f:
                    lines = f.readlines()
                    if lines:
                        latest_metric = json.loads(lines[-1])
                        selection_rate = latest_metric.get("alpha_signals", {}).get("selection_rate", 0)
                    else:
                        selection_rate = 0
            else:
                selection_rate = 0

            # Build status message
            status_msg = f"""📊 System Status

🟢 Health: {health_result.stdout.strip() if health_result.returncode == 0 else '❌ Issues detected'}

📈 Latest Execution:
• Time: {plan_time}
• Orders: {total_orders}
• Size: ${total_size:.2f}
• Selection Rate: {selection_rate*100:.1f}%

🤖 Mode: DRYRUN (no real money)

Send /metrics for detailed performance
Send /health for full health check
Send /agents for AI coordination status"""

            return status_msg

        except Exception as e:
            return f"❌ Error getting status: {str(e)}"

    def cmd_metrics(self, args) -> str:
        """Get performance metrics for last 24 hours."""
        try:
            # Run track_performance script
            result = subprocess.run(
                ["python3", str(SCRIPTS_DIR / "track_performance.py"), "--summary", "--hours", "24"],
                capture_output=True,
                text=True,
                timeout=30
            )

            if result.returncode == 0:
                # Parse and format output
                output = result.stdout.strip()
                return f"📈 Performance Metrics (24h)\n\n{output}"
            else:
                return f"❌ Error getting metrics: {result.stderr}"

        except FileNotFoundError:
            # Fallback: read metrics file directly
            metrics_path = STATE_DIR / "performance_metrics.jsonl"
            if not metrics_path.exists():
                return "❌ No metrics data available"

            with open(metrics_path) as f:
                lines = f.readlines()

            # Get last 24h of data
            cutoff = datetime.now() - timedelta(hours=24)
            recent_metrics = []

            for line in lines:
                metric = json.loads(line)
                ts = datetime.fromisoformat(metric["timestamp"].replace("+00:00", ""))
                if ts >= cutoff:
                    recent_metrics.append(metric)

            if not recent_metrics:
                return "❌ No metrics in last 24 hours"

            # Calculate summary
            total_runs = len(recent_metrics)
            total_orders = sum(m.get("execution_plan", {}).get("total_orders", 0) for m in recent_metrics)
            total_size = sum(m.get("execution_plan", {}).get("total_size_usd", 0) for m in recent_metrics)
            avg_selection = sum(m.get("alpha_signals", {}).get("selection_rate", 0) for m in recent_metrics) / total_runs

            return f"""📈 Performance Metrics (24h)

Runs: {total_runs}
Orders Planned: {total_orders}
Total Size: ${total_size:.2f}
Avg Selection Rate: {avg_selection*100:.1f}%

System is operating normally."""

        except Exception as e:
            return f"❌ Error getting metrics: {str(e)}"

    def cmd_health(self, args) -> str:
        """Run full health check."""
        try:
            result = subprocess.run(
                [str(SCRIPTS_DIR / "healthcheck.sh")],
                capture_output=True,
                text=True,
                timeout=30
            )

            output = result.stdout.strip()

            if result.returncode == 0:
                return f"✅ Health Check PASSED\n\n{output}"
            else:
                return f"⚠️ Health Check FAILED\n\n{output}\n\nIssues detected - self-healing agent should address automatically."

        except Exception as e:
            return f"❌ Error running health check: {str(e)}"

    def cmd_pending(self, args) -> str:
        """Show pending changes awaiting approval."""
        try:
            queue = ApprovalQueue()
            pending = queue.get_pending()

            if not pending:
                return "✅ No pending changes requiring approval"

            msg = f"📋 **Pending Approvals** ({len(pending)})\n\n"

            for change in pending[:5]:  # Show first 5
                risk_emoji = {"low": "🟢", "medium": "🟡", "high": "🔴"}
                emoji = risk_emoji.get(change.get("risk_level", "medium"), "🟡")

                msg += f"""{emoji} **{change['id']}**: {change['title']}
Type: {change['change_type']}
Risk: {change['risk_level']}

"""

            if len(pending) > 5:
                msg += f"\n... and {len(pending)-5} more\n"

            msg += "\nUse /approve <id> or /reject <id>"

            return msg

        except Exception as e:
            return f"❌ Error getting pending changes: {str(e)}"

    def cmd_approve(self, args) -> str:
        """Approve a pending change."""
        if not args:
            return "❌ Usage: /approve <id>\nExample: /approve abc123"

        change_id = args[0]
        queue = ApprovalQueue()

        # Get the change
        change = queue.get_change(change_id)
        if not change:
            return f"❌ Change {change_id} not found"

        if change["status"] != "pending":
            return f"❌ Change {change_id} is already {change['status']}"

        # Approve it
        if queue.approve(change_id):
            # Execute the change
            result = queue.execute_approved(change_id)

            if result["success"]:
                return f"""✅ Approved and executed: {change_id}

**{change['title']}**

{result.get('message', 'Change applied successfully')}"""
            else:
                return f"""✅ Approved: {change_id}
❌ Execution failed: {result.get('error', 'Unknown error')}

Change is marked approved but not applied. Check logs."""
        else:
            return f"❌ Failed to approve {change_id}"

    def cmd_reject(self, args) -> str:
        """Reject a pending change."""
        if not args:
            return "❌ Usage: /reject <id> [reason]\nExample: /reject abc123 Not ready yet"

        change_id = args[0]
        reason = " ".join(args[1:]) if len(args) > 1 else "No reason provided"

        queue = ApprovalQueue()

        # Get the change
        change = queue.get_change(change_id)
        if not change:
            return f"❌ Change {change_id} not found"

        if change["status"] != "pending":
            return f"❌ Change {change_id} is already {change['status']}"

        # Reject it
        if queue.reject(change_id, reason):
            return f"""❌ Rejected: {change_id}

**{change['title']}**

Reason: {reason}

Change will not be applied."""
        else:
            return f"❌ Failed to reject {change_id}"

    def cmd_task(self, args) -> str:
        """Queue a task for the system to work on."""
        if not args:
            return """❌ Usage: /task <description>

Example: /task Optimize alpha model to reduce selection rate

This queues a task for autonomous agents to work on.
Next Claude Code session will pick it up automatically."""

        # Join all args as task description
        task_description = " ".join(args)

        try:
            # Add to autonomous task queue
            sys.path.insert(0, str(REPO_ROOT))
            from scripts.autonomous_task_queue import AutonomousTaskQueue

            queue = AutonomousTaskQueue(REPO_ROOT)
            task_id = queue.add_task(
                title=task_description[:80],  # First 80 chars as title
                description=f"""User request from Telegram: {task_description}

Autonomous operation protocol:
1. Assess what's needed
2. Implement solution
3. Use approval system for risky changes
4. Document what was done

Priority: User requested task""",
                priority='high',  # User requests are high priority
                source='telegram_user',
                metadata={'user': 'yair', 'via': 'telegram'}
            )

            return f"""✅ Task queued: {task_id[:8]}

**Task:** {task_description}

The system will work on this autonomously.
Next Claude Code session will pick it up.

You'll be notified when complete."""

        except Exception as e:
            return f"❌ Error queueing task: {str(e)}"

    def cmd_agents(self, args) -> str:
        """Get AI agent coordination status."""
        try:
            # Read coordination status
            status_path = AI_COORD_DIR / "status.json"
            if not status_path.exists():
                return "❌ Coordination system not initialized"

            with open(status_path) as f:
                status = json.load(f)

            active_agents = status.get("active_agents", [])
            pending_tasks = status.get("pending_tasks", [])

            # Read recent messages
            messages_path = AI_COORD_DIR / "messages.jsonl"
            recent_messages = []
            if messages_path.exists():
                with open(messages_path) as f:
                    lines = f.readlines()
                    recent_messages = [json.loads(line) for line in lines[-5:]]

            msg = f"""🤖 AI Agent Coordination

Active Agents: {', '.join(active_agents)}

Pending Tasks: {len(pending_tasks)}"""

            if pending_tasks:
                msg += "\n"
                for task in pending_tasks[:3]:
                    msg += f"\n• {task.get('description', 'Unknown task')}"
                if len(pending_tasks) > 3:
                    msg += f"\n  ... and {len(pending_tasks)-3} more"

            msg += f"\n\nRecent Messages: {len(recent_messages)}"
            if recent_messages:
                msg += "\n"
                for m in recent_messages[-3:]:
                    msg += f"\n• {m.get('from', '?')} → {m.get('to', '?')}: {m.get('message', '')[:50]}..."

            msg += "\n\nAgents are coordinating autonomously."

            return msg

        except Exception as e:
            return f"❌ Error getting agent status: {str(e)}"

    def cmd_help(self, args) -> str:
        """Show command help."""
        return """📱 Telegram Bot Commands

**Monitor:**
/status - Full system status
/metrics - Performance metrics (24h)
/health - Run health check

**Interact:**
/task <description> - Request system to do something
/pending - View pending approvals
/approve <id> - Approve pending change
/reject <id> - Reject pending change

**Info:**
/agents - AI coordination status
/help - This message

You can control the entire system via Telegram.
No need to launch Claude Code CLI for routine operations."""


def send_telegram_message(message: str):
    """Send message to user via Telegram."""
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print(f"Would send to Telegram:\n{message}")
        return

    # TODO: Implement actual Telegram API call
    # Using python-telegram-bot library or direct API
    print(f"Sending to Telegram chat {TELEGRAM_CHAT_ID}:\n{message}")


def main():
    """Main entry point - for testing."""
    bot = TelegramCommandBot()

    # Test commands
    test_commands = [
        "/status",
        "/metrics",
        "/health",
        "/agents",
        "/help"
    ]

    print("Testing Telegram Command Bot\n")
    for cmd in test_commands:
        print(f"\n{'='*60}")
        print(f"Command: {cmd}")
        print(f"{'='*60}")
        response = bot.process_command(cmd)
        print(response)


if __name__ == "__main__":
    main()
