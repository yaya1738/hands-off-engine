#!/usr/bin/env python3
"""
Tri-Agent Backend Session Runner v0.2 (CPU-Aligned)

Orchestrates 3-way discussions between ChatGPT, Claude, and GitHub Copilot Agent
using AI Nexus backend providers.

Now aligned with CpuInstance abstraction (Part 1 of Spark Plug Architecture).

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

See: docs/SPARK_PLUG_ARCHITECTURE_v0.1.md (Part 1)
"""

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional

# Add repo root to path
REPO_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(REPO_ROOT))

from ai_nexus.provider_openai import call_chatgpt
from ai_nexus.provider_claude import call_claude
from ai_nexus.provider_copilot import call_github_copilot
from ai_nexus.spark_plug_types import (
    CpuInstance,
    CpuConfig,
    CpuMessage,
    create_cpu_message
)
from ai_nexus.memory_kernels import load_kernel, list_kernels

# Agent provider mapping
AGENT_PROVIDERS = {
    "chatgpt": call_chatgpt,
    "claude_cli": call_claude,
    "github_copilot_agent": call_github_copilot
}

DEFAULT_AGENTS = ["chatgpt", "claude_cli"]  # Copilot is stub in v0.1


class TriAgentSession:
    """
    Manages a multi-round backend session between AI agents

    Now wrapped with CpuInstance abstraction (Part 1 of Spark Plug).
    Each session is treated as a CpuInstance in burst mode.
    """

    def __init__(
        self,
        conversation_id: str,
        session_goal: str = "General discussion",
        bound_kernels: Optional[List[str]] = None,
        max_rounds: Optional[int] = None,
        max_cost_usd: float = 1.0
    ):
        self.conversation_id = conversation_id
        self.session_goal = session_goal
        self.intercom_dir = REPO_ROOT / "ai" / "intercom" / conversation_id
        self.thread_file = self.intercom_dir / "thread.jsonl"
        self.metadata_file = self.intercom_dir / "metadata.json"
        self.cpu_instance_file = self.intercom_dir / "cpu_instance.json"

        # Ensure directory exists
        self.intercom_dir.mkdir(parents=True, exist_ok=True)

        # Load or create CpuInstance
        self.cpu = self._load_or_create_cpu_instance(
            bound_kernels=bound_kernels or [],
            max_rounds=max_rounds,
            max_cost_usd=max_cost_usd
        )

        # Load or create metadata (legacy compatibility)
        self.metadata = self._load_or_create_metadata()

    def _load_or_create_cpu_instance(
        self,
        bound_kernels: List[str],
        max_rounds: Optional[int],
        max_cost_usd: float
    ) -> CpuInstance:
        """Load existing CpuInstance or create new"""
        if self.cpu_instance_file.exists():
            with open(self.cpu_instance_file) as f:
                return CpuInstance.from_dict(json.load(f))
        else:
            cpu_id = f"cpu_{self.conversation_id}"
            cpu = CpuInstance(
                cpu_id=cpu_id,
                mode="burst",
                bound_kernels=bound_kernels,
                intercom_path=str(self.thread_file),
                status="idle",
                config=CpuConfig(
                    max_rounds=max_rounds,
                    max_cost_usd=max_cost_usd,
                    safety_profile="design_only"
                )
            )
            self._save_cpu_instance(cpu)
            return cpu

    def _save_cpu_instance(self, cpu: CpuInstance):
        """Save CpuInstance to file"""
        with open(self.cpu_instance_file, 'w') as f:
            f.write(cpu.to_json())

    def _load_or_create_metadata(self) -> Dict:
        """Load existing metadata or create new (legacy compatibility)"""
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

    def load_thread(self) -> List[CpuMessage]:
        """Load all messages from thread as CpuMessage objects"""
        if not self.thread_file.exists():
            return []

        messages = []
        with open(self.thread_file) as f:
            for line in f:
                if line.strip():
                    messages.append(CpuMessage.from_jsonl_line(line))
        return messages

    def load_thread_dicts(self) -> List[Dict]:
        """Load all messages as dicts (for provider compatibility)"""
        if not self.thread_file.exists():
            return []

        messages = []
        with open(self.thread_file) as f:
            for line in f:
                if line.strip():
                    messages.append(json.loads(line))
        return messages

    def append_message(self, message: CpuMessage):
        """Append CpuMessage to thread"""
        with open(self.thread_file, 'a') as f:
            f.write(message.to_jsonl_line() + '\n')

    def load_bound_kernels(self) -> Dict[str, str]:
        """Load summaries of bound kernels for CPU context"""
        kernel_summaries = {}
        for kernel_id in self.cpu.bound_kernels:
            kernel = load_kernel(kernel_id)
            if kernel:
                kernel_summaries[kernel_id] = kernel.summary
        return kernel_summaries

    def run_round(self, agents: List[str]) -> List[CpuMessage]:
        """Run one round of discussion with specified agents"""
        messages_dicts = self.load_thread_dicts()  # For provider compatibility
        messages = self.load_thread()
        new_messages = []

        print(f"\n{'='*60}")
        print(f"ROUND {self.metadata['rounds_completed'] + 1}")
        print(f"CPU: {self.cpu.cpu_id} (status: {self.cpu.status})")
        print(f"{'='*60}\n")

        # Load kernel context if bound
        if self.cpu.bound_kernels:
            print(f"📚 Bound kernels: {', '.join(self.cpu.bound_kernels)}")
            kernel_summaries = self.load_bound_kernels()
            for kid, summary in kernel_summaries.items():
                print(f"   {kid}: {summary[:80]}...")
            print()

        # Update CPU status
        self.cpu.status = "running"
        self._save_cpu_instance(self.cpu)

        for agent_id in agents:
            if agent_id not in AGENT_PROVIDERS:
                print(f"⚠️  Unknown agent: {agent_id} (skipping)")
                continue

            print(f"🤖 Calling {agent_id}...")

            # Call provider
            provider_func = AGENT_PROVIDERS[agent_id]
            response = provider_func(
                agent_id=agent_id,
                prior_messages=messages_dicts,
                session_goal=self.session_goal
            )

            # Create CpuMessage
            msg_id = f"msg-{len(messages) + len(new_messages) + 1:04d}"
            message = create_cpu_message(
                msg_id=msg_id,
                from_=agent_id,
                content=response['content'],
                role="assistant",
                tokens=response.get('tokens', 0),
                cost_usd=response.get('cost_usd', 0.0),
                model=response.get('model', 'unknown'),
                tags=[self.metadata['topic']] if 'topic' in self.metadata else [],
                related_kernels=self.cpu.bound_kernels
            )

            if 'error' in response:
                message.meta['error'] = response['error']

            # Append to thread
            self.append_message(message)
            new_messages.append(message)
            messages.append(message)

            # Print response summary
            content_preview = message.content[:200]
            if len(message.content) > 200:
                content_preview += "..."

            print(f"   ✓ {message.meta.get('model', 'unknown')} ({message.meta.get('tokens', 0)} tokens)")
            print(f"   {content_preview}\n")

        # Update metadata
        self.metadata['rounds_completed'] += 1
        self.metadata['participants'] = list(set(self.metadata['participants'] + agents))
        self._save_metadata(self.metadata)

        # Update CPU status
        self.cpu.status = "idle"
        self._save_cpu_instance(self.cpu)

        return new_messages

    def run_session(self, agents: List[str], rounds: int):
        """Run multiple rounds of discussion"""
        print(f"\n{'='*60}")
        print(f"TRI-AGENT BACKEND SESSION (CPU-ALIGNED)")
        print(f"{'='*60}")
        print(f"CPU ID: {self.cpu.cpu_id}")
        print(f"Mode: {self.cpu.mode}")
        print(f"Conversation: {self.conversation_id}")
        print(f"Goal: {self.session_goal}")
        print(f"Agents: {', '.join(agents)}")
        print(f"Rounds: {rounds}")
        print(f"Bound Kernels: {', '.join(self.cpu.bound_kernels) if self.cpu.bound_kernels else 'none'}")
        print(f"Storage: {self.thread_file}")
        print(f"Safety: {self.cpu.config.safety_profile}")
        print(f"{'='*60}")

        for round_num in range(rounds):
            new_messages = self.run_round(agents)

        # Mark CPU as stopped
        self.cpu.status = "stopped"
        self._save_cpu_instance(self.cpu)

        # Print summary
        all_messages = self.load_thread()
        print(f"\n{'='*60}")
        print(f"SESSION COMPLETE")
        print(f"{'='*60}")
        print(f"CPU ID: {self.cpu.cpu_id}")
        print(f"Total messages: {len(all_messages)}")
        print(f"Rounds completed: {self.metadata['rounds_completed']}")
        print(f"\nLast message from each agent:")
        print(f"{'='*60}\n")

        for agent_id in agents:
            agent_messages = [m for m in all_messages if m.from_ == agent_id]
            if agent_messages:
                last = agent_messages[-1]
                content_preview = last.content[:150]
                if len(last.content) > 150:
                    content_preview += "..."
                print(f"[{agent_id}]:")
                print(f"  {content_preview}\n")

        print(f"Full thread: {self.thread_file}")
        print(f"CPU Instance: {self.cpu_instance_file}")
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

    parser.add_argument(
        "--bind-kernels",
        default="",
        help="Comma-separated list of kernel IDs to bind to CPU (optional)"
    )

    parser.add_argument(
        "--max-cost",
        type=float,
        default=1.0,
        help="Maximum cost in USD (default: 1.0)"
    )

    args = parser.parse_args()

    # Parse agents list
    agents = [a.strip() for a in args.agents.split(",")]

    # Parse bind-kernels list
    bound_kernels = [k.strip() for k in args.bind_kernels.split(",") if k.strip()]

    # Validate agents
    for agent in agents:
        if agent not in AGENT_PROVIDERS:
            print(f"Error: Unknown agent '{agent}'")
            print(f"Available agents: {', '.join(AGENT_PROVIDERS.keys())}")
            sys.exit(1)

    # Validate kernels
    if bound_kernels:
        available_kernels = list_kernels()
        for kernel_id in bound_kernels:
            if kernel_id not in available_kernels:
                print(f"Warning: Kernel '{kernel_id}' not found")
                print(f"Available kernels: {', '.join(available_kernels) if available_kernels else 'none'}")
                print("Continuing without this kernel...")
                bound_kernels.remove(kernel_id)

    # Run session
    session = TriAgentSession(
        conversation_id=args.conversation_id,
        session_goal=args.session_goal,
        bound_kernels=bound_kernels,
        max_rounds=args.rounds,
        max_cost_usd=args.max_cost
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
