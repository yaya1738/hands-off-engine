"""
Hands-Off Bridge Health Monitor
Read-only status integration.
"""

from pathlib import Path
import json
from datetime import datetime


BRIDGE = Path.home() / "hands_off_bridge_state.json"


class HandsOffBridgeHealth:

    def check(self):
        result = {
            "component": "hands_off_bridge",
            "time": datetime.now().isoformat(),
        }

        if not BRIDGE.exists():
            result["status"] = "missing"
            return result

        try:
            data = json.loads(BRIDGE.read_text())
            result["status"] = "healthy"
            result["keys"] = list(data.keys())
        except Exception as exc:
            result["status"] = "error"
            result["error"] = str(exc)

        return result


if __name__ == "__main__":
    print(json.dumps(
        HandsOffBridgeHealth().check(),
        indent=2
    ))
