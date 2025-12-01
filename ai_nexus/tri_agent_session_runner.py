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
from ai_nexus.memory_kernels import load_kernel, list_kernels, append_kernel_update
from ai_nexus.spark_plug_types import KernelUpdate
import time

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
        max_cost_usd: float = 1.0,
        continuous: bool = False,
        max_steps: int = 20,
        max_duration_seconds: int = 900,
        kernel_update_mode: str = "none",
        previous_session_id: Optional[str] = None,
        depends_on: Optional[List[str]] = None,
        session_order: Optional[int] = None
    ):
        self.conversation_id = conversation_id
        self.session_goal = session_goal
        self.intercom_dir = REPO_ROOT / "ai" / "intercom" / conversation_id
        self.thread_file = self.intercom_dir / "thread.jsonl"
        self.metadata_file = self.intercom_dir / "metadata.json"
        self.cpu_instance_file = self.intercom_dir / "cpu_instance.json"
        self.kernel_update_mode = kernel_update_mode

        # Ensure directory exists
        self.intercom_dir.mkdir(parents=True, exist_ok=True)

        # Load or create CpuInstance
        self.cpu = self._load_or_create_cpu_instance(
            bound_kernels=bound_kernels or [],
            max_rounds=max_rounds,
            max_cost_usd=max_cost_usd,
            continuous=continuous,
            max_steps=max_steps,
            max_duration_seconds=max_duration_seconds,
            previous_session_id=previous_session_id,
            depends_on=depends_on or [],
            session_order=session_order
        )

        # Load or create metadata (legacy compatibility)
        self.metadata = self._load_or_create_metadata()

    def _load_or_create_cpu_instance(
        self,
        bound_kernels: List[str],
        max_rounds: Optional[int],
        max_cost_usd: float,
        continuous: bool,
        max_steps: int,
        max_duration_seconds: int,
        previous_session_id: Optional[str],
        depends_on: List[str],
        session_order: Optional[int]
    ) -> CpuInstance:
        """Load existing CpuInstance or create new"""
        if self.cpu_instance_file.exists():
            with open(self.cpu_instance_file) as f:
                return CpuInstance.from_dict(json.load(f))
        else:
            cpu_id = f"cpu_{self.conversation_id}"
            mode = "continuous" if continuous else "burst"
            cpu = CpuInstance(
                cpu_id=cpu_id,
                mode=mode,
                bound_kernels=bound_kernels,
                intercom_path=str(self.thread_file),
                status="idle",
                config=CpuConfig(
                    max_rounds=max_rounds,
                    max_cost_usd=max_cost_usd,
                    safety_profile="design_only",
                    max_steps=max_steps,
                    max_duration_seconds=max_duration_seconds
                ),
                previous_session_id=previous_session_id,
                depends_on=depends_on,
                session_order=session_order
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

    def _validate_session_dependencies(self) -> bool:
        """
        Validate that all session dependencies are met before execution.
        
        Returns:
            bool: True if dependencies are satisfied, False otherwise
        """
        # Check if there's a previous session requirement
        if self.cpu.previous_session_id:
            prev_session_path = REPO_ROOT / "ai" / "intercom" / self.cpu.previous_session_id / "cpu_instance.json"
            
            if not prev_session_path.exists():
                print(f"⚠️  WARNING: Previous session '{self.cpu.previous_session_id}' not found!")
                print(f"   This session should follow {self.cpu.previous_session_id} but it doesn't exist.")
                return False
            
            # Check if previous session is completed
            with open(prev_session_path) as f:
                prev_cpu = CpuInstance.from_dict(json.load(f))
                
            if prev_cpu.status not in ["stopped", "completed"]:
                print(f"⚠️  WARNING: Previous session '{self.cpu.previous_session_id}' is not completed!")
                print(f"   Status: {prev_cpu.status}")
                print(f"   This session should wait for {self.cpu.previous_session_id} to complete.")
                return False
            
            print(f"✓ Previous session '{self.cpu.previous_session_id}' completed successfully")
        
        # Check all dependencies
        if self.cpu.depends_on:
            for dep_id in self.cpu.depends_on:
                dep_path = REPO_ROOT / "ai" / "intercom" / dep_id / "cpu_instance.json"
                
                if not dep_path.exists():
                    print(f"⚠️  WARNING: Dependency session '{dep_id}' not found!")
                    print(f"   This session depends on {dep_id} but it doesn't exist.")
                    return False
                
                with open(dep_path) as f:
                    dep_cpu = CpuInstance.from_dict(json.load(f))
                
                if dep_cpu.status not in ["stopped", "completed"]:
                    print(f"⚠️  WARNING: Dependency session '{dep_id}' is not completed!")
                    print(f"   Status: {dep_cpu.status}")
                    print(f"   This session should wait for {dep_id} to complete.")
                    return False
                
                print(f"✓ Dependency session '{dep_id}' completed successfully")
        
        # Check session order if specified
        if self.cpu.session_order is not None:
            # Find all sessions with order numbers
            intercom_root = REPO_ROOT / "ai" / "intercom"
            if intercom_root.exists():
                for session_dir in intercom_root.iterdir():
                    if not session_dir.is_dir():
                        continue
                    
                    cpu_file = session_dir / "cpu_instance.json"
                    if not cpu_file.exists():
                        continue
                    
                    with open(cpu_file) as f:
                        other_cpu = CpuInstance.from_dict(json.load(f))
                    
                    # Check if there are earlier sessions that should complete first
                    if (other_cpu.session_order is not None and 
                        other_cpu.session_order < self.cpu.session_order and
                        other_cpu.status not in ["stopped", "completed"]):
                        print(f"⚠️  WARNING: Earlier session '{other_cpu.cpu_id}' (order {other_cpu.session_order}) is not completed!")
                        print(f"   This session (order {self.cpu.session_order}) should wait.")
                        return False
        
        return True

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

        # Validate session dependencies before starting
        print(f"\n🔍 Validating session dependencies...")
        if not self._validate_session_dependencies():
            print(f"\n❌ Session dependency validation FAILED!")
            print(f"   This session cannot run until dependencies are satisfied.")
            print(f"   Aborting session to prevent jumping ahead of session order.")
            self.cpu.status = "blocked"
            self._save_cpu_instance(self.cpu)
            return
        
        print(f"✓ All session dependencies satisfied\n")

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

    def run_continuous_session(self, agents: List[str]):
        """Run continuous CPU loop with safety caps (v0.2)"""
        print(f"\n{'='*60}")
        print(f"TRI-AGENT CONTINUOUS SESSION (v0.2)")
        print(f"{'='*60}")
        print(f"CPU ID: {self.cpu.cpu_id}")
        print(f"Mode: {self.cpu.mode}")
        print(f"Conversation: {self.conversation_id}")
        print(f"Goal: {self.session_goal}")
        print(f"Agents: {', '.join(agents)}")
        print(f"Max Steps: {self.cpu.config.max_steps}")
        print(f"Max Duration: {self.cpu.config.max_duration_seconds}s")
        print(f"Bound Kernels: {', '.join(self.cpu.bound_kernels) if self.cpu.bound_kernels else 'none'}")
        print(f"Kernel Update Mode: {self.kernel_update_mode}")
        print(f"Storage: {self.thread_file}")
        print(f"Safety: {self.cpu.config.safety_profile}")
        print(f"{'='*60}\n")

        # Validate session dependencies before starting
        print(f"🔍 Validating session dependencies...")
        if not self._validate_session_dependencies():
            print(f"\n❌ Session dependency validation FAILED!")
            print(f"   This session cannot run until dependencies are satisfied.")
            print(f"   Aborting session to prevent jumping ahead of session order.")
            self.cpu.status = "blocked"
            self._save_cpu_instance(self.cpu)
            return
        
        print(f"✓ All session dependencies satisfied\n")

        # Initialize timers
        start_time = time.time()
        step_count = 0

        # Continuous loop
        while True:
            # Check caps
            elapsed = time.time() - start_time
            if step_count >= self.cpu.config.max_steps:
                print(f"\n⏹️  Stopped: Reached max steps ({self.cpu.config.max_steps})")
                break
            if elapsed >= self.cpu.config.max_duration_seconds:
                print(f"\n⏹️  Stopped: Reached max duration ({self.cpu.config.max_duration_seconds}s)")
                break

            # Run one step
            print(f"\n--- Step {step_count + 1} ---")
            self.run_round(agents)
            step_count += 1

            # Update CPU tracking
            self.cpu.steps_completed = step_count
            self.cpu.duration_seconds = time.time() - start_time
            self._save_cpu_instance(self.cpu)

        # Final CPU state
        self.cpu.status = "stopped"
        self.cpu.steps_completed = step_count
        self.cpu.duration_seconds = time.time() - start_time
        self._save_cpu_instance(self.cpu)

        # Apply kernel updates if requested
        if self.kernel_update_mode == "append_notes" and self.cpu.bound_kernels:
            self._apply_kernel_updates()

        # Print summary
        all_messages = self.load_thread()
        print(f"\n{'='*60}")
        print(f"CONTINUOUS SESSION COMPLETE")
        print(f"{'='*60}")
        print(f"CPU ID: {self.cpu.cpu_id}")
        print(f"Total steps: {step_count}")
        print(f"Duration: {self.cpu.duration_seconds:.1f}s")
        print(f"Total messages: {len(all_messages)}")
        print(f"Kernel updates applied: {self.cpu.kernel_updates_applied}")
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

    def _apply_kernel_updates(self):
        """Apply kernel updates in append_notes mode (v0.2)"""
        print(f"\n📝 Applying kernel updates...")

        # Generate session summary
        all_messages = self.load_thread()
        summary = self._generate_session_summary(all_messages)

        # Create update for each bound kernel
        update = KernelUpdate(
            update_type="summary_edit",
            content={
                "conversation_id": self.conversation_id,
                "cpu_id": self.cpu.cpu_id,
                "session_goal": self.session_goal,
                "summary": summary,
                "steps": self.cpu.steps_completed,
                "duration_seconds": self.cpu.duration_seconds,
                "raw_ref": str(self.thread_file)
            },
            source=self.cpu.cpu_id,
            agent="system"
        )

        # Apply to each kernel
        for kernel_id in self.cpu.bound_kernels:
            try:
                append_kernel_update(kernel_id, update)
                print(f"   ✓ Updated kernel: {kernel_id}")
            except Exception as e:
                print(f"   ⚠️  Failed to update kernel {kernel_id}: {e}")

        self.cpu.kernel_updates_applied = True
        self._save_cpu_instance(self.cpu)

    def _generate_session_summary(self, messages: List[CpuMessage]) -> str:
        """Generate a compact summary of the session (v0.2)"""
        if not messages:
            return "No messages in session."

        # Simple heuristic summary
        summary_parts = []
        summary_parts.append(f"Session: {self.conversation_id}")
        summary_parts.append(f"Goal: {self.session_goal}")
        summary_parts.append(f"Messages: {len(messages)}")

        # Extract key topics from messages (simple keyword extraction)
        agent_counts = {}
        for msg in messages:
            agent_counts[msg.from_] = agent_counts.get(msg.from_, 0) + 1

        summary_parts.append(f"Participants: {', '.join(f'{a}({c})' for a, c in agent_counts.items())}")

        return " | ".join(summary_parts)


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

    # v0.2: Continuous mode flags
    parser.add_argument(
        "--continuous",
        action="store_true",
        help="Enable continuous mode (loop until max-steps or max-duration-seconds)"
    )

    parser.add_argument(
        "--max-steps",
        type=int,
        default=20,
        help="Maximum steps for continuous mode (default: 20)"
    )

    parser.add_argument(
        "--max-duration-seconds",
        type=int,
        default=900,
        help="Maximum wall-clock seconds for continuous mode (default: 900)"
    )

    # v0.2: Kernel update mode
    parser.add_argument(
        "--kernel-update-mode",
        choices=["none", "append_notes"],
        default="none",
        help="Kernel update mode: 'none' (default) or 'append_notes' (v0.2)"
    )

    # Session ordering arguments
    parser.add_argument(
        "--previous-session",
        default="",
        help="ID of previous session that must complete before this one (enforces sequential ordering)"
    )

    parser.add_argument(
        "--depends-on",
        default="",
        help="Comma-separated list of session IDs this session depends on (all must be completed)"
    )

    parser.add_argument(
        "--session-order",
        type=int,
        default=None,
        help="Explicit order number for this session in a sequence (e.g., 1, 2, 3)"
    )

    args = parser.parse_args()

    # Parse agents list
    agents = [a.strip() for a in args.agents.split(",")]

    # Parse bind-kernels list
    bound_kernels = [k.strip() for k in args.bind_kernels.split(",") if k.strip()]

    # Parse depends-on list
    depends_on = [d.strip() for d in args.depends_on.split(",") if d.strip()]

    # Parse previous session
    previous_session_id = args.previous_session.strip() if args.previous_session else None

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
        max_cost_usd=args.max_cost,
        continuous=args.continuous,
        max_steps=args.max_steps,
        max_duration_seconds=args.max_duration_seconds,
        kernel_update_mode=args.kernel_update_mode,
        previous_session_id=previous_session_id,
        depends_on=depends_on,
        session_order=args.session_order
    )

    try:
        if args.continuous:
            # v0.2: Continuous mode
            session.run_continuous_session(agents=agents)
        else:
            # v0.1: Burst mode (backward compatible)
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
