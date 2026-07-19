import json
from datetime import datetime, timezone

from factory_introspection_execution_adapter import run as execution_run
from factory_introspection_extension_adapter import run as extension_run


REQUIRED = {
    "module_discovery",
    "function_signature_inspection",
    "method_signature_inspection",
    "safe_dynamic_probe",
}


def run():

    execution = execution_run()
    extension = extension_run()

    combined = set()

    extension_caps = extension.get(
        "extension_capabilities",
        {}
    )

    for key, value in extension_caps.items():
        if value:
            combined.add(key)


    missing = sorted(
        REQUIRED - combined
    )


    if not missing:
        decision = {
            "decision": "introspection_capability_complete",
            "action": "reuse_existing_system",
        }

    else:
        decision = {
            "decision": "introspection_capability_incomplete",
            "action": "create_only_missing_capabilities",
            "missing": missing,
        }


    return {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "component": "factory_introspection_capability_completion_verifier",
        "existing_tool": execution.get("decision"),
        "extension": extension_caps,
        "verification": decision,
    }


if __name__ == "__main__":
    print(json.dumps(run(), indent=2))
