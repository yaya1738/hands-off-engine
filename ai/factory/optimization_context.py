from typing import Any, Dict


class OptimizationContext:
    def build(
        self,
        health: Dict[str, Any],
        metrics: Dict[str, Any],
        history: Any,
        state: Dict[str, Any],
    ) -> Dict[str, Any]:
        return {
            "health": health,
            "metrics": metrics,
            "history": history,
            "state": state,
        }
