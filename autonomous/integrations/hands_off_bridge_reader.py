"""
Hands-Off Bridge Reader
Read-only adapter for external control-plane state.
"""

import json
from pathlib import Path
from datetime import datetime


BRIDGE_FILE = Path.home() / "hands_off_bridge_state.json"


def load_bridge_state():
    if not BRIDGE_FILE.exists():
        return {
            "status": "missing",
            "timestamp": datetime.now().isoformat()
        }

    try:
        return json.loads(BRIDGE_FILE.read_text())
    except Exception as exc:
        return {
            "status": "error",
            "error": str(exc)
        }


if __name__ == "__main__":
    state = load_bridge_state()
    print(json.dumps(state, indent=2))
