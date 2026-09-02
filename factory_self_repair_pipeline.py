import json
import subprocess
import sys
from datetime import datetime, timezone


def run_tool(command):
    """Run a fixed executable/argument vector without shell interpretation."""
    result = subprocess.run(
        command,
        shell=False,
        capture_output=True,
        text=True,
    )

    return {
        "command": command,
        "success": result.returncode == 0,
        "stdout": result.stdout,
        "stderr": result.stderr,
    }


def parse_json_output(result):
    try:
        return json.loads(result["stdout"])
    except Exception:
        return {
            "raw_output": result["stdout"],
            "parse_error": True,
        }


def run_pipeline(goal):
    stages = []

    tools = [
        [sys.executable, "factory_capability_composer.py", goal],
        [sys.executable, "factory_capability_binding_executor.py", goal],
        [sys.executable, "factory_capability_execution_bridge.py", goal],
        [sys.executable, "factory_capability_validation_bridge.py", goal],
    ]

    for tool in tools:
        result = run_tool(tool)
        stages.append(parse_json_output(result))

    decision = "unknown"

    if stages:
        last = stages[-1]

        if isinstance(last, dict):
            if last.get("decision") == "validated":
                decision = "validated"
            elif "validation_pipeline" in last:
                decision = "validation_detected"

    return {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "goal": goal,
        "stages": stages,
        "decision": decision,
    }


if __name__ == "__main__":
    goal = " ".join(sys.argv[1:])

    if not goal:
        goal = "create automatic program builder"

    print(json.dumps(
        run_pipeline(goal),
        indent=2,
        default=str,
    ))
