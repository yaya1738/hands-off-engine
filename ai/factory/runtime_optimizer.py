from typing import Any, Dict


class FactoryRuntimeOptimizer:
    def __init__(
        self,
        runtime: Any,
        optimizer: Any,
    ):
        self.runtime = runtime
        self.optimizer = optimizer

    def optimize(self) -> Dict[str, Any]:
        health = self.runtime.status()

        history = self.runtime.controller.memory.recall_all()

        telemetry = {}

        return self.optimizer.run_cycle(
            health,
            history,
            telemetry,
        )
