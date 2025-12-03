#!/usr/bin/env python3
"""
AI SESSION INITIALIZER - INTEGRAFIX
====================================

Loads context from previous AI sessions to provide continuity.

This script should be run at the start of any AI session to:
1. Load memories from previous sessions
2. Build context string for the AI
3. Record session start
4. Set up session end handlers

Usage:
    # At session start
    from ai.session_init import initialize_session
    context = initialize_session("Implementing new feature X")

    # At session end
    from ai.session_init import end_session
    end_session(["Completed feature X", "Fixed bug Y"], ["Test feature X"])

Serving: Yair Siegel
"""

import sys
import atexit
from datetime import datetime, timezone
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# Session state
_current_session = None
_session_initialized = False


def initialize_session(task_description: str = "AI session") -> str:
    """
    Initialize a new AI session with context from previous sessions.

    Args:
        task_description: What this session is working on

    Returns:
        Context string containing relevant memories
    """
    global _current_session, _session_initialized

    if _session_initialized:
        return get_current_context()

    try:
        from integrafix.ai_memory import get_memory

        # Create session with unique ID
        session_id = f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        _current_session = get_memory(session_id)

        # Start session
        _current_session.start_session(task_description)

        # Build context from previous sessions
        context = _current_session.build_context()

        # Register end handler
        atexit.register(_auto_end_session)

        _session_initialized = True

        print(f"[SESSION INIT] Session {session_id} started")
        print(f"[SESSION INIT] Loaded {_current_session.status()['total_memories']} memories")

        return context

    except ImportError:
        print("[SESSION INIT] AI memory not available")
        return ""
    except Exception as e:
        print(f"[SESSION INIT] Error: {e}")
        return ""


def get_current_context() -> str:
    """Get the current session's context."""
    if _current_session:
        return _current_session.build_context()
    return ""


def remember(content: str, memory_type: str = "context", priority: str = "medium"):
    """
    Remember something during this session.

    Args:
        content: What to remember
        memory_type: decision, learning, error, success, context, insight
        priority: critical, high, medium, low, ephemeral
    """
    if not _current_session:
        return None

    try:
        from integrafix.ai_memory import MemoryType, MemoryPriority

        type_map = {
            "decision": MemoryType.DECISION,
            "learning": MemoryType.LEARNING,
            "error": MemoryType.ERROR,
            "success": MemoryType.SUCCESS,
            "context": MemoryType.CONTEXT,
            "insight": MemoryType.INSIGHT,
            "code_change": MemoryType.CODE_CHANGE,
        }

        priority_map = {
            "critical": MemoryPriority.CRITICAL,
            "high": MemoryPriority.HIGH,
            "medium": MemoryPriority.MEDIUM,
            "low": MemoryPriority.LOW,
            "ephemeral": MemoryPriority.EPHEMERAL,
        }

        return _current_session.remember(
            content=content,
            memory_type=type_map.get(memory_type, MemoryType.CONTEXT),
            priority=priority_map.get(priority, MemoryPriority.MEDIUM),
        )
    except Exception:
        return None


def remember_decision(decision: str, reasoning: str, outcome: str = ""):
    """Remember a decision made during this session."""
    if _current_session:
        return _current_session.remember_decision(decision, reasoning, outcome)


def remember_learning(what_learned: str, how_learned: str):
    """Remember something learned during this session."""
    if _current_session:
        return _current_session.remember_learning(what_learned, how_learned)


def remember_error(error: str, solution: str = ""):
    """Remember an error encountered during this session."""
    if _current_session:
        return _current_session.remember_error(error, solution)


def remember_success(what_worked: str, why_worked: str):
    """Remember a success during this session."""
    if _current_session:
        return _current_session.remember_success(what_worked, why_worked)


def recall(query: str = None, limit: int = 5):
    """Recall memories matching a query."""
    if _current_session:
        return _current_session.recall(query=query, limit=limit)
    return []


def end_session(outcomes: list = None, next_actions: list = None):
    """
    End the current session with a summary.

    Args:
        outcomes: List of what was accomplished
        next_actions: List of what should be done next
    """
    global _session_initialized

    if not _current_session:
        return

    try:
        _current_session.end_session(
            outcomes=outcomes or ["Session ended"],
            next_actions=next_actions or []
        )

        # Save context for next session
        _current_session.save_context()

        print(f"[SESSION END] Session ended")
        print(f"[SESSION END] Recorded {len(outcomes or [])} outcomes")
        print(f"[SESSION END] Next actions: {len(next_actions or [])}")

        _session_initialized = False

    except Exception as e:
        print(f"[SESSION END] Error: {e}")


def _auto_end_session():
    """Auto-end session on exit if not explicitly ended."""
    if _session_initialized and _current_session:
        try:
            _current_session.end_session(
                outcomes=["Session ended automatically"],
                next_actions=["Review session outcomes"]
            )
            _current_session.save_context()
        except Exception:
            pass


def get_session_status():
    """Get current session status."""
    if _current_session:
        return _current_session.status()
    return {"initialized": False}


def main():
    """Demo the session initializer."""
    print("=" * 70)
    print("AI SESSION INITIALIZER - INTEGRAFIX")
    print("=" * 70)
    print()

    # Initialize session
    context = initialize_session("Testing session persistence")

    print("\n[LOADED CONTEXT]")
    print("-" * 70)
    print(context or "(no previous context)")
    print("-" * 70)

    # Remember some things
    print("\n[RECORDING MEMORIES]")
    remember_decision(
        decision="Use file-based persistence for session memory",
        reasoning="Simple, reliable, works across AI sessions"
    )
    print("  + Recorded decision")

    remember_learning(
        what_learned="Session initialization must be automatic",
        how_learned="Testing session_init.py"
    )
    print("  + Recorded learning")

    remember_success(
        what_worked="INTEGRAFIX AI memory integration",
        why_worked="Wired memory system into orchestrator and session init"
    )
    print("  + Recorded success")

    # Show status
    status = get_session_status()
    print(f"\n[SESSION STATUS]")
    print(f"  Memories: {status.get('total_memories', 0)}")
    print(f"  Sessions: {status.get('total_sessions', 0)}")

    # End session
    end_session(
        outcomes=["Tested session initialization", "Memory persistence working"],
        next_actions=["Integrate into Claude startup", "Add to autonomous scripts"]
    )

    print("\n" + "=" * 70)
    print("Session initialization complete")
    print("=" * 70)


if __name__ == "__main__":
    main()
