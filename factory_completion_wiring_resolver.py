import json
import inspect
from datetime import datetime, timezone

TARGET_STATES = [
    "ready_for_review",
    "complete",
    "completed",
    "register",
    "verify",
    "approve"
]


MODULES = [
    "ai.factory.development_orchestrator",
    "ai.factory.development_executor",
    "ai.factory.artifact_registry",
    "ai.factory.verification_registry",
    "ai.factory.runtime",
]


def inspect_modules():

    found = []

    for module_name in MODULES:
        try:
            module = __import__(
                module_name,
                fromlist=["*"]
            )

            for name in dir(module):
                obj = getattr(module, name)

                if inspect.isclass(obj):

                    methods = []

                    for method in dir(obj):
                        if any(
                            x in method.lower()
                            for x in TARGET_STATES
                        ):
                            methods.append(method)

                    if methods:
                        found.append({
                            "module": module_name,
                            "class": name,
                            "methods": methods
                        })

        except Exception:
            pass

    return found


def run():

    matches = inspect_modules()

    if matches:

        decision = {
            "decision":
            "existing_completion_wiring_candidates_found",
            "action":
            "create_adapter_using_existing_components"
        }

    else:

        decision = {
            "decision":
            "no_completion_components_found",
            "action":
            "request_new_completion_bridge"
        }

    return {
        "timestamp":
        datetime.now(timezone.utc).isoformat(),
        "component":
        "factory_completion_wiring_resolver",
        "decision":
        decision,
        "matches":
        matches
    }


if __name__ == "__main__":
    print(json.dumps(run(), indent=2))
