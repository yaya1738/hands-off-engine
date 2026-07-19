import json
from datetime import datetime, timezone


def extract_ready_state(obj):
    if isinstance(obj, dict):
        if obj.get("status") == "ready_for_review":
            return obj
        for value in obj.values():
            found = extract_ready_state(value)
            if found:
                return found
    elif isinstance(obj, list):
        for item in obj:
            found = extract_ready_state(item)
            if found:
                return found
    return None


def run():
    report = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "component": "factory_review_completion_activation_test",
        "checks": {}
    }

    # Generate a lifecycle object
    try:
        from factory_construction_router import run as router_run

        lifecycle = router_run(
            "activation test capability"
        )

        report["checks"]["construction"] = {
            "status": "available",
            "lifecycle_created": True
        }

    except Exception as e:
        report["checks"]["construction"] = {
            "status": "failed",
            "error": str(e)
        }
        return report


    ready = extract_ready_state(lifecycle)

    report["checks"]["review_state"] = {
        "found": bool(ready),
        "state": ready
    }


    # Completion bridge
    try:
        from factory_completion_wiring_adapter import run as completion_run

        adapter = completion_run()

        report["checks"]["completion_adapter"] = {
            "status": "available",
            "methods": adapter.get("available_methods", [])
        }

    except Exception as e:
        report["checks"]["completion_adapter"] = {
            "status": "missing",
            "error": str(e)
        }


    # Registration capability
    registration = False

    try:
        from ai.factory.artifact_registry import FactoryArtifactRegistry

        registry = FactoryArtifactRegistry()

        registration = hasattr(
            registry,
            "register_artifact"
        )

    except Exception:
        pass


    report["checks"]["artifact_registration"] = {
        "available": registration
    }


    if (
        ready
        and report["checks"]["completion_adapter"].get("status") == "available"
        and registration
    ):
        report["decision"] = {
            "status": "PASS",
            "action": "review_completion_path_available"
        }
    else:
        report["decision"] = {
            "status": "INCOMPLETE",
            "action": "missing_review_completion_link"
        }


    return report


if __name__ == "__main__":
    print(json.dumps(run(), indent=2))
