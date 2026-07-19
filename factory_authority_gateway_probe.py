import json
from datetime import datetime, timezone

def run():
    result = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "component": "factory_authority_gateway_probe",
        "authority_points": {}
    }

    checks = {
        "goal_entry": [
            "submit_goal",
            "create_development_task",
            "register_goal"
        ],
        "construction_entry": [
            "run_development_cycle",
            "execute_task",
            "execute"
        ],
        "completion_entry": [
            "complete_reviewed_task",
            "complete_task",
            "register_artifact"
        ]
    }

    import pkgutil
    import importlib
    import inspect

    for module in pkgutil.walk_packages(["ai/factory"], "ai.factory."):
        try:
            mod = importlib.import_module(module.name)

            for name, obj in inspect.getmembers(mod):
                if inspect.isclass(obj):
                    methods = dir(obj)

                    for area, keys in checks.items():
                        found = [
                            k for k in keys
                            if k in methods
                        ]

                        if found:
                            result["authority_points"].setdefault(
                                area, []
                            ).append({
                                "module": module.name,
                                "class": name,
                                "matches": found
                            })

        except Exception:
            pass

    return result


if __name__ == "__main__":
    print(json.dumps(run(), indent=2))
