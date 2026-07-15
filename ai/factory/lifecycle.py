from typing import Any, Dict


class FactoryLifecycle:
    def __init__(
        self,
        daemon: Any,
        persistence: Any,
    ):
        self.daemon = daemon
        self.persistence = persistence

    def startup(self) -> Dict[str, Any]:
        state = self.persistence.load()

        result = self.daemon.start()

        return {
            "startup": result,
            "restored_state": state,
        }

    def shutdown(
        self,
        state: Dict[str, Any],
    ) -> Dict[str, Any]:

        self.persistence.save(
            state
        )

        return self.daemon.stop()

    def recover(self):
        state = self.persistence.load()

        return {
            "recovered": state is not None,
            "state": state,
        }

    def status(self):
        return self.daemon.status()
