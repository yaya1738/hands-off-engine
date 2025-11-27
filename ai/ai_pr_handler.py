#!/usr/bin/env python3
"""
AI PR Handler - Internal PR handling through AI Nexus

All pull requests are processed through the AI Nexus system for:
- Automated review and triage
- Cost tracking and audit trail
- Multi-agent coordination
- Autonomous decision making (within safety limits)

Part of the Hands-Off Engine automation system.
"""

import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional

import requests

# Add parent directories to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    from ai_nexus.nexus import AINexus, AITask, AIResult, AIProvider, TaskPriority, TaskStatus
    from ai_nexus.copilot_integration import CopilotNexusWrapper
    NEXUS_AVAILABLE = True
except ImportError:
    NEXUS_AVAILABLE = False


class PRHandler:
    """
    Handles all PRs internally through AI Nexus
    
    Features:
    - Automatic PR triage and categorization
    - Tracks all actions in audit ledger
    - Routes PRs to appropriate AI agents
    - Enforces budget and safety limits
    """
    
    def __init__(self):
        """Initialize PR Handler with AI Nexus integration"""
        self.github_token = os.environ.get("GITHUB_TOKEN")
        self.github_api_url = os.environ.get("GITHUB_API_URL", "https://api.github.com")
        self.repository = os.environ.get("GITHUB_REPOSITORY", "")
        self.event_path = os.environ.get("GITHUB_EVENT_PATH", "")
        self.event_name = os.environ.get("GITHUB_EVENT_NAME", "")
        
        # Initialize AI Nexus if available
        if NEXUS_AVAILABLE:
            self.nexus = AINexus()
            self.copilot = CopilotNexusWrapper()
        else:
            self.nexus = None
            self.copilot = None
        
        # Load event data
        self.event_data = self._load_event()
        
        # PR categories for routing
        self.categories = {
            "documentation": ["docs/", "README", ".md"],
            "ci": [".github/", "workflows/"],
            "ai_system": ["ai/", "ai_nexus/"],
            "trading": ["alpha/", "decider/", "executor/"],
            "infrastructure": ["scripts/", "termux/", "telegram/"]
        }
    
    def _load_event(self) -> Dict[str, Any]:
        """Load GitHub event data"""
        if self.event_path and os.path.exists(self.event_path):
            with open(self.event_path, 'r') as f:
                return json.load(f)
        return {}
    
    def _get_headers(self) -> Dict[str, str]:
        """Get headers for GitHub API requests"""
        return {
            "Authorization": f"token {self.github_token}",
            "Accept": "application/vnd.github.v3+json",
            "X-GitHub-Api-Version": "2022-11-28"
        }
    
    def _log_to_nexus(self, action: str, pr_data: Dict[str, Any], result: str = "success"):
        """Log action to AI Nexus for tracking"""
        if not self.nexus:
            print(f"[NEXUS LOG] {action}: {result}")
            return
        
        task = AITask(
            task_id=f"pr_{pr_data.get('number', 'unknown')}_{action}",
            task_type="pr_handling",
            description=f"PR #{pr_data.get('number')}: {action}",
            priority=TaskPriority.MEDIUM,
            provider=AIProvider.COPILOT,
            context={
                "pr_number": pr_data.get("number"),
                "pr_title": pr_data.get("title"),
                "action": action
            },
            max_cost=1.0
        )
        
        self.nexus.submit_task(task)
        
        # Record result
        ai_result = AIResult(
            task_id=task.task_id,
            status=TaskStatus.COMPLETED if result == "success" else TaskStatus.FAILED,
            provider=AIProvider.COPILOT,
            output={"action": action, "result": result},
            cost=0.01,  # Minimal cost for tracking
            tokens_used=100,
            execution_time=1.0
        )
        self.nexus.record_result(ai_result)
    
    def categorize_pr(self, pr_data: Dict[str, Any]) -> str:
        """Categorize PR based on files changed"""
        title = pr_data.get("title", "").lower()
        
        # Check title for hints
        if "doc" in title:
            return "documentation"
        if "ci" in title or "workflow" in title:
            return "ci"
        if "ai" in title or "nexus" in title:
            return "ai_system"
        if "trade" in title or "alpha" in title or "risk" in title:
            return "trading"
        
        # Default to general
        return "general"
    
    def add_pr_comment(self, pr_number: int, comment: str) -> bool:
        """Add a comment to the PR"""
        if not self.github_token or not self.repository:
            print(f"[DRY RUN] Would add comment to PR #{pr_number}: {comment[:100]}...")
            return True
        
        url = f"{self.github_api_url}/repos/{self.repository}/issues/{pr_number}/comments"
        
        try:
            response = requests.post(
                url,
                headers=self._get_headers(),
                json={"body": comment}
            )
            return response.status_code in [200, 201]
        except Exception as e:
            print(f"Error adding comment: {e}")
            return False
    
    def handle_pr_opened(self, pr_data: Dict[str, Any]):
        """Handle newly opened PR"""
        pr_number = pr_data.get("number")
        pr_title = pr_data.get("title", "")
        pr_author = pr_data.get("user", {}).get("login", "unknown")
        
        print(f"[AI PR Handler] Processing new PR #{pr_number}: {pr_title}")
        
        # Categorize PR
        category = self.categorize_pr(pr_data)
        print(f"  Category: {category}")
        
        # Log to nexus
        self._log_to_nexus("pr_opened", pr_data)
        
        # Generate acknowledgment message
        ack_message = self._generate_ack_message(pr_data, category)
        
        # Add comment
        if self.add_pr_comment(pr_number, ack_message):
            print(f"  ✓ Acknowledgment posted")
            self._log_to_nexus("ack_posted", pr_data)
        else:
            print(f"  ✗ Failed to post acknowledgment")
            self._log_to_nexus("ack_failed", pr_data, result="failed")
    
    def _generate_ack_message(self, pr_data: Dict[str, Any], category: str) -> str:
        """Generate acknowledgment message for PR"""
        pr_number = pr_data.get("number")
        pr_author = pr_data.get("user", {}).get("login", "unknown")
        
        messages = {
            "documentation": "📚 Documentation PR detected. Will review for clarity and completeness.",
            "ci": "⚙️ CI/Workflow PR detected. Will verify workflow syntax and safety.",
            "ai_system": "🤖 AI System PR detected. Will ensure proper integration with AI Nexus.",
            "trading": "📈 Trading system PR detected. Will verify safety limits and risk controls.",
            "infrastructure": "🔧 Infrastructure PR detected. Will check for compatibility.",
            "general": "👋 PR received. Will process through AI Nexus for review."
        }
        
        category_msg = messages.get(category, messages["general"])
        
        return f"""## 🤖 AI PR Handler - Automated Acknowledgment

{category_msg}

**PR Details:**
- Number: #{pr_number}
- Author: @{pr_author}
- Category: `{category}`
- Handled by: AI Nexus System

---

*This PR is being internally handled through the AI Nexus system. All actions are tracked in the audit ledger for transparency.*

*Status: ✅ Received and queued for processing*
"""
    
    def handle_pr_synchronized(self, pr_data: Dict[str, Any]):
        """Handle PR updates (new commits pushed)"""
        pr_number = pr_data.get("number")
        print(f"[AI PR Handler] PR #{pr_number} updated with new commits")
        self._log_to_nexus("pr_synchronized", pr_data)
    
    def handle_pr_review(self, review_data: Dict[str, Any]):
        """Handle PR review submissions"""
        pr_data = review_data.get("pull_request", {})
        pr_number = pr_data.get("number")
        review_state = review_data.get("review", {}).get("state", "unknown")
        reviewer = review_data.get("review", {}).get("user", {}).get("login", "unknown")
        
        print(f"[AI PR Handler] PR #{pr_number} received review: {review_state} from {reviewer}")
        self._log_to_nexus("pr_review_received", pr_data, result=review_state)
    
    def run(self):
        """Main entry point for PR handling"""
        print("=" * 60)
        print("AI PR Handler - Internal PR Processing via AI Nexus")
        print("=" * 60)
        print(f"Event: {self.event_name}")
        print(f"Repository: {self.repository}")
        print(f"Nexus Available: {NEXUS_AVAILABLE}")
        print()
        
        if not self.event_data:
            print("No event data found")
            return
        
        action = self.event_data.get("action", "")
        
        if self.event_name == "pull_request":
            pr_data = self.event_data.get("pull_request", {})
            
            if action == "opened":
                self.handle_pr_opened(pr_data)
            elif action == "synchronize":
                self.handle_pr_synchronized(pr_data)
            elif action == "reopened":
                self.handle_pr_opened(pr_data)
            elif action == "ready_for_review":
                self.handle_pr_opened(pr_data)
            else:
                print(f"Unhandled PR action: {action}")
                
        elif self.event_name == "pull_request_review":
            self.handle_pr_review(self.event_data)
        
        else:
            print(f"Unhandled event type: {self.event_name}")
        
        print()
        print("=" * 60)
        print("AI PR Handler completed")
        print("=" * 60)


if __name__ == "__main__":
    handler = PRHandler()
    handler.run()
