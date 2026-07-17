from typing import Any, Dict, List


class FactoryIntegrityChecker:
    def __init__(self):
        self._history: List[Dict[str, Any]] = []

    def check_runtime(self, runtime):
        checks = {}

        required_components = [
            "decision",
            "feedback",
            "learning_loop",
            "adaptive_decision",
            "improvement_orchestrator",
            "development_pipeline",
            "strategy_manager",
            "resource_allocator",
        ]

        for component in required_components:
            checks[component] = hasattr(runtime, component)

        result = {
            "healthy": all(checks.values()),
            "checks": checks,
        }

        self._history.append(result)

        return result

    def history(self):
        return self._history
