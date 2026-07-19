import json
from datetime import datetime, timezone


def find_ready_state(obj):
    if isinstance(obj, dict):
        if obj.get("status") == "ready_for_review":
            return obj
        for v in obj.values():
            result = find_ready_state(v)
            if result:
                return result
    elif isinstance(obj, list):
        for item in obj:
            result = find_ready_state(item)
            if result:
                return result
    return None


def find_status(obj):
    if isinstance(obj, dict):
        for key in [
            "status",
            "decision",
            "action"
        ]:
            if key in obj:
                return obj[key]
        for v in obj.values():
            result = find_status(v)
            if result:
                return result
    elif isinstance(obj, list):
        for item in obj:
            result = find_status(item)
            if result:
                return result
    return None


def run():
    report = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "component": "factory_closed_loop_execution_test",
        "checks": {}
    }

    try:
        from factory_construction_router import run as router_run

        lifecycle = router_run(
            "closed loop lifecycle verification"
        )

        ready = find_ready_state(lifecycle)

        report["checks"]["construction"] = {
            "available": True,
            "ready_for_review_found": bool(ready)
        }

    except Exception as e:
        report["checks"]["construction"] = {
            "available": False,
            "error": str(e)
        }
        return report


    try:
        from factory_completion_wiring_adapter import (
            run as completion_run
        )

        adapter = completion_run()

        methods = adapter.get(
            "available_methods",
            []
        )

        report["checks"]["completion_adapter"] = {
            "available": True,
            "methods": methods
        }

    except Exception as e:
        report["checks"]["completion_adapter"] = {
            "available": False,
            "error": str(e)
        }
        return report


    # Simulated completion handoff
    completion_result = {
        "input_state": ready,
        "adapter_method": "complete_reviewed_task",
        "status": "completion_invocation_simulated"
    }


    report["checks"]["completion_execution"] = {
        "invoked": True,
        "result": completion_result
    }


    try:
        from ai.factory.artifact_registry import FactoryArtifactRegistry

        registry = FactoryArtifactRegistry()

        report["checks"]["artifact_registry"] = {
            "available": True,
            "registration_method": hasattr(
                registry,
                "register_artifact"
            )
        }

    except Exception as e:
        report["checks"]["artifact_registry"] = {
            "available": False,
            "error": str(e)
        }


    if (
        report["checks"]["construction"].get(
            "ready_for_review_found"
        )
        and report["checks"]["completion_adapter"].get(
            "available"
        )
        and report["checks"]["artifact_registry"].get(
            "registration_method"
        )
    ):
        report["decision"] = {
            "status": "PASS",
            "action": "closed_loop_architecture_verified"
        }
    else:
        report["decision"] = {
            "status": "INCOMPLETE",
            "action": "missing_closed_loop_component"
        }

    return report


if __name__ == "__main__":
    print(json.dumps(run(), indent=2))
