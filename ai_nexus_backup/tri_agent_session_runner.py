#!/usr/bin/env python3
"""
Tri-Agent Backend Session Runner v0.1

Orchestrates 3-way discussions between ChatGPT, Claude, and GitHub Copilot Agent
using AI Nexus backend providers.

Usage:
    python -m ai_nexus.tri_agent_session_runner \\
        --conversation-id 20251125_risk_model_tuning \\
        --rounds 2 \\
        --agents chatgpt,claude_cli

Example:
    python -m ai_nexus.tri_agent_session_runner \\
        --conversation-id 20251125_test \\
        --session-goal "Discuss optimal Kelly fraction" \\
        --rounds 1 \\
        --agents chatgpt,claude_cli
"""

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import List, Dict

# Add repo root to path
REPO_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(REPO_ROOT))

from ai_nexus.provider_openai import call_chatgpt
from ai_nexus.provider_claude import call_claude
from ai_nexus.provider_copilot import call_github_copilot

# Agent provider mapping
AGENT_PROVIDERS = {
    "chatgpt": call_chatgpt,
    "claude_cli": call_claude,
    "github_copilot_agent": call_github_copilot
}

DEFAULT_AGENTS = ["chatgpt", "claude_cli"]  # Copilot is stub in v0.1


class TriAgentSession:
    """Manages a multi-round backend session between AI agents"""

    def __init__(self, conversation_id: str, session_goal: str = "General discussion"):
        self.conversation_id = conversation_id
        self.session_goal = session_goal
        self.intercom_dir = REPO_ROOT / "ai" / "intercom" / conversation_id
        self.thread_file = self.intercom_dir / "thread.jsonl"
        self.metadata_file = self.intercom_dir / "metadata.json"

        # Ensure directory exists
        self.intercom_dir.mkdir(parents=True, exist_ok=True)

        # Load or create metadata
        self.metadata = self._load_or_create_metadata()

    def _load_or_create_metadata(self) -> Dict:
        """Load existing metadata or create new"""
        if self.metadata_file.exists():
            with open(self.metadata_file) as f:
                return json.load(f)
        else:
            metadata = {
                "conversation_id": self.conversation_id,
                "created": datetime.utcnow().isoformat() + "Z",
                "topic": self.conversation_id.split("_", 1)[-1] if "_" in self.conversation_id else "discussion",
                "goal": self.session_goal,
                "participants": [],
                "status": "active",
                "rounds_completed": 0
            }
            self._save_metadata(metadata)
            return metadata

    def _save_metadata(self, metadata: Dict):
        """Save metadata to file"""
        with open(self.metadata_file, 'w') as f:
            json.dump(metadata, f, indent=2)

    def load_thread(self) -> List[Dict]:
        """Load all messages from thread"""
        if not self.thread_file.exists():
            return []

        messages = []
        with open(self.thread_file) as f:
            for line in f:
                if line.strip():
                    messages.append(json.loads(line))
        return messages

    def append_message(self, message: Dict):
        """Append message to thread"""
        with open(self.thread_file, 'a') as f:
            f.write(json.dumps(message) + '\n')

    def run_round(self, agents: List[str]) -> List[Dict]:
        """Run one round of discussion with specified agents"""
        messages = self.load_thread()
        new_messages = []

        print(f"\n{'='*60}")
        print(f"ROUND {self.metadata['rounds_completed'] + 1}")
        print(f"{'='*60}\n")

        for agent_id in agents:
            if agent_id not in AGENT_PROVIDERS:
                print(f"⚠️  Unknown agent: {agent_id} (skipping)")
                continue

            print(f"🤖 Calling {agent_id}...")

            # Call provider
            provider_func = AGENT_PROVIDERS[agent_id]
            response = provider_func(
                agent_id=agent_id,
                prior_messages=messages,
                session_goal=self.session_goal
            )

            # Create message
            msg_id = f"msg-{len(messages) + len(new_messages) + 1:04d}"
            message = {
                "msg_id": msg_id,
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "from_agent": agent_id,
                "topic": self.metadata['topic'],
                "content": response['content'],
                "model": response.get('model', 'unknown'),
                "tokens": response.get('tokens', 0)
            }

            if 'error' in response:
                message['error'] = response['error']

            # Append to thread
            self.append_message(message)
            new_messages.append(message)
            messages.append(message)

            # Print response summary
            content_preview = message['content'][:200]
            if len(message['content']) > 200:
                content_preview += "..."

            print(f"   ✓ {message['model']} ({message['tokens']} tokens)")
            print(f"   {content_preview}\n")

        # Update metadata
        self.metadata['rounds_completed'] += 1
        self.metadata['participants'] = list(set(self.metadata['participants'] + agents))
        self._save_metadata(self.metadata)

        return new_messages

    def run_session(self, agents: List[str], rounds: int):
        """Run multiple rounds of discussion"""
        print(f"\n{'='*60}")
        print(f"TRI-AGENT BACKEND SESSION")
        print(f"{'='*60}")
        print(f"Conversation: {self.conversation_id}")
        print(f"Goal: {self.session_goal}")
        print(f"Agents: {', '.join(agents)}")
        print(f"Rounds: {rounds}")
        print(f"Storage: {self.thread_file}")
        print(f"{'='*60}")

        for round_num in range(rounds):
            new_messages = self.run_round(agents)

        # Print summary
        all_messages = self.load_thread()
        print(f"\n{'='*60}")
        print(f"SESSION COMPLETE")
        print(f"{'='*60}")
        print(f"Total messages: {len(all_messages)}")
        print(f"Rounds completed: {self.metadata['rounds_completed']}")
        print(f"\nLast message from each agent:")
        print(f"{'='*60}\n")

        for agent_id in agents:
            agent_messages = [m for m in all_messages if m['from_agent'] == agent_id]
            if agent_messages:
                last = agent_messages[-1]
                content_preview = last['content'][:150]
                if len(last['content']) > 150:
                    content_preview += "..."
                print(f"[{agent_id}]:")
                print(f"  {content_preview}\n")

        print(f"Full thread: {self.thread_file}")
        print(f"{'='*60}\n")


def main():
    """CLI entrypoint"""
    parser = argparse.ArgumentParser(
        description="Run a tri-agent backend session",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )

    parser.add_argument(
        "--conversation-id",
        required=True,
        help="Conversation ID (e.g., 20251125_risk_model)"
    )

    parser.add_argument(
        "--session-goal",
        default="General discussion and analysis",
        help="Description of session purpose"
    )

    parser.add_argument(
        "--rounds",
        type=int,
        default=1,
        help="Number of discussion rounds (default: 1)"
    )

    parser.add_argument(
        "--agents",
        default="chatgpt,claude_cli",
        help="Comma-separated list of agents (default: chatgpt,claude_cli)"
    )

    args = parser.parse_args()

    # Parse agents list
    agents = [a.strip() for a in args.agents.split(",")]

    # Validate agents
    for agent in agents:
        if agent not in AGENT_PROVIDERS:
            print(f"Error: Unknown agent '{agent}'")
            print(f"Available agents: {', '.join(AGENT_PROVIDERS.keys())}")
            sys.exit(1)

    # Run session
    session = TriAgentSession(
        conversation_id=args.conversation_id,
        session_goal=args.session_goal
    )

    try:
        session.run_session(agents=agents, rounds=args.rounds)
    except KeyboardInterrupt:
        print("\n\n⏹️  Session interrupted by user")
        print(f"Partial thread saved to: {session.thread_file}")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
