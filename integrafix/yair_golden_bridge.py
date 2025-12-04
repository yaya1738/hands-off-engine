#!/usr/bin/env python3
"""
INTEGRAFIX: Yair Golden Bridge
==============================

THE GOLDEN CONNECTION: Yair ↔ System

This bridge makes Claude the interface between Yair and the trading system.
When Yair speaks naturally, Claude interprets and wires it into the system.

NO FRICTION. NO FORMS. JUST TALK.

Usage:
    from integrafix.yair_golden_bridge import golden_bridge
    
    # Yair says something, Claude interprets it
    golden_bridge.process("Bitcoin gonna pump, like 80% chance it hits 110k")
    golden_bridge.process("Don't trade sports, I don't know sports")
    golden_bridge.process("Max $30 per trade")

Serving: Yair Siegel
"""

import json
import re
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any

PROJECT_ROOT = Path(__file__).parent.parent
STATE_DIR = PROJECT_ROOT / "state"
GOLDEN_STATE = STATE_DIR / "yair_golden_bridge.json"
KERNEL_FILE = STATE_DIR / "yair_context_kernel.json"
ESTIMATES_FILE = STATE_DIR / "human_probability_estimates.json"


class YairGoldenBridge:
    """
    Golden bridge between Yair's natural language and the trading system.
    
    Claude interprets Yair's words and wires them into the system.
    """
    
    def __init__(self):
        self.state = self._load_state()
    
    def _load_state(self) -> Dict:
        if GOLDEN_STATE.exists():
            with open(GOLDEN_STATE) as f:
                return json.load(f)
        return {
            "created_at": datetime.now(timezone.utc).isoformat(),
            "estimates": {},
            "preferences": {},
            "rules": {},
            "history": []
        }
    
    def _save_state(self):
        self.state["updated_at"] = datetime.now(timezone.utc).isoformat()
        with open(GOLDEN_STATE, 'w') as f:
            json.dump(self.state, f, indent=2)
        self._sync_to_kernel()
        self._sync_to_estimates()
    
    def _sync_to_kernel(self):
        """Sync state to yair_context_kernel.json"""
        kernel = {
            "master": "Yair Siegel",
            "updated_at": datetime.now(timezone.utc).isoformat(),
            "active_estimates": self.state.get("estimates", {}),
            "risk_preferences": self.state.get("preferences", {}),
            "trading_rules": self.state.get("rules", {}),
            "golden_bridge": True
        }
        with open(KERNEL_FILE, 'w') as f:
            json.dump(kernel, f, indent=2)
    
    def _sync_to_estimates(self):
        """Sync estimates to human_probability_estimates.json"""
        data = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "source": "yair_golden_bridge",
            "estimates": self.state.get("estimates", {})
        }
        with open(ESTIMATES_FILE, 'w') as f:
            json.dump(data, f, indent=2)
    
    # ==================== CORE METHODS ====================
    
    def set_estimate(self, market_id: str, probability: float, notes: str = "") -> Dict:
        """Set a probability estimate for a market."""
        self.state["estimates"][market_id] = probability
        self.state["history"].append({
            "type": "estimate",
            "market": market_id,
            "probability": probability,
            "notes": notes,
            "timestamp": datetime.now(timezone.utc).isoformat()
        })
        self._save_state()
        return {"success": True, "market": market_id, "probability": probability}
    
    def set_preference(self, key: str, value: Any) -> Dict:
        """Set a trading preference."""
        self.state["preferences"][key] = value
        self.state["history"].append({
            "type": "preference",
            "key": key,
            "value": value,
            "timestamp": datetime.now(timezone.utc).isoformat()
        })
        self._save_state()
        return {"success": True, "preference": key, "value": value}
    
    def set_rule(self, key: str, value: Any) -> Dict:
        """Set a trading rule."""
        self.state["rules"][key] = value
        self.state["history"].append({
            "type": "rule",
            "key": key,
            "value": value,
            "timestamp": datetime.now(timezone.utc).isoformat()
        })
        self._save_state()
        return {"success": True, "rule": key, "value": value}
    
    def get_status(self) -> Dict:
        """Get current bridge status."""
        return {
            "estimates_count": len(self.state.get("estimates", {})),
            "estimates": self.state.get("estimates", {}),
            "preferences": self.state.get("preferences", {}),
            "rules": self.state.get("rules", {}),
            "history_count": len(self.state.get("history", []))
        }
    
    def clear_all(self):
        """Clear all data (reset)."""
        self.state = {
            "created_at": datetime.now(timezone.utc).isoformat(),
            "estimates": {},
            "preferences": {},
            "rules": {},
            "history": []
        }
        self._save_state()
        return {"success": True, "message": "All data cleared"}


# Global instance
_bridge: Optional[YairGoldenBridge] = None

def get_golden_bridge() -> YairGoldenBridge:
    global _bridge
    if _bridge is None:
        _bridge = YairGoldenBridge()
    return _bridge

# Convenience alias
golden_bridge = get_golden_bridge()


if __name__ == "__main__":
    bridge = get_golden_bridge()
    print(json.dumps(bridge.get_status(), indent=2))
