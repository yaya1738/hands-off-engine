#!/usr/bin/env python3
"""
INTEGRAFIX: Startup Script
==========================

Run this at the beginning of any Claude session or script to:
1. Load AI memory context from previous sessions
2. Initialize process coordinator
3. Show system status
4. Provide continuity

Usage:
    from integrafix.startup import init_session, get_context

    # At session start
    context = init_session("Working on trading improvements")
    print(context)  # Shows what happened in previous sessions
"""

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

STATE_DIR = PROJECT_ROOT / "state"


def init_session(task_description: str = "Claude Code session") -> str:
    """
    Initialize a new session with full context.

    Args:
        task_description: What this session is working on

    Returns:
        Context string from previous sessions
    """
    output = []
    output.append("=" * 70)
    output.append("INTEGRAFIX SESSION INITIALIZATION")
    output.append("=" * 70)
    output.append("")

    # 1. Load AI memory
    try:
        from integrafix.ai_memory import get_memory

        memory = get_memory()
        memory.start_session(task_description)

        context = memory.build_context()
        if context:
            output.append("[AI MEMORY] Context from previous sessions:")
            output.append(context[:2000])  # Limit size
            output.append("")
    except Exception as e:
        output.append(f"[AI MEMORY] Failed to load: {e}")
        context = ""

    # 2. Initialize process coordinator
    try:
        from integrafix.process_coordinator import get_coordinator, ProcessState

        coord = get_coordinator()

        # Check running processes
        status = coord.status()
        output.append("[PROCESS COORDINATOR]")
        output.append(f"  Registered processes: {len(status['processes'])}")
        for name, info in status['processes'].items():
            alive = "ALIVE" if coord.is_alive(name) else "DEAD"
            output.append(f"    {name}: {info['state']} ({alive})")
        output.append("")
    except Exception as e:
        output.append(f"[PROCESS COORDINATOR] Failed: {e}")

    # 3. Check integration score
    try:
        from integrafix.methodology import get_methodology

        m = get_methodology()
        score = m.calculate_integration_score()
        fixed = sum(1 for g in m.gaps.values() if g.fixed)
        total = len(m.gaps)

        output.append("[INTEGRATION STATUS]")
        output.append(f"  Score: {score:.1%}")
        output.append(f"  Gaps fixed: {fixed}/{total}")

        unfixed = [g for g in m.gaps.values() if not g.fixed]
        if unfixed:
            output.append("  Remaining gaps:")
            for g in unfixed[:3]:
                output.append(f"    - {g.description[:50]}")
        output.append("")
    except Exception as e:
        output.append(f"[INTEGRATION STATUS] Failed: {e}")

    # 4. Check trading pipeline
    try:
        from integrafix.trading_pipeline import get_pipeline

        pipeline = get_pipeline()
        status = pipeline.status()

        output.append("[TRADING PIPELINE]")
        output.append(f"  Total signals: {status['state'].get('total_signals', 0)}")
        output.append(f"  Total trades: {status['state'].get('total_trades', 0)}")
        output.append(f"  Win rate: {status['state'].get('win_rate', 0):.1%}")
        output.append(f"  Total P&L: ${status['state'].get('total_pnl', 0):.2f}")
        output.append("")
    except Exception as e:
        output.append(f"[TRADING PIPELINE] Failed: {e}")

    # 5. Show recent activity
    try:
        backend_state = STATE_DIR / "backend_loop.json"
        if backend_state.exists():
            with open(backend_state) as f:
                data = json.load(f)
                output.append("[RECENT ACTIVITY]")
                output.append(f"  Backend loop cycle: {data.get('cycle', 'unknown')}")
                output.append(f"  Last updated: {data.get('last_updated', 'unknown')[:19]}")
    except:
        pass

    output.append("")
    output.append("=" * 70)
    output.append(f"Session started: {datetime.now(timezone.utc).isoformat()}")
    output.append(f"Task: {task_description}")
    output.append("=" * 70)

    return "\n".join(output)


def get_context() -> str:
    """Get AI memory context without starting a new session."""
    try:
        from integrafix.ai_memory import AIMemory
        return AIMemory.load_context()
    except:
        return ""


def end_session(outcomes: list, next_actions: list):
    """End session and save context for next time."""
    try:
        from integrafix.ai_memory import get_memory

        memory = get_memory()
        memory.end_session(outcomes, next_actions)
        memory.save_context()
        print("✓ Session context saved for next time")
    except Exception as e:
        print(f"Failed to save session: {e}")


def main():
    """Test startup initialization."""
    context = init_session("Testing integrafix startup")
    print(context)


if __name__ == "__main__":
    main()
