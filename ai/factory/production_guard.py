from typing import Any, Dict, List


class FactoryProductionGuard:
    def __init__(self):
        self.safe = True
        self._history: List[Dict[str, Any]] = []

    def validate(
        self,
        config: Dict[str, Any],
    ):
        required = config.get(
            "required",
            True,
        )

        result = {
            "valid": bool(required),
            "status": (
                "READY"
                if required
                else "BLOCKED"
            ),
        }

        self._history.append(
            result
        )

        return result

    def safe_mode(self):
        self.safe = True

        result = {
            "mode": "SAFE",
        }

        self._history.append(
            result
        )

        return result

    def health_report(
        self,
    ):
        result = {
            "safe": self.safe,
            "status": "HEALTHY",
        }

        self._history.append(
            result
        )

        return result

    def history(self):
        return self._history
