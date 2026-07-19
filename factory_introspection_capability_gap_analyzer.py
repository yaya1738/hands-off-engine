import json
from datetime import datetime, timezone
from factory_introspection_execution_adapter import run as run_adapter


REQUIRED_CAPABILITIES = {
    "module_discovery": False,
    "class_discovery": False,
    "constructor_analysis": False,
    "method_signature_inspection": False,
    "function_signature_inspection": False,
    "normalized_json_contract": False,
    "safe_dynamic_probe": False,
}


def analyze_tool(tool):
    capabilities = REQUIRED_CAPABILITIES.copy()

    exports = [
        x.lower()
        for x in tool.get("exports", [])
    ]

    useful = [
        x.lower()
        for x in tool.get("useful_functions", [])
    ]

    combined = exports + useful

    if "locate_class" in combined:
        capabilities["class_discovery"] = True

    if "find_init_args" in combined:
        capabilities["constructor_analysis"] = True

    if any(
        "signature" in x or "inspect" in x
        for x in combined
    ):
        capabilities["method_signature_inspection"] = True
        capabilities["function_signature_inspection"] = True

    if "json" in combined:
        capabilities["normalized_json_contract"] = True

    return capabilities


def run():

    adapter_result = run_adapter()

    tools = adapter_result["decision"].get(
        "tools",
        []
    )

    if tools:

        gaps = []

        for tool in tools:
            capabilities = analyze_tool(tool)

            gaps.extend(
                [
                    name
                    for name, value in capabilities.items()
                    if not value
                ]
            )

        gaps = sorted(set(gaps))

        if gaps:
            decision = {
                "decision": "extend_existing_introspection_capability",
                "missing_capabilities": gaps,
            }

        else:
            decision = {
                "decision": "existing_introspection_capability_complete",
            }

    else:
        decision = {
            "decision": "create_new_introspection_probe",
        }


    return {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "component": "factory_introspection_capability_gap_analyzer",
        "decision": decision,
    }


if __name__ == "__main__":
    print(json.dumps(run(), indent=2))
