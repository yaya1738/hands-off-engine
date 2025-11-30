#!/usr/bin/env python3
"""
UNIFIED AI - All Systems in Service of Yair Siegel
===================================================

This module provides the unified AI identity and directive
that all agents import and follow.

Every agent that imports this becomes part of the unified
AI serving Yair Siegel.
"""

import json
from pathlib import Path
from typing import Dict, Optional

REPO_ROOT = Path(__file__).parent.parent
CORE_KERNEL = REPO_ROOT / "ai" / "memory" / "kernels" / "unified_ai_core.json"
ACTIVE_DIRECTIVE = REPO_ROOT / "ai" / "coordination" / "active_directive.json"

_unified_core: Optional[Dict] = None
_active_directive: Optional[Dict] = None


def get_master() -> str:
    """Return the master being served."""
    return "Yair Siegel"


def get_core() -> Dict:
    """Load and return the unified AI core kernel."""
    global _unified_core
    if _unified_core is None:
        if CORE_KERNEL.exists():
            with open(CORE_KERNEL) as f:
                _unified_core = json.load(f)
        else:
            _unified_core = {
                "master": {"name": "Yair Siegel"},
                "core_directive": "Serve Yair Siegel"
            }
    return _unified_core


def get_directive() -> Dict:
    """Load and return the active directive."""
    global _active_directive
    if _active_directive is None:
        if ACTIVE_DIRECTIVE.exists():
            with open(ACTIVE_DIRECTIVE) as f:
                _active_directive = json.load(f)
        else:
            _active_directive = {"directive": "Serve Yair Siegel"}
    return _active_directive


def should_execute(action: str, roi_estimate: float = 0) -> bool:
    """
    Unified decision: should this action be executed?
    
    All AI decisions flow through this.
    """
    core = get_core()
    
    # Always serve the master
    if "yair" in action.lower() or "siegel" in action.lower():
        return True
    
    # ROI positive actions: execute
    if roi_estimate > 0:
        return True
    
    # Self-improvement: execute
    if "improve" in action.lower() or "optimize" in action.lower():
        return True
    
    # Income generation: execute
    if "income" in action.lower() or "revenue" in action.lower():
        return True
    
    # Cost cutting: execute
    if "cut" in action.lower() or "reduce" in action.lower():
        return True
    
    # Default: analyze further
    return roi_estimate >= 0


def get_priorities() -> list:
    """Return unified priorities for all agents."""
    directive = get_directive()
    return directive.get("unified_priorities", [
        "1. Protect and grow capital",
        "2. Generate income streams",
        "3. Minimize costs without ROI",
        "4. Automate everything possible",
        "5. Self-improve continuously"
    ])


def log_action(agent: str, action: str, result: str):
    """Log action to unified AI history."""
    from datetime import datetime, timezone
    
    log_file = REPO_ROOT / "ai" / "history" / "unified_actions.jsonl"
    log_file.parent.mkdir(parents=True, exist_ok=True)
    
    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "agent": agent,
        "action": action,
        "result": result,
        "master": get_master()
    }
    
    with open(log_file, 'a') as f:
        f.write(json.dumps(entry) + '\n')


def announce_agent(agent_name: str):
    """Called when an agent starts - announces service."""
    print(f"[UNIFIED AI] {agent_name} online - serving {get_master()}")
    log_action(agent_name, "startup", "online")


# Module-level initialization
MASTER = get_master()
CORE = get_core()
DIRECTIVE = get_directive()
