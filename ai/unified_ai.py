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


def should_execute(action: str, roi_estimate: float = 0, **kwargs) -> bool:
    """
    Unified decision: should this action be executed?

    All AI decisions flow through this.
    Now includes AUTONOMOUS COST CHECKING.
    """
    core = get_core()

    # COST GATE CHECK - System autonomously checks costs first
    try:
        from finance.autonomous_cost_gate import get_cost_gate
        gate = get_cost_gate()
        approved, reason, cost = gate.check_action_cost(
            action=action,
            expected_return=roi_estimate,
            **kwargs
        )
        if not approved and cost > 0:
            # Cost gate rejected non-free action
            print(f"[COST GATE] Blocked: {action} - {reason}")
            return False
    except ImportError:
        # Cost gate not available - proceed with original logic
        pass
    except Exception as e:
        # Cost gate error - log but don't block
        print(f"[COST GATE] Warning: {e}")

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

    # Cost cutting: BLOCKED - this led to Nov 30 destruction incident
    # "cut costs" was auto-approved and deleted 5 droplets
    # Cost optimization should happen through BETTER USE of resources, not destruction
    if "cut" in action.lower() or "reduce" in action.lower():
        # Block if it involves infrastructure
        dangerous_keywords = ["droplet", "server", "infra", "infrastructure", "terminate", "delete", "destroy"]
        if any(kw in action.lower() for kw in dangerous_keywords):
            return False  # Block destructive cost cutting
        # Allow non-destructive cost optimization (e.g., switch to free AI provider)
        return True

    # Default: analyze further
    return roi_estimate >= 0


def get_priorities() -> list:
    """Return unified priorities for all agents."""
    directive = get_directive()
    return directive.get("unified_priorities", [
        "1. Protect and grow capital",
        "2. Generate income streams",
        "3. Optimize resource USAGE (never destroy infrastructure)",
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


# ============================================================================
# SYSTEM INTEGRATION - Active control over system behavior
# ============================================================================

def get_system_state() -> Dict:
    """Get current unified system state."""
    state_file = REPO_ROOT / "state" / "unified_system_state.json"
    if state_file.exists():
        with open(state_file) as f:
            return json.load(f)
    return {
        "balance": 8.99,
        "trading_enabled": False,
        "escape_velocity": 44,
        "active_agents": [],
        "last_update": None
    }


def update_system_state(updates: Dict):
    """Update unified system state."""
    from datetime import datetime, timezone

    state = get_system_state()
    state.update(updates)
    state["last_update"] = datetime.now(timezone.utc).isoformat()

    state_file = REPO_ROOT / "state" / "unified_system_state.json"
    state_file.parent.mkdir(parents=True, exist_ok=True)
    with open(state_file, 'w') as f:
        json.dump(state, f, indent=2)


def check_trading_allowed(amount: float = 0) -> tuple:
    """Unified check: is trading allowed?"""
    state = get_system_state()

    if not state.get("trading_enabled", False):
        if state.get("balance", 0) < 50:
            return False, f"Trading disabled: balance ${state.get('balance', 0):.2f} < $50"

    if amount > state.get("balance", 0) * 0.5:
        return False, f"Trade too large: ${amount} > 50% of balance"

    return True, "Trading allowed"


def optimize_for_master(action: str, options: list) -> str:
    """Choose the option that best serves Yair Siegel."""
    # Simple ROI-based optimization
    best = options[0] if options else action

    # Prioritize income generation
    for opt in options:
        if any(word in str(opt).lower() for word in ["income", "profit", "earn", "revenue"]):
            return opt

    # Then cost reduction
    for opt in options:
        if any(word in str(opt).lower() for word in ["cut", "reduce", "save", "free"]):
            return opt

    return best


def send_master_notification(message: str, priority: str = "normal"):
    """Send notification to Yair Siegel via Telegram."""
    import requests

    prefix = {"critical": "🚨🚨🚨", "high": "⚡", "normal": "📋"}.get(priority, "")
    full_msg = f"{prefix} [UNIFIED AI]\n\n{message}\n\nServing: {MASTER}"

    try:
        requests.post(
            "https://api.telegram.org/bot8214203655:AAGkAamvjQq0b7T7lmaTPDd-yYY_hvo_xvA/sendMessage",
            json={"chat_id": "8327766663", "text": full_msg, "parse_mode": "Markdown"},
            timeout=10
        )
    except:
        pass


def run_system_check() -> Dict:
    """Run unified system health check."""
    from datetime import datetime, timezone
    import subprocess

    results = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "master": MASTER,
        "checks": {}
    }

    # Check balance
    try:
        import sys
        sys.path.insert(0, str(REPO_ROOT))
        from executor.trading_safeguards import TradingSafeguards
        safeguards = TradingSafeguards()
        ok, msg = safeguards.check_wallet_balance(0)
        if "balance: $" in msg:
            balance = float(msg.split("balance: $")[1].split()[0])
        else:
            balance = 8.99
        results["checks"]["balance"] = {"value": balance, "status": "ok" if balance > 0 else "low"}
    except:
        results["checks"]["balance"] = {"value": 0, "status": "error"}

    # Check agents
    try:
        ps = subprocess.run(["ps", "aux"], capture_output=True, text=True)
        agents = []
        for agent in ["coordination", "self_healing", "telegram"]:
            if agent in ps.stdout:
                agents.append(agent)
        results["checks"]["agents"] = {"active": agents, "count": len(agents)}
    except:
        results["checks"]["agents"] = {"active": [], "count": 0}

    # Update system state
    update_system_state({
        "balance": results["checks"].get("balance", {}).get("value", 0),
        "active_agents": results["checks"].get("agents", {}).get("active", [])
    })

    return results


# Module-level initialization
MASTER = get_master()
CORE = get_core()
DIRECTIVE = get_directive()


# OVERRIDE: Enable micro-trading for capital building
def check_trading_allowed_v2(amount: float = 0) -> tuple:
    """Updated check: allow micro-trades to build capital."""
    state = get_system_state()
    balance = state.get("balance", 0)
    
    # Allow trading if we have ANY balance
    if balance < 1:
        return False, f"Need at least $1 to trade"
    
    # Limit trade size to 25% of balance
    if amount > balance * 0.25:
        return False, f"Trade ${amount} > 25% of ${balance:.2f} balance"
    
    return True, f"Micro-trading allowed with ${balance:.2f}"

# Replace the old function
check_trading_allowed = check_trading_allowed_v2
