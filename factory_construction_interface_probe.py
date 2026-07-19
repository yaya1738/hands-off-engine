import json
import inspect
import importlib
from datetime import datetime, timezone

TARGETS = [
    "ai.factory.development_orchestrator",
    "ai.factory.development_executor",
    "ai.factory.development_pipeline",
    "ai.factory.artifact_registry",
]

KEYWORDS = [
    "create",
    "build",
    "develop",
    "execute",
    "run",
    "register",
    "artifact",
    "task",
]


def inspect_module(module_name):
    result = {
        "module": module_name,
        "classes": []
    }

    try:
        module = importlib.import_module(module_name)

        for name, obj in inspect.getmembers(module, inspect.isclass):

            if not obj.__module__ == module_name:
                continue

            methods = []

            for method_name, method in inspect.getmembers(obj, inspect.isfunction):
                if any(k in method_name.lower() for k in KEYWORDS):
                    try:
                        signature = str(inspect.signature(method))
                    except Exception:
                        signature = "unknown"

                    methods.append({
                        "name": method_name,
                        "signature": signature
                    })

            result["classes"].append({
                "class": name,
                "methods": methods
            })

    except Exception as e:
        result["error"] = str(e)

    return result


def run():
    return {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "component": "factory_construction_interface_probe",
        "interfaces": [
            inspect_module(t)
            for t in TARGETS
        ]
    }


if __name__ == "__main__":
    print(json.dumps(run(), indent=2))
