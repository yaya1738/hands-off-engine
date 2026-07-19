import json
from datetime import datetime, timezone


def safe_import(module, name):
    try:
        mod = __import__(module, fromlist=[name])
        return getattr(mod, name)
    except Exception as e:
        return None, str(e)


def run():
    report = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "component": "factory_construction_lifecycle_simulator",
        "simulation": {}
    }

    # Router
    try:
        from factory_construction_router import run as router_run

        router_result = router_run(
            "dry run create lifecycle verification utility"
        )

        report["simulation"]["router"] = {
            "status": "executed",
            "result": router_result
        }

    except Exception as e:
        report["simulation"]["router"] = {
            "status": "failed",
            "error": str(e)
        }


    # Check construction organs
    organs = {}

    targets = [
        (
            "development_orchestrator",
            "ai.factory.development_orchestrator",
            "FactoryDevelopmentOrchestrator"
        ),
        (
            "development_executor",
            "ai.factory.development_executor",
            "FactoryDevelopmentExecutor"
        ),
        (
            "artifact_registry",
            "ai.factory.artifact_registry",
            "FactoryArtifactRegistry"
        ),
        (
            "runtime",
            "ai.factory.runtime",
            "FactoryRuntime"
        ),
    ]

    for key, module, cls in targets:
        obj = safe_import(module, cls)

        if isinstance(obj, tuple):
            organs[key] = {
                "status": "missing",
                "error": obj[1]
            }
        else:
            organs[key] = {
                "status": "available",
                "class": cls
            }

    report["simulation"]["organs"] = organs


    # Completion adapter
    try:
        from factory_completion_wiring_adapter import run as completion_run

        report["simulation"]["completion"] = {
            "status": "available",
            "result": completion_run()
        }

    except Exception as e:
        report["simulation"]["completion"] = {
            "status": "missing",
            "error": str(e)
        }


    failures = []

    for name, data in organs.items():
        if data["status"] != "available":
            failures.append(name)

    if report["simulation"]["completion"]["status"] != "available":
        failures.append("completion_adapter")


    if failures:
        report["decision"] = {
            "status": "INCOMPLETE",
            "action": "missing_lifecycle_links",
            "missing": failures
        }
    else:
        report["decision"] = {
            "status": "PASS",
            "action": "construction_lifecycle_ready_for_activation_test"
        }

    return report


if __name__ == "__main__":
    print(json.dumps(run(), indent=2))
