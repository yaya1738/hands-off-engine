"""Read-only compatibility facade for the legacy self-repair pipeline.

Execution of local factory tools is governed by FactoryAuthorityGateway.
"""
import json
from datetime import datetime, timezone


def run_tool(command):
    return {
        "command": command,
        "success": False,
        "stdout": "",
        "stderr": "[FACTORY-AUTHORITY] direct tool execution is disabled; submit through FactoryAuthorityGateway",
        "authority_required": True,
    }


def parse_json_output(result):
    try:
        return json.loads(result.get("stdout", ""))
    except Exception:
        return {"raw_output": result.get("stdout", ""), "parse_error": True}


def run_pipeline(goal):
    return {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "goal": goal,
        "stages": [],
        "decision": "validation_requires_authority",
        "authority": "FactoryAuthorityGateway",
        "disabled": True,
    }


if __name__ == "__main__":
    import sys
    goal = " ".join(sys.argv[1:]) or "create automatic program builder"
    print(json.dumps(run_pipeline(goal), indent=2))
