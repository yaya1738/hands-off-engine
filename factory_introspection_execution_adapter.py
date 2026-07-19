import json
import importlib
import subprocess
from datetime import datetime, timezone


TARGET_TOOL_KEYWORDS = [
    "inspect",
    "contract",
    "probe",
    "reflection",
    "introspect",
]


def discover_tools():
    result = subprocess.run(
        ["python", "factory_forensic_engine.py"],
        capture_output=True,
        text=True,
        timeout=120,
    )

    output = result.stdout
    start = output.find("{")

    if start == -1:
        return []

    try:
        report = json.loads(output[start:])
    except Exception:
        return []

    matches = []

    for tool in report.get("available_tools", []):
        name = tool.get("tool", "").lower()
        exports = " ".join(
            tool.get("exports", [])
        ).lower()

        combined = name + " " + exports

        if any(
            keyword in combined
            for keyword in TARGET_TOOL_KEYWORDS
        ):
            matches.append(tool)

    return matches


def inspect_tool(tool):

    module_name = tool.get("tool")

    if not module_name:
        return {
            "usable": False,
            "reason": "missing_module_name",
        }

    python_module = module_name.replace(".py", "")

    try:
        module = importlib.import_module(
            python_module
        )

    except Exception as e:
        return {
            "tool": module_name,
            "usable": False,
            "reason": "import_failed",
            "error": str(e),
        }


    exports = []

    for name in dir(module):
        if not name.startswith("_"):
            exports.append(name)


    useful_functions = [
        name
        for name in exports
        if any(
            keyword in name.lower()
            for keyword in [
                "inspect",
                "locate",
                "find",
                "contract",
                "class",
                "init",
            ]
        )
    ]


    return {
        "tool": module_name,
        "usable": True,
        "exports": exports,
        "useful_functions": useful_functions,
    }


def run():

    tools = discover_tools()

    inspected = [
        inspect_tool(tool)
        for tool in tools
    ]

    usable = [
        item
        for item in inspected
        if item.get("usable")
        and item.get("useful_functions")
    ]


    if usable:
        decision = {
            "decision": "reuse_existing_introspection_capability",
            "tools": usable,
        }

    else:
        decision = {
            "decision": "create_missing_probe_utility",
            "utility": {
                "name": "factory_introspection_probe.py",
                "purpose": [
                    "discover modules",
                    "discover classes",
                    "discover functions",
                    "inspect signatures",
                    "return normalized contracts",
                ],
            },
        }


    return {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "component": "factory_introspection_execution_adapter",
        "decision": decision,
    }


if __name__ == "__main__":
    print(json.dumps(run(), indent=2))
