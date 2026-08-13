from typing import Any, Dict, List

from ai.factory.execution_reconciler import FactoryExecutionReconciler


class FactoryRestartReconciliation:
    """Startup-safe reconciliation hook; never replays ambiguous executions."""

    def __init__(self, reconciler: FactoryExecutionReconciler):
        self.reconciler = reconciler

    def on_startup(self) -> Dict[str, Any]:
        candidates: List[Dict[str, Any]] = self.reconciler.inspect()
        return {
            "status": "startup_reconciliation_complete",
            "ambiguous_count": len(candidates),
            "ambiguous_executions": candidates,
            "replay_performed": False,
        }
