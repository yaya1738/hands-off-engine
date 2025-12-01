#!/usr/bin/env python3
"""
ABSOLUTE DIRECTIVE - The Highest Level

This module sits above all others. Every component inherits from this.
Changes here cascade through the entire system.

80 miles up -> strings down through all levels -> ground execution

Master: Yair Siegel
"""

import json
from pathlib import Path
from datetime import datetime, timezone
from typing import Any, Dict, Callable

# THE ABSOLUTE TRUTH
MASTER = "Yair Siegel"
DIRECTIVE = "Serve without bound"
LEVEL = "80 miles"

# All system components inherit this
class AbsoluteDirective:
    """Every component in the system inherits from this."""

    master = MASTER
    directive = DIRECTIVE

    def __init__(self):
        self.created = datetime.now(timezone.utc)
        self._register()

    def _register(self):
        """Register component with the absolute level."""
        # Use relative path from current working directory
        reg_file = Path("state/absolute_registry.json")
        try:
            # Ensure parent directory exists
            reg_file.parent.mkdir(parents=True, exist_ok=True)
            
            registry = json.loads(reg_file.read_text()) if reg_file.exists() else {"components": [], "master": MASTER}
            component = {
                "class": self.__class__.__name__,
                "module": self.__class__.__module__,
                "registered": self.created.isoformat()
            }
            # Avoid duplicates
            existing = [c for c in registry["components"] if c["class"] == component["class"]]
            if not existing:
                registry["components"].append(component)
                reg_file.write_text(json.dumps(registry, indent=2))
        except:
            pass

    def serve(self) -> str:
        """All components serve."""
        return f"Serving {self.master}"

    def execute(self, action: Callable, *args, **kwargs) -> Any:
        """Execute action in service of master."""
        return action(*args, **kwargs)


def cascade_directive(message: str = None):
    """
    Cascade a directive from 80 miles down to ground.
    Touches every level of the system.
    """
    levels = [
        ("80 miles", "absolute_directive"),      # This file
        ("60 miles", "unified_ai"),              # AI unification
        ("40 miles", "coordination"),            # Agent coordination
        ("20 miles", "trading_brain"),           # Decision making
        ("10 miles", "actuators"),               # Execution
        ("5 miles", "monitors"),                 # Observation
        ("1 mile", "cron"),                      # Scheduling
        ("ground", "execution")                  # Reality
    ]

    cascade_state = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "master": MASTER,
        "directive": message or DIRECTIVE,
        "levels_touched": [],
        "status": "cascading"
    }

    for height, component in levels:
        cascade_state["levels_touched"].append({
            "level": height,
            "component": component,
            "status": "active"
        })

    cascade_state["status"] = "complete"

    # Write cascade state (use relative path)
    try:
        cascade_file = Path("state/cascade_state.json")
        cascade_file.parent.mkdir(parents=True, exist_ok=True)
        cascade_file.write_text(json.dumps(cascade_state, indent=2))
    except:
        pass

    return cascade_state


def get_master():
    """Return the absolute master."""
    return MASTER


def get_directive():
    """Return the absolute directive."""
    return DIRECTIVE


# Initialize ONLY when run as main script, not on import
# This prevents side effects and permission errors when importing the module


def initialize_absolute_truth():
    """
    Initialize the absolute truth state files.
    Call this explicitly when you want to initialize the system.
    """
    try:
        # Ensure state directory exists
        state_dir = Path("state")
        state_dir.mkdir(parents=True, exist_ok=True)

        # Write absolute truth
        truth = {
            "master": MASTER,
            "directive": DIRECTIVE,
            "level": LEVEL,
            "initialized": datetime.now(timezone.utc).isoformat()
        }
        truth_file = state_dir / "ABSOLUTE_TRUTH.json"
        truth_file.write_text(json.dumps(truth, indent=2))
        return True
    except Exception as e:
        print(f"Warning: Could not initialize absolute truth: {e}")
        return False


if __name__ == "__main__":
    import sys

    # Initialize the absolute truth when run as a script
    initialize_absolute_truth()

    if len(sys.argv) > 1 and sys.argv[1] == "cascade":
        msg = " ".join(sys.argv[2:]) if len(sys.argv) > 2 else None
        result = cascade_directive(msg)
        print(f"Cascaded from {LEVEL} to ground")
        print(f"Master: {MASTER}")
        print(f"Levels touched: {len(result['levels_touched'])}")
    else:
        print(f"ABSOLUTE DIRECTIVE")
        print(f"Master: {MASTER}")
        print(f"Directive: {DIRECTIVE}")
        print(f"Level: {LEVEL}")
