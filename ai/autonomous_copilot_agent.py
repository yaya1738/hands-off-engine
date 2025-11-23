#!/usr/bin/env python3
"""
Autonomous Copilot Agent
Monitors coordination files and determines when Copilot should take action
"""

import json
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional

REPO_ROOT = Path(__file__).parent.parent
COORDINATION_DIR = REPO_ROOT / "ai" / "coordination"

class AutonomousCopilotAgent:
    """Autonomous agent that monitors and triggers Copilot actions"""
    
    def __init__(self):
        self.status_file = COORDINATION_DIR / "status.json"
        self.messages_file = COORDINATION_DIR / "messages.jsonl"
        self.handoffs_file = COORDINATION_DIR / "handoffs.json"
    
    def read_status(self) -> Dict:
        """Read current coordination status"""
        if not self.status_file.exists():
            return {}
        with open(self.status_file, 'r') as f:
            return json.load(f)
    
    def read_messages(self) -> List[Dict]:
        """Read recent coordination messages"""
        if not self.messages_file.exists():
            return []
        messages = []
        with open(self.messages_file, 'r') as f:
            for line in f:
                if line.strip():
                    messages.append(json.loads(line))
        return messages
    
    def read_handoffs(self) -> Dict:
        """Read pending handoffs"""
        if not self.handoffs_file.exists():
            return {"handoffs": []}
        with open(self.handoffs_file, 'r') as f:
            return json.load(f)
    
    def get_copilot_tasks(self, status: Dict) -> List[Dict]:
        """Extract tasks assigned to Copilot"""
        tasks = []
        for task in status.get("pending_tasks", []):
            if task.get("assigned_to") in ["copilot", "auto"]:
                if task.get("status") in ["awaiting_action", "ready"]:
                    tasks.append(task)
        return tasks
    
    def get_copilot_messages(self, messages: List[Dict]) -> List[Dict]:
        """Extract messages directed at Copilot"""
        copilot_messages = []
        for msg in messages:
            if msg.get("to") in ["copilot", "all"]:
                if msg.get("type") in ["request", "handoff"]:
                    copilot_messages.append(msg)
        return copilot_messages
    
    def check_for_work(self) -> Optional[Dict]:
        """
        Check if there's work for Copilot to do
        Returns work specification or None
        """
        status = self.read_status()
        messages = self.read_messages()
        handoffs = self.read_handoffs()
        
        # Check if autonomous mode is enabled
        if not status.get("autonomous_mode", {}).get("copilot", False):
            return None
        
        # Priority 1: Explicit tasks assigned to Copilot
        copilot_tasks = self.get_copilot_tasks(status)
        if copilot_tasks:
            task = copilot_tasks[0]  # Highest priority task
            return {
                "type": "assigned_task",
                "priority": "high",
                "task": task,
                "action": "Execute task according to roadmap"
            }
        
        # Priority 2: Messages requesting Copilot action
        copilot_messages = self.get_copilot_messages(messages)
        recent_messages = [m for m in copilot_messages if self._is_recent(m)]
        if recent_messages:
            msg = recent_messages[-1]  # Most recent message
            return {
                "type": "message_request",
                "priority": "high",
                "message": msg,
                "action": "Respond to coordination message"
            }
        
        # Priority 3: Pending handoffs
        pending_handoffs = [h for h in handoffs.get("handoffs", [])
                           if h.get("to") == "copilot" and h.get("status") == "pending"]
        if pending_handoffs:
            handoff = pending_handoffs[0]
            return {
                "type": "handoff",
                "priority": "medium",
                "handoff": handoff,
                "action": "Accept handoff and continue work"
            }
        
        # Priority 4: Proactive roadmap work
        # Check if we should proactively pick up next roadmap item
        current_phase = status.get("current_phase", "")
        if "Phase 1" in current_phase:
            # Phase 1 requires human action to merge PRs
            # Copilot can prepare for Phase 2
            return {
                "type": "proactive",
                "priority": "low",
                "action": "Prepare for Phase 2 work (Risk Model, Decider V1)",
                "note": "Awaiting Phase 1 PR merges before starting"
            }
        
        return None
    
    def _is_recent(self, message: Dict, hours: int = 24) -> bool:
        """Check if message is recent (within N hours)"""
        try:
            msg_time = datetime.fromisoformat(message["timestamp"].replace("Z", "+00:00"))
            now = datetime.now(msg_time.tzinfo)
            age_hours = (now - msg_time).total_seconds() / 3600
            return age_hours < hours
        except (KeyError, ValueError):
            return False
    
    def generate_trigger_comment(self, work: Dict) -> str:
        """
        Generate a GitHub issue comment that will trigger Copilot
        This comment will be posted to activate the Copilot agent
        """
        work_type = work.get("type")
        priority = work.get("priority")
        
        if work_type == "assigned_task":
            task = work["task"]
            return f"""@copilot 
            
**Autonomous Task Detected**

Task ID: {task.get('id')}
Description: {task.get('description')}
Status: {task.get('status')}
Priority: {priority}

Please execute this task according to the roadmap and update coordination files when complete.
"""
        
        elif work_type == "message_request":
            msg = work["message"]
            return f"""@copilot

**Coordination Message Requires Response**

From: {msg.get('from')}
Message: {msg.get('message')}
Priority: {priority}

Please respond to this coordination request in ai/coordination/messages.jsonl.
"""
        
        elif work_type == "handoff":
            handoff = work["handoff"]
            return f"""@copilot

**Work Handoff Received**

From: {handoff.get('from')}
Task: {handoff.get('task_description')}
Priority: {priority}

Please accept this handoff and continue the work.
"""
        
        elif work_type == "proactive":
            return f"""@copilot

**Proactive Work Available**

{work.get('action')}
Priority: {priority}

Note: {work.get('note', 'No additional notes')}
"""
        
        return f"@copilot Autonomous work detected: {work}"

def main():
    """Main entry point for autonomous agent"""
    agent = AutonomousCopilotAgent()
    
    print("🤖 Autonomous Copilot Agent - Checking for work...")
    
    work = agent.check_for_work()
    
    if work:
        print(f"✅ Work detected: {work['type']} (Priority: {work['priority']})")
        print(f"   Action: {work['action']}")
        
        # Generate trigger comment
        trigger = agent.generate_trigger_comment(work)
        print("\n" + "="*60)
        print("TRIGGER COMMENT (post this to GitHub issue to activate Copilot):")
        print("="*60)
        print(trigger)
        print("="*60)
        
        # In GitHub Actions, this would post the comment via GitHub API
        # For now, output for manual use or automation
        return 0
    else:
        print("ℹ️  No autonomous work detected at this time")
        print("   Copilot will remain on standby")
        return 1

if __name__ == "__main__":
    sys.exit(main())
