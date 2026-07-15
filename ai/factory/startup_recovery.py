from typing import Any, Dict, List


class FactoryStartupRecovery:
    def __init__(self, state_store):
        self.state_store = state_store
        self._history: List[Dict[str, Any]] = []

    def restore(self):
        state = self.state_store.load()

        result = {
            "status": "RESTORED",
            "state": state,
        }

        self._history.append(result)

        return result

    def validate(
        self,
        state: Dict[str, Any],
    ):
        valid = isinstance(
            state,
            dict,
        )

        result = {
            "status": (
                "VALID"
                if valid
                else "INVALID"
            ),
            "valid": valid,
        }

        self._history.append(result)

        return result

    def startup(self):
        restored = self.restore()

        validation = self.validate(
            restored["state"]
        )

        result = {
            "status": (
                "READY"
                if validation["valid"]
                else "FAILED"
            ),
            "state": restored["state"],
        }

        self._history.append(result)

        return result

    def history(self):
        return self._history
