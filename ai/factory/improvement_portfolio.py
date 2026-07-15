from typing import Any, Dict, List


class FactoryImprovementPortfolio:
    def __init__(self):
        self._initiatives: List[Dict[str, Any]] = []
        self._history: List[Dict[str, Any]] = []

    def add(
        self,
        initiative: Dict[str, Any],
    ):
        initiative.setdefault(
            "status",
            "PENDING",
        )

        self._initiatives.append(
            initiative
        )

        self._history.append(
            {
                "action": "ADD",
                "initiative": initiative,
            }
        )

        return initiative

    def update(
        self,
        name: str,
        changes: Dict[str, Any],
    ):
        for initiative in self._initiatives:
            if initiative.get(
                "name"
            ) == name:
                initiative.update(
                    changes
                )

                self._history.append(
                    {
                        "action": "UPDATE",
                        "initiative": initiative,
                    }
                )

                return initiative

        return None

    def prioritize(self):
        return sorted(
            self._initiatives,
            key=lambda item: item.get(
                "priority",
                0,
            ),
            reverse=True,
        )

    def active(self):
        return [
            initiative
            for initiative in self._initiatives
            if initiative.get(
                "status"
            ) == "ACTIVE"
        ]

    def history(self):
        return self._history
