from typing import Any, Dict


class FactoryDaemon:
    def __init__(
        self,
        service: Any,
        state_stream: Any = None,
        optimizer: Any = None,
    ):
        self.service = service
        self.state_stream = state_stream
        self.optimizer = optimizer
        self.running = False

    def start(self) -> Dict[str, Any]:
        self.running = True

        return {
            "status": "started",
        }

    def stop(self) -> Dict[str, Any]:
        self.running = False

        return {
            "status": "stopped",
        }

    def status(self) -> Dict[str, Any]:
        return {
            "running": self.running,
        }

    def tick(self):
        if not self.running:
            return {
                "status": "inactive",
            }

        result = {
            "status": "active",
        }

        if self.optimizer:
            result["optimization"] = (
                self.optimizer.optimize()
            )

        if self.state_stream:
            self.state_stream.publish_state(
                result
            )

        return result
