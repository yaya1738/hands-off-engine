from typing import Any, Dict, List


class FactoryIntegrityChecker:
    def __init__(self):
        self._history: List[Dict[str, Any]] = []

    def check_runtime(self, runtime):
        checks = {}

        component_contracts = {
            "decision": [
                "select_action",
                "history",
            ],
            "feedback": [
                "analyze",
                "score",
                "history",
            ],
            "learning_loop": [
                "record_outcome",
                "analyze_feedback",
                "history",
            ],
            "adaptive_decision": [
                "decide",
                "learn",
                "history",
            ],
            "improvement_orchestrator": [],
            "development_pipeline": [],
            "strategy_manager": [],
            "resource_allocator": [],
        }

        for component, methods in component_contracts.items():
            instance = getattr(runtime, component, None)

            checks[component] = (
                instance is not None
                and all(
                    hasattr(instance, method)
                    for method in methods
                )
            )

        behavior = {}

        probes = {
            "decision": "history",
            "feedback": "history",
            "learning_loop": "history",
            "adaptive_decision": "history",
        }

        for component, method in probes.items():
            instance = getattr(runtime, component, None)

            try:
                value = getattr(instance, method)()
                behavior[component] = isinstance(value, list)
            except Exception:
                behavior[component] = False

        checks.update(
            {
                f"{component}_behavior": healthy
                for component, healthy in behavior.items()
            }
        )

        result = {
            "healthy": all(checks.values()),
            "checks": checks,
        }

        self._history.append(result)

        return result

    def history(self):
        return self._history
