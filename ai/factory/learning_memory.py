from typing import Any, Dict, List


class FactoryLearningMemory:
    def __init__(self):
        self.memory: List[Dict[str, Any]] = []
        self._history: List[Dict[str, Any]] = []

    def remember(
        self,
        experience: Dict[str, Any],
    ):
        self.memory.append(
            experience
        )

        result = {
            "stored": True,
            "experience": experience,
        }

        self._history.append(
            result
        )

        return result

    def record_outcome(
        self,
        outcome: Dict[str, Any],
    ):
        entry = {
            "type": "OUTCOME",
            "data": outcome,
        }

        self.memory.append(
            entry
        )

        self._history.append(
            entry
        )

        return entry

    def retrieve(
        self,
        key: str = None,
    ):
        if key is None:
            result = self.memory

        else:
            result = [
                item
                for item in self.memory
                if key in str(item)
            ]

        self._history.append(
            {
                "retrieved": result,
            }
        )

        return result

    def patterns(self):
        result = {
            "count": len(
                self.memory
            ),
        }

        self._history.append(
            result
        )

        return result

    def history(self):
        return self._history


    def store(
        self,
        item,
    ):
        if not hasattr(self, "_memory"):
            self._memory = []

        self._memory.append(item)

        return item


    def history(self):
        return self._history
