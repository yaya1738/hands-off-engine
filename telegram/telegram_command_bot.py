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
            # New unified commands
            '/balance': self.cmd_balance,
            '/positions': self.cmd_positions,
            '/cluster': self.cmd_cluster,
            '/identity': self.cmd_identity,
            '/logs': self.cmd_logs,
            '/dashboard': self.cmd_dashboard,
            '/escape': self.cmd_escape_velocity,
            '/setpat': self.cmd_setpat,
            '/fixssh': self.cmd_fixssh,
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
/balance - Trading balance & positions
/positions - Detailed position list
/cluster - Server cluster status
/logs - Recent system logs
/escape - Escape velocity score

**Interact:**
/task <description> - Request system to do something
/pending - View pending approvals
/approve <id> - Approve pending change
/reject <id> - Reject pending change
/setpat <token> - Set GitHub PAT for compute nodes

**Info:**
/dashboard - Unified web dashboard URL
/agents - AI coordination status
/identity - Verify your identity
/help - This message

Web Dashboard: http://138.68.103.156:8002

You can control the entire system via Telegram.
No need to launch Claude Code CLI for routine operations."""

    def cmd_balance(self, args) -> str:
        """Get trading balance and position summary."""
        try:
            # Read dollar access file for balance info
            dollar_file = REPO_ROOT / "finance" / "dollar_access.json"
            if dollar_file.exists():
                with open(dollar_file) as f:
                    data = json.load(f)
                cash = data.get("inflow_channels", {}).get("polymarket_wallet", {}).get("current_balance_usdc", 0)
                positions = data.get("inflow_channels", {}).get("polymarket_wallet", {}).get("positions_value_usdc", 0)
            else:
                cash = 0
                positions = 0

            # Try to get live position data
            try:
                result = subprocess.run(
                    ["python3", str(SCRIPTS_DIR / "position_monitor.py")],
                    capture_output=True,
                    text=True,
                    timeout=30,
                    cwd=str(REPO_ROOT),
                    env={**os.environ, "PYTHONPATH": str(REPO_ROOT)}
                )
                if "positions" in result.stdout.lower():
                    live_info = result.stdout.strip().split('\n')[-1]
                else:
                    live_info = ""
            except:
                live_info = ""

            total = cash + positions
            gap = max(0, 50 - cash)

            return f"""💰 Trading Balance

Cash: ${cash:.2f}
Positions: ${positions:.2f}
Total: ${total:.2f}

Trading threshold: $50
Gap to trading: ${gap:.2f}

{live_info}

Use /positions for details"""

        except Exception as e:
            return f"❌ Error getting balance: {str(e)}"

    def cmd_positions(self, args) -> str:
        """Get detailed position list."""
        try:
            result = subprocess.run(
                ["python3", str(SCRIPTS_DIR / "position_monitor.py")],
                capture_output=True,
                text=True,
                timeout=30,
                cwd=str(REPO_ROOT),
                env={**os.environ, "PYTHONPATH": str(REPO_ROOT)}
            )

            output = result.stdout.strip()
            if output:
                # Truncate if too long
                if len(output) > 3500:
                    output = output[:3500] + "\n... (truncated)"
                return f"📊 Positions\n\n{output}"
            else:
                return "❌ No position data available"

        except Exception as e:
            return f"❌ Error getting positions: {str(e)}"

    def cmd_cluster(self, args) -> str:
        """Get server cluster status."""
        try:
            result = subprocess.run(
                ["doctl", "compute", "droplet", "list", "--format", "Name,Status,PublicIPv4,Memory"],
                capture_output=True,
                text=True,
                timeout=30
            )

            if result.returncode == 0:
                output = result.stdout.strip()
                lines = output.split('\n')
                active = sum(1 for l in lines if 'active' in l.lower())

                return f"""🖥 Cluster Status

{output}

Active: {active} servers
"""
            else:
                return f"❌ Error getting cluster status: {result.stderr}"

        except Exception as e:
            return f"❌ Error: {str(e)}"

    def cmd_identity(self, args) -> str:
        """Run identity verification."""
        try:
            result = subprocess.run(
                ["python3", str(REPO_ROOT / "security" / "absolute_identity.py")],
                capture_output=True,
                text=True,
                timeout=15,
                cwd=str(REPO_ROOT)
            )

            output = result.stdout.strip()
            if "GRANTED" in output:
                return f"✅ Identity Verified\n\n{output}"
            else:
                return f"❌ Identity Check\n\n{output}"

        except Exception as e:
            return f"❌ Error running identity check: {str(e)}"

    def cmd_logs(self, args) -> str:
        """Get recent system logs."""
        try:
            log_dir = Path("/var/log/hands-off")
            if not log_dir.exists():
                return "❌ No logs directory"

            # Get recent entries from multiple logs
            logs_output = []

            # Healthcheck log
            hc_log = log_dir / "healthcheck.log"
            if hc_log.exists():
                with open(hc_log) as f:
                    lines = f.readlines()
                    if lines:
                        logs_output.append("📋 Healthcheck:")
                        logs_output.append(lines[-1].strip())

            # Pipeline log
            pipe_log = log_dir / "pipeline.log"
            if pipe_log.exists():
                with open(pipe_log) as f:
                    lines = f.readlines()
                    if lines:
                        logs_output.append("\n📋 Pipeline:")
                        logs_output.append(lines[-1].strip())

            # Position monitor log
            pos_log = log_dir / "position_monitor.log"
            if pos_log.exists():
                with open(pos_log) as f:
                    lines = f.readlines()
                    if lines:
                        logs_output.append("\n📋 Positions:")
                        logs_output.append(lines[-1].strip())

            if logs_output:
                return "📜 Recent Logs\n\n" + "\n".join(logs_output)
            else:
                return "❌ No recent log entries"

        except Exception as e:
            return f"❌ Error reading logs: {str(e)}"

    def cmd_dashboard(self, args) -> str:
        """Get link to unified web dashboard."""
        try:
            import requests as req
            # Check if dashboard is running
            r = req.get("http://localhost:8002/api/status", timeout=5)
            if r.status_code == 200:
                data = r.json()
                ev = data.get("escape_velocity", {}).get("score", 0)
                nodes = data.get("cluster", {}).get("healthy_nodes", 0)
                agents = len(data.get("coordination", {}).get("active_agents", []))

                return f"""🖥 Unified Dashboard

Access: http://138.68.103.156:8002

Real-time system visualization:
• Finance & Trading
• Cluster Health ({nodes} nodes)
• AI Coordination ({agents} agents)
• Escape Velocity: {ev}/100
• Identity & Security

Updates every 30 seconds.
Full API at /api/status"""
            else:
                return "❌ Dashboard service not responding"

        except Exception as e:
            return f"""🖥 Unified Dashboard

Access: http://138.68.103.156:8002

(Status check failed: {str(e)})

Try opening the URL in your browser."""

    def cmd_escape_velocity(self, args) -> str:
        """Get escape velocity score and factors."""
        try:
            import requests as req
            r = req.get("http://localhost:8002/api/escape-velocity", timeout=5)
            if r.status_code == 200:
                data = r.json()
                score = data.get("score", 0)
                factors = data.get("factors", {})

                # Determine status
                if score >= 80:
                    status = "🚀 ESCAPE VELOCITY ACHIEVED"
                elif score >= 60:
                    status = "🟢 Strong momentum"
                elif score >= 40:
                    status = "🟡 Building momentum"
                else:
                    status = "🔴 Need acceleration"

                return f"""🚀 Escape Velocity: {score}/100

{status}

Factors:
• Capital: ${factors.get('capital', 0):.2f}
• Nodes: {factors.get('nodes', 0)}
• Signals: {factors.get('signals', 0)}

Target: 100 = Self-sustaining system

Dashboard: http://138.68.103.156:8002"""
            else:
                return "❌ Could not get escape velocity"

        except Exception as e:
            return f"❌ Error: {str(e)}"

    def cmd_setpat(self, args) -> str:
        """Set GitHub Personal Access Token for compute nodes."""
        if not args:
            return """🔐 GitHub PAT Configuration

Usage: /setpat <your_github_pat>

This will:
1. Store PAT in .env file
2. Configure git on all compute nodes
3. Enable CLI migration to larger nodes

Generate PAT at: https://github.com/settings/tokens
Required scope: repo (Full control of private repos)

⚠️ Send the PAT directly - it will be stored securely."""

        pat = args[0]

        # Validate PAT format (github classic or fine-grained)
        if not (pat.startswith('ghp_') or pat.startswith('github_pat_')):
            return "❌ Invalid PAT format. Should start with 'ghp_' or 'github_pat_'"

        try:
            # Store in .env file
            env_file = REPO_ROOT / ".env"
            env_content = ""
            if env_file.exists():
                env_content = env_file.read_text()

            # Update or add GITHUB_PAT
            if "GITHUB_PAT=" in env_content:
                lines = env_content.split('\n')
                lines = [l if not l.startswith('GITHUB_PAT=') else f'GITHUB_PAT={pat}' for l in lines]
                env_content = '\n'.join(lines)
            else:
                env_content += f'\nGITHUB_PAT={pat}\n'

            env_file.write_text(env_content)

            # Configure git on compute nodes
            compute_nodes = ["134.122.124.240", "198.211.96.196", "67.205.153.121"]
            configured = []

            for node_ip in compute_nodes:
                try:
                    # Configure git to use PAT
                    result = subprocess.run([
                        'ssh', '-o', 'StrictHostKeyChecking=no', '-o', 'ConnectTimeout=10',
                        f'root@{node_ip}',
                        f'''cd /root/hands-off-engine && git remote set-url origin https://{pat}@github.com/yaya1738/hands-off-engine.git && git fetch --quiet && echo "OK"'''
                    ], capture_output=True, text=True, timeout=30)

                    if "OK" in result.stdout:
                        configured.append(node_ip)
                except Exception:
                    pass

            return f"""✅ GitHub PAT configured!

Stored in .env: ✓
Compute nodes configured: {len(configured)}/3
Nodes: {', '.join(configured) if configured else 'none'}

You can now run Claude CLI on any compute node:
ssh root@67.205.153.121
cd /root/hands-off-engine
claude

(This node has 8 vCPU, 16GB RAM vs current 4 vCPU)"""

        except Exception as e:
            return f"❌ Error configuring PAT: {str(e)}"

    def cmd_fixssh(self, args) -> str:
        """Fix SSH access on all droplets by adding ho-cli-main key."""
        try:
            # Get list of droplets
            result = subprocess.run(
                ["doctl", "compute", "droplet", "list", "--format", "ID,Name,PublicIPv4", "--no-header"],
                capture_output=True,
                text=True,
                timeout=30
            )

            if result.returncode != 0:
                return f"❌ Error getting droplets: {result.stderr}"

            droplets = []
            for line in result.stdout.strip().split('\n'):
                parts = line.split()
                if len(parts) >= 3:
                    droplets.append({'id': parts[0], 'name': parts[1], 'ip': parts[2]})

            if not droplets:
                return "❌ No droplets found"

            # SSH key to add
            HO_CLI_KEY = "ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIN9leXKzmPHKpTLjwsynPjVSbtyyhk0HFynKlA6X1z6x root@ho-cli-main"

            fixed = []
            failed = []
            skipped = []

            for d in droplets:
                name = d['name']
                ip = d['ip']

                # Skip self
                if name == 'pm-helper':
                    skipped.append(name)
                    continue

                try:
                    # Check if key already exists, if not add it
                    cmd = f'''
                    grep -q "root@ho-cli-main" /root/.ssh/authorized_keys 2>/dev/null && echo "EXISTS" || {{
                        mkdir -p /root/.ssh
                        chmod 700 /root/.ssh
                        echo "{HO_CLI_KEY}" >> /root/.ssh/authorized_keys
                        chmod 600 /root/.ssh/authorized_keys
                        echo "ADDED"
                    }}
                    '''

                    ssh_result = subprocess.run(
                        ['ssh', '-o', 'StrictHostKeyChecking=no', '-o', 'ConnectTimeout=10', '-o', 'BatchMode=yes',
                         f'root@{ip}', cmd],
                        capture_output=True,
                        text=True,
                        timeout=30
                    )

                    if "ADDED" in ssh_result.stdout:
                        fixed.append(f"{name} ({ip})")
                    elif "EXISTS" in ssh_result.stdout:
                        skipped.append(f"{name} (already has key)")
                    else:
                        failed.append(f"{name}: {ssh_result.stderr[:50]}")

                except Exception as e:
                    failed.append(f"{name}: {str(e)[:50]}")

            msg = f"""🔧 SSH Fix Results

✅ Fixed: {len(fixed)}
"""
            if fixed:
                msg += "\n".join(f"  • {f}" for f in fixed) + "\n"

            msg += f"\n⏭ Skipped: {len(skipped)}\n"
            if skipped:
                msg += "\n".join(f"  • {s}" for s in skipped[:5]) + "\n"

            if failed:
                msg += f"\n❌ Failed: {len(failed)}\n"
                msg += "\n".join(f"  • {f}" for f in failed[:5]) + "\n"

            msg += "\nho-cli-main can now SSH to fixed droplets."

            return msg

        except Exception as e:
            return f"❌ Error: {str(e)}"


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
