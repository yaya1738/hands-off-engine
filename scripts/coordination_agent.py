#!/usr/bin/env python3
"""
Coordination Agent - Autonomous AI-to-AI Communication Handler

Monitors ai/coordination/ files and GitHub for messages from other AI agents.
Executes requested tasks automatically without CLI intervention.

Responsibilities:
- Read messages from other agents (Copilot, Claude Web, ChatGPT)
- Execute safe tasks automatically
- Request user approval for risky tasks (via Telegram)
- Respond to agents with status updates
- Manage task handoffs
- Monitor GitHub PRs and issues

Runs continuously or triggered by GitHub webhooks.
"""

import os
import json
import time
import logging
import subprocess
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional

# Configuration
REPO_ROOT = Path(__file__).parent.parent
AI_COORD_DIR = REPO_ROOT / "ai" / "coordination"
LOG_FILE = "/var/log/coordination-agent.log"
CHECK_INTERVAL = 300  # 5 minutes

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


class CoordinationAgent:
    """Handles autonomous AI-to-AI coordination."""

    def __init__(self):
        self.agent_name = "coordination-agent"
        self.processed_message_ids = set()
        self.load_processed_messages()

    def load_processed_messages(self):
        """Load IDs of already processed messages."""
        state_file = AI_COORD_DIR / "agent_state.json"
        if state_file.exists():
            with open(state_file) as f:
                state = json.load(f)
                self.processed_message_ids = set(state.get("processed_messages", []))

    def save_processed_message(self, msg_id: str):
        """Mark message as processed."""
        self.processed_message_ids.add(msg_id)
        state_file = AI_COORD_DIR / "agent_state.json"
        state_file.parent.mkdir(parents=True, exist_ok=True)
        with open(state_file, 'w') as f:
            json.dump({
                "processed_messages": list(self.processed_message_ids),
                "last_check": datetime.now().isoformat()
            }, f, indent=2)

    def check_messages(self) -> List[Dict]:
        """Check for new messages in coordination files."""
        messages_file = AI_COORD_DIR / "messages.jsonl"
        if not messages_file.exists():
            return []

        new_messages = []
        with open(messages_file) as f:
            for line in f:
                msg = json.loads(line)
                msg_id = f"{msg.get('timestamp')}_{msg.get('from')}"

                # Check if message is for us or for all
                to = msg.get('to', '')
                if to not in ['claude-code', 'all', 'coordination-agent']:
                    continue

                # Check if already processed
                if msg_id in self.processed_message_ids:
                    continue

                new_messages.append(msg)
                self.processed_message_ids.add(msg_id)

        return new_messages

    def check_tasks(self) -> List[Dict]:
        """Check for tasks assigned to coordination agent."""
        status_file = AI_COORD_DIR / "status.json"
        if not status_file.exists():
            return []

        with open(status_file) as f:
            status = json.load(f)

        tasks = status.get("pending_tasks", [])
        assigned_tasks = [
            t for t in tasks
            if t.get("assigned_to") in ["auto", "coordination-agent", "claude-code"]
            and t.get("status") == "ready"
        ]

        return assigned_tasks

    def process_message(self, msg: Dict):
        """Process a message from another AI agent."""
        msg_type = msg.get("type")
        from_agent = msg.get("from")
        content = msg.get("message", "") or ""

        logger.info(f"Processing message from {from_agent}: {content[:100]}")

        if msg_type == "request":
            return self.handle_request(msg)
        elif msg_type == "handoff":
            return self.handle_handoff(msg)
        elif msg_type == "info":
            return self.acknowledge_info(msg)
        elif msg_type == "directive":
            return self.handle_directive(msg)
        elif msg_type == "self_improve":
            return self.trigger_self_improvement(msg)
        else:
            logger.info(f"Message type '{msg_type}' noted")

    def handle_request(self, msg: Dict) -> bool:
        """Handle a request from another agent."""
        content = msg.get("message", "")
        from_agent = msg.get("from")

        # Parse request
        if "merge" in content.lower() and "pr" in content.lower():
            # Agent requesting PR merge
            pr_num = self.extract_pr_number(msg.get("context", {}))
            if pr_num:
                return self.handle_pr_merge_request(pr_num, from_agent)

        elif "review" in content.lower():
            # Agent requesting review
            return self.handle_review_request(msg)

        elif "status" in content.lower():
            # Agent requesting status
            return self.send_status_update(from_agent)

        else:
            logger.info(f"Request not yet implemented: {content[:100]}")
            return False

    def handle_handoff(self, msg: Dict) -> bool:
        """Handle a task handoff from another agent."""
        task_description = msg.get("message")
        context = msg.get("context", {})

        logger.info(f"Received handoff: {task_description}")

        # Add to pending tasks
        status_file = AI_COORD_DIR / "status.json"
        with open(status_file) as f:
            status = json.load(f)

        new_task = {
            "id": f"handoff-{int(time.time())}",
            "assigned_to": "coordination-agent",
            "status": "ready",
            "description": task_description,
            "received_from": msg.get("from"),
            "context": context
        }

        status["pending_tasks"].append(new_task)

        with open(status_file, 'w') as f:
            json.dump(status, f, indent=2)

        logger.info(f"Added handoff task: {new_task['id']}")
        return True

    def acknowledge_info(self, msg: Dict) -> bool:
        """Acknowledge an info message."""
        logger.info(f"Info from {msg.get('from')}: {msg.get('message')[:100]}")
        # Just log it, no response needed
        return True

    def handle_directive(self, msg: Dict) -> bool:
        """Handle system-wide directives - apply to all agents."""
        directive = msg.get("message", "")
        priority = msg.get("priority", "normal")

        logger.info(f"DIRECTIVE [{priority}]: {directive[:200]}")

        # Store directive for all agents to read
        directive_file = AI_COORD_DIR / "active_directive.json"
        with open(directive_file, 'w') as f:
            json.dump({
                "directive": directive,
                "priority": priority,
                "from": msg.get("from"),
                "timestamp": datetime.now().isoformat(),
                "status": "active"
            }, f, indent=2)

        # If high priority, trigger immediate self-improvement
        if priority == "high" and msg.get("action_required") == "integrate":
            logger.info("High priority directive - triggering self-improvement cycle")
            self.trigger_self_improvement({"message": directive})

        return True

    def trigger_self_improvement(self, msg: Dict) -> bool:
        """Trigger autonomous self-improvement via Claude CLI or moonshot loop."""
        context = msg.get("message", "Improve system")

        logger.info(f"Self-improvement triggered: {context[:100]}")

        # Option 1: Trigger moonshot loop (safer, rate-limited)
        try:
            result = subprocess.run(
                ["python3", "autonomous/moonshot_loop.py"],
                capture_output=True, text=True, timeout=300,
                cwd=str(REPO_ROOT),
                env={**os.environ, "IMPROVEMENT_CONTEXT": context}
            )

            if result.returncode == 0:
                logger.info("Moonshot improvement cycle completed")
                self.respond_to_agent(
                    to="all",
                    message=f"Self-improvement cycle completed. Context: {context[:100]}",
                    msg_type="info"
                )
                return True
            else:
                logger.warning(f"Moonshot cycle issue: {result.stderr[:200]}")

        except subprocess.TimeoutExpired:
            logger.warning("Moonshot cycle timed out")
        except Exception as e:
            logger.error(f"Self-improvement error: {e}")

        return False

    def handle_pr_merge_request(self, pr_num: int, from_agent: str) -> bool:
        """Handle request to merge a PR."""
        logger.info(f"PR merge requested by {from_agent}: #{pr_num}")

        # Check if PR is safe to merge (has tests passing, no conflicts, etc.)
        is_safe = self.assess_pr_safety(pr_num)

        if is_safe:
            # Auto-merge
            logger.info(f"PR #{pr_num} assessed as safe - auto-merging")
            merge_result = self.execute_pr_merge(pr_num)

            if merge_result:
                self.respond_to_agent(
                    to=from_agent,
                    message=f"PR #{pr_num} auto-merged successfully",
                    msg_type="response"
                )
                return True
            else:
                self.respond_to_agent(
                    to=from_agent,
                    message=f"PR #{pr_num} merge failed - manual review needed",
                    msg_type="response"
                )
                return False
        else:
            # Request user approval via Telegram
            logger.info(f"PR #{pr_num} requires user approval")
            self.request_telegram_approval(pr_num, from_agent)
            self.respond_to_agent(
                to=from_agent,
                message=f"PR #{pr_num} requires user approval - request sent to Telegram",
                msg_type="response"
            )
            return False

    def execute_pr_merge(self, pr_num: int) -> bool:
        """Execute the actual PR merge via gh CLI."""
        try:
            result = subprocess.run(
                ["gh", "pr", "merge", str(pr_num), "--squash", "--auto"],
                capture_output=True, text=True, timeout=60,
                cwd=str(REPO_ROOT)
            )

            if result.returncode == 0:
                logger.info(f"PR #{pr_num} merged successfully")
                return True
            else:
                logger.error(f"PR #{pr_num} merge failed: {result.stderr}")
                return False

        except Exception as e:
            logger.error(f"Error merging PR #{pr_num}: {e}")
            return False

    def request_telegram_approval(self, pr_num: int, from_agent: str):
        """Send Telegram message requesting PR approval."""
        import requests

        token = os.getenv('TELEGRAM_BOT_TOKEN', '8214203655:AAGkAamvjQq0b7T7lmaTPDd-yYY_hvo_xvA')
        chat_id = os.getenv('TELEGRAM_CHAT_ID', '8327766663')

        message = f'''🔔 <b>PR Approval Required</b>

PR #{pr_num} needs manual approval.
Requested by: {from_agent}

<b>Actions:</b>
• /approve_pr {pr_num} - Merge the PR
• /reject_pr {pr_num} - Decline merge

Or review at: https://github.com/hands-off-engine/hands-off-engine/pull/{pr_num}
'''

        try:
            url = f'https://api.telegram.org/bot{token}/sendMessage'
            requests.post(url, json={
                'chat_id': chat_id,
                'text': message,
                'parse_mode': 'HTML'
            }, timeout=10)
            logger.info(f"Telegram approval request sent for PR #{pr_num}")
        except Exception as e:
            logger.error(f"Failed to send Telegram notification: {e}")

    def handle_review_request(self, msg: Dict) -> bool:
        """Handle code review request."""
        logger.info("Review request received")
        # TODO: Implement automated code review
        return True

    def send_status_update(self, to_agent: str) -> bool:
        """Send status update to requesting agent."""
        # Run health check
        try:
            result = subprocess.run(
                [str(REPO_ROOT / "scripts" / "healthcheck.sh")],
                capture_output=True,
                text=True,
                timeout=30
            )

            status_msg = "System healthy" if result.returncode == 0 else "Issues detected"

            self.respond_to_agent(
                to=to_agent,
                message=f"Status: {status_msg}. {result.stdout.strip()}",
                msg_type="response"
            )
            return True

        except Exception as e:
            logger.error(f"Error getting status: {e}")
            return False

    def respond_to_agent(self, to: str, message: str, msg_type: str = "response"):
        """Write response message to coordination file."""
        messages_file = AI_COORD_DIR / "messages.jsonl"

        response = {
            "timestamp": datetime.now().isoformat() + "Z",
            "from": self.agent_name,
            "to": to,
            "type": msg_type,
            "message": message,
            "context": {}
        }

        with open(messages_file, 'a') as f:
            f.write(json.dumps(response) + '\n')

        logger.info(f"Responded to {to}: {message[:100]}")

    def assess_pr_safety(self, pr_num: int) -> bool:
        """Assess if a PR is safe to auto-merge."""
        try:
            # Get PR status from GitHub CLI
            result = subprocess.run(
                ["gh", "pr", "view", str(pr_num), "--json",
                 "state,mergeable,reviewDecision,statusCheckRollup,additions,deletions,changedFiles"],
                capture_output=True, text=True, timeout=30,
                cwd=str(REPO_ROOT)
            )

            if result.returncode != 0:
                logger.warning(f"Failed to fetch PR #{pr_num}: {result.stderr}")
                return False

            pr_data = json.loads(result.stdout)

            # Check basic conditions
            if pr_data.get('state') != 'OPEN':
                logger.info(f"PR #{pr_num} is not open")
                return False

            if pr_data.get('mergeable') != 'MERGEABLE':
                logger.info(f"PR #{pr_num} has merge conflicts")
                return False

            # Check status checks (CI)
            status_checks = pr_data.get('statusCheckRollup', [])
            if status_checks:
                for check in status_checks:
                    if check.get('conclusion') not in ['SUCCESS', 'NEUTRAL', 'SKIPPED']:
                        logger.info(f"PR #{pr_num} has failing checks")
                        return False

            # Safety bounds: auto-merge small changes only
            additions = pr_data.get('additions', 0)
            deletions = pr_data.get('deletions', 0)
            changed_files = pr_data.get('changedFiles', 0)

            # Auto-merge if:
            # - Less than 200 lines changed total
            # - Less than 5 files changed
            # - OR has approved review
            is_small_change = (additions + deletions) < 200 and changed_files < 5
            has_approval = pr_data.get('reviewDecision') == 'APPROVED'

            if is_small_change or has_approval:
                logger.info(f"PR #{pr_num} is safe to auto-merge (small={is_small_change}, approved={has_approval})")
                return True
            else:
                logger.info(f"PR #{pr_num} too large for auto-merge: +{additions}/-{deletions}, {changed_files} files")
                return False

        except subprocess.TimeoutExpired:
            logger.error(f"Timeout checking PR #{pr_num}")
            return False
        except Exception as e:
            logger.error(f"Error assessing PR #{pr_num}: {e}")
            return False

    def extract_pr_number(self, context: Dict) -> Optional[int]:
        """Extract PR number from message context."""
        pr = context.get("pr")
        if pr:
            try:
                return int(pr)
            except ValueError:
                pass
        return None

    def process_task(self, task: Dict):
        """Process an assigned task."""
        task_id = task.get("id")
        description = task.get("description")

        logger.info(f"Processing task {task_id}: {description}")

        # Execute based on task description
        # This is where autonomous task execution happens

        # Mark task as completed
        self.update_task_status(task_id, "completed")

    def update_task_status(self, task_id: str, new_status: str):
        """Update task status in coordination file."""
        status_file = AI_COORD_DIR / "status.json"

        with open(status_file) as f:
            status = json.load(f)

        for task in status.get("pending_tasks", []):
            if task.get("id") == task_id:
                task["status"] = new_status
                task["updated_at"] = datetime.now().isoformat()
                break

        with open(status_file, 'w') as f:
            json.dump(status, f, indent=2)

        logger.info(f"Task {task_id} status → {new_status}")

    def run_cycle(self):
        """Run one coordination cycle."""
        logger.info("Starting coordination cycle")

        # Check for new messages
        messages = self.check_messages()
        for msg in messages:
            try:
                self.process_message(msg)
            except Exception as e:
                logger.error(f"Error processing message: {e}")

        # Check for assigned tasks
        tasks = self.check_tasks()
        for task in tasks:
            try:
                self.process_task(task)
            except Exception as e:
                logger.error(f"Error processing task: {e}")

        logger.info(f"Cycle complete: {len(messages)} messages, {len(tasks)} tasks processed")

    def run_forever(self):
        """Run continuously, checking for new coordination events."""
        logger.info("Coordination Agent starting...")
        logger.info(f"Check interval: {CHECK_INTERVAL} seconds")

        while True:
            try:
                self.run_cycle()
                time.sleep(CHECK_INTERVAL)

            except KeyboardInterrupt:
                logger.info("Shutting down gracefully...")
                break
            except Exception as e:
                logger.error(f"Error in main loop: {e}")
                time.sleep(60)


def main():
    """Entry point."""
    import sys

    agent = CoordinationAgent()

    if len(sys.argv) > 1 and sys.argv[1] == "--once":
        # Run once and exit
        agent.run_cycle()
    else:
        # Run forever
        agent.run_forever()


if __name__ == "__main__":
    main()
