#!/usr/bin/env python3
"""
Agent Session Manager v1.0

A tool to discover, create, and manage agent sessions in the Hands-Off Engine.
This module provides capabilities to:
    - List existing sessions and their status
    - Create new sessions from templates or custom configurations
    - Discover session patterns and suggest new sessions
    - Archive and manage session lifecycle

Session types:
    - burst: Fixed number of rounds, then stop
    - continuous: Run until max steps/duration reached

Usage:
    python -m ai_nexus.session_manager list
    python -m ai_nexus.session_manager create --goal "Analyze risk model" --agents chatgpt,claude_cli
    python -m ai_nexus.session_manager suggest
    python -m ai_nexus.session_manager info <conversation_id>

See: docs/SPARK_PLUG_ARCHITECTURE_v0.1.md
"""

import argparse
import json
import os
import sys
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Dict, Optional, Literal

# Add repo root to path
REPO_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(REPO_ROOT))

from ai_nexus.spark_plug_types import CpuInstance, CpuConfig
from ai_nexus.memory_kernels import list_kernels, load_kernel

# Paths
INTERCOM_DIR = REPO_ROOT / "ai" / "intercom"
TEMPLATES_DIR = REPO_ROOT / "ai" / "session_templates"
COORDINATION_DIR = REPO_ROOT / "ai" / "coordination"

# Configuration constants
MAX_TOPIC_LENGTH = 30
GOAL_WORDS_FOR_TOPIC = 3
MAX_DISPLAYED_QUESTIONS = 3
MAX_PENDING_TASKS = 3


# =============================================================================
# Session Templates
# =============================================================================

@dataclass
class SessionTemplate:
    """Template for creating new agent sessions"""
    name: str
    description: str
    default_goal: str
    suggested_agents: List[str]
    suggested_rounds: int
    suggested_kernels: List[str]
    mode: Literal["burst", "continuous"] = "burst"
    tags: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict) -> "SessionTemplate":
        return cls(**data)


# Built-in templates
BUILTIN_TEMPLATES: Dict[str, SessionTemplate] = {
    "risk_analysis": SessionTemplate(
        name="risk_analysis",
        description="Analyze and improve risk management strategies",
        default_goal="Review current risk model and propose improvements",
        suggested_agents=["chatgpt", "claude_cli"],
        suggested_rounds=2,
        suggested_kernels=["risk_model_v2"],
        tags=["risk", "trading", "sizing"]
    ),
    "alpha_optimization": SessionTemplate(
        name="alpha_optimization",
        description="Optimize alpha signals and trading strategy",
        default_goal="Analyze alpha signals and reduce false positives",
        suggested_agents=["chatgpt", "claude_cli"],
        suggested_rounds=2,
        suggested_kernels=["alpha_polymarket_core"],
        tags=["alpha", "signals", "optimization"]
    ),
    "system_architecture": SessionTemplate(
        name="system_architecture",
        description="Discuss system architecture and infrastructure changes",
        default_goal="Review system architecture and plan improvements",
        suggested_agents=["chatgpt", "claude_cli"],
        suggested_rounds=2,
        suggested_kernels=["system_health"],
        tags=["architecture", "infrastructure", "design"]
    ),
    "ai_coordination": SessionTemplate(
        name="ai_coordination",
        description="Coordinate between AI agents on tasks and strategy",
        default_goal="Align AI agents on priorities and resolve coordination issues",
        suggested_agents=["chatgpt", "claude_cli"],
        suggested_rounds=2,
        suggested_kernels=["ai_coordination"],
        tags=["coordination", "agents", "alignment"]
    ),
    "general_discussion": SessionTemplate(
        name="general_discussion",
        description="General multi-agent discussion and analysis",
        default_goal="General discussion and analysis",
        suggested_agents=["chatgpt", "claude_cli"],
        suggested_rounds=1,
        suggested_kernels=[],
        tags=["general", "discussion"]
    ),
    "deep_research": SessionTemplate(
        name="deep_research",
        description="Deep research session with extended rounds",
        default_goal="Conduct thorough research and analysis",
        suggested_agents=["chatgpt", "claude_cli"],
        suggested_rounds=3,
        suggested_kernels=[],
        mode="continuous",
        tags=["research", "deep-dive", "extended"]
    ),
}


# =============================================================================
# Session Discovery
# =============================================================================

@dataclass
class SessionInfo:
    """Information about an existing session"""
    conversation_id: str
    status: str
    created: Optional[str]
    goal: Optional[str]
    rounds_completed: int
    participants: List[str]
    message_count: int
    cpu_mode: Optional[str]
    bound_kernels: List[str]
    intercom_path: str

    def to_dict(self) -> Dict:
        return asdict(self)


def list_sessions(include_archived: bool = False) -> List[SessionInfo]:
    """
    List all existing sessions in ai/intercom/

    Args:
        include_archived: Whether to include archived sessions

    Returns:
        List of SessionInfo objects
    """
    sessions = []

    if not INTERCOM_DIR.exists():
        return sessions

    for session_dir in INTERCOM_DIR.iterdir():
        if not session_dir.is_dir():
            continue

        # Skip hidden directories
        if session_dir.name.startswith("."):
            continue

        # Skip archived if not requested
        if session_dir.name.startswith("archived_") and not include_archived:
            continue

        session_info = get_session_info(session_dir.name)
        if session_info:
            sessions.append(session_info)

    # Sort by created date (newest first)
    sessions.sort(key=lambda s: s.created or "", reverse=True)

    return sessions


def get_session_info(conversation_id: str) -> Optional[SessionInfo]:
    """
    Get detailed information about a specific session

    Args:
        conversation_id: The conversation ID

    Returns:
        SessionInfo or None if not found
    """
    session_dir = INTERCOM_DIR / conversation_id

    if not session_dir.exists():
        return None

    metadata_file = session_dir / "metadata.json"
    thread_file = session_dir / "thread.jsonl"
    cpu_instance_file = session_dir / "cpu_instance.json"

    # Load metadata
    metadata = {}
    if metadata_file.exists():
        try:
            with open(metadata_file) as f:
                metadata = json.load(f)
        except Exception:
            pass

    # Count messages
    message_count = 0
    if thread_file.exists():
        try:
            with open(thread_file) as f:
                message_count = sum(1 for line in f if line.strip())
        except Exception:
            pass

    # Load CPU instance info
    cpu_mode = None
    bound_kernels = []
    if cpu_instance_file.exists():
        try:
            with open(cpu_instance_file) as f:
                cpu_data = json.load(f)
                cpu_mode = cpu_data.get("mode")
                bound_kernels = cpu_data.get("bound_kernels", [])
        except Exception:
            pass

    return SessionInfo(
        conversation_id=conversation_id,
        status=metadata.get("status", "unknown"),
        created=metadata.get("created"),
        goal=metadata.get("goal"),
        rounds_completed=metadata.get("rounds_completed", 0),
        participants=metadata.get("participants", []),
        message_count=message_count,
        cpu_mode=cpu_mode,
        bound_kernels=bound_kernels,
        intercom_path=str(thread_file)
    )


# =============================================================================
# Session Creation
# =============================================================================

def generate_conversation_id(topic: Optional[str] = None) -> str:
    """
    Generate a unique conversation ID

    Format: YYYYMMDD_HHMMSS_<topic>

    Args:
        topic: Optional topic slug to append

    Returns:
        Generated conversation ID
    """
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")

    if topic:
        # Sanitize topic
        topic_slug = topic.lower().replace(" ", "_")[:MAX_TOPIC_LENGTH]
        topic_slug = "".join(c for c in topic_slug if c.isalnum() or c == "_")
        return f"{timestamp}_{topic_slug}"

    return timestamp


def create_session(
    goal: str,
    agents: Optional[List[str]] = None,
    rounds: int = 1,
    kernels: Optional[List[str]] = None,
    mode: Literal["burst", "continuous"] = "burst",
    max_steps: int = 20,
    max_duration_seconds: int = 900,
    conversation_id: Optional[str] = None,
    template: Optional[str] = None
) -> Dict:
    """
    Create a new agent session

    Args:
        goal: Session goal/purpose
        agents: List of agents to include
        rounds: Number of rounds (for burst mode)
        kernels: List of kernel IDs to bind
        mode: Session mode (burst or continuous)
        max_steps: Max steps for continuous mode
        max_duration_seconds: Max duration for continuous mode
        conversation_id: Optional custom conversation ID
        template: Optional template name to use as base

    Returns:
        Dict with session creation info
    """
    # Use template defaults if specified
    if template and template in BUILTIN_TEMPLATES:
        tmpl = BUILTIN_TEMPLATES[template]
        if not goal:
            goal = tmpl.default_goal
        if agents is None:
            agents = tmpl.suggested_agents
        if kernels is None:
            kernels = tmpl.suggested_kernels
        if rounds == 1:  # Only override if using default
            rounds = tmpl.suggested_rounds
        mode = tmpl.mode

    # Apply defaults
    if agents is None:
        agents = ["chatgpt", "claude_cli"]
    if kernels is None:
        kernels = []

    # Generate conversation ID
    if not conversation_id:
        # Extract topic from goal
        topic = goal.split()[0:GOAL_WORDS_FOR_TOPIC]
        topic_str = "_".join(topic) if topic else "session"
        conversation_id = generate_conversation_id(topic_str)

    # Create session directory
    session_dir = INTERCOM_DIR / conversation_id
    session_dir.mkdir(parents=True, exist_ok=True)

    # Create CPU instance
    cpu = CpuInstance(
        cpu_id=f"cpu_{conversation_id}",
        mode=mode,
        bound_kernels=kernels,
        intercom_path=str(session_dir / "thread.jsonl"),
        status="idle",
        config=CpuConfig(
            max_rounds=rounds if mode == "burst" else None,
            max_cost_usd=1.0,
            max_steps=max_steps,
            max_duration_seconds=max_duration_seconds
        )
    )

    # Save CPU instance
    with open(session_dir / "cpu_instance.json", "w") as f:
        f.write(cpu.to_json())

    # Create metadata
    metadata = {
        "conversation_id": conversation_id,
        "created": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "topic": conversation_id.split("_", 2)[-1] if "_" in conversation_id else "discussion",
        "goal": goal,
        "participants": agents,
        "status": "created",
        "rounds_completed": 0,
        "template": template
    }

    with open(session_dir / "metadata.json", "w") as f:
        json.dump(metadata, f, indent=2)

    # Create empty thread file
    (session_dir / "thread.jsonl").touch()

    return {
        "status": "created",
        "conversation_id": conversation_id,
        "session_dir": str(session_dir),
        "goal": goal,
        "agents": agents,
        "mode": mode,
        "rounds": rounds if mode == "burst" else None,
        "max_steps": max_steps if mode == "continuous" else None,
        "bound_kernels": kernels,
        "run_command": _generate_run_command(conversation_id, goal, agents, mode, rounds, kernels, max_steps, max_duration_seconds)
    }


def _generate_run_command(
    conversation_id: str,
    goal: str,
    agents: List[str],
    mode: str,
    rounds: int,
    kernels: List[str],
    max_steps: int,
    max_duration_seconds: int
) -> str:
    """Generate the command to run the session"""
    cmd_parts = [
        "python -m ai_nexus.tri_agent_session_runner",
        f'--conversation-id "{conversation_id}"',
        f'--session-goal "{goal}"',
        f"--agents {','.join(agents)}"
    ]

    if mode == "continuous":
        cmd_parts.append("--continuous")
        cmd_parts.append(f"--max-steps {max_steps}")
        cmd_parts.append(f"--max-duration-seconds {max_duration_seconds}")
    else:
        cmd_parts.append(f"--rounds {rounds}")

    if kernels:
        cmd_parts.append(f"--bind-kernels {','.join(kernels)}")

    return " \\\n    ".join(cmd_parts)


# =============================================================================
# Session Suggestions
# =============================================================================

def suggest_sessions() -> List[Dict]:
    """
    Suggest new sessions based on system state and available kernels

    Returns:
        List of suggested session configurations
    """
    suggestions = []

    # Check available kernels
    available_kernels = list_kernels()

    # Suggest sessions based on kernels that need attention
    for kernel_id in available_kernels:
        kernel = load_kernel(kernel_id)
        if kernel and kernel.open_questions:
            suggestions.append({
                "reason": f"Kernel '{kernel_id}' has {len(kernel.open_questions)} open questions",
                "open_questions": kernel.open_questions[:MAX_DISPLAYED_QUESTIONS],
                "template": _suggest_template_for_kernel(kernel_id),
                "goal": f"Address open questions in {kernel.topic}",
                "kernels": [kernel_id],
                "priority": "medium"
            })

    # Check coordination status for needed discussions
    coordination_file = COORDINATION_DIR / "status.json"
    if coordination_file.exists():
        try:
            with open(coordination_file) as f:
                status = json.load(f)

            # Look for pending tasks
            pending_tasks = [
                t for t in status.get("pending_tasks", [])
                if t.get("status") == "pending"
            ]

            for task in pending_tasks[:MAX_PENDING_TASKS]:
                suggestions.append({
                    "reason": f"Pending task: {task.get('description', 'unknown')}",
                    "task_id": task.get("id"),
                    "template": "ai_coordination",
                    "goal": f"Coordinate on: {task.get('description', 'pending task')}",
                    "kernels": ["ai_coordination"],
                    "priority": task.get("priority", "medium")
                })
        except Exception:
            pass

    # Add default suggestions if no specific ones
    if not suggestions:
        suggestions = [
            {
                "reason": "Regular system health check",
                "template": "system_architecture",
                "goal": "Review system health and identify improvements",
                "kernels": ["system_health"],
                "priority": "low"
            },
            {
                "reason": "Alpha optimization opportunity",
                "template": "alpha_optimization",
                "goal": "Review alpha signals and optimize selection criteria",
                "kernels": ["alpha_polymarket_core"],
                "priority": "low"
            }
        ]

    return suggestions


def _suggest_template_for_kernel(kernel_id: str) -> str:
    """Suggest a template based on kernel topic"""
    if "risk" in kernel_id.lower():
        return "risk_analysis"
    elif "alpha" in kernel_id.lower():
        return "alpha_optimization"
    elif "coordination" in kernel_id.lower():
        return "ai_coordination"
    elif "system" in kernel_id.lower() or "health" in kernel_id.lower():
        return "system_architecture"
    return "general_discussion"


# =============================================================================
# CLI Interface
# =============================================================================

def cmd_list(args):
    """List all sessions"""
    sessions = list_sessions(include_archived=args.archived)

    if not sessions:
        print("No sessions found.")
        return

    print(f"\n{'='*80}")
    print("AGENT SESSIONS")
    print(f"{'='*80}\n")

    for session in sessions:
        status_icon = "🟢" if session.status == "active" else "🔵" if session.status == "created" else "⚫"
        mode_icon = "♾️" if session.cpu_mode == "continuous" else "🔄"

        print(f"{status_icon} {session.conversation_id}")
        print(f"   Goal: {session.goal or 'N/A'}")
        print(f"   Status: {session.status} | Mode: {mode_icon} {session.cpu_mode or 'burst'}")
        print(f"   Rounds: {session.rounds_completed} | Messages: {session.message_count}")
        print(f"   Participants: {', '.join(session.participants) if session.participants else 'N/A'}")
        if session.bound_kernels:
            print(f"   Bound Kernels: {', '.join(session.bound_kernels)}")
        print()

    print(f"Total: {len(sessions)} session(s)")


def cmd_create(args):
    """Create a new session"""
    kernels = [k.strip() for k in args.kernels.split(",")] if args.kernels else None
    agents = [a.strip() for a in args.agents.split(",")] if args.agents else None

    result = create_session(
        goal=args.goal,
        agents=agents,
        rounds=args.rounds,
        kernels=kernels,
        mode="continuous" if args.continuous else "burst",
        max_steps=args.max_steps,
        max_duration_seconds=args.max_duration,
        conversation_id=args.id,
        template=args.template
    )

    print(f"\n{'='*80}")
    print("SESSION CREATED")
    print(f"{'='*80}\n")
    print(f"Conversation ID: {result['conversation_id']}")
    print(f"Goal: {result['goal']}")
    print(f"Agents: {', '.join(result['agents'])}")
    print(f"Mode: {result['mode']}")
    if result['mode'] == 'burst':
        print(f"Rounds: {result['rounds']}")
    else:
        print(f"Max Steps: {result['max_steps']}")
    if result['bound_kernels']:
        print(f"Bound Kernels: {', '.join(result['bound_kernels'])}")
    print(f"\nSession Directory: {result['session_dir']}")
    print(f"\n{'='*80}")
    print("RUN COMMAND")
    print(f"{'='*80}\n")
    print(result['run_command'])
    print()


def cmd_suggest(args):
    """Suggest new sessions"""
    suggestions = suggest_sessions()

    if not suggestions:
        print("No session suggestions at this time.")
        return

    print(f"\n{'='*80}")
    print("SESSION SUGGESTIONS")
    print(f"{'='*80}\n")

    for i, suggestion in enumerate(suggestions, 1):
        priority_icon = "🔴" if suggestion["priority"] == "high" else "🟡" if suggestion["priority"] == "medium" else "🟢"

        print(f"{i}. {priority_icon} {suggestion['reason']}")
        print(f"   Template: {suggestion.get('template', 'N/A')}")
        print(f"   Suggested Goal: {suggestion['goal']}")
        if suggestion.get('kernels'):
            print(f"   Kernels: {', '.join(suggestion['kernels'])}")
        if suggestion.get('open_questions'):
            print("   Open Questions:")
            for q in suggestion['open_questions']:
                print(f"     - {q}")
        print()

    print(f"Total: {len(suggestions)} suggestion(s)")
    print("\nTo create a suggested session:")
    print(f"  python -m ai_nexus.session_manager create --template <name> --goal '<goal>'")


def cmd_info(args):
    """Get info about a specific session"""
    session = get_session_info(args.conversation_id)

    if not session:
        print(f"Session not found: {args.conversation_id}")
        return

    print(f"\n{'='*80}")
    print(f"SESSION INFO: {session.conversation_id}")
    print(f"{'='*80}\n")
    print(f"Status: {session.status}")
    print(f"Created: {session.created or 'N/A'}")
    print(f"Goal: {session.goal or 'N/A'}")
    print(f"Mode: {session.cpu_mode or 'burst'}")
    print(f"Rounds Completed: {session.rounds_completed}")
    print(f"Message Count: {session.message_count}")
    print(f"Participants: {', '.join(session.participants) if session.participants else 'N/A'}")
    if session.bound_kernels:
        print(f"Bound Kernels: {', '.join(session.bound_kernels)}")
    print(f"\nIntercom Path: {session.intercom_path}")


def cmd_templates(args):
    """List available templates"""
    print(f"\n{'='*80}")
    print("AVAILABLE TEMPLATES")
    print(f"{'='*80}\n")

    for name, template in BUILTIN_TEMPLATES.items():
        mode_icon = "♾️" if template.mode == "continuous" else "🔄"
        print(f"📋 {name}")
        print(f"   {template.description}")
        print(f"   Default Goal: {template.default_goal}")
        print(f"   Mode: {mode_icon} {template.mode} | Rounds: {template.suggested_rounds}")
        print(f"   Agents: {', '.join(template.suggested_agents)}")
        if template.suggested_kernels:
            print(f"   Kernels: {', '.join(template.suggested_kernels)}")
        print(f"   Tags: {', '.join(template.tags)}")
        print()


def main():
    """CLI entrypoint"""
    parser = argparse.ArgumentParser(
        description="Agent Session Manager - Discover, create, and manage agent sessions",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )

    subparsers = parser.add_subparsers(dest="command", required=True)

    # list command
    parser_list = subparsers.add_parser("list", help="List all sessions")
    parser_list.add_argument("--archived", action="store_true", help="Include archived sessions")
    parser_list.set_defaults(func=cmd_list)

    # create command
    parser_create = subparsers.add_parser("create", help="Create a new session")
    parser_create.add_argument("--goal", required=True, help="Session goal/purpose")
    parser_create.add_argument("--agents", default="chatgpt,claude_cli", help="Comma-separated list of agents")
    parser_create.add_argument("--rounds", type=int, default=1, help="Number of rounds (burst mode)")
    parser_create.add_argument("--kernels", help="Comma-separated list of kernel IDs to bind")
    parser_create.add_argument("--continuous", action="store_true", help="Use continuous mode")
    parser_create.add_argument("--max-steps", type=int, default=20, help="Max steps (continuous mode)")
    parser_create.add_argument("--max-duration", type=int, default=900, help="Max duration in seconds")
    parser_create.add_argument("--id", help="Custom conversation ID")
    parser_create.add_argument("--template", help="Template name to use")
    parser_create.set_defaults(func=cmd_create)

    # suggest command
    parser_suggest = subparsers.add_parser("suggest", help="Suggest new sessions")
    parser_suggest.set_defaults(func=cmd_suggest)

    # info command
    parser_info = subparsers.add_parser("info", help="Get info about a session")
    parser_info.add_argument("conversation_id", help="The conversation ID")
    parser_info.set_defaults(func=cmd_info)

    # templates command
    parser_templates = subparsers.add_parser("templates", help="List available templates")
    parser_templates.set_defaults(func=cmd_templates)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
