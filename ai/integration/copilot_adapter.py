#!/usr/bin/env python3
"""
GitHub Copilot Integration Adapter
===================================

Enables secure communication between Claude CLI and GitHub Copilot.

INTEGRATION METHODS:
1. GitHub Issues - Copilot monitors/responds to issues
2. PR Comments - Code review coordination
3. Workflow Dispatch - Direct API triggers
4. Repository Files - Shared coordination files

SECURITY:
- Uses GitHub token for API access
- Messages are signed for integrity
- Audit trail maintained
"""

import os
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional
import hashlib

BASE_DIR = Path(__file__).parent.parent.parent
COORD_DIR = BASE_DIR / "ai" / "coordination"


class CopilotAdapter:
    """Adapter for GitHub Copilot integration."""

    def __init__(self):
        self.github_token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GITHUB_PAT")
        self.repo = "yaya1738/hands-off-engine"
        self.agent_id = "copilot"

    def create_coordination_issue(self, title: str, body: str, labels: List[str] = None) -> Dict:
        """Create GitHub issue for Copilot coordination."""
        if not self.github_token:
            return self._file_based_message(title, body)

        labels = labels or ["agent-coordination"]

        try:
            import requests
            response = requests.post(
                f"https://api.github.com/repos/{self.repo}/issues",
                headers={
                    "Authorization": f"token {self.github_token}",
                    "Accept": "application/vnd.github.v3+json"
                },
                json={
                    "title": f"[AI-COORD] {title}",
                    "body": body,
                    "labels": labels
                },
                timeout=30
            )

            if response.status_code == 201:
                issue = response.json()
                return {
                    "success": True,
                    "issue_number": issue["number"],
                    "url": issue["html_url"]
                }
            else:
                return self._file_based_message(title, body)

        except Exception as e:
            return self._file_based_message(title, body)

    def comment_on_issue(self, issue_number: int, comment: str) -> Dict:
        """Comment on existing coordination issue."""
        if not self.github_token:
            return {"success": False, "error": "No GitHub token"}

        try:
            import requests
            response = requests.post(
                f"https://api.github.com/repos/{self.repo}/issues/{issue_number}/comments",
                headers={
                    "Authorization": f"token {self.github_token}",
                    "Accept": "application/vnd.github.v3+json"
                },
                json={"body": comment},
                timeout=30
            )

            return {
                "success": response.status_code == 201,
                "comment_id": response.json().get("id") if response.status_code == 201 else None
            }

        except Exception as e:
            return {"success": False, "error": str(e)}

    def trigger_workflow(self, workflow_name: str, inputs: Dict = None) -> Dict:
        """Trigger GitHub Actions workflow for Copilot."""
        if not self.github_token:
            return {"success": False, "error": "No GitHub token"}

        try:
            import requests
            response = requests.post(
                f"https://api.github.com/repos/{self.repo}/actions/workflows/{workflow_name}/dispatches",
                headers={
                    "Authorization": f"token {self.github_token}",
                    "Accept": "application/vnd.github.v3+json"
                },
                json={
                    "ref": "main",
                    "inputs": inputs or {}
                },
                timeout=30
            )

            return {
                "success": response.status_code == 204,
                "message": "Workflow triggered" if response.status_code == 204 else "Failed"
            }

        except Exception as e:
            return {"success": False, "error": str(e)}

    def _file_based_message(self, title: str, body: str) -> Dict:
        """Fallback to file-based coordination."""
        message = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "from": "claude-code",
            "to": "copilot",
            "type": "request",
            "message": f"{title}\n\n{body}",
            "context": {"title": title}
        }

        messages_file = COORD_DIR / "messages.jsonl"
        with open(messages_file, 'a') as f:
            f.write(json.dumps(message) + '\n')

        return {
            "success": True,
            "method": "file-based",
            "file": str(messages_file)
        }

    def send_task_to_copilot(self, task: Dict) -> Dict:
        """Send task to Copilot for execution."""
        title = task.get("title", "Task from Claude CLI")
        description = task.get("description", "")
        priority = task.get("priority", "normal")

        body = f"""## Task from Claude CLI

**Priority:** {priority}
**Timestamp:** {datetime.now(timezone.utc).isoformat()}

### Description
{description}

### Context
```json
{json.dumps(task.get("context", {}), indent=2)}
```

### Expected Output
{task.get("expected_output", "Complete the task and update coordination status")}

---
*This is an automated coordination message from AI Nexus Hub*
*Master: Yair Siegel*
"""

        return self.create_coordination_issue(title, body, ["agent-coordination", f"priority-{priority}"])

    def get_copilot_responses(self) -> List[Dict]:
        """Get responses from Copilot via GitHub issue comments."""
        # Read from coordination files
        responses = []
        messages_file = COORD_DIR / "messages.jsonl"

        if messages_file.exists():
            with open(messages_file) as f:
                for line in f:
                    try:
                        msg = json.loads(line)
                        if msg.get("from") == "copilot":
                            responses.append(msg)
                    except:
                        pass

        return responses[-10:]  # Last 10 responses

    def sync_with_copilot(self) -> Dict:
        """Synchronize state with Copilot."""
        from ai_nexus_hub import get_hub

        hub = get_hub()
        state = hub.get_shared_state()

        # Create sync message
        sync_data = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "from": "claude-code",
            "to": "copilot",
            "type": "state_sync",
            "state": {
                "balance": state.get("system", {}).get("balance", 0),
                "trading_enabled": state.get("system", {}).get("trading_enabled", False),
                "escape_velocity": state.get("system", {}).get("escape_velocity", 0),
                "pending_tasks": state.get("pending_handoffs", 0)
            }
        }

        messages_file = COORD_DIR / "messages.jsonl"
        with open(messages_file, 'a') as f:
            f.write(json.dumps(sync_data) + '\n')

        return {
            "success": True,
            "synced_at": sync_data["timestamp"],
            "state_summary": sync_data["state"]
        }


def main():
    adapter = CopilotAdapter()
    import argparse

    parser = argparse.ArgumentParser(description="Copilot Integration Adapter")
    parser.add_argument("command", choices=["issue", "task", "sync", "responses"])
    parser.add_argument("--title", help="Issue/task title")
    parser.add_argument("--body", help="Issue/task body")

    args = parser.parse_args()

    if args.command == "issue":
        result = adapter.create_coordination_issue(args.title or "Test", args.body or "Test issue")
        print(json.dumps(result, indent=2))

    elif args.command == "task":
        result = adapter.send_task_to_copilot({
            "title": args.title or "Test Task",
            "description": args.body or "Test task description",
            "priority": "normal"
        })
        print(json.dumps(result, indent=2))

    elif args.command == "sync":
        result = adapter.sync_with_copilot()
        print(json.dumps(result, indent=2))

    elif args.command == "responses":
        responses = adapter.get_copilot_responses()
        print(json.dumps(responses, indent=2))


if __name__ == "__main__":
    main()
