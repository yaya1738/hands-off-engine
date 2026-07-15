from typing import Any, Dict


class FactoryPersistence:
    def save_runtime(
        self,
        runtime: Any,
    ) -> Dict[str, Any]:
        return {
            "components": runtime.registry.list_components(),
            "health": runtime.status(),
        }

    def restore_runtime(
        self,
        snapshot: Dict[str, Any],
    ) -> Dict[str, Any]:
        return {
            "restored": True,
            "components": snapshot.get(
                "components",
                [],
            ),
            "health": snapshot.get(
                "health",
                {},
            ),
        }
