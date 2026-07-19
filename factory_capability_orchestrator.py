from pathlib import Path
import json
import importlib


OUTPUT = Path("factory_capability_orchestration_result.json")


TOOLS = [
    "factory_capability_analyzer",
    "factory_capability_decision_engine",
    "factory_capability_integration_planner",
    "factory_execution_binding_planner",
    "factory_capability_safety_gate",
    "factory_artifact_registry",
]


def load_tool(name):
    try:
        return importlib.import_module(name)
    except Exception as e:
        return {
            "error": str(e)
        }


def inspect_existing_capabilities():
    result = []

    for tool in TOOLS:
        module = load_tool(tool)

        if isinstance(module, dict):
            result.append({
                "tool": tool,
                "loaded": False,
                "error": module["error"],
            })
            continue

        exported = [
            x for x in dir(module)
            if not x.startswith("_")
        ]

        result.append({
            "tool": tool,
            "loaded": True,
            "exports": exported,
        })

    return result


def decide(request):
    capabilities = inspect_existing_capabilities()

    available = [
        x["tool"]
        for x in capabilities
        if x["loaded"]
    ]

    decision = {
        "request": request,
        "available_tools": available,
        "action": None,
        "reason": None,
    }

    if available:
        decision["action"] = "compose_existing_capabilities"
        decision["reason"] = (
            "Existing factory tools available. "
            "Do not create new tool yet."
        )
    else:
        decision["action"] = "create_new_capability"
        decision["reason"] = (
            "No usable existing capability detected."
        )

    return decision


def main():

    request = {
        "goal": (
            "automatically validate and manage "
            "factory phase transitions"
        )
    }

    result = {
        "capability_scan": inspect_existing_capabilities(),
        "decision": decide(request),
    }

    OUTPUT.write_text(
        json.dumps(
            result,
            indent=2,
        )
    )

    print(
        json.dumps(
            result,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
