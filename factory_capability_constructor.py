import json
import subprocess
import sys
from pathlib import Path
from datetime import datetime, timezone


OUTPUT = Path("factory_capability_constructor_report.json")


TOOLS = [
    "factory_forensic_engine.py",
    "factory_artifact_registry.py",
    "factory_capability_analyzer.py",
    "factory_architecture_audit.py",
    "factory_capability_decision_engine.py",
    "factory_capability_integration_planner.py",
    "factory_capability_safety_gate.py",
]


def run_tool(tool):
    try:
        result = subprocess.run(
            ["python", tool],
            capture_output=True,
            text=True,
        )

        return {
            "tool": tool,
            "success": result.returncode == 0,
            "stdout": result.stdout[-2000:],
            "stderr": result.stderr[-1000:],
        }

    except Exception as e:
        return {
            "tool": tool,
            "success": False,
            "error": str(e),
        }


def build_capability(goal):

    report = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "goal": goal,
        "mode": "compose_existing_capabilities",
        "tools": [],
    }

    for tool in TOOLS:
        if Path(tool).exists():
            report["tools"].append(
                run_tool(tool)
            )

    report["decision"] = {
        "action": "analyze_existing_factory_capabilities",
        "next_step": "integration_planning",
    }

    OUTPUT.write_text(
        json.dumps(report, indent=2)
    )

    return report


def main():
    goal = " ".join(sys.argv[1:]) or "unknown capability"

    print(
        json.dumps(
            build_capability(goal),
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
