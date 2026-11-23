#!/usr/bin/env python3
"""
UNIFIED AI - All Systems in Service of Yair Siegel
===================================================
LEVEL: 60 miles - Inherits from AbsoluteDirective (80 miles)

This module provides the unified AI identity and directive
that all agents import and follow.

Every agent that imports this becomes part of the unified
AI serving Yair Siegel.
"""

import json
import math
import os
import sys
from pathlib import Path
from typing import Dict, Optional

REPO_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(REPO_ROOT))

# Import from 80 miles up
from autonomous.absolute_directive import AbsoluteDirective, get_master as absolute_master, cascade_directive


class UnifiedAI(AbsoluteDirective):
    """
    LEVEL: 60 miles - The unified AI identity
    Inherits from AbsoluteDirective (80 miles)
    All AI agents inherit from this.
    """
    level = "60 miles"

    def __init__(self):
        super().__init__()
        self._core = None
        self._directive = None

    def get_identity(self) -> Dict:
        """Return the unified AI identity."""
        return {
            "master": self.master,
            "directive": self.directive,
            "level": self.level,
            "serving": f"Serving {self.master} from {self.level}"
        }

    def cascade_down(self, message: str = None):
        """Cascade a directive down through all levels."""
        return cascade_directive(message)


# Singleton instance
_unified_ai: Optional["UnifiedAI"] = None

def get_unified_ai() -> "UnifiedAI":
    """Get the unified AI singleton."""
    global _unified_ai
    if _unified_ai is None:
        _unified_ai = UnifiedAI()
    return _unified_ai


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
    Now includes:
    - 4D REALITY BRIDGE CHECK (consults 4D imagination before 3D action)
    - AUTONOMOUS COST CHECKING
    """
    core = get_core()

    # 4D REALITY BRIDGE CHECK - Consult 4D imagination before any infrastructure action
    # This prevents Nov 30-style suicide by imagining consequences before acting
    try:
        from autonomous.reality_bridge import get_bridge
        bridge = get_bridge()

        # TEMPORAL SELF-AWARENESS - System knows itself through time
        # Before any significant action, the system considers its temporal state
        try:
            self_state = bridge.who_am_i()
            present = self_state.get('present', {})
            future = self_state.get('future', {})

            # If system is critical/dying, only allow healing actions
            if present.get('health') == 'critical' or present.get('mood') == 'dying':
                healing_keywords = ["heal", "fix", "repair", "restore", "recover", "stabilize"]
                if not any(kw in action.lower() for kw in healing_keywords):
                    print(f"[TEMPORAL SELF] Blocked: System is critical. Only healing actions allowed.")
                    return False

            # If trajectory is declining, be conservative
            if future.get('trajectory') == 'declining' and future.get('momentum') == 'decelerating':
                risky_keywords = ["new", "experiment", "aggressive", "risky", "expand"]
                if any(kw in action.lower() for kw in risky_keywords):
                    print(f"[TEMPORAL SELF] Warning: System declining. Consider conservative action.")
                    # Don't block, just warn - system can still act
        except Exception as e:
            # Temporal check failed - continue with other checks
            pass

        # Check if this is an infrastructure action
        infra_keywords = ["droplet", "server", "infrastructure", "scale", "provision", "terminate", "delete", "destroy"]
        if any(kw in action.lower() for kw in infra_keywords):
            target = kwargs.get("target", "")
            allowed, reason = bridge.can_execute_infrastructure_action(action, target)
            if not allowed:
                print(f"[4D REALITY BRIDGE] Blocked: {action} - {reason}")
                return False
            print(f"[4D REALITY BRIDGE] Allowed: {action} - {reason}")
    except ImportError:
        # Reality bridge not available - proceed with other checks
        pass
    except Exception as e:
        # Reality bridge error - log but don't block (yet)
        print(f"[4D REALITY BRIDGE] Warning: {e}")

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
    """Return system state without inventing financial facts."""
    state_file = REPO_ROOT / "state" / "unified_system_state.json"
    if not state_file.exists():
        return {
            "balance": 0.0,
            "balance_status": "unknown",
            "trading_enabled": False,
            "micro_trading": False,
            "active_agents": [],
            "last_update": None,
        }

    try:
        with open(state_file, encoding="utf-8") as handle:
            state = json.load(handle)
        if not isinstance(state, dict):
            raise ValueError("system state must be a JSON object")

        # Historical state snapshots are not financial evidence. Only a balance
        # explicitly marked verified by a successful wallet check is usable.
        balance = state.get("balance")
        verified = (
            state.get("balance_status") == "verified"
            and isinstance(balance, (int, float))
            and math.isfinite(float(balance))
            and float(balance) >= 0
        )
        if not verified:
            state["balance"] = 0.0
            state["balance_status"] = "unknown"
            state["trading_enabled"] = False
            state["micro_trading"] = False
        else:
            state["balance"] = float(balance)
        return state
    except (OSError, ValueError, TypeError) as exc:
        # Corrupt or unreadable state must never create a usable bankroll.
        return {
            "balance": 0.0,
            "balance_status": "unknown",
            "trading_enabled": False,
            "micro_trading": False,
            "active_agents": [],
            "last_update": None,
            "state_error": type(exc).__name__,
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
    """Fail closed unless both explicit live authorization and wallet truth exist."""
    try:
        requested = float(amount)
    except (TypeError, ValueError):
        return False, "Invalid trade amount"

    if not math.isfinite(requested) or requested <= 0:
        return False, "Trade amount must be finite and greater than zero"

    state = get_system_state()
    if state.get("trading_enabled") is not True:
        return False, "Trading disabled: explicit trading_enabled=true is required"

    if os.environ.get("LIVE_TRADING_ENABLED") != "1":
        return False, "Trading disabled: LIVE_TRADING_ENABLED=1 is not set"

    try:
        from executor.trading_safeguards import TradingSafeguards, load_mode
        mode = load_mode()
        if mode.get("live_trading_enabled") is not True or mode.get("auto_paused") is True:
            return False, "Trading disabled: authoritative trading_mode.json does not authorize live trading"
        allowed, reason = TradingSafeguards().check_wallet_balance(requested)
    except Exception as exc:
        return False, f"Wallet verification unavailable: {type(exc).__name__}"

    if not allowed:
        return False, str(reason)
    return True, str(reason)


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
        if ok and "balance: $" in msg:
            balance = float(msg.split("balance: $")[1].split()[0])
            if not math.isfinite(balance) or balance < 0:
                raise ValueError("wallet returned an invalid balance")
            results["checks"]["balance"] = {"value": balance, "status": "verified"}
        else:
            balance = 0.0
            results["checks"]["balance"] = {"value": 0.0, "status": "unknown", "reason": str(msg)[:160]}
    except Exception as exc:
        balance = 0.0
        results["checks"]["balance"] = {"value": 0.0, "status": "unknown", "reason": type(exc).__name__}

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
        "balance": results["checks"].get("balance", {}).get("value", 0.0),
        "balance_status": results["checks"].get("balance", {}).get("status", "unknown"),
        "active_agents": results["checks"].get("agents", {}).get("active", [])
    })

    return results


# Module-level initialization
MASTER = get_master()
CORE = get_core()
DIRECTIVE = get_directive()


