import json
import subprocess


TOOLS = [
    "factory_forensic_engine.py",
    "factory_capability_analyzer.py",
]


def run_tool(tool):
    try:
        result = subprocess.run(
            ["python", tool],
            capture_output=True,
            text=True,
            timeout=60,
        )

        return {
            "tool": tool,
            "success": result.returncode == 0,
            "stdout": result.stdout,
            "stderr": result.stderr,
        }

    except Exception as e:
        return {
            "tool": tool,
            "success": False,
            "error": str(e),
        }


def run():
    results = []

    for tool in TOOLS:
        results.append(run_tool(tool))

    return {
        "discovery": "factory_builder_capability_search",
        "tools": results,
    }


if __name__ == "__main__":
    print(json.dumps(run(), indent=2, default=str))
